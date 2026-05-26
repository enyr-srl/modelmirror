"""
Test suite for environment-variable parser functionality.
"""

import os
import tempfile
import unittest
from pathlib import Path

from pydantic import BaseModel

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
