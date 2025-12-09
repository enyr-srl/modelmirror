"""
Test suite for ValidationService with complex dataclass hierarchies.

Tests dataclass validation including inheritance chains, nested dataclasses,
mutable defaults, and __post_init__ behavior.
"""

import unittest
from unittest.mock import Mock

from modelmirror.instance.validation_service import ValidationService
from tests.test_validation_service import (
    BaseDataclass,
    DataclassWithCallableField,
    DataclassWithDefaults,
    DataclassWithMutableDefaults,
    DataclassWithNestedDataclass,
    DataclassWithRegularInheritance,
    DerivedDataclass,
    MultiLevelDataclass,
    RegularClassWithDataclass,
    SimpleDataclass,
)


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
        params = {
            "id": 3,
            "name": "service",
            "description": "complex",
            "category": "production",
        }

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
        params = {
            "name": "test",
            "items": ["a", "b", "c"],
            "config": {"setting": "value"},
        }

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
