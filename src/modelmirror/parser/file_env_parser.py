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
