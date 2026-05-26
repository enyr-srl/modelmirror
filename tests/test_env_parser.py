"""
Test suite for environment-variable parser functionality.
"""

import os
import tempfile
import unittest
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from modelmirror.env.env_factory import EnvFactory
from modelmirror.mirror import Mirror
from modelmirror.parser.default_env_parser import DefaultEnvParser
from modelmirror.parser.env_parser import EnvParser
from modelmirror.parser.mirror_env import MirrorEnv


class TestEnvFactory(unittest.TestCase):
    """Test EnvFactory environment access."""

    def setUp(self):
        self.factory = EnvFactory()
        self._original_environ = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._original_environ)

    def test_get_returns_value_for_set_variable(self):
        os.environ["MODELMIRROR_TEST_DB_URL"] = "postgres://localhost/test"
        self.assertEqual(
            self.factory.get("MODELMIRROR_TEST_DB_URL"),
            "postgres://localhost/test",
        )

    def test_get_returns_empty_string_for_set_but_empty_variable(self):
        os.environ["MODELMIRROR_TEST_EMPTY"] = ""
        self.assertEqual(self.factory.get("MODELMIRROR_TEST_EMPTY"), "")

    def test_get_raises_value_error_for_unset_variable(self):
        os.environ.pop("MODELMIRROR_TEST_MISSING", None)
        with self.assertRaises(ValueError):
            self.factory.get("MODELMIRROR_TEST_MISSING")


class TestDefaultEnvParser(unittest.TestCase):
    """Test DefaultEnvParser prefix detection and resolution."""

    def setUp(self):
        self.parser = DefaultEnvParser()
        self._original_environ = dict(os.environ)
        os.environ["MODELMIRROR_TEST_DB_URL"] = "postgres://localhost/test"
        os.environ["MODELMIRROR_TEST_EMPTY"] = ""

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._original_environ)

    def test_default_env_parser_is_an_env_parser(self):
        self.assertIsInstance(self.parser, EnvParser)

    def test_parses_prefixed_name_and_strips_prefix(self):
        result = self.parser.parse("ENV_MODELMIRROR_TEST_DB_URL")
        self.assertIsInstance(result, MirrorEnv)
        if result is not None:
            self.assertEqual(result.value, "postgres://localhost/test")

    def test_returns_none_for_non_prefixed_string(self):
        # Lowercase, and a bare uppercase name without the ENV_ marker.
        self.assertIsNone(self.parser.parse("database_url"))
        self.assertIsNone(self.parser.parse("MODELMIRROR_TEST_DB_URL"))

    def test_returns_mirror_env_with_empty_value_for_set_but_empty_variable(self):
        result = self.parser.parse("ENV_MODELMIRROR_TEST_EMPTY")
        self.assertIsInstance(result, MirrorEnv)
        if result is not None:
            self.assertEqual(result.value, "")

    def test_raises_value_error_for_prefixed_but_unset_variable(self):
        os.environ.pop("MODELMIRROR_TEST_MISSING", None)
        with self.assertRaises(ValueError):
            self.parser.parse("ENV_MODELMIRROR_TEST_MISSING")


