# Repository Guidelines

## Project Structure & Module Organization

JavSP is a Poetry-managed Python package. Core source lives in `javsp/`: `__main__.py` provides the CLI entry point, `web/` contains site-specific crawlers, `cropper/` contains cover-cropping code, and shared helpers include `config.py`, `file.py`, `image.py`, `nfo.py`, and `avid.py`. Tests live in `unittest/`; crawler fixtures are JSON files in `unittest/data/` named like `IPX-177 (javdb).json`. Static runtime data is in `data/`, images and icons are in `image/`, packaging support is in `setup.py`, and Docker files are in `docker/`.

## Build, Test, and Development Commands

- `poetry install`: install runtime and development dependencies from `pyproject.toml` and `poetry.lock`.
- `poetry run javsp`: run the CLI entry point locally.
- `poetry run pytest`: run the full test suite.
- `poetry run pytest unittest/test_crawlers.py --only javdb`: run crawler fixture tests for one crawler.
- `poetry run flake8 javsp unittest tools`: run the configured lint tool.
- `poetry build`: build distributable package artifacts.
- `poetry run python setup.py build`: build the cx_Freeze executable bundle.
- Local uv environment is available in `.venv` with Python 3.12. Use `UV_CACHE_DIR=.uv-cache uv run --no-sync <command>` to reuse it without trying to regenerate a uv lock from the Poetry project.
- Useful local smoke checks:
  - `UV_CACHE_DIR=.uv-cache uv run --no-sync javsp --help`
  - `UV_CACHE_DIR=.uv-cache uv run --no-sync python -m javsp --help`
  - `UV_CACHE_DIR=.uv-cache uv pip check`
- Local cx_Freeze build command with uv: `UV_CACHE_DIR=.uv-cache uv run --no-sync python setup.py build_exe -b dist`.

## Coding Style & Naming Conventions

Target Python 3.10 through 3.12. Use 4-space indentation, type hints where they clarify cross-module contracts, and grouped imports: standard library, third-party, then local. Name modules and functions in `snake_case`, classes in `PascalCase`, constants in `UPPER_SNAKE_CASE`, and crawler modules after their service key, for example `javsp/web/javbus.py`. Prefer existing helpers before adding abstractions.

## Testing Guidelines

Tests use `pytest` and are stored as `unittest/test_*.py`. Add focused unit tests for parser, filename, config, or image behavior near the related test file. For crawler changes, add or update a JSON fixture under `unittest/data/` using the `AVID (crawler).json` naming pattern. Use `--only <crawler>` while iterating, then run the full suite before submitting.

For offline/local development, use this stable baseline:

- `UV_CACHE_DIR=.uv-cache uv run --no-sync pytest unittest/test_avid.py unittest/test_file.py unittest/test_func.py unittest/test_lib.py`

Do not treat these as offline baseline tests:

- `unittest/test_crawlers.py`: accesses real crawler sites.
- `unittest/test_proxyfree.py`: depends on network reachability and live proxy-free endpoints.
- `unittest/test_exe.py`: expects a built Windows `dist/JavSP.exe`.

## Commit & Pull Request Guidelines

Recent history uses concise fix-oriented subjects, often `fix:` or `fix#<issue>:` and sometimes Chinese descriptions. Keep commit subjects short and specific, reference issues when applicable, and avoid bundling unrelated changes. Pull requests should describe the behavior change, list verification commands, link issues, and note crawler or fixture updates. Include screenshots only for visible image, packaging, or UI-facing changes.

## Security & Configuration Tips

Do not commit personal paths, cookies, credentials, or proxy secrets. Treat `config.yml` as the sample/default configuration and keep local overrides out of version control. Network-facing crawler changes should handle missing fields, anti-bot responses, and timeouts defensively.
