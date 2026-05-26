"""
Test suite for file-backed environment-parser functionality.
"""

import tempfile
import unittest
from pathlib import Path

from modelmirror.file_env.file_env_factory import FileEnvFactory


class TestFileEnvFactory(unittest.TestCase):
    """Test FileEnvFactory directory-backed file reading."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.envs_dir = Path(self.temp_dir) / "envs"
        self.envs_dir.mkdir()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_get_returns_value_for_present_file(self):
        (self.envs_dir / "DB_URL").write_text("postgres://localhost/app")
        factory = FileEnvFactory(str(self.envs_dir))
        self.assertEqual(factory.get("DB_URL"), "postgres://localhost/app")

    def test_get_strips_surrounding_whitespace(self):
        (self.envs_dir / "TOKEN").write_text("  tok_12345\n")
        factory = FileEnvFactory(str(self.envs_dir))
        self.assertEqual(factory.get("TOKEN"), "tok_12345")

    def test_get_returns_empty_string_for_present_but_empty_file(self):
        (self.envs_dir / "EMPTY").write_text("")
        factory = FileEnvFactory(str(self.envs_dir))
        self.assertEqual(factory.get("EMPTY"), "")

    def test_get_raises_value_error_for_absent_file(self):
        factory = FileEnvFactory(str(self.envs_dir))
        with self.assertRaises(ValueError):
            factory.get("MISSING")

    def test_get_raises_value_error_for_nonexistent_directory(self):
        factory = FileEnvFactory(str(Path(self.temp_dir) / "nonexistent"))
        with self.assertRaises(ValueError):
            factory.get("ANYTHING")


if __name__ == "__main__":
    unittest.main(verbosity=2)
