"""
Comprehensive test suite for ModelMirror JSON configuration handling.

This test suite covers all possible JSON configuration patterns and structures
that the ModelMirror library should handle correctly.
"""

import unittest
from typing import List, Dict, Any
from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror
from tests.fixtures.test_classes import (
    SimpleService, DatabaseService, UserService, ConfigurableService,
    ComplexService, ServiceWithDefaults, ServiceWithOptionals
)


class SimpleConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    service: SimpleService


class DatabaseConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    database: DatabaseService


class UserServiceConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    user_service: UserService
    database: DatabaseService


class ListConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    services: List[SimpleService]


class DictConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    services: Dict[str, SimpleService]


class MixedConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    database: DatabaseService
    user_service: UserService
    services: List[SimpleService]
    service_map: Dict[str, SimpleService]


class ComplexNestedConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    complex_service: ComplexService


class TestJSONConfigurations(unittest.TestCase):
    """Test suite for JSON configuration patterns."""

    def setUp(self):
        """Set up test fixtures."""
        self.mirror = Mirror('tests.fixtures')

    def test_simple_instance_creation(self):
        """Test basic instance creation from JSON."""
        config = self.mirror.reflect_typed('tests/configs/simple.json', SimpleConfig)
        
        self.assertIsInstance(config.service, SimpleService)
        self.assertEqual(config.service.name, "test_service")

    def test_instance_with_multiple_parameters(self):
        """Test instance creation with multiple constructor parameters."""
        config = self.mirror.reflect_typed('tests/configs/database.json', DatabaseConfig)
        
        self.assertIsInstance(config.database, DatabaseService)
        self.assertEqual(config.database.host, "localhost")
        self.assertEqual(config.database.port, 5432)
        self.assertEqual(config.database.database_name, "testdb")

    def test_singleton_reference_basic(self):
        """Test basic singleton reference functionality."""
        instances = self.mirror.reflect_raw('tests/configs/singleton_basic.json')
        
        db1 = instances.get(DatabaseService, '$main_db')
        db2 = instances.get(DatabaseService, '$main_db')
        
        self.assertIs(db1, db2)
        self.assertEqual(db1.host, "localhost")

    def test_singleton_reference_in_dependency_injection(self):
        """Test singleton reference used in dependency injection."""
        config = self.mirror.reflect_typed('tests/configs/dependency_injection.json', UserServiceConfig)
        
        # Both services should reference the same database instance
        self.assertIs(config.user_service.database, config.database)
        self.assertEqual(config.database.host, "localhost")

    def test_list_of_instances_no_singletons(self):
        """Test list containing multiple instances without singletons."""
        config = self.mirror.reflect_typed('tests/configs/list_instances.json', ListConfig)
        
        self.assertEqual(len(config.services), 3)
        self.assertIsInstance(config.services[0], SimpleService)
        self.assertIsInstance(config.services[1], SimpleService)
        self.assertIsInstance(config.services[2], SimpleService)
        
        # Each should be a different instance
        self.assertIsNot(config.services[0], config.services[1])
        self.assertIsNot(config.services[1], config.services[2])

    def test_list_with_singleton_references(self):
        """Test list containing singleton references."""
        config = self.mirror.reflect_typed('tests/configs/list_with_singletons.json', ListConfig)
        
        self.assertEqual(len(config.services), 3)
        # First and third should be the same instance (singleton reference)
        self.assertIs(config.services[0], config.services[2])
        # Second should be different
        self.assertIsNot(config.services[0], config.services[1])

    def test_list_mixed_instances_and_references(self):
        """Test list with mix of new instances and singleton references."""
        config = self.mirror.reflect_typed('tests/configs/list_mixed.json', ListConfig)
        
        self.assertEqual(len(config.services), 4)
        # Check that singleton references work correctly
        self.assertIs(config.services[1], config.services[3])
        # Check that new instances are different
        self.assertIsNot(config.services[0], config.services[1])
        self.assertIsNot(config.services[0], config.services[2])

    def test_dictionary_of_instances(self):
        """Test dictionary containing instances."""
        config = self.mirror.reflect_typed('tests/configs/dict_instances.json', DictConfig)
        
        self.assertEqual(len(config.services), 2)
        self.assertIn("primary", config.services)
        self.assertIn("secondary", config.services)
        self.assertIsInstance(config.services["primary"], SimpleService)
        self.assertIsInstance(config.services["secondary"], SimpleService)

    def test_dictionary_with_singleton_references(self):
        """Test dictionary with singleton references."""
        config = self.mirror.reflect_typed('tests/configs/dict_with_singletons.json', DictConfig)
        
        self.assertEqual(len(config.services), 3)
        # Check singleton reference works
        self.assertIs(config.services["primary"], config.services["backup"])
        self.assertIsNot(config.services["primary"], config.services["secondary"])

    def test_nested_object_creation(self):
        """Test nested object creation within properties."""
        config = self.mirror.reflect_typed('tests/configs/nested_objects.json', ComplexNestedConfig)
        
        self.assertIsInstance(config.complex_service, ComplexService)
        self.assertIsInstance(config.complex_service.database, DatabaseService)
        self.assertIsInstance(config.complex_service.user_service, UserService)
        # Verify nested dependency injection
        self.assertIs(config.complex_service.user_service.database, config.complex_service.database)

    def test_deeply_nested_structures(self):
        """Test deeply nested object structures."""
        config = self.mirror.reflect_typed('tests/configs/deep_nesting.json', ComplexNestedConfig)
        
        # Verify deep nesting works correctly
        self.assertIsInstance(config.complex_service.database, DatabaseService)
        self.assertEqual(config.complex_service.database.host, "nested.example.com")

    def test_circular_singleton_references(self):
        """Test that circular singleton references are handled correctly."""
        with self.assertRaises(Exception):
            self.mirror.reflect_raw('tests/configs/circular_references.json')

    def test_missing_singleton_reference(self):
        """Test error handling for missing singleton references."""
        with self.assertRaises(Exception) as context:
            self.mirror.reflect_raw('tests/configs/missing_singleton.json')
        
        self.assertIn("has not a corresponding reference", str(context.exception))

    def test_duplicate_singleton_names(self):
        """Test error handling for duplicate singleton names."""
        with self.assertRaises(Exception) as context:
            self.mirror.reflect_raw('tests/configs/duplicate_singletons.json')
        
        self.assertIn("Duplicate instance ID", str(context.exception))

    def test_invalid_registry_reference(self):
        """Test error handling for invalid registry references."""
        with self.assertRaises(ValueError) as context:
            self.mirror.reflect_raw('tests/configs/invalid_registry.json')
        
        self.assertIn("Registry item", str(context.exception))

    def test_malformed_reference_object(self):
        """Test error handling for malformed $reference objects."""
        with self.assertRaises(Exception):
            self.mirror.reflect_raw('tests/configs/malformed_reference.json')

    def test_empty_configuration(self):
        """Test handling of empty configuration files."""
        class EmptyConfig(BaseModel):
            pass
        
        config = self.mirror.reflect_typed('tests/configs/empty.json', EmptyConfig)
        self.assertIsInstance(config, EmptyConfig)

    def test_configuration_with_null_values(self):
        """Test handling of null values in configuration."""
        class ServiceWithOptionalsConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            service: ServiceWithOptionals
        
        config = self.mirror.reflect_typed('tests/configs/with_nulls.json', ServiceWithOptionalsConfig)
        
        self.assertIsInstance(config.service, ServiceWithOptionals)
        self.assertIsNone(config.service.optional_param)

    def test_configuration_with_default_values(self):
        """Test that default values are properly handled."""
        class ServiceWithDefaultsConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            service: ServiceWithDefaults
        
        config = self.mirror.reflect_typed('tests/configs/with_defaults.json', ServiceWithDefaultsConfig)
        
        self.assertIsInstance(config.service, ServiceWithDefaults)
        # Should use default value when not specified
        self.assertEqual(config.service.timeout, 30)

    def test_mixed_complex_configuration(self):
        """Test complex configuration with all features combined."""
        config = self.mirror.reflect_typed('tests/configs/complex_mixed.json', MixedConfig)
        
        # Verify all components are created
        self.assertIsInstance(config.database, DatabaseService)
        self.assertIsInstance(config.user_service, UserService)
        self.assertEqual(len(config.services), 2)
        self.assertEqual(len(config.service_map), 2)
        
        # Verify dependency injection works
        self.assertIs(config.user_service.database, config.database)
        
        # Verify singleton references in collections
        self.assertIs(config.services[0], config.service_map["primary"])

    def test_raw_reflection_instance_retrieval(self):
        """Test various ways to retrieve instances from raw reflection."""
        instances = self.mirror.reflect_raw('tests/configs/complex_mixed.json')
        
        # Test getting by type
        database = instances.get(DatabaseService)
        self.assertIsInstance(database, DatabaseService)
        
        # Test getting by singleton name
        primary_service = instances.get(SimpleService, '$primary_service')
        self.assertIsInstance(primary_service, SimpleService)
        
        # Test getting list of instances
        all_services = instances.get(list[SimpleService])
        self.assertIsInstance(all_services, list)
        self.assertTrue(len(all_services) > 0)
        
        # Test getting dictionary of instances
        service_dict = instances.get(dict[str, SimpleService])
        self.assertIsInstance(service_dict, dict)

    def test_pydantic_validation_integration(self):
        """Test that Pydantic validation works with reflected instances."""
        class ConfigurableServiceConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            service: ConfigurableService
        
        # This should pass validation
        config = self.mirror.reflect_typed('tests/configs/valid_pydantic.json', ConfigurableServiceConfig)
        self.assertIsInstance(config.service, ConfigurableService)
        
        # This should fail validation
        with self.assertRaises(Exception):
            self.mirror.reflect_typed('tests/configs/invalid_pydantic.json', ConfigurableServiceConfig)

    def test_type_safety_with_schema(self):
        """Test type safety when using Pydantic schemas."""
        config = self.mirror.reflect_typed('tests/configs/type_safe.json', UserServiceConfig)
        
        # IDE should have full type information
        self.assertEqual(config.database.host, "localhost")
        self.assertEqual(config.user_service.cache_enabled, True)

    def test_list_of_different_types(self):
        """Test lists containing different types of services."""
        # This tests the flexibility of the system
        instances = self.mirror.reflect_raw('tests/configs/heterogeneous_list.json')
        
        # Get all instances as a mixed list
        simple_services = instances.get(list[SimpleService])
        database_services = instances.get(list[DatabaseService])
        user_services = instances.get(list[UserService])
        
        # Should contain different types of services
        total_services = len(simple_services) + len(database_services) + len(user_services)
        self.assertTrue(total_services > 0)

    def test_configuration_inheritance_patterns(self):
        """Test configuration patterns that simulate inheritance."""
        config = self.mirror.reflect_typed('tests/configs/inheritance_pattern.json', ComplexNestedConfig)
        
        # Verify that base configuration is properly extended
        self.assertIsInstance(config.complex_service, ComplexService)


if __name__ == '__main__':
    unittest.main()