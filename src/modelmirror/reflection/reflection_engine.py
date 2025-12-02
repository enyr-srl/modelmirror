"""
Core reflection engine for processing configurations.
"""

from glob import glob
from graphlib import TopologicalSorter
from typing import Any, TypeVar

from pydantic import BaseModel

from modelmirror.class_provider.class_reference import ClassReference
from modelmirror.instance.instance_properties import InstanceProperties
from modelmirror.instance.reference_service import ReferenceService
from modelmirror.parser.code_link_parser import CodeLinkParser
from modelmirror.parser.value_parser import ValueParser
from modelmirror.reflections import Reflections
from modelmirror.utils import json_utils
from modelmirror.utils.json_utils import NodeContext

T = TypeVar("T", bound=BaseModel)


class ReflectionEngine:
    """Core engine for processing configuration reflections."""

    def __init__(
        self, registered_classes: list[ClassReference], code_link_parser: CodeLinkParser, value_parser: ValueParser
    ):
        self.__registered_classes = registered_classes
        self.__code_link_parser = code_link_parser
        self.__instance_properties: dict[str, InstanceProperties] = {}
        self.__singleton_path: dict[str, str] = {}
        self.__value_parser = value_parser
        self.__reset_state()

    def reflect_typed(self, config_path: str, model: type[T]) -> T:
        self.__reset_state()

        reflection_config_file = self.__get_reflection_config_file(config_path)
        with open(reflection_config_file) as file:
            json_utils.json_load_with_context(file, self.__create_instance_map)
            instances = self.__resolve_instances()

        with open(reflection_config_file) as file:
            raw_model = json_utils.json_load_with_context(file, hook=self.__instantiate_model(instances))
            return model(**raw_model)

    def reflect_raw(self, config_path: str) -> Reflections:
        self.__reset_state()

        reflection_config_file = self.__get_reflection_config_file(config_path)
        with open(reflection_config_file) as file:
            json_utils.json_load_with_context(file, self.__create_instance_map)
            return Reflections(self.__resolve_instances(), self.__singleton_path)

    def __reset_state(self):
        self.__reference_service = ReferenceService()
        self.__instance_properties: dict[str, InstanceProperties] = {}
        self.__singleton_path: dict[str, str] = {}

    def __get_reflection_config_file(self, config_path: str) -> str:
        reflection_config = glob(config_path)
        if len(reflection_config) == 1:
            return reflection_config[0]
        raise Exception("Wrong config path")

    def __create_instance_map(self, node_context: NodeContext):
        node = node_context.node

        if not isinstance(node, dict):
            return node
        if not self.__code_link_parser._is_code_link_node(node):
            return node
        code_link = self.__code_link_parser.parse(node)
        if not code_link:
            return node
        class_reference = self.__get_class_reference(code_link.id)

        node_id = node_context.path_str
        refs = self.__reference_service.find(list(code_link.params.values()))

        self.__instance_properties[node_id] = InstanceProperties(
            node_id,
            node_context.parent_type,
            class_reference,
            refs,
            code_link.params,
        )

        instance = code_link.instance
        if not instance:
            return node
        if instance in self.__singleton_path:
            raise Exception(
                f"Duplicate instance ID '{instance}'. Instance IDs must be globally unique across the whole config file."
            )
        self.__singleton_path[instance] = node_id

    def __get_class_reference(self, id: str) -> ClassReference:
        for registered_class in self.__registered_classes:
            if registered_class.id == id:
                return registered_class
        raise ValueError(f"Registry item with id {id} not found")

    def __resolve_instances(self) -> dict[str, Any]:
        instance_refs: dict[str, list[str]] = {}
        for instance, properties in self.__instance_properties.items():
            instance_refs[instance] = self.__refs_to_paths(properties.refs)
        instance_names = list(TopologicalSorter(instance_refs).static_order())
        return self.__reference_service.resolve(instance_names, self.__instance_properties, self.__singleton_path)

    def __refs_to_paths(self, refs: list[str]) -> list[str]:
        paths: list[str] = []
        for ref in refs:
            if ref not in self.__singleton_path:
                raise Exception(f"Id {ref} has not a corresponding reference")
            paths.append(self.__singleton_path[ref])
        return paths

    def __instantiate_model(self, instances: dict[str, Any]):
        def _hook(node_context: json_utils.NodeContext) -> Any:
            node = node_context.node
            instance_id = node_context.path_str
            if instance_id in instances:
                return instances[instance_id]
            if isinstance(node, str) and node.startswith("$"):
                if node not in self.__singleton_path:
                    raise Exception(f"Instance '{node}' not found")
                instance_path = self.__singleton_path[node]
                if instance_path not in instances:
                    raise Exception(f"Instance path '{instance_path}' not found")
                return instances[instance_path]
            return node

        return _hook
