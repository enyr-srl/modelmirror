"""
Test suite for type resolution functionality.
"""

import json
import os
import tempfile
import unittest
from typing import Type

from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror
from tests.fixtures.test_classes import DatabaseService, SimpleService
from tests.fixtures.test_classes_with_types import ServiceWithTypeRef
from tests.fixtures.test_factory_classes import ServiceFactory


class TypeResolutionConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    service_type: Type[SimpleService]
    database_type: Type[DatabaseService]


class ServiceWithTypeConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    service_class: Type[SimpleService]
    name: str


class TestTypeResolution(unittest.TestCase):
    """Test suite for type resolution functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mirror = Mirror("tests.fixtures")

    def test_basic_type_resolution(self):
        """Test that type references resolve to correct classes."""
        config_data = {
            "service_with_type": {
                "$mirror": "service_with_type_ref",
                "name": "TestService",
                "service_type": "$simple_service$",
            }
        }

        class ServiceConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            service_with_type: ServiceWithTypeRef

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = self.mirror.reflect(config_path, ServiceConfig)
            # Verify that type reference is resolved correctly
            self.assertTrue(isinstance(config.service_with_type.service_type, type))
            self.assertEqual(config.service_with_type.service_type, SimpleService)
        finally:
            os.unlink(config_path)

    def test_type_instantiation_works(self):
        """Test that resolved types can be instantiated correctly."""
        config_data = {
            "factory": {"$mirror": "service_factory", "service_class": "$simple_service$", "dependency_service": None}
        }

        class FactoryConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            factory: ServiceFactory

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = self.mirror.reflect(config_path, FactoryConfig)

            # Verify the type is resolved correctly
            self.assertEqual(config.factory.service_class.__name__, "SimpleService")

            # Test that we can instantiate the resolved type
            instance = config.factory.service_class(name="DynamicInstance")
            self.assertEqual(instance.__class__.__name__, "SimpleService")
            self.assertEqual(instance.name, "DynamicInstance")

        finally:
            os.unlink(config_path)

    def test_invalid_type_reference_raises_error(self):
        """Test that invalid type references raise appropriate errors."""
        config_data = {
            "service_with_invalid_type": {
                "$mirror": "service_with_type_ref",
                "name": "TestService",
                "service_type": "$nonexistent_service$",
            }
        }

        class InvalidConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            service_with_invalid_type: ServiceWithTypeRef

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            with self.assertRaises(KeyError) as context:
                self.mirror.reflect(config_path, InvalidConfig)

            # Verify the error message mentions the missing class
            self.assertIn("nonexistent_service", str(context.exception))
            self.assertIn("not found", str(context.exception))

        finally:
            os.unlink(config_path)

    def test_mixed_type_and_instance_references(self):
        """Test configuration with both type and instance references."""
        config_data = {
            "database_instance": {
                "$mirror": "database_service:my_db",
                "host": "localhost",
                "port": 5432,
                "database_name": "testdb",
            },
            "service_with_type": {
                "$mirror": "service_with_type_ref",
                "name": "MixedService",
                "service_type": "$simple_service$",
            },
        }

        class MixedConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            database_instance: DatabaseService
            service_with_type: ServiceWithTypeRef

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = self.mirror.reflect(config_path, MixedConfig)

            # Verify instance is created
            self.assertIsInstance(config.database_instance, DatabaseService)
            self.assertEqual(config.database_instance.host, "localhost")

            # Verify type is resolved in the service
            self.assertEqual(config.service_with_type.service_type.__name__, "SimpleService")
            self.assertTrue(config.service_with_type.service_type == SimpleService)

        finally:
            os.unlink(config_path)

    def test_type_resolution_with_raw_reflection(self):
        """Test type resolution works with raw reflection."""
        config_data = {
            "service_with_type": {
                "$mirror": "service_with_type_ref",
                "name": "TestService",
                "service_type": "$simple_service$",
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            instances = self.mirror.reflect_raw(config_path)

            # Get the service instance
            from tests.fixtures.test_classes_with_types import ServiceWithTypeRef

            service = instances.get(ServiceWithTypeRef)

            self.assertIsNotNone(service)
            self.assertEqual(service.name, "TestService")
            self.assertEqual(service.service_type.__name__, "SimpleService")

        finally:
            os.unlink(config_path)


if __name__ == "__main__":
    unittest.main()
