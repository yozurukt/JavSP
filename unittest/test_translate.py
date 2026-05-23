import os
import sys

import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import javsp.web.translate as translate_mod


class FakeResponse:
    def __init__(self, status_code=200, body=None, reason="OK"):
        self.status_code = status_code
        self._body = body
        self.reason = reason

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


def test_openai_translate_preserves_actress_names(monkeypatch):
    requests_seen = []

    def fake_post(url, headers, json, timeout):
        requests_seen.append(json)
        return FakeResponse(
            body={
                "choices": [
                    {
                        "message": {"content": "__JAVSP_NAME_0__ 的翻译"},
                        "finish_reason": "stop",
                    }
                ]
            }
        )

    monkeypatch.setattr(translate_mod.requests, "post", fake_post)

    result = translate_mod.openai_translate(
        "葵つかさ の紹介",
        "https://api.example.test/v1/chat/completions",
        "key",
        "model",
        actress=["葵つかさ"],
    )

    assert result == "葵つかさ 的翻译"
    user_message = requests_seen[0]["messages"][1]["content"]
    assert "__JAVSP_NAME_0__" in user_message
    assert "葵つかさ" not in user_message


def test_openai_translate_retries_retryable_http_error(monkeypatch):
    responses = [
        FakeResponse(
            status_code=500,
            body={"error": {"message": "temporary failure"}},
            reason="Server Error",
        ),
        FakeResponse(
            body={
                "choices": [
                    {
                        "message": {"content": "翻译结果"},
                        "finish_reason": "stop",
                    }
                ]
            }
        ),
    ]
    monkeypatch.setattr(translate_mod.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(translate_mod, "OPENAI_RETRY_BASE_DELAY", 0)
    monkeypatch.setattr(
        translate_mod.requests,
        "post",
        lambda *args, **kwargs: responses.pop(0),
    )

    result = translate_mod.openai_translate(
        "本文",
        "https://api.example.test/v1/chat/completions",
        "key",
        "model",
    )

    assert result == "翻译结果"
    assert responses == []


def test_openai_translate_extracts_error_json(monkeypatch):
    def fake_post(url, headers, json, timeout):
        return FakeResponse(
            status_code=400,
            body={"error": {"message": "bad request detail"}},
            reason="Bad Request",
        )

    monkeypatch.setattr(translate_mod.requests, "post", fake_post)

    result = translate_mod.openai_translate(
        "本文",
        "https://api.example.test/v1/chat/completions",
        "key",
        "model",
    )

    assert result == {"error_code": 400, "error_msg": "bad request detail"}


def test_openai_translate_detects_truncated_response(monkeypatch):
    def fake_post(url, headers, json, timeout):
        return FakeResponse(
            body={
                "choices": [
                    {
                        "message": {"content": "被截断"},
                        "finish_reason": "length",
                    }
                ]
            }
        )

    monkeypatch.setattr(translate_mod.requests, "post", fake_post)

    result = translate_mod.openai_translate(
        "本文",
        "https://api.example.test/v1/chat/completions",
        "key",
        "model",
    )

    assert result["error_code"] == "length"


def test_openai_translate_retries_request_exception(monkeypatch):
    calls = []

    def fake_post(url, headers, json, timeout):
        calls.append(1)
        if len(calls) == 1:
            raise requests.exceptions.Timeout("timeout")
        return FakeResponse(
            body={
                "choices": [
                    {
                        "message": {"content": "翻译结果"},
                        "finish_reason": "stop",
                    }
                ]
            }
        )

    monkeypatch.setattr(translate_mod.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(translate_mod, "OPENAI_RETRY_BASE_DELAY", 0)
    monkeypatch.setattr(translate_mod.requests, "post", fake_post)

    result = translate_mod.openai_translate(
        "本文",
        "https://api.example.test/v1/chat/completions",
        "key",
        "model",
    )

    assert result == "翻译结果"
    assert len(calls) == 2


def test_openai_translate_supports_responses_endpoint(monkeypatch):
    requests_seen = []

    def fake_post(url, headers, json, timeout):
        requests_seen.append(json)
        return FakeResponse(
            body={
                "status": "completed",
                "error": None,
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": "__JAVSP_NAME_0__ 的翻译",
                            }
                        ],
                    }
                ],
            }
        )

    monkeypatch.setattr(translate_mod.requests, "post", fake_post)

    result = translate_mod.openai_translate(
        "葵つかさ の紹介",
        "https://api.example.test/v1/responses",
        "key",
        "model",
        actress=["葵つかさ"],
    )

    assert result == "葵つかさ 的翻译"
    assert requests_seen[0]["input"] == "__JAVSP_NAME_0__ の紹介"
    assert "instructions" in requests_seen[0]
    assert "max_output_tokens" in requests_seen[0]
    assert "messages" not in requests_seen[0]
    assert "max_tokens" not in requests_seen[0]


def test_openai_translate_detects_incomplete_responses_response(monkeypatch):
    def fake_post(url, headers, json, timeout):
        return FakeResponse(
            body={
                "status": "incomplete",
                "error": None,
                "incomplete_details": {"reason": "max_output_tokens"},
                "output": [],
            }
        )

    monkeypatch.setattr(translate_mod.requests, "post", fake_post)

    result = translate_mod.openai_translate(
        "本文",
        "https://api.example.test/v1/responses",
        "key",
        "model",
    )

    assert result["error_code"] == "max_output_tokens"
