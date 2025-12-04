from abc import ABC, abstractmethod

from modelmirror.parser.miirror_secret import MirrorSecret


class SecretParser(ABC):
    @abstractmethod
    def parse(self, name: str) -> MirrorSecret | None:
        raise NotImplementedError
