import unittest
from modelmirror.utils import json_utils


class TestJsonUtils(unittest.TestCase):
    def test_hook_with_parent(self):
        with open('/workspace/tests/injection/testConfigProp.json') as file:
            result = json_utils.json_load_with_context(file, self.my_hook)
            print(result)
    
    def my_hook(self, node_context: json_utils.NodeContext):
        node = node_context.node
        parent_key = node_context.parent_key
        parent_type = node_context.parent_type
        if "$reference" in node:
            print(f"parent_key={parent_key!r}, parent_type={parent_type!r}")
        return node

        