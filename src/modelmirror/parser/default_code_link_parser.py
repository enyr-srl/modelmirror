from typing import Any

from modelmirror.parser.code_link_parser import CodeLinkParser, ParsedKey


class DefaultCodeLinkParser(CodeLinkParser):
    __name__: str

    def __init__(self, placeholder: str = "$mirror"):
        self._placeholder = placeholder
        self.__name__ = f"{self.__class__.__name__}:{placeholder}"

    def _is_code_link_node(self, node: dict[str, Any]) -> bool:
        if self._placeholder in node:
            return True
        return False

    def _is_valid(self, node: dict[str, Any]) -> bool:
        if isinstance(node[self._placeholder], str):
            return True
        raise ValueError(f"Value of '{self._placeholder}' must be a string")

    def _create_code_link(self, node: dict[str, Any]) -> ParsedKey:
        raw_reference: str = node.pop(self._placeholder)
        params: dict[str, Any] = {name: prop for name, prop in node.items()}
        if ":" in raw_reference:
            id, instance = raw_reference.split(":", 1)
            return ParsedKey(id=id, instance=f"${instance}", params=params)
        return ParsedKey(id=raw_reference, instance=None, params=params)
