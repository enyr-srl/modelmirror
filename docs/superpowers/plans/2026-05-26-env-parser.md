# Environment-variable Parser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve `ENV_`-prefixed strings in a config to the matching environment variable's value, mirroring the existing secret-parser feature.

**Architecture:** A new `EnvParser` ABC + `MirrorEnv` value object + `DefaultEnvParser`, with environment access isolated in an `EnvFactory` (parallel to `SecretParser`/`MirrorSecret`/`DefaultSecretParser`/`SecretFactory`). The parser is wired into `Mirror` as a parallel `env_parser` parameter and applied to every string node *before* the secret parser. A missing variable raises `ValueError`; a set-but-empty variable (`FOO=""`) resolves to `""`.

**Tech Stack:** Python 3.10+, `pydantic` (already a dependency), `unittest` (test runner). No new dependencies.

**Spec:** `docs/superpowers/specs/2026-05-26-env-parser-design.md`

**Test runner notes:**
- Run all env tests: `.venv/bin/python -m unittest tests.test_env_parser -v`
- Run one test: `.venv/bin/python -m unittest tests.test_env_parser.TestEnvFactory.test_get_returns_value_for_set_variable -v`
- Full suite: `.venv/bin/python -m unittest discover -s tests -v`

---

### Task 1: `EnvFactory` (isolated environment access)

`EnvFactory` reads a single environment variable and defines what "missing" means. It mirrors `SecretFactory` but reads `os.getenv` instead of a directory, and treats only an *unset* variable (not an empty one) as missing.

**Files:**
- Create: `src/modelmirror/env/__init__.py` (empty package marker)
- Create: `src/modelmirror/env/env_factory.py`
- Test: `tests/test_env_parser.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_env_parser.py`:

```python
"""
Test suite for environment-variable parser functionality.
"""

import os
import unittest

from modelmirror.env.env_factory import EnvFactory


class TestEnvFactory(unittest.TestCase):
    """Test EnvFactory environment access."""

    def setUp(self):
        self.factory = EnvFactory()
        self._original_environ = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._original_environ)

    def test_get_returns_value_for_set_variable(self):
        os.environ["MODELMIRROR_TEST_DB_URL"] = "postgres://localhost/test"
        self.assertEqual(
            self.factory.get("MODELMIRROR_TEST_DB_URL"),
            "postgres://localhost/test",
        )

    def test_get_returns_empty_string_for_set_but_empty_variable(self):
        os.environ["MODELMIRROR_TEST_EMPTY"] = ""
        self.assertEqual(self.factory.get("MODELMIRROR_TEST_EMPTY"), "")

    def test_get_raises_value_error_for_unset_variable(self):
        os.environ.pop("MODELMIRROR_TEST_MISSING", None)
        with self.assertRaises(ValueError):
            self.factory.get("MODELMIRROR_TEST_MISSING")


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m unittest tests.test_env_parser.TestEnvFactory -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'modelmirror.env'`

- [ ] **Step 3: Create the empty package marker**

Create `src/modelmirror/env/__init__.py` as an empty file (zero bytes), matching `src/modelmirror/secrets/__init__.py`.

- [ ] **Step 4: Write minimal implementation**

Create `src/modelmirror/env/env_factory.py`:

```python
import os


class EnvFactory:
    def get(self, name: str) -> str:
        value = os.getenv(name)
        if value is not None:
            return value
        raise ValueError(f"Environment variable {name} not found")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python -m unittest tests.test_env_parser.TestEnvFactory -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add src/modelmirror/env/__init__.py src/modelmirror/env/env_factory.py tests/test_env_parser.py
git commit -m "feat: add EnvFactory for environment-variable access

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: `MirrorEnv`, `EnvParser` ABC, and `DefaultEnvParser`

`MirrorEnv` is the value object (parallel to `MirrorSecret`). `EnvParser` is the abstract interface (parallel to `SecretParser`). `DefaultEnvParser` recognises the `ENV_` prefix, strips it, and delegates reading to `EnvFactory`; unlike `DefaultSecretParser`, it does **not** catch `ValueError`, so a missing variable propagates.

**Files:**
- Create: `src/modelmirror/parser/mirror_env.py`
- Create: `src/modelmirror/parser/env_parser.py`
- Create: `src/modelmirror/parser/default_env_parser.py`
- Test: `tests/test_env_parser.py` (append a new test class)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_env_parser.py` (add the imports near the top with the others, and the new class before the `if __name__` block):

