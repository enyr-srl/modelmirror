import threading
from typing import Any

from modelmirror.parser.code_link_parser import CodeLinkParser
from modelmirror.parser.model_link_parser import ModelLinkParser


class MirrorSingletons:
    __instances: dict[str, Any] = {}
    __lock = threading.Lock()

    @classmethod
    def get_or_create_instance(
        cls,
        mirror_class: type,
        package_name: str,
        code_link_parser: CodeLinkParser,
        model_link_parser: ModelLinkParser,
    ) -> Any:
        """Get existing singleton or create new one."""
        instance_key = cls.__create_instance_key(package_name, code_link_parser, model_link_parser)

        with cls.__lock:
            if instance_key not in cls.__instances:
                instance: Any = object.__new__(mirror_class)
                cls.__instances[instance_key] = instance

            return cls.__instances[instance_key]

    @classmethod
    def __create_instance_key(
        cls, package_name: str, code_link_parser: CodeLinkParser, model_link_parser: ModelLinkParser
    ) -> str:
        """Create unique key for Mirror instance."""
        return f"{package_name}:{id(code_link_parser)}:{id(model_link_parser)}"
