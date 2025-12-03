from dataclasses import dataclass
from typing import Any

from modelmirror.class_provider.class_scanner import IsolatedClassReference
from modelmirror.parser.model_link import ModelLink


@dataclass
class InstanceProperties:
    node_id: str
    parent_type: type
    class_reference: IsolatedClassReference
    model_links: list[ModelLink]
    config_params: dict[str, Any]
