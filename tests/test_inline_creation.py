"""
Test suite for inline instance creation patterns.
"""

import json
import os
import sys
import tempfile
import unittest

# Add workspace to path when running directly
if __name__ == "__main__":
    workspace_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if workspace_path not in sys.path:
        sys.path.insert(0, workspace_path)

from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror
from tests.fixtures.fast_api_classes import AppModel
from tests.fixtures.test_classes import DatabaseService, SimpleService, UserService


class MixedConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    database: DatabaseService
    user_service: UserService
    simple_services: list[SimpleService]


class TestInlineCreation(unittest.TestCase):
    """Test inline instance creation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mirror = Mirror("tests.fixtures")

    def test_nested_inline_instance_creation(self):
        """Test that nested inline instances are created correctly."""
        config = self.mirror.reflect("tests/configs/fast-api.json", AppModel)

        # Verify structure is created correctly
        self.assertIsNotNone(config.international)
        self.assertIsNotNone(config.international.language)
        self.assertEqual(len(config.dataSourcesParams), 1)

    def test_mixed_inline_and_reference_instances(self):
        """Test mixing inline instances with singleton references."""
        config_data = {
            "database": {
                "$mirror": "database_service:shared_db",
                "host": "localhost",
                "port": 5432,
                "database_name": "testdb",
            },
            "user_service": {"$mirror": "user_service", "database": "$shared_db", "cache_enabled": True},
            "simple_services": [
                {"$mirror": "simple_service:service1", "name": "FirstService"},
                "$service1",
                {"$mirror": "simple_service", "name": "ThirdService"},
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = self.mirror.reflect(config_path, MixedConfig)

            # Verify database singleton
            self.assertEqual(config.database.host, "localhost")
            self.assertIs(config.user_service.database, config.database)

            # Verify mixed list: singleton reference, same singleton, new instance
            self.assertEqual(len(config.simple_services), 3)
            self.assertIs(config.simple_services[0], config.simple_services[1])  # Same singleton
            self.assertIsNot(config.simple_services[0], config.simple_services[2])  # Different instances

        finally:
            os.unlink(config_path)

    def test_deeply_nested_inline_instances(self):
        """Test deeply nested inline instance creation."""
        config_data = {
            "user_service": {
                "$mirror": "user_service",
                "database": {
                    "$mirror": "database_service:nested_db",
                    "host": "nested.example.com",
                    "port": 3306,
                    "database_name": "nested",
                },
                "cache_enabled": False,
            },
            "database": "$nested_db",
        }

        class NestedConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            user_service: UserService
            database: DatabaseService

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = self.mirror.reflect(config_path, NestedConfig)

            # Verify nested inline instance becomes singleton
            self.assertIs(config.user_service.database, config.database)
            self.assertEqual(config.database.host, "nested.example.com")

        finally:
            os.unlink(config_path)

    def test_inline_instances_in_arrays(self):
        """Test inline instances within arrays."""
        config_data = {
            "simple_services": [
                {"$mirror": "simple_service", "name": "Service1"},
                {"$mirror": "simple_service:shared", "name": "SharedService"},
                {"$mirror": "simple_service", "name": "Service3"},
                "$shared",
            ]
        }

        class ArrayConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            simple_services: list[SimpleService]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = self.mirror.reflect(config_path, ArrayConfig)

            # Verify array structure
            self.assertEqual(len(config.simple_services), 4)
            self.assertIs(config.simple_services[1], config.simple_services[3])  # Singleton reference
            self.assertIsNot(config.simple_services[0], config.simple_services[2])  # Different instances

        finally:
            os.unlink(config_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
