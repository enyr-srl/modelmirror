"""
Tests for Mirror class customization features: custom parsers and placeholders.
"""

import json
import unittest

from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror
from modelmirror.parser.default_key_parser import DefaultKeyParser
from modelmirror.parser.key_parser import FormatValidation, KeyParser, ParsedKey
from tests.fixtures.test_classes import DatabaseService, SimpleService, UserService


class CustomKeyParser(KeyParser):
    """Custom parser that uses @ symbol for instances: service@instance"""

    def _validate(self, key: str) -> FormatValidation:
        return FormatValidation(is_valid=True)

    def _parse(self, key: str) -> ParsedKey:
        if "@" in key:
            id_part, instance = key.split("@", 1)
            return ParsedKey(id=id_part, instance=instance)
        return ParsedKey(id=key, instance=None)


class VersionedKeyParser(KeyParser):
    """Parser that requires version: service:v1.0@instance"""

    def _validate(self, key: str) -> FormatValidation:
        if ":" not in key:
            return FormatValidation(False, "Version required: use 'id:version' or 'id:version@instance'")
        return FormatValidation(True)

    def _parse(self, key: str) -> ParsedKey:
        if "@" in key:
            id_version, instance = key.split("@", 1)
        else:
            id_version, instance = key, None

        id_part, version = id_version.split(":", 1)
        # For testing, we ignore version and just use id
        return ParsedKey(id=id_part, instance=instance)


class TestConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    service: SimpleService


class TestMirrorCustomization(unittest.TestCase):
    """Test suite for Mirror customization features."""

    def setUp(self):
        """Set up test fixtures."""
        self.default_mirror = Mirror("tests.fixtures")

    def test_default_parser_and_placeholder(self):
        """Test that default parser and placeholder work correctly."""
        # Create config with default $mirror placeholder
        config_data = {"service": {"$mirror": "simple_service", "name": "default_test"}}

        with open("/tmp/test_default.json", "w") as f:
            json.dump(config_data, f)

        config = self.default_mirror.reflect("/tmp/test_default.json", TestConfig)
        self.assertEqual(config.service.name, "default_test")

    def test_custom_placeholder(self):
        """Test Mirror with custom placeholder."""
        mirror = Mirror("tests.fixtures", DefaultKeyParser("$ref"))

        config_data = {"service": {"$ref": "simple_service", "name": "custom_placeholder"}}

        with open("/tmp/test_custom_placeholder.json", "w") as f:
            json.dump(config_data, f)

        config = mirror.reflect("/tmp/test_custom_placeholder.json", TestConfig)
        self.assertEqual(config.service.name, "custom_placeholder")

    def test_custom_parser_with_at_symbol(self):
        """Test Mirror with custom parser using @ for instances."""
        mirror = Mirror("tests.fixtures", key_parser=CustomKeyParser(placeholder="$mirror"))

        config_data = {
            "database": {
                "$mirror": "database_service@shared_db",
                "host": "localhost",
                "port": 5432,
                "database_name": "testdb",
            },
            "user_service": {"$mirror": "user_service", "database": "$shared_db", "cache_enabled": True},
        }

        with open("/tmp/test_custom_parser.json", "w") as f:
            json.dump(config_data, f)

        class CustomConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            database: DatabaseService
            user_service: UserService

        config = mirror.reflect("/tmp/test_custom_parser.json", CustomConfig)
        self.assertEqual(config.database.host, "localhost")
        self.assertTrue(config.user_service.cache_enabled)
        self.assertIs(config.user_service.database, config.database)

    def test_versioned_parser(self):
        """Test Mirror with versioned parser."""
        mirror = Mirror("tests.fixtures", key_parser=VersionedKeyParser(placeholder="$mirror"))

        config_data = {"service": {"$mirror": "simple_service:v1.0", "name": "versioned_service"}}

        with open("/tmp/test_versioned.json", "w") as f:
            json.dump(config_data, f)

        config = mirror.reflect("/tmp/test_versioned.json", TestConfig)
        self.assertEqual(config.service.name, "versioned_service")

    def test_versioned_parser_with_instance(self):
        """Test versioned parser with instance."""
        mirror = Mirror("tests.fixtures", key_parser=VersionedKeyParser(placeholder="$mirror"))

        config_data = {
            "database": {
                "$mirror": "database_service:v2.0@main_db",
                "host": "versioned.host",
                "port": 5432,
                "database_name": "versiondb",
            },
            "user_service": {"$mirror": "user_service:v1.0", "database": "$main_db", "cache_enabled": False},
        }

        with open("/tmp/test_versioned_instance.json", "w") as f:
            json.dump(config_data, f)

        class VersionedConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            database: DatabaseService
            user_service: UserService

        config = mirror.reflect("/tmp/test_versioned_instance.json", VersionedConfig)
        self.assertEqual(config.database.host, "versioned.host")
        self.assertFalse(config.user_service.cache_enabled)
        self.assertIs(config.user_service.database, config.database)

    def test_custom_placeholder_and_parser_together(self):
        """Test Mirror with both custom placeholder and parser."""
        mirror = Mirror("tests.fixtures", key_parser=CustomKeyParser(placeholder="$create"))

        config_data = {
            "service": {"$create": "simple_service@my_instance", "name": "combined_test"},
            "reference_test": {"value": "$my_instance"},  # This should resolve to the instance
        }

        with open("/tmp/test_combined.json", "w") as f:
            json.dump(config_data, f)

        class CombinedConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            service: SimpleService
            reference_test: dict

        config = mirror.reflect("/tmp/test_combined.json", CombinedConfig)
        self.assertEqual(config.service.name, "combined_test")
        self.assertIs(config.reference_test["value"], config.service)

    def test_parser_validation_error(self):
        """Test that parser validation errors are properly raised."""
        mirror = Mirror("tests.fixtures", key_parser=VersionedKeyParser(placeholder="$mirror"))

        config_data = {"service": {"$mirror": "simple_service", "name": "invalid"}}  # Missing version

        with open("/tmp/test_validation_error.json", "w") as f:
            json.dump(config_data, f)

        with self.assertRaises(ValueError) as context:
            mirror.reflect("/tmp/test_validation_error.json", TestConfig)

        self.assertIn("Version required", str(context.exception))

    def test_raw_reflection_with_custom_features(self):
        """Test raw reflection works with custom parser and placeholder."""
        mirror = Mirror("tests.fixtures", key_parser=CustomKeyParser(placeholder="$build"))

        config_data = {"service": {"$build": "simple_service@shared", "name": "raw_test"}}

        with open("/tmp/test_raw_custom.json", "w") as f:
            json.dump(config_data, f)

        instances = mirror.reflect_raw("/tmp/test_raw_custom.json")
        service = instances.get(SimpleService)
        self.assertEqual(service.name, "raw_test")

        # Test singleton retrieval
        shared_service = instances.get(SimpleService, "$shared")
        self.assertIs(service, shared_service)


if __name__ == "__main__":
    unittest.main()
