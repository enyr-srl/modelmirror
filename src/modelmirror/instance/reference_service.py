from typing import Any, Mapping

from modelmirror.class_provider.class_scanner import ClassReference
from modelmirror.instance.instance_properties import InstanceProperties
from modelmirror.instance.validation_service import ValidationService
from modelmirror.parser.model_link import ModelLink
from modelmirror.parser.model_link_parser import ModelLinkParser
from modelmirror.parser.secret_parser import SecretParser


class ReferenceService:
    def __init__(self) -> None:
        self.__instances: dict[str, Any] = {}
        self.__validation_service: ValidationService = ValidationService()

    def resolve(
        self,
        instance_names: list[str],
        instance_properties: dict[str, InstanceProperties],
        singleton_path: dict[str, str],
        model_link_parser: ModelLinkParser,
        registered_classes: list[ClassReference],
        secret_parser: SecretParser,
    ) -> dict[str, Any]:
        self.__instances = {}
        for instance_name in instance_names:
            properties = instance_properties.get(instance_name)
            if properties:
                resolved_params = self.__resolve_params(
                    properties, self.__instances, singleton_path, model_link_parser, registered_classes, secret_parser
                )
                self.__validation_service.validate_or_raise(properties.class_reference.cls, resolved_params)
                original_instance = (properties.class_reference.cls)(**resolved_params)
                self.__instances.update({instance_name: original_instance})
        return self.__instances

    def find(self, values: list[Any], model_link_parser: ModelLinkParser) -> list[ModelLink]:
        def resolve_value(value: Any) -> Any:
            model_link = model_link_parser.parse(value)
            if model_link:
                model_links.add(model_link)
                return value

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

        model_links: set[ModelLink] = set()
        for value in values:
            resolve_value(value)
        return list(model_links)

    def __resolve_params(
        self,
        properties: InstanceProperties,
        instances: dict[str, Any],
        singleton_path: dict[str, str],
        model_link_parser: ModelLinkParser,
        registered_classes: list[ClassReference],
        secret_parser: SecretParser,
    ) -> dict[str, Any]:
        def resolve_value(key: str, value: Any, node_id: str) -> Any:
            # "$something" -> instances["something"]
            model_link = model_link_parser.parse(value)
            if model_link:
                if model_link.type == "instance":
                    value = model_link.id
                    if value not in singleton_path:
                        raise KeyError(f"No instance found for '{value}'")
                    instance_path = singleton_path[value]
                    if instance_path not in instances:
                        raise KeyError(f"Instance '{instance_path}' not found for id {value[1:]}")
                    return instances[instance_path]

                if model_link.type == "type":
                    for registered_class in registered_classes:
                        if registered_class.id == model_link.id:
                            return registered_class.cls
                    raise KeyError(f"Class '{model_link.id}' not found. Check classes registration")

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

            if isinstance(value, str):
                mirror_secret = secret_parser.parse(value)
                if mirror_secret:
                    return mirror_secret.value
            return value

        return {k: resolve_value(k, v, properties.node_id) for k, v in properties.config_params.items()}
