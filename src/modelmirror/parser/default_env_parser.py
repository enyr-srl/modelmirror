from modelmirror.envs.env_factory import EnvFactory
from modelmirror.parser.env_parser import EnvParser
from modelmirror.parser.mirror_env import MirrorEnv


class DefaultEnvParser(EnvParser):
    _PREFIX = "ENV_"

    def __init__(self) -> None:
        self.__env_factory = EnvFactory()

    def parse(self, name: str) -> MirrorEnv | None:
        if not name.startswith(self._PREFIX):
            return None
        variable_name = name.removeprefix(self._PREFIX)
        return MirrorEnv(self.__env_factory.get(variable_name))
