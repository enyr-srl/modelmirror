from typing import Any, TypeVar

from pydantic import BaseModel

from modelmirror.class_provider.class_scanner import ClassScanner
from modelmirror.parser.code_link_parser import CodeLinkParser
from modelmirror.parser.default_code_link_parser import DefaultCodeLinkParser
from modelmirror.parser.default_model_link_parser import DefaultModelLinkParser
from modelmirror.parser.model_link_parser import ModelLinkParser
from modelmirror.reflection.reflection_engine import ReflectionEngine
from modelmirror.reflections import Reflections
from modelmirror.singleton.singleton_manager import MirrorSingletons

T = TypeVar("T", bound=BaseModel)


class Mirror:
    def __new__(
        cls,
        package_name: str = "app",
        code_link_parser: CodeLinkParser = DefaultCodeLinkParser(),
        model_link_parser: ModelLinkParser = DefaultModelLinkParser(),
        check_circular_types: bool = True,
    ) -> "Mirror":
        return MirrorSingletons.get_or_create_instance(
            cls, package_name, code_link_parser, model_link_parser, check_circular_types
        )

    def __init__(
        self,
        package_name: str = "app",
        code_link_parser: CodeLinkParser = DefaultCodeLinkParser(),
        model_link_parser: ModelLinkParser = DefaultModelLinkParser(),
        check_circular_types: bool = True,
    ):
        if hasattr(self, "_initialized"):
            return

        scanner = ClassScanner(package_name)
        registered_classes = scanner.scan()

        self.__engine = ReflectionEngine(registered_classes, code_link_parser, model_link_parser, check_circular_types)
        self.__cache: dict[str, Any] = {}
        self._initialized = True

    def reflect(self, config_path: str, model: type[T], *, cached: bool = True) -> T:
        """Reflect configuration with optional caching."""
        if not cached:
            return self.__engine.reflect_typed(config_path, model)

        cache_key = f"{config_path}:{model.__name__}"
        if cache_key in self.__cache:
            return self.__cache[cache_key]

        result = self.__engine.reflect_typed(config_path, model)
        self.__cache[cache_key] = result
        return result

    def reflect_raw(self, config_path: str, *, cached: bool = True) -> Reflections:
        """Reflect configuration returning raw instances with optional caching."""
        if not cached:
            return self.__engine.reflect_raw(config_path)

        cache_key = f"{config_path}:raw"
        if cache_key in self.__cache:
            return self.__cache[cache_key]

        result = self.__engine.reflect_raw(config_path)
        self.__cache[cache_key] = result
        return result
