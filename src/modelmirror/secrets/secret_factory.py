from pathlib import Path

from pydantic_settings import BaseSettings


class SecretFactory:
    def __init__(self, secrets_dir: str):
        self.__env: Environment = Environment(secrets_dir)

    def get(self, name: str) -> str:
        return self.__env.get_secret(name)


class Environment(BaseSettings):
    def __init__(self, secrets_dir: str):
        super().__init__(_secrets_dir=secrets_dir)
        self.__secrets_cache = self.__load_secrets(secrets_dir)

    def __load_secrets(self, secrets_dir: str) -> dict[str, str]:
        path = Path(secrets_dir)
        if not path.is_dir():
            return {}

        secrets: dict[str, str] = {}
        for secret_file in path.iterdir():
            if secret_file.is_file():
                secrets[secret_file.name] = secret_file.read_text(encoding="utf-8").strip()
        return secrets

    def get_secret(self, name: str) -> str:
        secret: str | None = self.__secrets_cache.get(name)
        if secret:
            return secret
        raise ValueError(f"Secret {name} not found")
