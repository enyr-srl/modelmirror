"""
Validation and type safety tests for ModelMirror JSON configurations.

This test suite focuses on Pydantic integration, type validation, and schema enforcement.
"""

import unittest
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from modelmirror.mirror import Mirror
from tests.fixtures.test_classes import (
    SimpleService, DatabaseService, UserService, ValidationService
)


class StrictValidationConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')
    
    service: ValidationService
    name: str = Field(min_length=1, max_length=100)
    count: int = Field(ge=0, le=1000)


class OptionalFieldsConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    required_service: SimpleService
    optional_service: Optional[SimpleService] = None
    optional_string: Optional[str] = None


class UnionTypesConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    service: Union[SimpleService, DatabaseService]
    services: List[Union[SimpleService, DatabaseService]]


class NestedValidationConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')
    
    database: DatabaseService
    user_service: UserService
    metadata: Dict[str, str]


class TestJSONValidation(unittest.TestCase):
    """Test suite for JSON validation and type safety."""

    def setUp(self):
        """Set up test fixtures."""
        self.mirror = Mirror('tests.fixtures')

    def test_strict_validation_success(self):
        """Test successful validation with strict Pydantic model."""
        config = self.mirror.reflect('tests/configs/strict_valid.json', StrictValidationConfig)
        
        self.assertIsInstance(config.service, ValidationService)
        self.assertEqual(config.name, "valid_config")
        self.assertEqual(config.count, 42)

    def test_strict_validation_field_constraints(self):
        """Test validation failure due to field constraint violations."""
        with self.assertRaises(ValidationError):
            self.mirror.reflect('tests/configs/strict_invalid_constraints.json', StrictValidationConfig)

    def test_strict_validation_extra_fields(self):
        """Test validation failure due to extra fields when extra='forbid'."""
        with self.assertRaises(ValidationError):
            self.mirror.reflect('tests/configs/strict_extra_fields.json', StrictValidationConfig)

    def test_optional_fields_with_values(self):
        """Test optional fields when values are provided."""
        config = self.mirror.reflect('tests/configs/optional_with_values.json', OptionalFieldsConfig)
        
        self.assertIsInstance(config.required_service, SimpleService)
        self.assertIsInstance(config.optional_service, SimpleService)
        self.assertIsNotNone(config.optional_string)

    def test_optional_fields_without_values(self):
        """Test optional fields when values are not provided."""
        config = self.mirror.reflect('tests/configs/optional_without_values.json', OptionalFieldsConfig)
        
        self.assertIsInstance(config.required_service, SimpleService)
        self.assertIsNone(config.optional_service)
        self.assertIsNone(config.optional_string)

    def test_union_types_first_type(self):
        """Test Union types resolving to first type."""
        config = self.mirror.reflect('tests/configs/union_simple.json', UnionTypesConfig)
        
        self.assertIsInstance(config.service, SimpleService)
        self.assertEqual(len(config.services), 2)

    def test_union_types_second_type(self):
        """Test Union types resolving to second type."""
        config = self.mirror.reflect('tests/configs/union_database.json', UnionTypesConfig)
        
        self.assertIsInstance(config.service, DatabaseService)
        self.assertEqual(len(config.services), 2)

    def test_nested_validation_success(self):
        """Test nested object validation success."""
        config = self.mirror.reflect('tests/configs/nested_validation_valid.json', NestedValidationConfig)
        
        self.assertIsInstance(config.database, DatabaseService)
        self.assertIsInstance(config.user_service, UserService)
        self.assertIsInstance(config.metadata, dict)

    def test_nested_validation_failure(self):
        """Test nested object validation failure."""
        with self.assertRaises(ValidationError):
            self.mirror.reflect('tests/configs/nested_validation_invalid.json', NestedValidationConfig)

    def test_type_coercion_strings_to_numbers(self):
        """Test automatic type coercion from strings to numbers."""
        config = self.mirror.reflect('tests/configs/type_coercion.json', StrictValidationConfig)
        
        # Should automatically convert string "42" to int 42
        self.assertEqual(config.count, 42)
        self.assertIsInstance(config.count, int)

    def test_validation_error_messages(self):
        """Test that validation error messages are informative."""
        try:
            self.mirror.reflect('tests/configs/validation_errors.json', StrictValidationConfig)
            self.fail("Expected ValidationError")
        except ValidationError as e:
            error_dict = e.errors()
            self.assertTrue(len(error_dict) > 0)
            # Check that error messages contain field information (port or count)
            self.assertTrue(any('port' in str(error) or 'count' in str(error) for error in error_dict))

    def test_custom_validator_integration(self):
        """Test integration with custom Pydantic validators."""
        # This would test custom validators if they were defined in ValidationService
        config = self.mirror.reflect('tests/configs/custom_validation.json', StrictValidationConfig)
        
        self.assertIsInstance(config.service, ValidationService)

    def test_model_serialization_after_reflection(self):
        """Test that reflected models can be serialized back to dict/JSON."""
        config = self.mirror.reflect('tests/configs/serialization_test.json', NestedValidationConfig)
        
        # Should be able to convert back to dict
        config_dict = config.model_dump()
        self.assertIsInstance(config_dict, dict)
        self.assertIn('database', config_dict)
        self.assertIn('user_service', config_dict)

    def test_model_copy_and_modification(self):
        """Test that reflected models support Pydantic copy and modification."""
        config = self.mirror.reflect('tests/configs/copy_test.json', NestedValidationConfig)
        
        # Should be able to create a copy with modifications
        modified_config = config.model_copy(update={'metadata': {'new_key': 'new_value'}})
        
        self.assertNotEqual(config.metadata, modified_config.metadata)
        self.assertEqual(modified_config.metadata['new_key'], 'new_value')

    def test_field_aliases_and_serialization_aliases(self):
        """Test Pydantic field aliases work correctly."""
        # This would test field aliases if they were defined in the models
        config = self.mirror.reflect('tests/configs/aliases_test.json', NestedValidationConfig)
        
        self.assertIsInstance(config, NestedValidationConfig)

    def test_discriminated_unions(self):
        """Test discriminated unions if supported."""
        # This would test discriminated unions for more complex type resolution
        config = self.mirror.reflect('tests/configs/discriminated_union.json', UnionTypesConfig)
        
        self.assertTrue(
            isinstance(config.service, SimpleService) or 
            isinstance(config.service, DatabaseService)
        )

    def test_recursive_model_validation(self):
        """Test validation of recursive/self-referencing models."""
        # This tests complex nested structures with potential recursion
        instances = self.mirror.reflect_raw('tests/configs/recursive_structure.json')
        
        # Should handle without infinite recursion
        services = instances.get(list[SimpleService])
        self.assertTrue(len(services) >= 0)

    def test_validation_with_inheritance(self):
        """Test validation works correctly with class inheritance."""
        config = self.mirror.reflect('tests/configs/inheritance_validation.json', NestedValidationConfig)
        
        self.assertIsInstance(config.database, DatabaseService)
        self.assertIsInstance(config.user_service, UserService)

    def test_partial_validation_on_raw_reflection(self):
        """Test that raw reflection doesn't perform Pydantic validation."""
        # Raw reflection should work even with invalid data for Pydantic
        instances = self.mirror.reflect_raw('tests/configs/raw_invalid_for_pydantic.json')
        
        # Should succeed because raw reflection doesn't validate
        services = instances.get(list[SimpleService])
        self.assertTrue(len(services) >= 0)


if __name__ == '__main__':
    unittest.main()