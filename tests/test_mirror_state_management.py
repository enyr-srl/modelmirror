"""
Test suite for Mirror class state management.

This test validates that the Mirror class properly manages its internal state
across multiple configuration loads.
"""

import unittest
from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror
from tests.fixtures.test_classes import SimpleService, DatabaseService


class SimpleConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    service: SimpleService


class DatabaseConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    database: DatabaseService


class TestMirrorStateManagement(unittest.TestCase):
    """Test suite for Mirror state management."""

    def test_multiple_configurations_with_same_singleton_names(self):
        """Test that Mirror can load multiple configs with same singleton names."""
        mirror = Mirror('tests.fixtures')
        
        # Load first configuration with singleton "shared_service"
        config1 = mirror.reflect('tests/configs/state_test_1.json', SimpleConfig)
        self.assertEqual(config1.service.name, "first_service")
        
        # Load second configuration with same singleton name "shared_service"
        # This should work without duplicate singleton error
        config2 = mirror.reflect('tests/configs/state_test_2.json', SimpleConfig)
        self.assertEqual(config2.service.name, "second_service")
        
        # Verify they are different instances
        self.assertIsNot(config1.service, config2.service)

    def test_raw_reflection_state_isolation(self):
        """Test that raw reflection calls are properly isolated."""
        mirror = Mirror('tests.fixtures')
        
        # Load first configuration
        instances1 = mirror.reflect_raw('tests/configs/state_test_1.json')
        service1 = instances1.get(SimpleService, '$shared_service')
        self.assertEqual(service1.name, "first_service")
        
        # Load second configuration with same singleton name
        instances2 = mirror.reflect_raw('tests/configs/state_test_2.json')
        service2 = instances2.get(SimpleService, '$shared_service')
        self.assertEqual(service2.name, "second_service")
        
        # Verify they are different instances
        self.assertIsNot(service1, service2)

    def test_mixed_typed_and_raw_reflection(self):
        """Test mixing typed and raw reflection calls."""
        mirror = Mirror('tests.fixtures')
        
        # Load with typed reflection
        typed_config = mirror.reflect('tests/configs/state_test_1.json', SimpleConfig)
        self.assertEqual(typed_config.service.name, "first_service")
        
        # Load with raw reflection using same singleton name
        raw_instances = mirror.reflect_raw('tests/configs/state_test_2.json')
        raw_service = raw_instances.get(SimpleService, '$shared_service')
        self.assertEqual(raw_service.name, "second_service")
        
        # Verify they are different instances
        self.assertIsNot(typed_config.service, raw_service)

    def test_state_reset_between_different_config_types(self):
        """Test state reset works with different configuration structures."""
        mirror = Mirror('tests.fixtures')
        
        # Load simple service configuration
        simple_config = mirror.reflect('tests/configs/state_test_1.json', SimpleConfig)
        self.assertEqual(simple_config.service.name, "first_service")
        
        # Load database configuration (different structure)
        db_config = mirror.reflect('tests/configs/state_test_db.json', DatabaseConfig)
        self.assertEqual(db_config.database.host, "state.test.db")
        
        # Load simple service again with same singleton name
        simple_config2 = mirror.reflect('tests/configs/state_test_2.json', SimpleConfig)
        self.assertEqual(simple_config2.service.name, "second_service")

    def test_singleton_references_cleared_between_loads(self):
        """Test that singleton references are properly cleared."""
        mirror = Mirror('tests.fixtures')
        
        # Load configuration with singleton
        instances1 = mirror.reflect_raw('tests/configs/state_test_1.json')
        
        # Verify singleton exists
        service1 = instances1.get(SimpleService, '$shared_service')
        self.assertIsNotNone(service1)
        
        # Load different configuration
        instances2 = mirror.reflect_raw('tests/configs/state_test_no_singleton.json')
        
        # Try to access the previous singleton - should not exist
        with self.assertRaises(Exception):
            instances2.get(SimpleService, '$shared_service')

    def test_instance_properties_cleared_between_loads(self):
        """Test that internal instance properties are cleared."""
        mirror = Mirror('tests.fixtures')
        
        # Load first configuration
        config1 = mirror.reflect('tests/configs/state_test_1.json', SimpleConfig)
        self.assertIsInstance(config1.service, SimpleService)
        
        # Load second configuration - should not have any leftover state
        config2 = mirror.reflect('tests/configs/state_test_2.json', SimpleConfig)
        self.assertIsInstance(config2.service, SimpleService)
        
        # Verify clean state by checking they're independent
        self.assertIsNot(config1.service, config2.service)


if __name__ == '__main__':
    unittest.main()