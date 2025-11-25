from typing import Any, Type, TypeVar

T = TypeVar("T")


class InstanceContainer:
    def __init__(self, instances: dict[str, Any]):
        self.__instances = instances
        self.__class_names: dict[type, list[str]] = {}

        self.__classes: dict[type, Any] = {}
        self.__lists: dict[type, list[Any]] = {}
        self.__dicts: dict[type, dict[str, Any]] = {}

        self.__set_class_names()
        self.__bind_instances()

    def get_id(self, id: str, interface: Type[T]) -> T:
        if id in self.__instances:
            return self.__instances[id]
        raise TypeError(f"Unknown instance id: {id}")

    def get_cls(self, interface: Type[T]) -> T:
        if interface not in self.__classes:
            raise TypeError(f"Unknown instance type: {interface}")
        return self.__classes[interface]  # type: ignore

    def get_dict(self, interface: type[dict[str, type]]) -> dict[str, Any]:
        return self.__dicts[interface]

    def get_list(self, interface: type[list[type]]) -> list[Any]:
        return self.__lists.get(interface, [])

    def __update_class(self, interface: type, impl: Any):
        self.__classes[interface] = impl

    def __update_dict(self, interface: type[dict[str, type]], impl: dict[str, Any]):
        if interface not in self.__dicts:
            self.__dicts[interface] = {}
        self.__dicts[interface] = impl

    def __update_list(self, interface: type[list[type]], impl: list[Any]):
        if interface not in self.__lists:
            self.__lists[interface] = []
        self.__lists[interface].extend(impl)

    def __set_class_names(self) -> None:
        for name, instance in self.__instances.items():
            hierarchy_types = [clazz for clazz in type(instance).mro() if clazz is not object]
            for hierarchy_type in hierarchy_types:
                if hierarchy_type not in self.__class_names:
                    self.__class_names[hierarchy_type] = []
                self.__class_names[hierarchy_type].append(name)

    def __bind_instances(self) -> None:
        for hierarchy_type, names in self.__class_names.items():
            if len(names) == 1:
                self.__update_class(hierarchy_type, self.__instances[names[0]])
            name_type = {name: self.__instances[name] for name in names}
            self.__update_dict(dict[str, hierarchy_type], name_type)  # type: ignore[valid-type]
            types = [self.__instances[name] for name in names]
            self.__update_list(list[hierarchy_type], types)  # type: ignore[valid-type]
