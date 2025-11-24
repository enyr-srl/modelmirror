import inspect
from typing import Any, Type, TypeVar, get_origin, overload

from modelmirror.instance.instance_container import InstanceContainer

T = TypeVar("T")


class Reflections:
    def __init__(self, instances: dict[str, Any], singleton_path: dict[str, str]):
        self.__instances = instances
        self.__class_names: dict[type, list[str]] = {}
        self.__instance_container = InstanceContainer(instances)
        self.__singleton_path = singleton_path

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

        if inspect.isclass(type) and id is not None and isinstance(id, str):
            if id.startswith("$"):
                id = self.__singleton_path[id]
            return self.__instance_container.get_id(id, type)

        if id is None:
            if type not in self.__class_names:
                raise TypeError(f"Unknown instance type: {type}")
            if len(self.__class_names[type]) > 1:
                raise TypeError(f"Multiple instances of type: {type}")
            return self.__instance_container.get_cls(type)  # type: ignore

        raise TypeError("Unsupported configuration arguments to get()")
