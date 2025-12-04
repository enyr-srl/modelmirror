from modelmirror.parser.miirror_secret import MirrorSecret
from modelmirror.parser.secret_parser import SecretParser
from modelmirror.secrets.secret_factory import SecretFactory


class DefaultSecretParser(SecretParser):
    def __init__(self, secrets_dir: str) -> None:
        self.__secret_factory = SecretFactory(secrets_dir)

    def parse(self, name: str) -> MirrorSecret | None:
        if name.isupper():
            return MirrorSecret(self.__secret_factory.get(name))
        return None