Add these imports below the existing `from modelmirror.env.env_factory import EnvFactory`:

```python
from modelmirror.parser.default_env_parser import DefaultEnvParser
from modelmirror.parser.env_parser import EnvParser
from modelmirror.parser.mirror_env import MirrorEnv
```

Add this test class:

```python
class TestDefaultEnvParser(unittest.TestCase):
    """Test DefaultEnvParser prefix detection and resolution."""

    def setUp(self):
        self.parser = DefaultEnvParser()
        self._original_environ = dict(os.environ)
        os.environ["MODELMIRROR_TEST_DB_URL"] = "postgres://localhost/test"
        os.environ["MODELMIRROR_TEST_EMPTY"] = ""

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._original_environ)

    def test_default_env_parser_is_an_env_parser(self):
        self.assertIsInstance(self.parser, EnvParser)

    def test_parses_prefixed_name_and_strips_prefix(self):
        result = self.parser.parse("ENV_MODELMIRROR_TEST_DB_URL")
        self.assertIsInstance(result, MirrorEnv)
        if result is not None:
            self.assertEqual(result.value, "postgres://localhost/test")

    def test_returns_none_for_non_prefixed_string(self):
        # Lowercase, and a bare uppercase name without the ENV_ marker.
        self.assertIsNone(self.parser.parse("database_url"))
        self.assertIsNone(self.parser.parse("MODELMIRROR_TEST_DB_URL"))

    def test_returns_mirror_env_with_empty_value_for_set_but_empty_variable(self):
        result = self.parser.parse("ENV_MODELMIRROR_TEST_EMPTY")
        self.assertIsInstance(result, MirrorEnv)
        if result is not None:
            self.assertEqual(result.value, "")

    def test_raises_value_error_for_prefixed_but_unset_variable(self):
        os.environ.pop("MODELMIRROR_TEST_MISSING", None)
        with self.assertRaises(ValueError):
            self.parser.parse("ENV_MODELMIRROR_TEST_MISSING")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m unittest tests.test_env_parser.TestDefaultEnvParser -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'modelmirror.parser.default_env_parser'`

- [ ] **Step 3: Create `MirrorEnv`**

Create `src/modelmirror/parser/mirror_env.py`:

```python
from dataclasses import dataclass


@dataclass
class MirrorEnv:
    value: str
```

- [ ] **Step 4: Create the `EnvParser` ABC**

Create `src/modelmirror/parser/env_parser.py`:

```python
from abc import ABC, abstractmethod

from modelmirror.parser.mirror_env import MirrorEnv


class EnvParser(ABC):
    @abstractmethod
    def parse(self, name: str) -> MirrorEnv | None:
        raise NotImplementedError
```

- [ ] **Step 5: Create `DefaultEnvParser`**

Create `src/modelmirror/parser/default_env_parser.py`:

```python
from modelmirror.env.env_factory import EnvFactory
from modelmirror.parser.env_parser import EnvParser
from modelmirror.parser.mirror_env import MirrorEnv


class DefaultEnvParser(EnvParser):
    __PREFIX = "ENV_"

    def __init__(self) -> None:
        self.__env_factory = EnvFactory()

    def parse(self, name: str) -> MirrorEnv | None:
        if not name.startswith(self.__PREFIX):
            return None
        variable_name = name.removeprefix(self.__PREFIX)
        return MirrorEnv(self.__env_factory.get(variable_name))
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/python -m unittest tests.test_env_parser.TestDefaultEnvParser -v`
Expected: PASS (5 tests)

- [ ] **Step 7: Commit**

