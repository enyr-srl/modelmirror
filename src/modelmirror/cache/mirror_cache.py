from typing import Any


class MirrorCache:
    __global_cache: dict[str, Any] = {}

    @classmethod
    def get_cached(cls, cache_key: str) -> Any | None:
        return cls.__global_cache.get(cache_key)

    @classmethod
    def set_cached(cls, cache_key: str, result: Any) -> None:
        cls.__global_cache[cache_key] = result

    @classmethod
    def create_cache_key(cls, config_path: str, model_name: str) -> str:
        return f"{config_path}:{model_name}"

    @classmethod
    def create_raw_cache_key(cls, config_path: str) -> str:
        return f"{config_path}:raw"
