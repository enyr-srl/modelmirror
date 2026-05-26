# File-backed Environment Parser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `FileEnvParser`, an `EnvParser` implementation that resolves `ENV_`-prefixed config values by reading files from a directory (default `/run/envs`) instead of `os.getenv` — for Docker Swarm `configs`.

**Architecture:** A new `FileEnvFactory` (mirrors `SecretFactory`: loads a directory of files into a cache) + a new `FileEnvParser` that implements the **existing** `EnvParser` ABC and returns the **existing** `MirrorEnv`. It is a drop-in for the `env_parser` slot — no changes to `Mirror`/engine/wiring. Missing file → `ValueError` (like `DefaultEnvParser`); empty file → `""`.

**Tech Stack:** Python 3.10+, `pydantic` (already present), `unittest`. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-05-26-file-env-parser-design.md`

**Test runner notes:**
- Run all file-env tests: `.venv/bin/python -m unittest tests.test_file_env_parser -v`
- Run one class: `.venv/bin/python -m unittest tests.test_file_env_parser.TestFileEnvFactory -v`
- Full suite: `.venv/bin/python -m unittest discover -s tests`

---

### Task 1: `FileEnvFactory` (directory-backed file reading)

`FileEnvFactory` mirrors `SecretFactory` (`src/modelmirror/secrets/secret_factory.py`) — read it for the pattern — but its `get` distinguishes "file present but empty" (returns `""`) from "file absent" (raises). Read `src/modelmirror/env/env_factory.py` too, since it made the same present-vs-absent distinction.

**Files:**
- Create: `src/modelmirror/file_env/__init__.py` (empty package marker)
- Create: `src/modelmirror/file_env/file_env_factory.py`
- Test: `tests/test_file_env_parser.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_file_env_parser.py`:

```python
"""
Test suite for file-backed environment-parser functionality.
"""

import tempfile
import unittest
from pathlib import Path

from modelmirror.file_env.file_env_factory import FileEnvFactory


