"""
Class registers for test fixtures.
These registers link the test classes to their schema identifiers.
"""

from modelmirror.class_provider.class_reference import ClassReference
from modelmirror.class_provider.class_register import ClassRegister
from tests.fixtures.test_classes import (
    ComplexService,
    ConfigurableService,
    DatabaseService,
    DictService,
    ListService,
    NestedService,
    ServiceWithDefaults,
    ServiceWithOptionals,
    SimpleService,
    UserService,
    ValidationService,
)
from tests.fixtures.test_classes_with_types import CircularServiceA, CircularServiceB, ServiceWithTypeRef
from tests.fixtures.test_factory_classes import CircularDependentService, DependentService, ServiceFactory


class SimpleServiceRegister(ClassRegister):
    reference = ClassReference(id="simple_service", cls=SimpleService)


class DatabaseServiceRegister(ClassRegister):
    reference = ClassReference(id="database_service", cls=DatabaseService)


class UserServiceRegister(ClassRegister):
    reference = ClassReference(id="user_service", cls=UserService)


class ConfigurableServiceRegister(ClassRegister):
    reference = ClassReference(id="configurable_service", cls=ConfigurableService)


class ComplexServiceRegister(ClassRegister):
    reference = ClassReference(id="complex_service", cls=ComplexService)


class ServiceWithDefaultsRegister(ClassRegister):
    reference = ClassReference(id="service_with_defaults", cls=ServiceWithDefaults)


class ServiceWithOptionalsRegister(ClassRegister):
    reference = ClassReference(id="service_with_optionals", cls=ServiceWithOptionals)


class ListServiceRegister(ClassRegister):
    reference = ClassReference(id="list_service", cls=ListService)


class DictServiceRegister(ClassRegister):
    reference = ClassReference(id="dict_service", cls=DictService)


class NestedServiceRegister(ClassRegister):
    reference = ClassReference(id="nested_service", cls=NestedService)


class ValidationServiceRegister(ClassRegister):
    reference = ClassReference(id="validation_service", cls=ValidationService)


class ServiceWithTypeRefRegister(ClassRegister):
    reference = ClassReference(id="service_with_type_ref", cls=ServiceWithTypeRef)


class CircularServiceARegister(ClassRegister):
    reference = ClassReference(id="circular_service_a", cls=CircularServiceA)


class CircularServiceBRegister(ClassRegister):
    reference = ClassReference(id="circular_service_b", cls=CircularServiceB)


class ServiceFactoryRegister(ClassRegister):
    reference = ClassReference(id="service_factory", cls=ServiceFactory)


class DependentServiceRegister(ClassRegister):
    reference = ClassReference(id="dependent_service", cls=DependentService)


class CircularDependentServiceRegister(ClassRegister):
    reference = ClassReference(id="circular_dependent_service", cls=CircularDependentService)
