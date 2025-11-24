import json
from dataclasses import dataclass
from typing import Any, Callable, TextIO

PathItem = str | int


@dataclass
class NodeContext:
    node: Any
    parent_type: type
    parent_key: PathItem | None
    path: tuple[PathItem, ...]  # full path from root to this node

    @property
    def path_str(self) -> str:
        return ".".join([str(part) for part in self.path])


HookWithContext = Callable[[NodeContext], Any]


def json_load_with_context(fp: TextIO, hook: HookWithContext) -> Any:
    data = json.load(fp)
    return _walk(data, parent=None, parent_key=None, path=(), hook=hook)


def json_loads_with_context(s: str, hook: HookWithContext) -> Any:
    data = json.loads(s)
    return _walk(data, parent=None, parent_key=None, path=(), hook=hook)


def _walk(
    node: Any,
    parent: Any | None,
    parent_key: PathItem | None,
    path: tuple[PathItem, ...],
    hook: HookWithContext,
) -> Any:

    if isinstance(node, dict):
        # Recurse into children, mutating dict in place
        for k, v in list(node.items()):
            child_path = (*path, k)
            node[k] = _walk(v, parent=node, parent_key=k, path=child_path, hook=hook)
        return hook(NodeContext(node, type(parent), parent_key, path))

    elif isinstance(node, list):
        # Recurse into children, mutating list in place
        for i, item in enumerate(node):
            child_path = (*path, i)
            node[i] = _walk(item, parent=node, parent_key=i, path=child_path, hook=hook)
        return hook(NodeContext(node, type(parent), parent_key, path))

    else:
        # Primitive
        return hook(NodeContext(node, type(parent), parent_key, path))
