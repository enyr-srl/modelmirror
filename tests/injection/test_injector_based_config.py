import unittest

from pydantic import BaseModel, ConfigDict


from modelmirror.mirror import Mirror

from tests.injection.nested.dict.test_nested_dict_singleton import TestNestedDictSingleton
from tests.injection.nested.list.test_nested_list import TestNestedList
from tests.injection.nested.list.test_nested_list_singleton import TestNestedListSingleton
from tests.injection.test import Test
from tests.injection.test_compose import TestCompose
from tests.injection.nested.dict.test_nested_dict import TestNestedDict
from tests.injection.test_pydantic import TestPydantic


class TestSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')
    instances_pydantic: list[TestPydantic]
    instances: list[Test]
    test_pydantic2: TestPydantic
    ciao: Test
    test1: Test
    composed_test: TestCompose

class TestNestedDictSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')
    test_nested: TestNestedDict

class TestNestedListSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')
    nested_list: TestNestedList

class TestNestedListSingletonSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')
    nested_list: TestNestedListSingleton

class TestNestedDictSingletonSchema(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')
    test_singleton: TestNestedDictSingleton

class TestBaseModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')
    test_pydantic: TestPydantic
    
class TestInjectorBasedConfig(unittest.TestCase):
    def test_nested_list_singleton(self):
        schema = Mirror('tests').reflect_typed('/workspace/tests/injection/nested/list/testNestedListSingleton.json', TestNestedListSingletonSchema)
        assert schema.nested_list.test_singleton == schema.nested_list.tests[0]

    def test_nested_list(self):
        schema = Mirror('tests').reflect_typed('/workspace/tests/injection/nested/list/testNestedList.json', TestNestedListSchema)
        schema.nested_list.say_hello()

    def test_nested_dict_singleton(self):
        schema = Mirror('tests').reflect_typed('/workspace/tests/injection/nested/dict/testNestedDictSingleton.json', TestNestedDictSingletonSchema)
        singleton = schema.test_singleton
        assert singleton.test_p_p == singleton.test_singleton

    def test_nested_dict(self):
        schema = Mirror('tests').reflect_typed('/workspace/tests/injection/nested/dict/testNestedDict.json', TestNestedDictSchema)
        test = schema.test_nested
        test.say_hello()

    def test_reflect_model(self):
        schema = Mirror('tests').reflect_typed('/workspace/tests/injection/testConfigProp.json', TestSchema)
        test = schema.test_pydantic2
        test.say_hello()

    def test_config_reflection(self):
        reflections = Mirror('tests').reflect_raw('/workspace/tests/injection/testConfigProp.json')
        test = reflections.get(Test, '$test2')
        tests = reflections.get(dict[str, TestPydantic])
        print(test)

    def test_base_model(self):
        configuration = Mirror('tests').reflect_typed('/workspace/tests/injection/testBaseModel.json', TestBaseModel)
        test = configuration.test_pydantic
        test.say_hello()
        