```bash
git add src/modelmirror/parser/mirror_env.py src/modelmirror/parser/env_parser.py src/modelmirror/parser/default_env_parser.py tests/test_env_parser.py
git commit -m "feat: add EnvParser, MirrorEnv, and DefaultEnvParser

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Wire `env_parser` through Mirror and resolve `ENV_` values in configs

Thread a new `env_parser: EnvParser = DefaultEnvParser()` parameter through `Mirror` → `MirrorSingletons` → `ReflectionEngine` → `ReferenceService`, and apply it to string nodes **before** the secret parser. This task is driven by an integration test that exercises the full path.

**Files:**
- Modify: `src/modelmirror/singleton/singleton_manager.py`
- Modify: `src/modelmirror/mirror.py`
- Modify: `src/modelmirror/reflection/reflection_engine.py`
- Modify: `src/modelmirror/instance/reference_service.py`
- Test: `tests/test_env_parser.py` (append a new integration test class)

- [ ] **Step 1: Write the failing integration test**

Append to `tests/test_env_parser.py`. Add these imports near the top with the others:

```python
import tempfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror
```

Add this test class before the `if __name__` block:

```python
class TestEnvParserIntegration(unittest.TestCase):
    """Test env parser integration with Mirror."""

    def setUp(self):
        self._original_environ = dict(os.environ)
        os.environ["MODELMIRROR_DB_URL"] = "postgres://localhost/app"
        os.environ["MODELMIRROR_TOKEN"] = "tok_12345"

        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "configs"
        self.config_dir.mkdir()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._original_environ)

        import shutil

        shutil.rmtree(self.temp_dir)

    def test_mirror_resolves_env_values(self):
        config_content = """{
    "database_url": "ENV_MODELMIRROR_DB_URL",
    "token": "ENV_MODELMIRROR_TOKEN",
    "normal_value": "regular_string"
}"""
        config_path = self.config_dir / "env_basic.json"
        config_path.write_text(config_content)

        class EnvConfig(BaseModel):
            database_url: str
            token: str
            normal_value: str

        mirror = Mirror("tests.fixtures", env_parser=DefaultEnvParser())
        config = mirror.reflect(str(config_path), EnvConfig)

        self.assertEqual(config.database_url, "postgres://localhost/app")
        self.assertEqual(config.token, "tok_12345")
        self.assertEqual(config.normal_value, "regular_string")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m unittest tests.test_env_parser.TestEnvParserIntegration.test_mirror_resolves_env_values -v`
Expected: FAIL with `TypeError: __new__() got an unexpected keyword argument 'env_parser'`

- [ ] **Step 3: Add `env_parser` to `MirrorSingletons`**

In `src/modelmirror/singleton/singleton_manager.py`, add the import below the existing parser imports:

```python
from modelmirror.parser.env_parser import EnvParser
```

Change `get_or_create_instance` to accept and forward `env_parser` (add the last parameter and pass it to `__create_instance_key`):

```python
    @classmethod
    def get_or_create_instance(
        cls,
        mirror_class: type,
        package_name: str,
        code_link_parser: CodeLinkParser,
        model_link_parser: ModelLinkParser,
        check_circular_types: bool,
        secret_parser: SecretParser,
        env_parser: EnvParser,
    ) -> Any:
        """Get existing singleton or create new one (automatically per thread/task context)."""
        instance_key = cls.__create_instance_key(
            package_name, code_link_parser, model_link_parser, check_circular_types, secret_parser, env_parser
        )
```

(Leave the rest of `get_or_create_instance` — the locking and creation — unchanged.)

Change `__create_instance_key` to accept `env_parser` and include it in the key:

```python
    @classmethod
    def __create_instance_key(
        cls,
        package_name: str,
        code_link_parser: CodeLinkParser,
        model_link_parser: ModelLinkParser,
        check_circular_types: bool,
        secret_parser: SecretParser,
        env_parser: EnvParser,
    ) -> str:
        """Create unique key for Mirror instance including thread/task context."""
        thread_id = threading.get_ident()
        key = f"{package_name}:{id(code_link_parser)}:{id(model_link_parser)}:{check_circular_types}:{secret_parser}:{env_parser}:{thread_id}"
        try:
            current_task = asyncio.current_task()
            if current_task:
                key += f":{id(current_task)}"
        except RuntimeError:
            pass

        return key
```

- [ ] **Step 4: Add `env_parser` to `Mirror`**

In `src/modelmirror/mirror.py`, add imports below the existing parser imports:

```python
from modelmirror.parser.default_env_parser import DefaultEnvParser
from modelmirror.parser.env_parser import EnvParser
```

Change `__new__` to accept `env_parser` and forward it:

```python
    def __new__(
        cls,
        package_name: str = "app",
        code_link_parser: CodeLinkParser = DefaultCodeLinkParser(),
        model_link_parser: ModelLinkParser = DefaultModelLinkParser(),
        check_circular_types: bool = True,
        secret_parser: SecretParser = DefaultSecretParser("/run/secrets"),
        env_parser: EnvParser = DefaultEnvParser(),
    ) -> "Mirror":
        return MirrorSingletons.get_or_create_instance(
            cls, package_name, code_link_parser, model_link_parser, check_circular_types, secret_parser, env_parser
        )