class TestFileEnvFactory(unittest.TestCase):
    """Test FileEnvFactory directory-backed file reading."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.envs_dir = Path(self.temp_dir) / "envs"
        self.envs_dir.mkdir()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_get_returns_value_for_present_file(self):
        (self.envs_dir / "DB_URL").write_text("postgres://localhost/app")
        factory = FileEnvFactory(str(self.envs_dir))
        self.assertEqual(factory.get("DB_URL"), "postgres://localhost/app")

    def test_get_strips_surrounding_whitespace(self):
        (self.envs_dir / "TOKEN").write_text("  tok_12345\n")
        factory = FileEnvFactory(str(self.envs_dir))
        self.assertEqual(factory.get("TOKEN"), "tok_12345")

    def test_get_returns_empty_string_for_present_but_empty_file(self):
        (self.envs_dir / "EMPTY").write_text("")
        factory = FileEnvFactory(str(self.envs_dir))
        self.assertEqual(factory.get("EMPTY"), "")

    def test_get_raises_value_error_for_absent_file(self):
        factory = FileEnvFactory(str(self.envs_dir))
        with self.assertRaises(ValueError):
            factory.get("MISSING")

    def test_get_raises_value_error_for_nonexistent_directory(self):
        factory = FileEnvFactory(str(Path(self.temp_dir) / "nonexistent"))
        with self.assertRaises(ValueError):
            factory.get("ANYTHING")


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m unittest tests.test_file_env_parser.TestFileEnvFactory -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'modelmirror.file_env'`

- [ ] **Step 3: Create the empty package marker**

Create `src/modelmirror/file_env/__init__.py` as an empty file (zero bytes), matching `src/modelmirror/secrets/__init__.py`.

- [ ] **Step 4: Write minimal implementation**

Create `src/modelmirror/file_env/file_env_factory.py`:

```python
from pathlib import Path


class FileEnvFactory:
    def __init__(self, envs_dir: str) -> None:
        self.__envs_cache = self.__load_envs(envs_dir)

    def get(self, name: str) -> str:
        if name in self.__envs_cache:
            return self.__envs_cache[name]
        raise ValueError(f"Environment file {name} not found")

    def __load_envs(self, envs_dir: str) -> dict[str, str]:
        path = Path(envs_dir)
        if not path.is_dir():
            return {}

        envs: dict[str, str] = {}
        for env_file in path.iterdir():
            if env_file.is_file():
                envs[env_file.name] = env_file.read_text(encoding="utf-8").strip()
        return envs
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m unittest tests.test_file_env_parser.TestFileEnvFactory -v`
Expected: PASS (5 tests)

- [ ] **Step 6: Commit**

```bash
git add src/modelmirror/file_env/__init__.py src/modelmirror/file_env/file_env_factory.py tests/test_file_env_parser.py
git commit -m "feat: add FileEnvFactory for directory-backed env values

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

Note: the repo has pre-commit hooks (black, ruff, isort, mypy). If a hook reformats/blocks, re-stage and re-commit so the final commit is clean; report any change a hook made. The new `file_env/` package may be caught by a broad `.gitignore` pattern (the `env/` package was, in earlier work) — if `git add` does not stage `src/modelmirror/file_env/`, add a `!src/modelmirror/file_env/` negation to `.gitignore` (check how `!src/modelmirror/env/` was handled) and include it in the commit.

---

### Task 2: `FileEnvParser` (drop-in `EnvParser`) + Mirror integration

`FileEnvParser` implements the existing `EnvParser` ABC (`src/modelmirror/parser/env_parser.py`) and returns the existing `MirrorEnv` (`src/modelmirror/parser/mirror_env.py`). It mirrors `DefaultEnvParser` (`src/modelmirror/parser/default_env_parser.py`) — `ENV_` prefix detection, prefix stripping, no catching of `ValueError` — but delegates to `FileEnvFactory` instead of `EnvFactory`. It is used as a drop-in `env_parser`; no wiring changes.

**Files:**
- Create: `src/modelmirror/parser/file_env_parser.py`
- Test: `tests/test_file_env_parser.py` (append two new test classes)

- [ ] **Step 1: Write the failing tests**

In `tests/test_file_env_parser.py`, add these imports next to the existing `from modelmirror.file_env.file_env_factory import FileEnvFactory`:

```python
from pydantic import BaseModel

from modelmirror.mirror import Mirror
from modelmirror.parser.env_parser import EnvParser
from modelmirror.parser.file_env_parser import FileEnvParser
from modelmirror.parser.mirror_env import MirrorEnv
```

Add these two test classes after `TestFileEnvFactory`, before the `if __name__` block:

```python
class TestFileEnvParser(unittest.TestCase):
    """Test FileEnvParser prefix detection and file resolution."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.envs_dir = Path(self.temp_dir) / "envs"
        self.envs_dir.mkdir()
        (self.envs_dir / "DB_URL").write_text("postgres://localhost/app")
        (self.envs_dir / "EMPTY").write_text("")
        self.parser = FileEnvParser(str(self.envs_dir))

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_file_env_parser_is_an_env_parser(self):
        self.assertIsInstance(self.parser, EnvParser)

    def test_parses_prefixed_name_and_strips_prefix(self):
        result = self.parser.parse("ENV_DB_URL")
        self.assertIsInstance(result, MirrorEnv)
        if result is not None:
            self.assertEqual(result.value, "postgres://localhost/app")

    def test_returns_none_for_non_prefixed_string(self):
        self.assertIsNone(self.parser.parse("db_url"))
        self.assertIsNone(self.parser.parse("DB_URL"))

    def test_returns_mirror_env_with_empty_value_for_present_but_empty_file(self):
        result = self.parser.parse("ENV_EMPTY")
        self.assertIsInstance(result, MirrorEnv)
        if result is not None:
            self.assertEqual(result.value, "")

    def test_raises_value_error_for_prefixed_but_absent_file(self):
        with self.assertRaises(ValueError):
            self.parser.parse("ENV_MISSING")


