from abc import ABC, abstractmethod
from typing import Any, final

from modelmirror.parser.code_link import CodeLink


class CodeLinkParser(ABC):
    @abstractmethod
    def _is_code_link_node(self, node: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _is_valid(self, node: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _create_code_link(self, node: dict[str, Any]) -> CodeLink:
        raise NotImplementedError

    @final
    def parse(self, node: dict[str, Any]) -> CodeLink | None:
        if not self._is_code_link_node(node):
            return None
        if not self._is_valid(node):
            return None
        return self._create_code_link(node)