```

Change `__init__` to accept `env_parser` and pass it to `ReflectionEngine`:

```python
    def __init__(
        self,
        package_name: str = "app",
        code_link_parser: CodeLinkParser = DefaultCodeLinkParser(),
        model_link_parser: ModelLinkParser = DefaultModelLinkParser(),
        check_circular_types: bool = True,
        secret_parser: SecretParser = DefaultSecretParser("/run/secrets"),
        env_parser: EnvParser = DefaultEnvParser(),
    ):
        if hasattr(self, "_initialized"):
            return

        scanner = ClassScanner(package_name)
        registered_classes = scanner.scan()

        self.__engine = ReflectionEngine(
            registered_classes, code_link_parser, model_link_parser, check_circular_types, secret_parser, env_parser
        )
        self.__cache: dict[str, Any] = {}
        self._initialized = True
```

- [ ] **Step 5: Add `env_parser` to `ReflectionEngine`**

In `src/modelmirror/reflection/reflection_engine.py`, add the import below the existing parser imports:

```python
from modelmirror.parser.env_parser import EnvParser
```

Change `__init__` to accept and store `env_parser` (add the last parameter and the assignment after `self.__secret_parser = secret_parser`):

```python
    def __init__(
        self,
        registered_classes: list[ClassReference],
        code_link_parser: CodeLinkParser,
        model_link_parser: ModelLinkParser,
        check_circular_types: bool,
        secret_parser: SecretParser,
        env_parser: EnvParser,
    ):
        self.__registered_classes = registered_classes
        self.__code_link_parser = code_link_parser
        self.__instance_properties: dict[str, InstanceProperties] = {}
        self.__singleton_path: dict[str, str] = {}
        self.__model_link_parser = model_link_parser
        self.__check_circular_types = check_circular_types
        self.__secret_parser = secret_parser
        self.__env_parser = env_parser
        self.__reset_state()
```

In `__resolve_instances`, pass `self.__env_parser` to `resolve` (add it as the last argument):

```python
        return self.__reference_service.resolve(
            instance_names,
            self.__instance_properties,
            self.__singleton_path,
            self.__model_link_parser,
            self.__registered_classes,
            self.__secret_parser,
            self.__env_parser,
        )
```

In the `_hook` inside `__instantiate_model`, resolve env before secret. Replace this block:

```python
            # Handle secrets for string values
            if isinstance(node, str):
                mirror_secret = self.__secret_parser.parse(node)
                if mirror_secret:
                    return mirror_secret.value

            return node
```

with:

```python
            # Handle env vars and secrets for string values (env takes precedence)
            if isinstance(node, str):
                mirror_env = self.__env_parser.parse(node)
                if mirror_env:
                    return mirror_env.value
                mirror_secret = self.__secret_parser.parse(node)
                if mirror_secret:
                    return mirror_secret.value

            return node
```

- [ ] **Step 6: Add `env_parser` to `ReferenceService`**

In `src/modelmirror/instance/reference_service.py`, add the import below the existing parser imports:

```python
from modelmirror.parser.env_parser import EnvParser
```

Change `resolve` to accept `env_parser` (add the last parameter) and pass it to `__resolve_params`:

```python
    def resolve(
        self,
        instance_names: list[str],
        instance_properties: dict[str, InstanceProperties],
        singleton_path: dict[str, str],
        model_link_parser: ModelLinkParser,
        registered_classes: list[ClassReference],
        secret_parser: SecretParser,
        env_parser: EnvParser,
    ) -> dict[str, Any]:
        self.__instances = {}
        for instance_name in instance_names:
            properties = instance_properties.get(instance_name)
            if properties:
                resolved_params = self.__resolve_params(
                    properties,
                    self.__instances,
                    singleton_path,
                    model_link_parser,
                    registered_classes,
                    secret_parser,
                    env_parser,
                )
                original_instance = self.__validation_service.validate_or_raise(
                    properties.class_reference.cls, resolved_params
                )
                self.__instances.update({instance_name: original_instance})
        return self.__instances
```

Change `__resolve_params` to accept `env_parser` (add the last parameter):

```python
    def __resolve_params(
        self,
        properties: InstanceProperties,
        instances: dict[str, Any],
        singleton_path: dict[str, str],
        model_link_parser: ModelLinkParser,
        registered_classes: list[ClassReference],
        secret_parser: SecretParser,
        env_parser: EnvParser,
    ) -> dict[str, Any]:
```

Inside `__resolve_params`, in the `resolve_value` closure, replace this block:

```python
            if isinstance(value, str):
                mirror_secret = secret_parser.parse(value)
                if mirror_secret:
                    return mirror_secret.value
            return value