class TestFileEnvParserIntegration(unittest.TestCase):
    """Test FileEnvParser as a drop-in env_parser for Mirror."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.envs_dir = Path(self.temp_dir) / "envs"
        self.envs_dir.mkdir()
        (self.envs_dir / "DB_URL").write_text("postgres://localhost/app")
        (self.envs_dir / "TOKEN").write_text("tok_12345")

        self.config_dir = Path(self.temp_dir) / "configs"
        self.config_dir.mkdir()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_mirror_resolves_file_env_values(self):
        config_content = """{
    "database_url": "ENV_DB_URL",
    "token": "ENV_TOKEN",
    "normal_value": "regular_string"
}"""
        config_path = self.config_dir / "file_env_basic.json"
        config_path.write_text(config_content)

        class FileEnvConfig(BaseModel):
            database_url: str
            token: str
            normal_value: str

        mirror = Mirror("tests.fixtures", env_parser=FileEnvParser(str(self.envs_dir)))
        config = mirror.reflect(str(config_path), FileEnvConfig)

        self.assertEqual(config.database_url, "postgres://localhost/app")
        self.assertEqual(config.token, "tok_12345")
        self.assertEqual(config.normal_value, "regular_string")

    def test_mirror_raises_when_file_is_missing(self):
        config_content = """{
    "database_url": "ENV_DEFINITELY_MISSING"
}"""
        config_path = self.config_dir / "file_env_missing.json"
        config_path.write_text(config_content)

        class MissingConfig(BaseModel):
            database_url: str

        mirror = Mirror("tests.fixtures", env_parser=FileEnvParser(str(self.envs_dir)))
        with self.assertRaises(ValueError):
            mirror.reflect(str(config_path), MissingConfig)
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `.venv/bin/python -m unittest tests.test_file_env_parser.TestFileEnvParser -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'modelmirror.parser.file_env_parser'`

- [ ] **Step 3: Write minimal implementation**

Create `src/modelmirror/parser/file_env_parser.py`:

```python
from modelmirror.file_env.file_env_factory import FileEnvFactory
from modelmirror.parser.env_parser import EnvParser
from modelmirror.parser.mirror_env import MirrorEnv


class FileEnvParser(EnvParser):
    _PREFIX = "ENV_"

    def __init__(self, envs_dir: str = "/run/envs") -> None:
        self.__file_env_factory = FileEnvFactory(envs_dir)

    def parse(self, name: str) -> MirrorEnv | None:
        if not name.startswith(self._PREFIX):
            return None
        variable_name = name.removeprefix(self._PREFIX)
        return MirrorEnv(self.__file_env_factory.get(variable_name))
```

- [ ] **Step 4: Run the new tests to verify they pass**

Run: `.venv/bin/python -m unittest tests.test_file_env_parser.TestFileEnvParser tests.test_file_env_parser.TestFileEnvParserIntegration -v`
Expected: PASS (7 tests: 5 unit + 2 integration)

- [ ] **Step 5: Run the full file-env module and the full suite**

Run: `.venv/bin/python -m unittest tests.test_file_env_parser -v` → Expected: PASS (12 tests total).
Run: `.venv/bin/python -m unittest discover -s tests` → Expected: ALL pass, no regressions.

- [ ] **Step 6: Commit**

```bash
git add src/modelmirror/parser/file_env_parser.py tests/test_file_env_parser.py
git commit -m "feat: add FileEnvParser drop-in EnvParser backed by files

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

Note: pre-commit hooks run on commit. Keep the `if result is not None:` guards in the tests — they satisfy the mypy hook (it does not narrow `MirrorEnv | None` from `assertIsInstance`), matching the existing `tests/test_env_parser.py` / `tests/test_secret_parser.py` pattern. If a hook reformats/blocks, re-stage and re-commit; report any change a hook made.

---

## Self-Review

**Spec coverage:**
- `FileEnvFactory` directory load + present/empty/absent semantics → Task 1 (5 tests). ✓
- Nonexistent directory tolerated at construction, raises on get → Task 1 (`test_get_raises_value_error_for_nonexistent_directory`). ✓
- Whitespace stripping → Task 1 (`test_get_strips_surrounding_whitespace`). ✓
- `FileEnvParser` implements `EnvParser`, returns `MirrorEnv` → Task 2 (`test_file_env_parser_is_an_env_parser`, prefix tests). ✓
- `ENV_` detection + strip → Task 2 (`test_parses_prefixed_name_and_strips_prefix`). ✓
- Non-prefixed → None → Task 2 (`test_returns_none_for_non_prefixed_string`). ✓
- Empty file → `""` → Task 2 (`test_returns_mirror_env_with_empty_value_for_present_but_empty_file`). ✓
- Absent file → raises (not caught) → Task 2 (`test_raises_value_error_for_prefixed_but_absent_file`). ✓
- Drop-in via `env_parser`, no wiring → Task 2 integration (`test_mirror_resolves_file_env_values`). ✓
- Missing file raises through `mirror.reflect` → Task 2 integration (`test_mirror_raises_when_file_is_missing`). ✓

**Placeholder scan:** No TBD/TODO; every code step has complete code. ✓

**Type consistency:** `FileEnvFactory.get(name: str) -> str`, `FileEnvParser(envs_dir: str = "/run/envs")`, `parse(name: str) -> MirrorEnv | None`. Reuses `EnvParser`/`MirrorEnv` unchanged. Consistent across tasks. ✓
