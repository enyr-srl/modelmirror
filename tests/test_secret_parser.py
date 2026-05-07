"""
Test suite for secret parser functionality.
"""

import tempfile
import unittest
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror
from modelmirror.parser.default_secret_parser import DefaultSecretParser
from modelmirror.parser.mirror_secret import MirrorSecret
from modelmirror.secrets.secret_factory import SecretFactory


class SecretConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    database_password: str
    api_key: str
    normal_value: str


class TestSecretParser(unittest.TestCase):
    """Test secret parser functionality."""

    def setUp(self):
        """Set up test fixtures with temporary secrets directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.secrets_dir = Path(self.temp_dir) / "secrets"
        self.secrets_dir.mkdir()

        # Create test secret files
        (self.secrets_dir / "DATABASE_PASSWORD").write_text("super_secret_db_pass")
        (self.secrets_dir / "API_KEY").write_text("sk-1234567890abcdef")
        (self.secrets_dir / "JWT_SECRET").write_text("jwt_signing_key_xyz")

        self.secret_parser = DefaultSecretParser(str(self.secrets_dir))

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_secret_parser_uppercase_detection(self):
        """Test that secret parser detects uppercase strings."""
        # Should detect uppercase strings
        result = self.secret_parser.parse("DATABASE_PASSWORD")
        self.assertIsInstance(result, MirrorSecret)
        if result is not None:
            self.assertEqual(result.value, "super_secret_db_pass")

        # Should not detect lowercase strings
        result = self.secret_parser.parse("database_password")
        self.assertIsNone(result)

        # Should not detect mixed case strings
        result = self.secret_parser.parse("Database_Password")
        self.assertIsNone(result)

    def test_secret_parser_file_reading(self):
        """Test that secret parser reads files correctly."""
        result = self.secret_parser.parse("API_KEY")
        self.assertIsNotNone(result)
        if result is not None:
            self.assertEqual(result.value, "sk-1234567890abcdef")

        result = self.secret_parser.parse("JWT_SECRET")
        self.assertIsNotNone(result)
        if result is not None:
            self.assertEqual(result.value, "jwt_signing_key_xyz")

    def test_secret_parser_returns_none_for_missing_secret_so_chain_can_fall_through(self):
        result = self.secret_parser.parse("MISSING_SECRET")
        self.assertIsNone(result)

    def test_secret_factory_direct_usage(self):
        """Test SecretFactory directly."""
        factory = SecretFactory(str(self.secrets_dir))

        # Test existing secret
        secret = factory.get("DATABASE_PASSWORD")
        self.assertEqual(secret, "super_secret_db_pass")

        # Test missing secret
        with self.assertRaises(ValueError):
            factory.get("NONEXISTENT")

    def test_secret_factory_empty_directory(self):
        """Test SecretFactory with empty directory."""
        empty_dir = Path(self.temp_dir) / "empty"
        empty_dir.mkdir()

        factory = SecretFactory(str(empty_dir))
        with self.assertRaises(ValueError):
            factory.get("ANY_SECRET")

    def test_secret_factory_nonexistent_directory(self):
        """Test SecretFactory with nonexistent directory."""
        nonexistent_dir = str(Path(self.temp_dir) / "nonexistent")

        factory = SecretFactory(nonexistent_dir)
        with self.assertRaises(ValueError):
            factory.get("ANY_SECRET")


class TestSecretParserIntegration(unittest.TestCase):
    """Test secret parser integration with Mirror."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.secrets_dir = Path(self.temp_dir) / "secrets"
        self.secrets_dir.mkdir()

        # Create test secrets
        (self.secrets_dir / "DB_PASSWORD").write_text("secret_db_pass")
        (self.secrets_dir / "API_TOKEN").write_text("token_12345")
        (self.secrets_dir / "AUTH_TOKEN").write_text("auth_token_xyz")
        (self.secrets_dir / "JWT_SECRET").write_text("jwt_secret_key")
        (self.secrets_dir / "ENCRYPTION_KEY").write_text("encryption_key_123")

        # Create config directory
        self.config_dir = Path(self.temp_dir) / "configs"
        self.config_dir.mkdir()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_mirror_with_secrets(self):
        """Test Mirror integration with secret parser."""
        # Create custom secret parser
        secret_parser = DefaultSecretParser(str(self.secrets_dir))
        mirror = Mirror("tests.fixtures", secret_parser=secret_parser)

        # Reflect configuration
        config = mirror.reflect("tests/configs/secret_basic.json", SecretConfig)

        # Verify secrets were resolved
        self.assertEqual(config.database_password, "secret_db_pass")
        self.assertEqual(config.api_key, "token_12345")
        self.assertEqual(config.normal_value, "regular_string")

    def test_mirror_with_mixed_secrets_and_references(self):
        """Test Mirror with both secrets and regular references."""
        # Create config with mixed content
        config_content = """{
    "service": {
        "$mirror": "simple_service",
        "name": "TestService"
    },
    "password": "DB_PASSWORD",
    "token": "API_TOKEN"
}"""
        config_path = self.config_dir / "mixed_config.json"
        config_path.write_text(config_content)

        secret_parser = DefaultSecretParser(str(self.secrets_dir))
        mirror = Mirror("tests.fixtures", secret_parser=secret_parser)

        # This should work with the simple service from fixtures
        from tests.fixtures.test_classes import SimpleService

        class MixedConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            service: SimpleService
            password: str
            token: str

        config = mirror.reflect(str(config_path), MixedConfig)

        # Verify service was created and secrets were resolved
        self.assertIsInstance(config.service, SimpleService)
        self.assertEqual(config.service.name, "TestService")
        self.assertEqual(config.password, "secret_db_pass")
        self.assertEqual(config.token, "token_12345")

    def test_mirror_secret_in_nested_structure(self):
        """Test secrets in nested data structures."""
        config_content = """{
    "database": {
        "host": "localhost",
        "credentials": {
            "username": "admin",
            "password": "DB_PASSWORD"
        }
    },
    "apis": [
        {
            "name": "service1",
            "token": "API_TOKEN"
        },
        {
            "name": "service2",
            "token": "regular_token"
        }
    ]
}"""
        config_path = self.config_dir / "nested_secrets.json"
        config_path.write_text(config_content)

        class NestedConfig(BaseModel):
            database: dict
            apis: list

        secret_parser = DefaultSecretParser(str(self.secrets_dir))
        mirror = Mirror("tests.fixtures", secret_parser=secret_parser)

        config = mirror.reflect(str(config_path), NestedConfig)

        # Verify nested secrets were resolved
        self.assertEqual(config.database["credentials"]["password"], "secret_db_pass")
        self.assertEqual(config.apis[0]["token"], "token_12345")
        self.assertEqual(config.apis[1]["token"], "regular_token")  # Not uppercase, not resolved

    def test_mirror_secret_with_caching(self):
        """Test that secret resolution works with Mirror caching."""
        config_content = """{
    "password": "DB_PASSWORD",
    "value": "normal"
}"""
        config_path = self.config_dir / "cache_test.json"
        config_path.write_text(config_content)

        class CacheConfig(BaseModel):
            password: str
            value: str

        secret_parser = DefaultSecretParser(str(self.secrets_dir))
        mirror = Mirror("tests.fixtures", secret_parser=secret_parser)

        # First call
        config1 = mirror.reflect(str(config_path), CacheConfig)
        self.assertEqual(config1.password, "secret_db_pass")

        # Second call (should use cache)
        config2 = mirror.reflect(str(config_path), CacheConfig)
        self.assertEqual(config2.password, "secret_db_pass")
        self.assertIs(config1, config2)  # Same object from cache

    def test_mirror_secret_without_caching(self):
        """Test secret resolution with caching disabled."""
        config_content = """{
    "password": "DB_PASSWORD"
}"""
        config_path = self.config_dir / "no_cache_test.json"
        config_path.write_text(config_content)

        class NoCacheConfig(BaseModel):
            password: str

        secret_parser = DefaultSecretParser(str(self.secrets_dir))
        mirror = Mirror("tests.fixtures", secret_parser=secret_parser)

        # Multiple calls without caching
        config1 = mirror.reflect(str(config_path), NoCacheConfig, cached=False)
        config2 = mirror.reflect(str(config_path), NoCacheConfig, cached=False)

        self.assertEqual(config1.password, "secret_db_pass")
        self.assertEqual(config2.password, "secret_db_pass")
        self.assertIsNot(config1, config2)  # Different objects


if __name__ == "__main__":
    unittest.main(verbosity=2)
