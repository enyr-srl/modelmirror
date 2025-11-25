from typing import Any, Mapping

from modelmirror.instance.instance_properties import InstanceProperties


class ReferenceService:
    def __init__(self) -> None:
        self.__instances: dict[str, Any] = {}

    def resolve(
        self,
        instance_names: list[str],
        instance_properties: dict[str, InstanceProperties],
        singleton_path: dict[str, str],
    ) -> dict[str, Any]:
        self.__instances = {}
        for instance_name in instance_names:
            properties = instance_properties.get(instance_name)
            if properties:
                resolved_params = self.__resolve_params(properties, self.__instances, singleton_path)
                self.__instances.update({instance_name: properties.class_reference.cls(**resolved_params)})
        return self.__instances

    def find(self, values: list[str]) -> list[str]:
        def resolve_value(value: Any) -> Any:
            if isinstance(value, str) and value.startswith("$"):
                refs.add(value)

            # Recurse into dicts
            if isinstance(value, Mapping):
                return {k: resolve_value(v) for k, v in value.items()}

            # Recurse into lists/tuples
            if isinstance(value, list):
                return [resolve_value(v) for v in value]
            if isinstance(value, tuple):
                return tuple(resolve_value(v) for v in value)

            # Anything else is returned as-is
            return value

        refs: set[str] = set()
        for v in values:
            resolve_value(v)
        return list(refs)

    def __resolve_params(
        self, properties: InstanceProperties, instances: dict[str, Any], singleton_path: dict[str, str]
    ) -> dict[str, Any]:
        def resolve_value(key: str, value: Any, node_id: str) -> Any:
            # "$something" -> instances["something"]
            if isinstance(value, str) and value.startswith("$"):
                if value not in singleton_path:
                    raise KeyError(f"No instance found for '{value}'")
                instance_path = singleton_path[value]
                if instance_path not in instances:
                    raise KeyError(f"Instance '{instance_path}' not found for id {value[1:]}")
                return instances[instance_path]

            if f"{node_id}.{key}" in instances:
                return instances[f"{node_id}.{key}"]

            # Recurse into dicts
            if isinstance(value, Mapping):
                return {k: resolve_value(k, v, f"{node_id}.{key}") for k, v in value.items()}

            # Recurse into lists/tuples
            if isinstance(value, list):
                return [resolve_value(str(i), v, f"{node_id}.{key}") for i, v in enumerate(value)]

            if isinstance(value, tuple):
                return tuple(resolve_value(str(i), v, f"{node_id}.{i}") for i, v in enumerate(value))

            # Anything else is returned as-is
            return value

        return {k: resolve_value(k, v, properties.node_id) for k, v in properties.config_params.items()}
