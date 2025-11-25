"""
Edge cases and error condition tests for ModelMirror JSON configurations.

This test suite focuses on boundary conditions, error handling, and edge cases
that the ModelMirror library should handle gracefully.
"""

import unittest
import json
from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror
from tests.fixtures.test_classes import SimpleService


class EdgeCaseConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    service: SimpleService


class TestJSONEdgeCases(unittest.TestCase):
    """Test suite for JSON configuration edge cases."""

    def setUp(self):
        """Set up test fixtures."""
        self.mirror = Mirror('tests.fixtures')

    def test_empty_json_object(self):
        """Test handling of completely empty JSON object."""
        class EmptyConfig(BaseModel):
            pass
        
        config = self.mirror.reflect_typed('tests/configs/empty.json', EmptyConfig)
        self.assertIsInstance(config, EmptyConfig)

    def test_json_with_only_primitives(self):
        """Test JSON containing only primitive values (no $reference objects)."""
        with open('tests/configs/primitives_only.json', 'w') as f:
            json.dump({
                "string_value": "test",
                "number_value": 42,
                "boolean_value": True,
                "null_value": None,
                "array_value": [1, 2, 3],
                "object_value": {"nested": "value"}
            }, f)
        
        instances = self.mirror.reflect_raw('tests/configs/primitives_only.json')
        # Should return empty instances since no $reference objects
        # Try to get any service type - should return empty list
        services = instances.get(list[SimpleService])
        self.assertEqual(len(services), 0)

    def test_deeply_nested_json_structure(self):
        """Test very deeply nested JSON structures."""
        instances = self.mirror.reflect_raw('tests/configs/deep_structure.json')
        services = instances.get(list[SimpleService])
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0].name, "deep_service")

    def test_large_array_of_instances(self):
        """Test handling of large arrays with many instances."""
        instances = self.mirror.reflect_raw('tests/configs/large_array.json')
        services = instances.get(list[SimpleService])
        self.assertEqual(len(services), 5)

    def test_unicode_and_special_characters(self):
        """Test handling of Unicode and special characters in JSON."""
        config = self.mirror.reflect_typed('tests/configs/unicode_test.json', EdgeCaseConfig)
        self.assertEqual(config.service.name, "测试服务_🚀_special-chars.test@domain.com")

    def test_json_with_comments_should_fail(self):
        """Test that JSON with comments fails gracefully."""
        with self.assertRaises(json.JSONDecodeError):
            self.mirror.reflect_raw('tests/configs/with_comments.json')

    def test_malformed_json_syntax(self):
        """Test handling of malformed JSON syntax."""
        with self.assertRaises(json.JSONDecodeError):
            self.mirror.reflect_raw('tests/configs/malformed.json')

    def test_reference_object_missing_registry(self):
        """Test $reference object missing required registry field."""
        with self.assertRaises(Exception):
            self.mirror.reflect_raw('tests/configs/missing_registry.json')

    def test_reference_object_with_extra_fields(self):
        """Test $reference object with unexpected extra fields."""
        # Should handle gracefully by ignoring extra fields
        instances = self.mirror.reflect_raw('tests/configs/extra_fields.json')
        services = instances.get(list[SimpleService])
        self.assertEqual(len(services), 1)

    def test_singleton_reference_case_sensitivity(self):
        """Test that singleton references are case sensitive."""
        with self.assertRaises(Exception):
            self.mirror.reflect_raw('tests/configs/case_sensitive.json')
    
    def test_valid_numeric_singleton_names(self):
        """Test that numeric singleton names work correctly when used properly."""
        # Create a valid config where numeric singleton is used in object field, not string field
        with open('tests/configs/valid_numeric_singleton.json', 'w') as f:
            json.dump({
                "service1": {
                    "$reference": {
                        "registry": {"schema": "simple_service", "version": "1.0.0"},
                        "instance": "123"
                    },
                    "name": "numeric_singleton"
                }
            }, f)
        
        instances = self.mirror.reflect_raw('tests/configs/valid_numeric_singleton.json')
        services = instances.get(list[SimpleService])
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0].name, "numeric_singleton")

    def test_numeric_and_boolean_singleton_names(self):
        """Test that putting $reference in string field is a user configuration error."""
        # This should fail because service2 has "name": "$123" which resolves to an object,
        # but SimpleService.name expects a string. This is a user configuration error.
        with self.assertRaises(Exception):
            self.mirror.reflect_raw('tests/configs/numeric_singleton.json')

    def test_empty_string_values(self):
        """Test handling of empty string values in configuration."""
        config_obj = self.mirror.reflect_typed('tests/configs/empty_strings.json', EdgeCaseConfig)
        self.assertEqual(config_obj.service.name, "")

    def test_very_long_string_values(self):
        """Test handling of very long string values."""
        config_obj = self.mirror.reflect_typed('tests/configs/long_strings.json', EdgeCaseConfig)
        self.assertEqual(len(config_obj.service.name), 1024)

    def test_nested_arrays_and_objects(self):
        """Test complex nested structures with arrays and objects."""
        instances = self.mirror.reflect_raw('tests/configs/complex_nested.json')
        services = instances.get(list[SimpleService])
        self.assertEqual(len(services), 2)


if __name__ == '__main__':
    unittest.main()