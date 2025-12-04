"""
Test suite for inline instance creation patterns.
"""

import unittest

from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror
from tests.fixtures.test_classes import DatabaseService, SimpleService, UserService
from tests.fixtures.test_helper_classes import AppModel


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
        config = self.mirror.reflect("tests/configs/inline_mixed.json", MixedConfig)

        # Verify database singleton
        self.assertEqual(config.database.host, "localhost")
        self.assertIs(config.user_service.database, config.database)

        # Verify mixed list: singleton reference, same singleton, new instance
        self.assertEqual(len(config.simple_services), 3)
        self.assertIs(config.simple_services[0], config.simple_services[1])  # Same singleton
        self.assertIsNot(config.simple_services[0], config.simple_services[2])  # Different instances

    def test_deeply_nested_inline_instances(self):
        """Test deeply nested inline instance creation."""

        class NestedConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            user_service: UserService
            database: DatabaseService

        config = self.mirror.reflect("tests/configs/inline_nested.json", NestedConfig)

        # Verify nested inline instance becomes singleton
        self.assertIs(config.user_service.database, config.database)
        self.assertEqual(config.database.host, "nested.example.com")

    def test_inline_instances_in_arrays(self):
        """Test inline instances within arrays."""

        class ArrayConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            simple_services: list[SimpleService]

        config = self.mirror.reflect("tests/configs/inline_arrays.json", ArrayConfig)

        # Verify array structure
        self.assertEqual(len(config.simple_services), 4)
        self.assertIs(config.simple_services[1], config.simple_services[3])  # Singleton reference
        self.assertIsNot(config.simple_services[0], config.simple_services[2])  # Different instances


if __name__ == "__main__":
    unittest.main(verbosity=2)
