# Design: File-backed environment parser (`FileEnvParser`)

Date: 2026-05-26

## Goal

Provide an `EnvParser` implementation that resolves `ENV_`-prefixed config values
by reading a **file** rather than `os.getenv`. This supports Docker Swarm `configs`
(and similar), which mount each value as a file in a directory instead of exposing
an environment variable.

It is the same `ENV_` concept as `DefaultEnvParser`, just file-backed — hence the
name `FileEnvParser`.

## Behaviour

- Implements the **existing** `EnvParser` ABC (`parser/env_parser.py`) and returns
  the **existing** `MirrorEnv` value object. No new interface or value object.
- Detection: identical to `DefaultEnvParser` — a config string is a reference when
  it starts with `ENV_`; the name read is the string with `ENV_` stripped.
  Example: `"ENV_DB_URL"` resolves the file `<envs_dir>/DB_URL`.
- Source: a file named after the (prefix-stripped) name, located in a configured
  directory, read via `FileEnvFactory` (mirrors `SecretFactory`).
- Default directory: `/run/envs` (overridable via the constructor).
- **Missing file → raises `ValueError`** (same as `DefaultEnvParser`; the explicit
  `ENV_` marker means a missing value is a configuration error). `FileEnvParser`
  does **not** catch the error — unlike `DefaultSecretParser`, which swallows it.
- **Empty file → resolves to `""`** (consistent with `DefaultEnvParser`'s handling
  of a set-but-empty variable). Only an *absent* file raises. This is why
  `FileEnvFactory.get` distinguishes "key present" from "value truthy", rather than
  reusing `SecretFactory`'s truthiness check.

## Integration: drop-in, no wiring

`FileEnvParser` is a drop-in for the existing `env_parser` slot:

```python
mirror = Mirror("app", env_parser=FileEnvParser("/run/envs"))
```

No changes to `Mirror`, `MirrorSingletons`, `ReflectionEngine`, or
`ReferenceService`. The engine already calls `env_parser.parse(node)` on every
string node; `FileEnvParser` satisfies that contract. (`FileEnvParser` and the
os-based `DefaultEnvParser` both claim the `ENV_` prefix, so they are alternatives,
not simultaneously-active parsers — which matches the Swarm use case of reading
files *instead of* os variables.)

## Components

| Existing parallel | New | Location |
|---|---|---|
| `SecretFactory(secrets_dir)` | `FileEnvFactory(envs_dir)` | `file_env/file_env_factory.py` |
| `DefaultEnvParser` (implements `EnvParser`) | `FileEnvParser` (implements `EnvParser`) | `parser/file_env_parser.py` |
| — (reused) | `EnvParser` ABC, `MirrorEnv` | `parser/env_parser.py`, `parser/mirror_env.py` |

### `FileEnvFactory`

Mirrors `SecretFactory`: on construction, loads every file in `envs_dir` into a
cache keyed by filename (value = file contents, stripped). A nonexistent directory
yields an empty cache (no error at construction). `get(name)` returns the cached
value when the key is present (including an empty string), and raises
`ValueError(f"Environment file {name} not found")` when the key is absent.

```python
import os
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

### `FileEnvParser`

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

## Testing

`unittest`, real files in a temp directory (mirroring `tests/test_secret_parser.py`
and `tests/test_env_parser.py`), no mocks. New file `tests/test_file_env_parser.py`.

Unit — `FileEnvFactory`:
1. Present file → returns its (stripped) content.
2. Present-but-empty file → returns `""`.
3. Absent file → raises `ValueError`.
4. Nonexistent directory → any `get` raises `ValueError` (empty cache, construction
   does not error).
5. File contents are stripped of surrounding whitespace/newlines.

Unit — `FileEnvParser`:
6. Is an instance of `EnvParser`.
7. `ENV_`-prefixed name with a present file → `MirrorEnv` whose value is the file
   contents; the prefix is stripped (`"ENV_DB_URL"` reads `DB_URL`).
8. Non-`ENV_` string → `None` (e.g. `"db_url"`, and a bare `"DB_URL"`).
9. `ENV_`-prefixed name with a present-but-empty file → `MirrorEnv("")`.
10. `ENV_`-prefixed name with an absent file → raises `ValueError` (not caught).

Integration — `Mirror`:
11. `Mirror(..., env_parser=FileEnvParser(tmp_dir))` resolves `ENV_`-prefixed config
    values from files, and passes non-`ENV_` strings through unchanged.
12. A missing file referenced by an `ENV_` value raises `ValueError` out of
    `mirror.reflect(...)`.

## Out of scope

- Any new `Mirror`/engine parameter or wiring (it reuses the `env_parser` slot).
- Changes to `DefaultEnvParser`, the secret parser, or `EnvFactory`/`SecretFactory`.
- Watching for file changes / reloading (configs are static for a container's life).
