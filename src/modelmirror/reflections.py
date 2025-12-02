import inspect
from typing import Any, Type, TypeVar, get_origin, overload

from modelmirror.instance.instance_container import InstanceContainer
from modelmirror.parser.model_link_parser import ModelLinkParser

T = TypeVar("T")


class Reflections:
    def __init__(self, instances: dict[str, Any], singleton_path: dict[str, str], model_link_parser: ModelLinkParser):
        self.__instance_container = InstanceContainer(instances)
        self.__singleton_path = singleton_path
        self.__model_link_parser = model_link_parser

    @overload
    def get(self, type: Type[T]) -> T: ...

    @overload
    def get(self, type: Type[T], id: str) -> T: ...

    @overload
    def get(self, type: list[Type[T]]) -> list[T]: ...

    @overload
    def get(self, type: dict[str, Type[T]]) -> dict[str, T]: ...

    def get(self, type: Any, id: Any | None = None) -> Any:
        if get_origin(type) == dict:
            return self.__instance_container.get_dict(type)  # type: ignore

        if get_origin(type) == list:
            return self.__instance_container.get_list(type)  # type: ignore

        if inspect.isclass(type) and id is not None:
            model_link = self.__model_link_parser.parse(id)
            if model_link and model_link.type == "instance":
                id = self.__singleton_path[model_link.id]
            return self.__instance_container.get_id(id, type)

        if id is None:
            return self.__instance_container.get_cls(type)  # type: ignore

        raise TypeError("Unsupported configuration arguments to get()")
