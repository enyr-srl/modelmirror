from modelmirror.class_provider.class_register import ClassRegister
from modelmirror.class_provider.class_reference import ClassReference
from tests.injection.nested.dict.test_nested_dict_singleton import TestNestedDictSingleton
from tests.injection.nested.list.test_nested_list import TestNestedList
from tests.injection.nested.list.test_nested_list_singleton import TestNestedListSingleton
from tests.injection.test import Test
from tests.injection.test_compose import TestCompose
from tests.injection.nested.dict.test_nested_dict import TestNestedDict
from tests.injection.test_pydantic import TestPydantic


class TestClassRegister(ClassRegister, reference=ClassReference(schema="test", version="0.0.1", cls=Test)):
    ...

class ComposedTestClassRegister(ClassRegister, reference=ClassReference(schema="test_compose", version="0.0.1", cls=TestCompose)):
    ...

class PydanticTestClassRegister(ClassRegister, reference=ClassReference(schema="test_pydantic", version="0.0.1", cls=TestPydantic)):
    ...

class TestNestedDictClassRegister(ClassRegister, reference=ClassReference(schema="test-nested", version="0.0.1", cls=TestNestedDict)):
    ...

class TestNestedSingletonClassRegister(ClassRegister, reference=ClassReference(schema="test-nested-singleton", version="0.0.1", cls=TestNestedDictSingleton)):
    ...

class TestNestedListClassRegister(ClassRegister, reference=ClassReference(schema="test-nested-list", version="0.0.1", cls=TestNestedList)):
    ...

class TestNestedListSingletonClassRegister(ClassRegister, reference=ClassReference(schema="test-nested-list-singleton", version="0.0.1", cls=TestNestedListSingleton)):
    ...
