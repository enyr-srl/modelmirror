"""
Test suite for ValidationService with safe init functionality.

This module tests the ValidationService class which provides safe initialization
of class instances while preventing side effects from being executed.
"""

import unittest
from dataclasses import dataclass, field
from typing import Callable, List
from unittest.mock import Mock

from pydantic import BaseModel, ConfigDict

from modelmirror.instance.validation_service import ValidationService

# ==============================================================================
# TEST FIXTURES: Basic Classes
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
# TEST FIXTURES: Classes with Special Initialization Patterns
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
# TEST FIXTURES: Hierarchy Classes (Inheritance Patterns)
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
# TEST FIXTURES: Complex Dataclass Hierarchies
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
    processor: Callable | None = None

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


@dataclass
class DataclassWithRegularInheritance:
    """Dataclass inheriting from regular class."""

    value: int
    extra: str = "default"

    def __post_init__(self):
        self.final_value = self.value * 2


class TestValidationService(unittest.TestCase):
    """Test ValidationService safe init functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.validation_service = ValidationService()

    def test_regular_class_no_side_effects(self):
        """Test that side effects in regular classes are executed during validation."""
        mock_callback = Mock()
        params = {"name": "test", "callback": mock_callback}

        self.validation_service.validate_or_raise(RegularClass, params)

        # Side effects should be called
        mock_callback.assert_called_once()
        mock_callback.get_data.assert_called_once()

    def test_class_variables_preserved(self):
        """Test that class variables are preserved after validation."""
        params = {"name": "test", "port": 8080}

        isolated_class = self.validation_service.validate_or_raise(ClassWithClassVars, params)

        # Class variables should be preserved
        self.assertEqual(isolated_class.default_timeout, 30)
        self.assertEqual(isolated_class.max_retries, 3)

    def test_dataclass_post_init(self):
        """Test that dataclass __post_init__ is executed during validation."""
        params = {"name": "test", "values": ["initial"]}

        instance = self.validation_service.validate_or_raise(DataclassWithPostInit, params)

        # __post_init__ should be executed
        self.assertEqual(instance.name, "test")
        self.assertEqual(instance.values, ["initial", "processed"])
        self.assertTrue(hasattr(instance, "_computed"))

    def test_pydantic_model_post_init(self):
        """Test that Pydantic model_post_init is executed during validation."""
        params = {"name": "service", "port": 8080, "computed_value": ""}

        instance = self.validation_service.validate_or_raise(PydanticModel, params)

        # model_post_init should be executed
        self.assertEqual(instance.name, "service")
        self.assertEqual(instance.port, 8080)
        self.assertEqual(instance.computed_value, "service:8080")

    def test_complex_class(self):
        """Test that side effects in complex classes are executed."""
        mock_factory = Mock()
        mock_logger = Mock()
        params = {"config": {"key": "value"}, "factory": mock_factory, "logger": mock_logger}

        self.validation_service.validate_or_raise(ComplexClass, params)

        # Side effect methods should be called
        mock_logger.info.assert_called_once()
        mock_factory.create_service.assert_called_once()
        mock_factory.register.assert_called_once()

    def test_validation_still_works(self):
        """Test that parameter validation works correctly."""
        # Missing required parameter should fail
        with self.assertRaises(Exception):
            self.validation_service.validate_or_raise(RegularClass, {"name": "test"})

        # Valid parameters should work
        mock_callback = Mock()
        params = {"name": "test", "callback": mock_callback}
        self.validation_service.validate_or_raise(RegularClass, params)

    def test_empty_init_class(self):
        """Test class with no __init__ method."""

        class NoInitClass:
            class_var = "test"

        params = {}
        isolated_class = self.validation_service.validate_or_raise(NoInitClass, params)
        self.assertEqual(isolated_class.class_var, "test")

    def test_class_with_only_private_vars(self):
        """Test class with only private variables."""

        class PrivateVarsClass:
            _private_var = "private"
            __very_private = "very_private"
            public_var = "public"

            def __init__(self, name: str):
                self.name = name

        params = {"name": "test"}
        isolated_class = self.validation_service.validate_or_raise(PrivateVarsClass, params)

        self.assertEqual(isolated_class.public_var, "public")
        self.assertTrue(hasattr(isolated_class, "_private_var"))
        self.assertTrue(hasattr(isolated_class, "_PrivateVarsClass__very_private"))

    def test_safe_class_validation(self):
        """Test that safe classes work normally without side effects."""
        params = {"name": "test", "value": 42}

        self.validation_service.validate_or_raise(SafeClass, params)

    def test_unsafe_class_validation_executes_side_effects(self):
        """Test that unsafe classes execute side effects during validation."""
        mock_callback = Mock()
        params = {"name": "test", "callback": mock_callback}

        self.validation_service.validate_or_raise(UnsafeClass, params)

        self.assertEqual(mock_callback.call_count, 2)

    def test_mixed_class_validation(self):
        """Test that mixed classes execute unsafe operations."""
        mock_func = Mock()
        params = {"name": "test", "value": 42, "func": mock_func}

        self.validation_service.validate_or_raise(MixedClass, params)

        # Function should be called twice (unsafe operations)
        self.assertEqual(mock_func.call_count, 2)

    def test_cls_parameter_handling(self):
        """Test that classes with cls parameter are handled correctly."""
        mock_cls = Mock()
        params = {"cls": mock_cls, "name": "test"}

        instance = self.validation_service.validate_or_raise(ClsParameterClass, params)

        instance.cls.assert_called_once()

    def test_complex_unsafe_class(self):
        """Test complex unsafe operations are executed exactly once."""
        mock_factory = Mock()
        mock_processor = Mock()
        params = {"name": "test", "factory": mock_factory, "processor": mock_processor}
        instance = self.validation_service.validate_or_raise(ComplexUnsafeClass, params)
        mock_factory.create.assert_called_once()
        mock_processor.assert_called_once_with("test")
        self.assertEqual(instance._processed, mock_processor.return_value)

    def test_validation_with_invalid_parameters(self):
        """Test that validation catches missing required parameters."""
        # Missing required parameter should raise validation error
        with self.assertRaises(Exception):
            self.validation_service.validate_or_raise(SafeClass, {"name": "test"})

        # Valid parameters should work
        self.validation_service.validate_or_raise(SafeClass, {"name": "test", "value": 42})

    def test_isolated_class_creation(self):
        """Test that validation returns an instance of the original class."""
        params = {"name": "test", "value": 10}

        instance = self.validation_service.validate_or_raise(SafeClass, params)

        # Instance should be of the original class
        self.assertIs(instance.__class__, SafeClass)

        # Values should be correctly set
        self.assertEqual(instance.name, "test")
        self.assertEqual(instance.value, 10)

    def test_fallback_behavior_when_ast_parsing_fails(self):
        """Test fallback behavior when AST parsing fails."""

        class ProblematicClass:
            def __init__(self, name: str):
                self.name = name

        # Should still work with fallback even if source is problematic
        params = {"name": "test"}
        self.validation_service.validate_or_raise(ProblematicClass, params)

    def test_empty_init_body_after_filtering(self):
        """Test behavior when all statements are unsafe operations."""

        class AllUnsafeClass:
            def __init__(self, func):
                func()
                func.call()

        mock_func = Mock()
        params = {"func": mock_func}

        # Should work even when all statements are unsafe
        self.validation_service.validate_or_raise(AllUnsafeClass, params)

        # Unsafe operations should be called
        mock_func.assert_called_once()
        mock_func.call.assert_called_once()

    def test_nested_function_calls(self):
        """Test that nested function calls are executed."""

        class NestedCallsClass:
            def __init__(self, name: str, service):
                self.name = name
                service.method().chain().call()

        mock_service = Mock()
        params = {"name": "test", "service": mock_service}
        self.validation_service.validate_or_raise(NestedCallsClass, params)
        mock_service.method.assert_called_once()
        mock_service.method.return_value.chain.assert_called_once()
        mock_service.method.return_value.chain.return_value.call.assert_called_once()


# ==============================================================================
# UNIT TESTS: Hierarchy Class Validation
# ==============================================================================


class TestValidationServiceHierarchy(unittest.TestCase):
    """Test ValidationService with class hierarchy and inheritance."""

    def setUp(self):
        """Set up test fixtures."""
        self.validation_service = ValidationService()

    def test_base_service_class(self):
        """Test validation of base service class with side effects."""
        mock_logger = Mock()
        params = {"name": "test_service", "logger": mock_logger}

        instance = self.validation_service.validate_or_raise(BaseServiceClass, params)

        self.assertEqual(instance.name, "test_service")
        self.assertEqual(instance.service_version, "1.0")
        mock_logger.info.assert_called_once()

    def test_derived_service_class(self):
        """Test validation of derived service class with super() call."""
        mock_logger = Mock()
        params = {"name": "derived_service", "logger": mock_logger, "port": 8080}

        instance = self.validation_service.validate_or_raise(DerivedServiceClass, params)

        self.assertEqual(instance.name, "derived_service")
        self.assertEqual(instance.port, 8080)
        # Should call logger twice (once in base, once in derived)
        self.assertEqual(mock_logger.info.call_count, 2)

    def test_multi_level_hierarchy(self):
        """Test validation with multi-level inheritance."""
        params = {"name": "test"}

        instance = self.validation_service.validate_or_raise(MultiLevelHierarchy, params)

        self.assertEqual(instance.name, "test")
        self.assertEqual(instance.base_attr, "base")

    def test_second_level_hierarchy(self):
        """Test validation with second level in hierarchy chain."""
        params = {"name": "test", "value": 42}

        instance = self.validation_service.validate_or_raise(SecondLevelHierarchy, params)

        self.assertEqual(instance.name, "test")
        self.assertEqual(instance.value, 42)

    def test_third_level_hierarchy(self):
        """Test validation with three-level inheritance chain."""
        params = {"name": "test", "value": 42, "config": {"key": "value"}}

        instance = self.validation_service.validate_or_raise(ThirdLevelHierarchy, params)

        self.assertEqual(instance.name, "test")
        self.assertEqual(instance.value, 42)
        self.assertEqual(instance.config, {"key": "value"})

    def test_hierarchy_with_side_effects(self):
        """Test validation of hierarchy with side effects in both base and derived."""
        mock_callback = Mock()
        params = {"callback": mock_callback}

        instance = self.validation_service.validate_or_raise(BaseWithSideEffects, params)

        self.assertIs(instance.callback, mock_callback)
        mock_callback.register.assert_called_once_with("base")

    def test_hierarchy_with_additional_side_effects(self):
        """Test validation of derived class with additional side effects."""
        mock_callback = Mock()
        mock_processor = Mock()
        params = {"callback": mock_callback, "processor": mock_processor}

        instance = self.validation_service.validate_or_raise(DerivedWithAdditionalSideEffects, params)

        self.assertIs(instance.callback, mock_callback)
        self.assertIs(instance.processor, mock_processor)
        # Base side effect called
        mock_callback.register.assert_called_once_with("base")
        # Derived side effect called
        mock_processor.process.assert_called_once()

    def test_abstract_base_pattern(self):
        """Test validation with abstract base pattern."""
        mock_service = Mock()
        params = {"name": "concrete", "service": mock_service}

        instance = self.validation_service.validate_or_raise(ConcreteImplementation, params)

        self.assertEqual(instance.name, "concrete")

    def test_multiple_inheritance(self):
        """Test validation with multiple inheritance."""
        params = {"param_a": "value_a", "param_b": "value_b", "param_c": "value_c"}

        instance = self.validation_service.validate_or_raise(MultipleInheritanceChild, params)

        self.assertEqual(instance.param_a, "value_a")
        self.assertEqual(instance.param_b, "value_b")
        self.assertEqual(instance.param_c, "value_c")
        self.assertEqual(instance.attr_a, "from_a")
        self.assertEqual(instance.attr_b, "from_b")

    def test_dataclass_with_class_hierarchy(self):
        """Test validation of classes derived from dataclass-like base."""
        params = {"name": "test", "value": 5}

        instance = self.validation_service.validate_or_raise(DerivedFromDataclassBase, params)

        self.assertEqual(instance.name, "test")
        self.assertEqual(instance.value, 5)

    def test_class_variables_inherited(self):
        """Test that inherited class variables are preserved."""
        mock_logger = Mock()
        params = {"name": "test", "logger": mock_logger, "port": 8080}

        instance = self.validation_service.validate_or_raise(DerivedServiceClass, params)

        # service_version is defined in base class
        self.assertEqual(instance.service_version, "1.0")

    def test_method_resolution_order(self):
        """Test that MRO is respected during validation."""
        params = {"param_a": "a", "param_b": "b", "param_c": "c"}

        instance = self.validation_service.validate_or_raise(MultipleInheritanceChild, params)

        # Verify all inheritance paths work
        self.assertIsInstance(instance, MultipleInheritanceExample)
        self.assertIsInstance(instance, MultipleInheritanceExampleB)
        self.assertIsInstance(instance, MultipleInheritanceChild)


# ==============================================================================
# UNIT TESTS: Complex Dataclass Hierarchies
# ==============================================================================


class TestComplexDataclassHierarchy(unittest.TestCase):
    """Test ValidationService with complex dataclass hierarchies."""

    def setUp(self):
        """Set up test fixtures."""
        self.validation_service = ValidationService()

    def test_simple_dataclass(self):
        """Test validation of simple dataclass with post_init."""
        params = {"name": "test", "value": 42}

        instance = self.validation_service.validate_or_raise(SimpleDataclass, params)

        self.assertEqual(instance.name, "test")
        self.assertEqual(instance.value, 42)
        # __post_init__ should be executed
        self.assertEqual(instance.processed, "test:42")

    def test_dataclass_with_defaults(self):
        """Test dataclass with complex default values."""
        params = {"name": "config"}

        instance = self.validation_service.validate_or_raise(DataclassWithDefaults, params)

        self.assertEqual(instance.name, "config")
        self.assertEqual(instance.tags, [])
        self.assertEqual(instance.metadata, {})
        # __post_init__ should be executed
        self.assertEqual(instance.tag_count, 0)
        self.assertEqual(instance.has_metadata, False)

    def test_dataclass_with_defaults_and_values(self):
        """Test dataclass with defaults provided at initialization."""
        params = {"name": "test", "tags": ["a", "b"], "metadata": {"key": "value"}}

        instance = self.validation_service.validate_or_raise(DataclassWithDefaults, params)

        self.assertEqual(instance.name, "test")
        self.assertEqual(instance.tags, ["a", "b"])
        self.assertEqual(instance.metadata, {"key": "value"})
        # __post_init__ should be executed
        self.assertEqual(instance.tag_count, 2)
        self.assertEqual(instance.has_metadata, True)

    def test_base_dataclass(self):
        """Test base dataclass with post_init computation."""
        params = {"id": 1, "name": "service"}

        instance = self.validation_service.validate_or_raise(BaseDataclass, params)

        self.assertEqual(instance.id, 1)
        self.assertEqual(instance.name, "service")
        # __post_init__ should be executed
        self.assertEqual(instance.base_computed, "base_1_service")

    def test_derived_dataclass(self):
        """Test derived dataclass with chained post_init."""
        params = {"id": 2, "name": "app", "description": "test_app"}

        instance = self.validation_service.validate_or_raise(DerivedDataclass, params)

        self.assertEqual(instance.id, 2)
        self.assertEqual(instance.name, "app")
        self.assertEqual(instance.description, "test_app")
        # Both base and derived __post_init__ should be executed
        self.assertEqual(instance.base_computed, "base_2_app")
        self.assertEqual(instance.derived_computed, "derived_test_app")

    def test_multi_level_dataclass(self):
        """Test three-level dataclass hierarchy."""
        params = {"id": 3, "name": "service", "description": "complex", "category": "production"}

        instance = self.validation_service.validate_or_raise(MultiLevelDataclass, params)

        self.assertEqual(instance.id, 3)
        self.assertEqual(instance.name, "service")
        self.assertEqual(instance.description, "complex")
        self.assertEqual(instance.category, "production")
        # All __post_init__ methods should be executed in order
        self.assertEqual(instance.base_computed, "base_3_service")
        self.assertEqual(instance.derived_computed, "derived_complex")
        self.assertEqual(instance.level_computed, "level_production")

    def test_dataclass_with_nested_dataclass(self):
        """Test dataclass containing another dataclass field."""
        config = SimpleDataclass(name="nested", value=100)
        params = {"title": "main", "config": config}

        instance = self.validation_service.validate_or_raise(DataclassWithNestedDataclass, params)

        self.assertEqual(instance.title, "main")
        self.assertEqual(instance.config.name, "nested")
        self.assertEqual(instance.config.value, 100)
        # Both dataclasses' __post_init__ should be executed
        self.assertEqual(instance.config.processed, "nested:100")
        self.assertEqual(instance.combined, "main:nested")

    def test_dataclass_with_callable_field_none(self):
        """Test dataclass with callable field set to None."""
        params = {"name": "test"}

        instance = self.validation_service.validate_or_raise(DataclassWithCallableField, params)

        self.assertEqual(instance.name, "test")
        self.assertIsNone(instance.processor)
        self.assertEqual(instance.processed_name, "test")

    def test_dataclass_with_callable_field_mock(self):
        """Test dataclass with callable field executing during validation."""
        mock_processor = Mock(return_value="processed_value")
        params = {"name": "test", "processor": mock_processor}

        instance = self.validation_service.validate_or_raise(DataclassWithCallableField, params)

        self.assertEqual(instance.name, "test")
        self.assertIs(instance.processor, mock_processor)
        # Processor should be called during __post_init__
        mock_processor.assert_called_once_with("test")
        self.assertEqual(instance.processed_name, "processed_value")

    def test_dataclass_with_mutable_defaults(self):
        """Test dataclass with mutable default factories."""
        params = {"name": "test"}

        instance = self.validation_service.validate_or_raise(DataclassWithMutableDefaults, params)

        self.assertEqual(instance.name, "test")
        self.assertEqual(instance.items, [])
        self.assertEqual(instance.config, {})
        self.assertEqual(instance.item_count, 0)
        self.assertTrue(instance.modified)

    def test_dataclass_with_mutable_defaults_populated(self):
        """Test dataclass with populated mutable fields."""
        params = {"name": "test", "items": ["a", "b", "c"], "config": {"setting": "value"}}

        instance = self.validation_service.validate_or_raise(DataclassWithMutableDefaults, params)

        self.assertEqual(instance.name, "test")
        self.assertEqual(instance.items, ["a", "b", "c"])
        self.assertEqual(instance.config, {"setting": "value"})
        self.assertEqual(instance.item_count, 3)
        self.assertTrue(instance.modified)

    def test_regular_class_with_dataclass(self):
        """Test regular class containing dataclass field."""
        config = SimpleDataclass(name="cfg", value=50)
        params = {"name": "container", "config": config}

        instance = self.validation_service.validate_or_raise(RegularClassWithDataclass, params)

        self.assertEqual(instance.name, "container")
        self.assertEqual(instance.config.name, "cfg")
        self.assertEqual(instance.config.value, 50)
        # Nested dataclass __post_init__ should be executed
        self.assertEqual(instance.config.processed, "cfg:50")
        self.assertEqual(instance.combined_value, "container_50")

    def test_dataclass_with_default_factory_independence(self):
        """Test that dataclass default factories are independent per instance."""
        params1 = {"name": "test1"}
        params2 = {"name": "test2"}

        instance1 = self.validation_service.validate_or_raise(DataclassWithDefaults, params1)
        instance2 = self.validation_service.validate_or_raise(DataclassWithDefaults, params2)

        # Modify instance1's lists
        instance1.tags.append("item1")
        instance1.metadata["key1"] = "value1"

        # instance2 should not be affected
        self.assertEqual(instance1.tags, ["item1"])
        self.assertEqual(instance2.tags, [])
        self.assertEqual(instance1.metadata, {"key1": "value1"})
        self.assertEqual(instance2.metadata, {})

    def test_multi_level_dataclass_with_defaults(self):
        """Test multi-level dataclass hierarchy with some default values."""
        params = {"id": 10, "name": "app"}

        instance = self.validation_service.validate_or_raise(MultiLevelDataclass, params)

        self.assertEqual(instance.id, 10)
        self.assertEqual(instance.name, "app")
        self.assertEqual(instance.description, "")  # default
        self.assertEqual(instance.category, "default")  # default
        # All __post_init__ methods should execute with defaults
        self.assertEqual(instance.base_computed, "base_10_app")
        self.assertEqual(instance.derived_computed, "derived_")
        self.assertEqual(instance.level_computed, "level_default")

    def test_dataclass_with_regular_inheritance(self):
        """Test dataclass with regular class inheritance."""
        params = {"value": 5, "extra": "custom"}

        instance = self.validation_service.validate_or_raise(DataclassWithRegularInheritance, params)

        self.assertEqual(instance.value, 5)
        self.assertEqual(instance.extra, "custom")
        # __post_init__ should be executed
        self.assertEqual(instance.final_value, 10)

    def test_dataclass_preserves_class_attributes(self):
        """Test that dataclass field defaults don't interfere with class attributes."""
        params = {"name": "test"}

        instance1 = self.validation_service.validate_or_raise(DataclassWithDefaults, params)
        instance2 = self.validation_service.validate_or_raise(DataclassWithDefaults, params)

        # Both should have independent field instances
        self.assertIsNot(instance1.tags, instance2.tags)
        self.assertIsNot(instance1.metadata, instance2.metadata)
        self.assertEqual(instance1.tags, instance2.tags)
        self.assertEqual(instance1.metadata, instance2.metadata)


