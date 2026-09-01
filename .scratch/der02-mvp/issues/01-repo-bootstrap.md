# 01: Repo bootstrap and tooling

**What to build:** A clean Python project skeleton for `der02` with `pyproject.toml`, `pytest`, `ruff`, and `src/der02/` as the installable package. `pytest` and `ruff` run green on an empty package. A `README.md` exists. A `CITATIONS.md` placeholder exists. `.gitignore` excludes common Python artefacts.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [ ] `pyproject.toml` declares Python 3.12+, deps pinned, dev deps (pytest, ruff) installed
- [ ] `src/der02/__init__.py` exists with a version string
- [ ] `tests/__init__.py` exists
- [ ] `pytest -q` passes
- [ ] `ruff check src tests` passes
- [ ] `README.md` describes the project in two paragraphs and lists run commands
- [ ] `CITATIONS.md` exists with section headers (TNO, CCPS, API RP 521, NIST WebBook) and is empty otherwise
- [ ] `.gitignore` excludes `__pycache__/`, `.venv/`, `.ruff_cache/`, `.pytest_cache/`, `dist/`, `*.egg-info`
- [ ] After `pip install -e ".[dev]"`, `python -c "import der02; print(der02.__version__)"` prints the version