class TestEnvParserIntegration(unittest.TestCase):
    """Test env parser integration with Mirror."""

    def setUp(self):
        self._original_environ = dict(os.environ)
        os.environ["MODELMIRROR_DB_URL"] = "postgres://localhost/app"
        os.environ["MODELMIRROR_TOKEN"] = "tok_12345"

        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "configs"
        self.config_dir.mkdir()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._original_environ)

        import shutil

        shutil.rmtree(self.temp_dir)

    def test_mirror_resolves_env_values(self):
        config_content = """{
    "database_url": "ENV_MODELMIRROR_DB_URL",
    "token": "ENV_MODELMIRROR_TOKEN",
    "normal_value": "regular_string"
}"""
        config_path = self.config_dir / "env_basic.json"
        config_path.write_text(config_content)

        class EnvConfig(BaseModel):
            database_url: str
            token: str
            normal_value: str

        mirror = Mirror("tests.fixtures", env_parser=DefaultEnvParser())
        config = mirror.reflect(str(config_path), EnvConfig)

        self.assertEqual(config.database_url, "postgres://localhost/app")
        self.assertEqual(config.token, "tok_12345")
        self.assertEqual(config.normal_value, "regular_string")

    def test_env_takes_precedence_over_secret_parser(self):

        from modelmirror.parser.default_secret_parser import DefaultSecretParser

        secrets_dir = Path(self.temp_dir) / "secrets"
        secrets_dir.mkdir()
        # A secret file whose name collides with the ENV_-prefixed string.
        (secrets_dir / "ENV_MODELMIRROR_DB_URL").write_text("secret_should_not_win")

        config_content = """{
    "database_url": "ENV_MODELMIRROR_DB_URL"
}"""
        config_path = self.config_dir / "env_precedence.json"
        config_path.write_text(config_content)

        class PrecedenceConfig(BaseModel):
            database_url: str

        mirror = Mirror(
            "tests.fixtures",
            secret_parser=DefaultSecretParser(str(secrets_dir)),
            env_parser=DefaultEnvParser(),
        )
        config = mirror.reflect(str(config_path), PrecedenceConfig)

        self.assertEqual(config.database_url, "postgres://localhost/app")

    def test_env_with_mirror_reference(self):
        from tests.fixtures.test_classes import SimpleService

        os.environ["MODELMIRROR_SERVICE_NAME"] = "EnvNamedService"

        config_content = """{
    "service": {
        "$mirror": "simple_service",
        "name": "ENV_MODELMIRROR_SERVICE_NAME"
    },
    "database_url": "ENV_MODELMIRROR_DB_URL",
    "token": "ENV_MODELMIRROR_TOKEN"
}"""
        config_path = self.config_dir / "env_mixed.json"
        config_path.write_text(config_content)

        class MixedConfig(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            service: SimpleService
            database_url: str
            token: str

        mirror = Mirror("tests.fixtures", env_parser=DefaultEnvParser())
        config = mirror.reflect(str(config_path), MixedConfig)

        self.assertIsInstance(config.service, SimpleService)
        # Resolved by ReferenceService.__resolve_params (instance constructor param).
        self.assertEqual(config.service.name, "EnvNamedService")
        # Resolved by the engine's __instantiate_model hook (top-level fields).
        self.assertEqual(config.database_url, "postgres://localhost/app")
        self.assertEqual(config.token, "tok_12345")

    def test_env_in_nested_structure(self):
        config_content = """{
    "database": {
        "host": "localhost",
        "url": "ENV_MODELMIRROR_DB_URL"
    },
    "services": [
        {"name": "service1", "token": "ENV_MODELMIRROR_TOKEN"},
        {"name": "service2", "token": "regular_token"}
    ]
}"""
        config_path = self.config_dir / "env_nested.json"
        config_path.write_text(config_content)

        class NestedConfig(BaseModel):
            database: dict
            services: list

        mirror = Mirror("tests.fixtures", env_parser=DefaultEnvParser())
        config = mirror.reflect(str(config_path), NestedConfig)

        self.assertEqual(config.database["url"], "postgres://localhost/app")
        self.assertEqual(config.services[0]["token"], "tok_12345")
        self.assertEqual(config.services[1]["token"], "regular_token")

    def test_env_resolution_with_caching(self):
        config_content = """{
    "database_url": "ENV_MODELMIRROR_DB_URL"
}"""
        config_path = self.config_dir / "env_cache.json"
        config_path.write_text(config_content)

        class CacheConfig(BaseModel):
            database_url: str

        mirror = Mirror("tests.fixtures", env_parser=DefaultEnvParser())
        config1 = mirror.reflect(str(config_path), CacheConfig)
        config2 = mirror.reflect(str(config_path), CacheConfig)

        self.assertEqual(config1.database_url, "postgres://localhost/app")
        self.assertIs(config1, config2)

    def test_env_resolution_without_caching(self):
        config_content = """{
    "database_url": "ENV_MODELMIRROR_DB_URL"
}"""
        config_path = self.config_dir / "env_no_cache.json"
        config_path.write_text(config_content)

        class NoCacheConfig(BaseModel):
            database_url: str

        mirror = Mirror("tests.fixtures", env_parser=DefaultEnvParser())
        config1 = mirror.reflect(str(config_path), NoCacheConfig, cached=False)
        config2 = mirror.reflect(str(config_path), NoCacheConfig, cached=False)

        self.assertEqual(config1.database_url, "postgres://localhost/app")
        self.assertEqual(config2.database_url, "postgres://localhost/app")
        self.assertIsNot(config1, config2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
