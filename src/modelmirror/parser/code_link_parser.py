from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, final


@dataclass
class ParsedKey:
    id: str
    params: dict[str, Any]
    instance: str | None = None


class CodeLinkParser(ABC):
    @abstractmethod
    def _is_code_link_node(self, node: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _is_valid(self, node: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _create_code_link(self, node: dict[str, Any]) -> ParsedKey:
        raise NotImplementedError

    @final
    def parse(self, node: dict[str, Any]) -> ParsedKey | None:
        if not self._is_code_link_node(node):
            return None
        if not self._is_valid(node):
            return None
        return self._create_code_link(node)
