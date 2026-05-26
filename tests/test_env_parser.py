"""
Test suite for environment-variable parser functionality.
"""

import os
import unittest

from modelmirror.env.env_factory import EnvFactory


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
