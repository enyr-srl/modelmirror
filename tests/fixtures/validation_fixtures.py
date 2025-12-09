"""
Shared test fixtures for ValidationService tests.

This module contains all test fixture classes used across the validation
service test suite.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, List

from pydantic import BaseModel, ConfigDict

# ==============================================================================
# Basic Classes
# ==============================================================================


class SafeClass:
    """Class with only safe assignments in __init__."""

    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value


class RegularClass:
    """Regular class with side effects in __init__.

    Demonstrates side effect behavior that should be handled safely.
    """

    class_var: int = 42

    def __init__(self, name: str, callback):
        self.name = name
        self.callback = callback
        callback()  # Side effect - will be executed during validation
        self._data = callback.get_data()  # Side effect - will be executed during validation


class UnsafeClass:
    """Class with multiple function calls in __init__.

    All function calls will be executed during validation.
    """

    def __init__(self, name: str, callback):
        self.name = name
        self.callback = callback
        callback()  # Side effect - will be executed during validation
        self._data = callback()  # Side effect - will be executed during validation


class MixedClass:
    """Class with both safe and unsafe operations in __init__.

    Safe assignments are kept, while function calls are executed.
    """

    def __init__(self, name: str, value: int, func):
        self.name = name  # Safe assignment - kept
        self.value = value  # Safe assignment - kept
        func()  # Unsafe - executed during validation
        self._result = func()  # Unsafe - executed during validation


# ==============================================================================
# Classes with Special Initialization Patterns
# ==============================================================================


class ClassWithClassVars:
    """Class with class variables that should be preserved during validation."""

    default_timeout: int = 30
    max_retries: int = 3

    def __init__(self, name: str, port: int):
        self.name = name
        self.port = port


@dataclass
class DataclassWithPostInit:
    """Dataclass with __post_init__ side effects.

    Post-init methods are always executed during instance creation.
    """

    name: str
    values: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.values.append("processed")
        self._computed = len(self.values)


class PydanticModel(BaseModel):
    """Pydantic model with model_post_init side effects.

    Pydantic's model_post_init is always executed during instance creation.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    port: int
    computed_value: str

    def model_post_init(self, __context):
        self.computed_value = f"{self.name}:{self.port}"


class ComplexClass:
    """Class with complex initialization logic including side effects."""

    version: str = "1.0"

    def __init__(self, config: dict, factory, logger):
        self.config = config
        self.factory = factory
        self.logger = logger
        logger.info("Initializing service")
        self._service = factory.create_service()
        self._connection = self._establish_connection()
        factory.register(self)

    def _establish_connection(self):
        return "connection"


class ClsParameterClass:
    """Class with cls parameter that conflicts with Pydantic."""

    def __init__(self, cls, name: str):
        self.cls = cls
        self.name = name
        cls()


class ComplexUnsafeClass:
    """Class with complex unsafe operations in __init__."""

    def __init__(self, name: str, factory, processor):
        self.name = name
        factory.create()
        self._processed = processor(name)


# ==============================================================================
# Hierarchy Classes (Inheritance Patterns)
# ==============================================================================


class BaseServiceClass:
    """Base service class with initialization logic."""

    service_version: str = "1.0"

    def __init__(self, name: str, logger):
        self.name = name
        self.logger = logger
        logger.info("Initializing base service")

    def log_message(self, msg: str):
        self.logger.info(msg)


class DerivedServiceClass(BaseServiceClass):
    """Derived service that extends base with additional initialization."""

    def __init__(self, name: str, logger, port: int):
        super().__init__(name, logger)
        self.port = port
        logger.info(f"Initialized derived service on port {port}")


class MultiLevelHierarchy:
    """First level of multi-level hierarchy."""

    base_attr: str = "base"

    def __init__(self, name: str):
        self.name = name


class SecondLevelHierarchy(MultiLevelHierarchy):
    """Second level in hierarchy chain."""

    def __init__(self, name: str, value: int):
        super().__init__(name)
        self.value = value


class ThirdLevelHierarchy(SecondLevelHierarchy):
    """Third level in hierarchy chain."""

    def __init__(self, name: str, value: int, config: dict):
        super().__init__(name, value)
        self.config = config


class BaseWithSideEffects:
    """Base class with side effects in initialization."""

    def __init__(self, callback):
        self.callback = callback
        callback.register("base")


