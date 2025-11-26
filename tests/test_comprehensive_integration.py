"""
Comprehensive integration tests for ModelMirror.

This test suite validates that all JSON configuration features work together
in complex, real-world scenarios.
"""

import unittest
from typing import List, Dict, Optional
from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror
from tests.fixtures.test_classes import (
    SimpleService, DatabaseService, UserService, ComplexService
)


class FullApplicationConfig(BaseModel):
    """Complete application configuration schema."""
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # Core services
    primary_database: DatabaseService
    secondary_database: DatabaseService
    user_service: UserService
    
    # Service collections
    microservices: List[SimpleService]
    service_registry: Dict[str, SimpleService]
    
    # Complex nested services
    orchestrator: ComplexService
    
    # Configuration metadata
    environment: str
    debug_mode: bool


class TestComprehensiveIntegration(unittest.TestCase):
    """Integration tests for complete application scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.mirror = Mirror('tests.fixtures')

    def test_full_application_configuration(self):
        """Test a complete application configuration with all features."""
        config = self.mirror.reflect(
            'tests/configs/full_application.json', 
            FullApplicationConfig
        )
        
        # Verify core services
        self.assertIsInstance(config.primary_database, DatabaseService)
        self.assertIsInstance(config.secondary_database, DatabaseService)
        self.assertIsInstance(config.user_service, UserService)
        
        # Verify different databases are used
        self.assertIsNot(config.primary_database, config.secondary_database)
        
        # Verify dependency injection
        self.assertIs(config.user_service.database, config.primary_database)
        
        # Verify collections
        self.assertEqual(len(config.microservices), 3)
        self.assertEqual(len(config.service_registry), 3)
        
        # Verify singleton references in collections
        self.assertIs(config.microservices[0], config.service_registry["auth"])
        
        # Verify complex nested service
        self.assertIsInstance(config.orchestrator, ComplexService)
        self.assertIs(config.orchestrator.database, config.primary_database)
        self.assertIs(config.orchestrator.user_service, config.user_service)
        
        # Verify configuration metadata
        self.assertEqual(config.environment, "production")
        self.assertEqual(config.debug_mode, False)

    def test_microservices_architecture_pattern(self):
        """Test configuration pattern for microservices architecture."""
        instances = self.mirror.reflect_raw('tests/configs/microservices_pattern.json')
        
        # Should have multiple databases for different services
        databases = instances.get(list[DatabaseService])
        self.assertGreaterEqual(len(databases), 2)
        
        # Should have multiple user services
        user_services = instances.get(list[UserService])
        self.assertGreaterEqual(len(user_services), 1)
        
        # Should have service registry
        service_registry = instances.get(dict[str, SimpleService])
        self.assertGreater(len(service_registry), 0)

    def test_configuration_with_environment_overrides(self):
        """Test configuration that simulates environment-specific overrides."""
        # Test development environment
        dev_mirror = Mirror('tests.fixtures')
        dev_config = dev_mirror.reflect(
            'tests/configs/environment_dev.json',
            FullApplicationConfig
        )
        
        self.assertEqual(dev_config.environment, "development")
        self.assertEqual(dev_config.debug_mode, True)
        self.assertEqual(dev_config.primary_database.host, "localhost")
        
        # Test production environment with new Mirror instance
        prod_mirror = Mirror('tests.fixtures')
        prod_config = prod_mirror.reflect(
            'tests/configs/environment_prod.json',
            FullApplicationConfig
        )
        
        self.assertEqual(prod_config.environment, "production")
        self.assertEqual(prod_config.debug_mode, False)
        self.assertEqual(prod_config.primary_database.host, "prod.db.example.com")

    def test_configuration_scaling_patterns(self):
        """Test configuration patterns for horizontal scaling."""
        instances = self.mirror.reflect_raw('tests/configs/scaling_pattern.json')
        
        # Should have multiple instances of the same service type
        services = instances.get(list[SimpleService])
        self.assertGreaterEqual(len(services), 5)
        
        # Should have load balancer configuration
        databases = instances.get(list[DatabaseService])
        self.assertGreaterEqual(len(databases), 2)

    def test_plugin_architecture_pattern(self):
        """Test configuration pattern for plugin-based architecture."""
        instances = self.mirror.reflect_raw('tests/configs/plugin_pattern.json')
        
        # Should have core services
        core_services = instances.get(list[ComplexService])
        self.assertGreaterEqual(len(core_services), 1)
        
        # Should have plugin services
        plugins = instances.get(list[SimpleService])
        self.assertGreaterEqual(len(plugins), 3)

    def test_configuration_validation_in_complex_scenario(self):
        """Test that validation works correctly in complex configurations."""
        # This should succeed
        config = self.mirror.reflect(
            'tests/configs/complex_valid.json',
            FullApplicationConfig
        )
        self.assertIsInstance(config, FullApplicationConfig)
        
        # This should fail validation
        with self.assertRaises(Exception):
            self.mirror.reflect(
                'tests/configs/complex_invalid.json',
                FullApplicationConfig
            )

    def test_performance_with_large_configuration(self):
        """Test performance with large, complex configurations."""
        import time
        
        start_time = time.time()
        config = self.mirror.reflect(
            'tests/configs/large_complex.json',
            FullApplicationConfig
        )
        end_time = time.time()
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(end_time - start_time, 5.0)  # 5 seconds max
        
        # Should still create all instances correctly
        self.assertIsInstance(config, FullApplicationConfig)

    def test_memory_efficiency_with_singletons(self):
        """Test that singleton references are memory efficient."""
        instances = self.mirror.reflect_raw('tests/configs/memory_test.json')
        
        # Get all user services that reference the shared database
        user_services = instances.get(list[UserService])
        
        # All user services should share the same database instance
        self.assertEqual(len(user_services), 3)
        
        # Verify all services reference the same database instance
        shared_db = user_services[0].database
        for service in user_services[1:]:
            self.assertIs(service.database, shared_db)

    def test_configuration_composition_patterns(self):
        """Test advanced composition patterns."""
        config = self.mirror.reflect(
            'tests/configs/composition_pattern.json',
            FullApplicationConfig
        )
        
        # Verify composition works correctly
        self.assertIsInstance(config.orchestrator.user_service, UserService)
        self.assertIsInstance(config.orchestrator.database, DatabaseService)
        
        # Verify shared dependencies
        self.assertIs(
            config.orchestrator.user_service.database,
            config.orchestrator.database
        )


if __name__ == '__main__':
    unittest.main()