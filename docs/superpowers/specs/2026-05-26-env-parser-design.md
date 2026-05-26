# Design: Environment-variable parser (`EnvParser`)

Date: 2026-05-26

## Goal

Add a parser that resolves environment variables referenced in a config, mirroring
the existing secret-parser feature. From the config's point of view this is just
another string value that gets parsed and substituted — nothing more. Type
validation continues to happen at the object (outer pydantic model) level.

`pydantic_settings` is **not** used: the parser only needs to detect a marker and
read `os.getenv`. No new runtime dependency is added.

## Detection & resolution

- A config string is an environment-variable reference when it starts with the
  prefix `ENV_`.
- The variable actually read is the string **without** the `ENV_` prefix.
  Example: config value `"ENV_DATABASE_URL"` resolves to `os.getenv("DATABASE_URL")`.
- The resolved string replaces the original value in the reflected config; the
  outer pydantic model then validates/coerces it (e.g. `str -> int`).

### Missing variable → raise

If an `ENV_`-prefixed variable is **not set** in the environment, this is treated
as a configuration error and raises `ValueError`. This is a deliberate difference
from `DefaultSecretParser`, which swallows the error and returns `None`: the `ENV_`
prefix is an explicit, intentional marker, so a missing value is a mistake worth
surfacing immediately rather than silently passing the literal string through.

### Set-but-empty variable

A variable that is set to the empty string (`FOO=""`) is considered *set* and
resolves to `""` (standard `os.getenv` semantics). Only an unset variable
(`os.getenv` returns `None`) raises.

## Components

Mirror the existing secret triad exactly:

| Secret (existing) | Env (new) | Location |
|---|---|---|
| `SecretParser` (ABC, `parse(name) -> MirrorSecret \| None`) | `EnvParser` (ABC, `parse(name) -> MirrorEnv \| None`) | `parser/env_parser.py` |
| `MirrorSecret(value: str)` | `MirrorEnv(value: str)` | `parser/mirror_env.py` |
| `DefaultSecretParser` | `DefaultEnvParser` | `parser/default_env_parser.py` |
| `SecretFactory` (reads a directory) | `EnvFactory` (reads `os.getenv`, raises `ValueError` if unset) | `env/env_factory.py` |

### `EnvParser` (abstract base class)

```python
class EnvParser(ABC):
    @abstractmethod
    def parse(self, name: str) -> MirrorEnv | None:
        raise NotImplementedError
```

### `MirrorEnv` (value object)

```python
@dataclass
class MirrorEnv:
    value: str
```

### `EnvFactory`

Single responsibility: read one environment variable, raising when it is unset.

```python
class EnvFactory:
    def get(self, name: str) -> str:
        value = os.getenv(name)
        if value is not None:
            return value
        raise ValueError(f"Environment variable {name} not found")
```

### `DefaultEnvParser`

Single responsibility: recognise the `ENV_` prefix and delegate reading to
`EnvFactory`. Unlike `DefaultSecretParser`, it does **not** catch `ValueError`,
so a missing variable propagates.

```python
class DefaultEnvParser(EnvParser):
    __PREFIX = "ENV_"

    def __init__(self) -> None:
        self.__env_factory = EnvFactory()

    def parse(self, name: str) -> MirrorEnv | None:
        if not name.startswith(self.__PREFIX):
            return None
        variable_name = name[len(self.__PREFIX):]
        return MirrorEnv(self.__env_factory.get(variable_name))
```

## Wiring (parallel `env_parser` parameter)

Add `env_parser: EnvParser = DefaultEnvParser()` alongside the existing
`secret_parser` everywhere it flows:

1. **`Mirror.__new__` / `Mirror.__init__`** — new keyword parameter, passed to
   `MirrorSingletons.get_or_create_instance` and `ReflectionEngine`.
2. **`MirrorSingletons.get_or_create_instance` / `__create_instance_key`** — accept
   `env_parser` and include it in the instance key, so two mirrors with different
   env parsers do not collide in the singleton cache.
3. **`ReflectionEngine.__init__`** — store `env_parser`; pass it to
   `ReferenceService.resolve`; use it in the `__instantiate_model` hook for string
   nodes.
4. **`ReferenceService.resolve` / `__resolve_params`** — accept `env_parser` and
   apply it to string values, the same way `secret_parser` is applied.

### Precedence on a string node

On every string node, run `env_parser` **before** `secret_parser`. Rationale:
`ENV_FOO` is also all-uppercase, so `DefaultSecretParser` would inspect it too;
the explicit `ENV_` marker must win. (In practice the secret parser also falls
through cleanly since no secret file is named `ENV_FOO`, but running env first
makes the precedence explicit and avoids a needless secret lookup.)

The substitution sites (both in `reflection_engine.__instantiate_model` and
`reference_service.__resolve_params`) become:

```python
if isinstance(node, str):
    mirror_env = env_parser.parse(node)
    if mirror_env:
        return mirror_env.value
    mirror_secret = secret_parser.parse(node)
    if mirror_secret:
        return mirror_secret.value
return node
```

## Testing (TDD, mirroring `tests/test_secret_parser.py`)

Use `unittest`, real environment variables (set in `setUp`, removed in
`tearDown` — analogous to the secret tests writing real files), no mocks. New file
`tests/test_env_parser.py`.

Unit tests — `DefaultEnvParser` / `EnvFactory`:

1. `ENV_`-prefixed name with the variable set → returns `MirrorEnv` whose `value`
   is the variable's value.
2. Prefix is stripped: `"ENV_DATABASE_URL"` reads `DATABASE_URL`, not
   `ENV_DATABASE_URL`.
3. Non-prefixed string → returns `None` (e.g. `"database_url"`, and importantly a
   bare uppercase `"DATABASE_URL"` with no `ENV_`).
4. `ENV_`-prefixed name with the variable **unset** → raises `ValueError`.
5. `ENV_`-prefixed name with the variable set to `""` → returns `MirrorEnv("")`.
6. `EnvFactory.get` returns the value for a set variable; raises `ValueError` for
   an unset one.

Integration tests — `Mirror`:

7. Config containing `"ENV_..."` values reflects with the env values substituted
   and validated by the model.
8. Mixed config: env vars + secrets + `$mirror`/`$instance` references all resolve
   together (mirror `test_mirror_with_mixed_secrets_and_references`).
9. Env reference inside a nested dict/list resolves (mirror
   `test_mirror_secret_in_nested_structure`).
10. Precedence: an `ENV_`-prefixed uppercase value is resolved by the env parser,
    not treated as a secret.
11. Caching on and off behave like the secret tests (same/different objects).

## Out of scope

- A composite/chained parser abstraction (the parallel-parameter approach was
  chosen instead).
- `pydantic_settings`, `.env` file loading, prefixes/case-config beyond the
  `ENV_` marker.
- Changing or refactoring the existing secret parser behaviour.