```

with:

```python
            if isinstance(value, str):
                mirror_env = env_parser.parse(value)
                if mirror_env:
                    return mirror_env.value
                mirror_secret = secret_parser.parse(value)
                if mirror_secret:
                    return mirror_secret.value
            return value
```

- [ ] **Step 7: Run the integration test to verify it passes**

Run: `.venv/bin/python -m unittest tests.test_env_parser.TestEnvParserIntegration.test_mirror_resolves_env_values -v`
Expected: PASS

- [ ] **Step 8: Run the full suite to verify nothing regressed**

Run: `.venv/bin/python -m unittest discover -s tests -v`
Expected: PASS (all existing tests still pass; the secret tests are unaffected because they pass an explicit `secret_parser` and the default `env_parser` ignores their non-`ENV_` strings)

- [ ] **Step 9: Commit**

```bash
git add src/modelmirror/singleton/singleton_manager.py src/modelmirror/mirror.py src/modelmirror/reflection/reflection_engine.py src/modelmirror/instance/reference_service.py tests/test_env_parser.py
git commit -m "feat: wire env_parser through Mirror and resolve ENV_ config values

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Integration coverage — precedence, mixed references, nesting, caching

These tests cover the remaining spec scenarios. They should pass against the Task 3 implementation without new production code; if any fails, the implementation has a gap to fix.

**Files:**
- Test: `tests/test_env_parser.py` (append tests to `TestEnvParserIntegration`)

- [ ] **Step 1: Add the precedence test**

A value that is `ENV_`-prefixed (and therefore also all-uppercase) must be resolved by the env parser, not the secret parser. Wire both parsers and assert the env value wins. Add to `TestEnvParserIntegration`:

```python
    def test_env_takes_precedence_over_secret_parser(self):
        import shutil

        from modelmirror.parser.default_secret_parser import DefaultSecretParser

        secrets_dir = Path(self.temp_dir) / "secrets"
        secrets_dir.mkdir()
        # A secret file whose name collides with the ENV_-prefixed string.
        (secrets_dir / "ENV_MODELMIRROR_DB_URL").write_text("secret_should_not_win")

        config_content = """{
    "database_url": "ENV_MODELMIRROR_DB_URL"
}"""
        config_path = self.config_dir / "env_precedence.json"
        config_path.write_text(config_content)

        class PrecedenceConfig(BaseModel):
            database_url: str

        mirror = Mirror(
            "tests.fixtures",
            secret_parser=DefaultSecretParser(str(secrets_dir)),
            env_parser=DefaultEnvParser(),
        )
        config = mirror.reflect(str(config_path), PrecedenceConfig)

        self.assertEqual(config.database_url, "postgres://localhost/app")
```

- [ ] **Step 2: Add the mixed-references test**

