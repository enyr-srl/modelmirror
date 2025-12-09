"""
Test suite for ValidationService with class hierarchy and inheritance.

Tests class inheritance patterns including single inheritance, multiple
inheritance, and abstract base patterns.
"""

import unittest
from unittest.mock import Mock

from modelmirror.instance.validation_service import ValidationService
from tests.test_validation_service import (
    BaseServiceClass,
    BaseWithSideEffects,
    ConcreteImplementation,
    DerivedFromDataclassBase,
    DerivedServiceClass,
    DerivedWithAdditionalSideEffects,
    MultiLevelHierarchy,
    MultipleInheritanceChild,
    MultipleInheritanceExample,
    MultipleInheritanceExampleB,
    SecondLevelHierarchy,
    ThirdLevelHierarchy,
)


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
