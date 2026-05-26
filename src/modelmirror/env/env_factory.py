import os


class EnvFactory:
    def get(self, name: str) -> str:
        value = os.getenv(name)
        if value is not None:
            return value
        raise ValueError(f"Environment variable {name} not found")