class DerivedWithAdditionalSideEffects(BaseWithSideEffects):
    """Derived class that adds more side effects."""

    def __init__(self, callback, processor):
        super().__init__(callback)
        self.processor = processor
        processor.process()


class AbstractBase:
    """Abstract-like base class with pure initialization."""

    def __init__(self, name: str):
        self.name = name

    def do_work(self):
        raise NotImplementedError


class ConcreteImplementation(AbstractBase):
    """Concrete implementation of abstract base."""

    def __init__(self, name: str, service):
        super().__init__(name)
        self.service = service

    def do_work(self):
        return self.service.execute()


class MultipleInheritanceExample:
    """First parent class for multiple inheritance."""

    attr_a: str = "from_a"

    def __init__(self, param_a: str):
        self.param_a = param_a


class MultipleInheritanceExampleB:
    """Second parent class for multiple inheritance."""

    attr_b: str = "from_b"

    def __init__(self, param_b: str):
        self.param_b = param_b


class MultipleInheritanceChild(MultipleInheritanceExample, MultipleInheritanceExampleB):
    """Child with multiple inheritance."""

    def __init__(self, param_a: str, param_b: str, param_c: str):
        MultipleInheritanceExample.__init__(self, param_a)
        MultipleInheritanceExampleB.__init__(self, param_b)
        self.param_c = param_c


class BaseDataclassHierarchy:
    """Base class for dataclass hierarchy tests."""

    def __init__(self, name: str):
        self.name = name


class DerivedFromDataclassBase(BaseDataclassHierarchy):
    """Regular class derived from simple base."""

    def __init__(self, name: str, value: int):
        super().__init__(name)
        self.value = value


# ==============================================================================
# Complex Dataclass Hierarchies
# ==============================================================================


@dataclass
class SimpleDataclass:
    """Simple dataclass with basic fields."""

    name: str
    value: int = 0

    def __post_init__(self):
        self.processed = f"{self.name}:{self.value}"


@dataclass
class DataclassWithDefaults:
    """Dataclass with complex default values."""

    name: str
    tags: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.tag_count = len(self.tags)
        self.has_metadata = bool(self.metadata)


@dataclass
class BaseDataclass:
    """Base dataclass for inheritance."""

    id: int
    name: str

    def __post_init__(self):
        self.base_computed = f"base_{self.id}_{self.name}"


@dataclass
class DerivedDataclass(BaseDataclass):
    """Dataclass derived from another dataclass."""

    description: str = ""

    def __post_init__(self):
        super().__post_init__()
        self.derived_computed = f"derived_{self.description}"


@dataclass
class MultiLevelDataclass(DerivedDataclass):
    """Three-level dataclass hierarchy."""

    category: str = "default"

    def __post_init__(self):
        super().__post_init__()
        self.level_computed = f"level_{self.category}"


@dataclass
class DataclassWithNestedDataclass:
    """Dataclass containing another dataclass field."""

    title: str
    config: SimpleDataclass

    def __post_init__(self):
        self.combined = f"{self.title}:{self.config.name}"


@dataclass
class DataclassWithCallableField:
    """Dataclass with a callable field that might be triggered."""

    name: str
    processor: Callable[[str], Any] | None = None

    def __post_init__(self):
        if self.processor:
            self.processed_name = self.processor(self.name)
        else:
            self.processed_name = self.name


@dataclass
class DataclassWithMutableDefaults:
    """Dataclass testing mutable default handling."""

    name: str
    items: List[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)

    def __post_init__(self):
        self.item_count = len(self.items)
        self.modified = True


class RegularClassWithDataclass:
    """Regular class containing a dataclass field."""

    def __init__(self, name: str, config: SimpleDataclass):
        self.name = name
        self.config = config
        self.combined_value = f"{name}_{config.value}"


class RegularBaseClass:
    """Regular (non-dataclass) base class."""

    def __init__(self, base_value: int):
        self.base_value = base_value

    def get_base_value(self):
        return self.base_value


@dataclass
class DataclassWithRegularInheritance(RegularBaseClass):
    """Dataclass inheriting from a regular (non-dataclass) class."""

    value: int
    extra: str = "default"

    def __post_init__(self):
        # Initialize the regular base class
        super().__init__(self.value)
        self.final_value = self.value * 2
