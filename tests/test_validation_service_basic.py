"""
Test suite for ValidationService core functionality.

Tests basic class validation, side effects handling, and parameter validation.
"""

import unittest
from unittest.mock import Mock

from modelmirror.instance.validation_service import ValidationService
from tests.test_validation_service import (
    ClassWithClassVars,
    ClsParameterClass,
    ComplexClass,
    ComplexUnsafeClass,
    DataclassWithPostInit,
    MixedClass,
    PydanticModel,
    RegularClass,
    SafeClass,
    UnsafeClass,
)


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