Env vars resolve both at the top level (handled by the engine's `__instantiate_model` hook) **and** as a `$mirror` instance constructor parameter (handled by `ReferenceService.__resolve_params`). Putting `ENV_MODELMIRROR_SERVICE_NAME` inside the service's `name` exercises the reference-service path; the top-level `database_url`/`token` exercise the hook path. Add to `TestEnvParserIntegration`:

```python
    def test_env_with_mirror_reference(self):
        from tests.fixtures.test_classes import SimpleService

        os.environ["MODELMIRROR_SERVICE_NAME"] = "EnvNamedService"

        config_content = """{
    "service": {
        "$mirror": "simple_service",
        "name": "ENV_MODELMIRROR_SERVICE_NAME"
    },
    "database_url": "ENV_MODELMIRROR_DB_URL",
    "token": "ENV_MODELMIRROR_TOKEN"
}"""
        config_path = self.config_dir / "env_mixed.json"
        config_path.write_text(config_content)

        class MixedConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            service: SimpleService
            database_url: str
            token: str

        mirror = Mirror("tests.fixtures", env_parser=DefaultEnvParser())
        config = mirror.reflect(str(config_path), MixedConfig)

        self.assertIsInstance(config.service, SimpleService)
        # Resolved by ReferenceService.__resolve_params (instance constructor param).
        self.assertEqual(config.service.name, "EnvNamedService")
        # Resolved by the engine's __instantiate_model hook (top-level fields).
        self.assertEqual(config.database_url, "postgres://localhost/app")
        self.assertEqual(config.token, "tok_12345")
```

(`MODELMIRROR_SERVICE_NAME` is removed automatically by `tearDown`, which restores the original environment.)

- [ ] **Step 3: Add the nested-structure test**

Env references resolve inside nested dicts and lists. Add to `TestEnvParserIntegration`:

```python
    def test_env_in_nested_structure(self):
        config_content = """{
    "database": {
        "host": "localhost",
        "url": "ENV_MODELMIRROR_DB_URL"
    },
    "services": [
        {"name": "service1", "token": "ENV_MODELMIRROR_TOKEN"},
        {"name": "service2", "token": "regular_token"}
    ]
}"""
        config_path = self.config_dir / "env_nested.json"
        config_path.write_text(config_content)

        class NestedConfig(BaseModel):
            database: dict
            services: list

        mirror = Mirror("tests.fixtures", env_parser=DefaultEnvParser())
        config = mirror.reflect(str(config_path), NestedConfig)

        self.assertEqual(config.database["url"], "postgres://localhost/app")
        self.assertEqual(config.services[0]["token"], "tok_12345")
        self.assertEqual(config.services[1]["token"], "regular_token")
```

- [ ] **Step 4: Add the caching tests**

Caching behaves like the secret tests: cached returns the same object, uncached returns a new one. Add to `TestEnvParserIntegration`:

```python
    def test_env_resolution_with_caching(self):
        config_content = """{
    "database_url": "ENV_MODELMIRROR_DB_URL"
}"""
        config_path = self.config_dir / "env_cache.json"
        config_path.write_text(config_content)

        class CacheConfig(BaseModel):
            database_url: str

        mirror = Mirror("tests.fixtures", env_parser=DefaultEnvParser())
        config1 = mirror.reflect(str(config_path), CacheConfig)
        config2 = mirror.reflect(str(config_path), CacheConfig)

        self.assertEqual(config1.database_url, "postgres://localhost/app")
        self.assertIs(config1, config2)

    def test_env_resolution_without_caching(self):
        config_content = """{
    "database_url": "ENV_MODELMIRROR_DB_URL"
}"""
        config_path = self.config_dir / "env_no_cache.json"
        config_path.write_text(config_content)

        class NoCacheConfig(BaseModel):
            database_url: str

        mirror = Mirror("tests.fixtures", env_parser=DefaultEnvParser())
        config1 = mirror.reflect(str(config_path), NoCacheConfig, cached=False)
        config2 = mirror.reflect(str(config_path), NoCacheConfig, cached=False)

        self.assertEqual(config1.database_url, "postgres://localhost/app")
        self.assertEqual(config2.database_url, "postgres://localhost/app")
        self.assertIsNot(config1, config2)
```

- [ ] **Step 5: Run the full env test class**

Run: `.venv/bin/python -m unittest tests.test_env_parser.TestEnvParserIntegration -v`
Expected: PASS (all integration tests)

- [ ] **Step 6: Run the full suite**

Run: `.venv/bin/python -m unittest discover -s tests -v`
Expected: PASS (no regressions)

- [ ] **Step 7: Commit**

```bash
git add tests/test_env_parser.py
git commit -m "test: cover env parser precedence, mixed refs, nesting, and caching

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage:**
- Detection by `ENV_` prefix + strip → Task 2 (Step 5), Task 3 (basic integration). ✓
- Read via `os.getenv`, isolated in `EnvFactory` → Task 1. ✓
- Missing variable raises `ValueError` → Task 1 (Step 1) + Task 2 (`test_raises_value_error_for_prefixed_but_unset_variable`). ✓
- Set-but-empty resolves to `""` → Task 1 + Task 2. ✓
- Component triad (`EnvParser`/`MirrorEnv`/`DefaultEnvParser`/`EnvFactory`) → Tasks 1–2. ✓
- Parallel `env_parser` param through Mirror/singleton/engine/reference_service → Task 3. ✓
- Precedence: env before secret → Task 3 (hook + resolve_value) + Task 4 (`test_env_takes_precedence_over_secret_parser`). ✓
- Validation stays at object level → demonstrated by typed `BaseModel` fields in integration tests. ✓
- Nested structures + caching → Task 4. ✓

**Placeholder scan:** No TBD/TODO; every code step contains complete code. ✓

**Type consistency:** `EnvParser.parse(name: str) -> MirrorEnv | None`, `MirrorEnv(value: str)`, `EnvFactory.get(name: str) -> str`, and the `env_parser` parameter ordering (always last, after `secret_parser`) are identical across all tasks and call sites. ✓
