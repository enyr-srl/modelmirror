from typing import Any

from modelmirror.parser.reference_parser import ReferenceParser


class MirrorSingletons:
    __instances: dict[str, Any] = {}

    @classmethod
    def get_or_create_instance(
        cls, mirror_class: type, package_name: str, parser: ReferenceParser, placeholder: str
    ) -> Any:
        """Get existing singleton or create new one."""
        instance_key = cls.__create_instance_key(package_name, parser, placeholder)

        if instance_key not in cls.__instances:
            instance: Any = object.__new__(mirror_class)
            cls.__instances[instance_key] = instance

        return cls.__instances[instance_key]

    @classmethod
    def __create_instance_key(cls, package_name: str, parser: ReferenceParser, placeholder: str) -> str:
        """Create unique key for Mirror instance."""
        return f"{package_name}:{type(parser).__name__}:{placeholder}"
