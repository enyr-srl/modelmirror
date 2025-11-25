from dataclasses import dataclass
from typing import Any

from modelmirror.class_provider.class_reference import ClassReference


@dataclass
class InstanceProperties:
    node_id: str
    parent_type: type
    class_reference: ClassReference
    refs: list[str]
    config_params: dict[str, Any]
