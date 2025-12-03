from typing import Any

from modelmirror.parser.model_link import ModelLink
from modelmirror.parser.model_link_parser import ModelLinkParser


class DefaultModelLinkParser(ModelLinkParser):
    def parse(self, value: Any) -> ModelLink | None:
        if isinstance(value, str) and value.startswith("$"):
            if value.endswith("$"):
                return ModelLink(id=value[1:-1], type="type")
            return ModelLink(id=value, type="instance")
        return None
