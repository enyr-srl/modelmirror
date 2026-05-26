from abc import ABC, abstractmethod

from modelmirror.parser.mirror_env import MirrorEnv


class EnvParser(ABC):
    @abstractmethod
    def parse(self, name: str) -> MirrorEnv | None:
        raise NotImplementedError
