"""
Test suite for environment-variable parser functionality.
"""

import os
import unittest

from modelmirror.env.env_factory import EnvFactory
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
