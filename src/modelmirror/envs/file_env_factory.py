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