# ==============================================================================
# INTEGRATION TESTS: Real-World Scenarios
# ==============================================================================


class TestValidationServiceIntegration(unittest.TestCase):
    """Integration tests for ValidationService with real scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.validation_service = ValidationService()

    def test_real_world_service_class(self):
        """Test with a realistic service class."""

        class DatabaseService:
            def __init__(self, host: str, port: int, logger):
                self.host = host
                self.port = port
                self.logger = logger
                logger.info(f"Connecting to {host}:{port}")  # Side effect - executed
                self._connection = self._create_connection()  # Side effect - executed

            def _create_connection(self):
                return f"connection to {self.host}:{self.port}"

        mock_logger = Mock()
        params = {"host": "localhost", "port": 5432, "logger": mock_logger}

        # Should validate without side effects
        self.validation_service.validate_or_raise(DatabaseService, params)

        # Logger should not be called during validation
        mock_logger.info.assert_called_once()

    def test_factory_pattern_class(self):
        """Test with factory pattern that has initialization side effects."""

        class ServiceFactory:
            def __init__(self, config: dict, registry):
                self.config = config
                self.registry = registry
                registry.register(self)  # Side effect - executed
                self._services = self._initialize_services()  # Side effect - executed

            def _initialize_services(self):
                return []

        mock_registry = Mock()
        params = {"config": {"key": "value"}, "registry": mock_registry}

        # Should validate without registering or initializing
        self.validation_service.validate_or_raise(ServiceFactory, params)

        # Registry should not be called
        mock_registry.register.assert_called_once()

    def test_validation_with_pydantic_model(self):
        """Test validation works correctly with validation logic."""

        class ServiceWithValidation:
            def __init__(self, name: str, port: int, callback):
                if port < 1 or port > 65535:
                    raise ValueError("Invalid port")
                self.name = name
                self.port = port
                self.callback = callback
                callback.initialize()  # Side effect - executed

        mock_callback = Mock()

        # Valid parameters should work
        valid_params = {"name": "service", "port": 8080, "callback": mock_callback}
        self.validation_service.validate_or_raise(ServiceWithValidation, valid_params)

        # Callback side effect should be called
        mock_callback.initialize.assert_called_once()

    def test_real_world_service_pattern(self):
        """Test with realistic service class pattern."""

        class DatabaseService:
            connection_timeout: int = 30

            def __init__(self, host: str, port: int, logger):
                self.host = host
                self.port = port
                self.logger = logger
                logger.info(f"Connecting to {host}:{port}")  # Side effect - executed
                self._pool = self._create_connection_pool()  # Side effect - executed

            def _create_connection_pool(self):
                return "pool"

        mock_logger = Mock()
        params = {"host": "localhost", "port": 5432, "logger": mock_logger}

        # Should validate without side effects
        self.validation_service.validate_or_raise(DatabaseService, params)

        # Logger should be called once
        mock_logger.info.assert_called_once()

    def test_factory_pattern_with_registration(self):
        """Test factory pattern that registers itself."""

        class ServiceFactory:
            registry_enabled: bool = True

            def __init__(self, config: dict, registry):
                self.config = config
                self.registry = registry
                registry.register(self)  # Side effect - executed
                self._initialize()  # Side effect - executed

            def _initialize(self):
                pass

        mock_registry = Mock()
        params = {"config": {"type": "factory"}, "registry": mock_registry}

        # Should validate without registration
        self.validation_service.validate_or_raise(ServiceFactory, params)

        # Registry should be called
        mock_registry.register.assert_called_once()

    def test_mixed_dataclass_and_regular_class(self):
        """Test validation works with mixed class types."""

        @dataclass
        class DataConfig:
            name: str
            enabled: bool = True

            def __post_init__(self):
                self.computed = f"{self.name}_computed"

        class RegularService:
            def __init__(self, config: DataConfig, processor):
                self.config = config
                self.processor = processor
                processor.initialize(config)  # Side effect - executed

        mock_processor = Mock()
        data_config = DataConfig(name="test", enabled=True)
        params = {"config": data_config, "processor": mock_processor}

        # Should validate without calling processor
        self.validation_service.validate_or_raise(RegularService, params)

        # Processor side effect should be called
        mock_processor.initialize.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
