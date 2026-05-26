"""
Test suite for file-backed environment-parser functionality.
"""

import tempfile
import unittest
from pathlib import Path

from pydantic import BaseModel

from modelmirror.envs.file_env_factory import FileEnvFactory
from modelmirror.mirror import Mirror
from modelmirror.parser.env_parser import EnvParser
from modelmirror.parser.file_env_parser import FileEnvParser
from modelmirror.parser.mirror_env import MirrorEnv


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


class TestFileEnvParser(unittest.TestCase):
    """Test FileEnvParser prefix detection and file resolution."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.envs_dir = Path(self.temp_dir) / "envs"
        self.envs_dir.mkdir()
        (self.envs_dir / "DB_URL").write_text("postgres://localhost/app")
        (self.envs_dir / "EMPTY").write_text("")
        self.parser = FileEnvParser(str(self.envs_dir))

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_file_env_parser_is_an_env_parser(self):
        self.assertIsInstance(self.parser, EnvParser)

    def test_parses_prefixed_name_and_strips_prefix(self):
        result = self.parser.parse("ENV_DB_URL")
        self.assertIsInstance(result, MirrorEnv)
        if result is not None:
            self.assertEqual(result.value, "postgres://localhost/app")

    def test_returns_none_for_non_prefixed_string(self):
        self.assertIsNone(self.parser.parse("db_url"))
        self.assertIsNone(self.parser.parse("DB_URL"))

    def test_returns_mirror_env_with_empty_value_for_present_but_empty_file(self):
        result = self.parser.parse("ENV_EMPTY")
        self.assertIsInstance(result, MirrorEnv)
        if result is not None:
            self.assertEqual(result.value, "")

    def test_raises_value_error_for_prefixed_but_absent_file(self):
        with self.assertRaises(ValueError):
            self.parser.parse("ENV_MISSING")


class TestFileEnvParserIntegration(unittest.TestCase):
    """Test FileEnvParser as a drop-in env_parser for Mirror."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.envs_dir = Path(self.temp_dir) / "envs"
        self.envs_dir.mkdir()
        (self.envs_dir / "DB_URL").write_text("postgres://localhost/app")
        (self.envs_dir / "TOKEN").write_text("tok_12345")

        self.config_dir = Path(self.temp_dir) / "configs"
        self.config_dir.mkdir()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_mirror_resolves_file_env_values(self):
        config_content = """{
    "database_url": "ENV_DB_URL",
    "token": "ENV_TOKEN",
    "normal_value": "regular_string"
}"""
        config_path = self.config_dir / "file_env_basic.json"
        config_path.write_text(config_content)

        class FileEnvConfig(BaseModel):
            database_url: str
            token: str
            normal_value: str

        mirror = Mirror("tests.fixtures", env_parser=FileEnvParser(str(self.envs_dir)))
        config = mirror.reflect(str(config_path), FileEnvConfig)

        self.assertEqual(config.database_url, "postgres://localhost/app")
        self.assertEqual(config.token, "tok_12345")
        self.assertEqual(config.normal_value, "regular_string")

    def test_mirror_raises_when_file_is_missing(self):
        config_content = """{
    "database_url": "ENV_DEFINITELY_MISSING"
}"""
        config_path = self.config_dir / "file_env_missing.json"
        config_path.write_text(config_content)

        class MissingConfig(BaseModel):
            database_url: str

        mirror = Mirror("tests.fixtures", env_parser=FileEnvParser(str(self.envs_dir)))
        with self.assertRaises(ValueError):
            mirror.reflect(str(config_path), MissingConfig)


if __name__ == "__main__":
    unittest.main(verbosity=2)
