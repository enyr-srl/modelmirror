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
        config_data = {"service_type": "$simple_service$", "database_type": "$database_service$"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = self.mirror.reflect(config_path, TypeResolutionConfig)

            # Verify that type references return the actual classes
            self.assertEqual(config.service_type, SimpleService)
            self.assertEqual(config.database_type, DatabaseService)

            # Verify they are actual class types, not instances
            self.assertTrue(isinstance(config.service_type, type))
            self.assertTrue(isinstance(config.database_type, type))

        finally:
            os.unlink(config_path)

    def test_type_instantiation_works(self):
        """Test that resolved types can be instantiated correctly."""
        config_data = {"service_class": "$simple_service$", "name": "TestService"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = self.mirror.reflect(config_path, ServiceWithTypeConfig)

            # Verify the type is resolved correctly
            self.assertEqual(config.service_class, SimpleService)

            # Test that we can instantiate the resolved type
            instance = config.service_class(name="DynamicInstance")
            self.assertIsInstance(instance, SimpleService)
            self.assertEqual(instance.name, "DynamicInstance")

        finally:
            os.unlink(config_path)

    def test_invalid_type_reference_raises_error(self):
        """Test that invalid type references raise appropriate errors."""
        config_data = {"service_type": "$nonexistent_service$", "database_type": "$database_service$"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            with self.assertRaises(KeyError) as context:
                self.mirror.reflect(config_path, TypeResolutionConfig)

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
            "service_type": "$simple_service$",
            "database_type": "$database_service$",
        }

        class MixedConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            database_instance: DatabaseService
            service_type: Type[SimpleService]
            database_type: Type[DatabaseService]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = self.mirror.reflect(config_path, MixedConfig)

            # Verify instance is created
            self.assertIsInstance(config.database_instance, DatabaseService)
            self.assertEqual(config.database_instance.host, "localhost")

            # Verify types are resolved
            self.assertEqual(config.service_type, SimpleService)
            self.assertEqual(config.database_type, DatabaseService)

            # Verify types are classes, not instances
            self.assertTrue(isinstance(config.service_type, type))
            self.assertTrue(isinstance(config.database_type, type))

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
            self.assertEqual(service.service_type, SimpleService)

        finally:
            os.unlink(config_path)


if __name__ == "__main__":
    unittest.main()
