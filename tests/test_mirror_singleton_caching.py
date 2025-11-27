"""
Test suite for Mirror singleton behavior and caching functionality.
"""

import unittest

from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror
from tests.fixtures.test_classes import DatabaseService, SimpleService


class TestConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    service: SimpleService


class DatabaseConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    database: DatabaseService


class TestMirrorSingletonCaching(unittest.TestCase):
    """Test Mirror singleton behavior and caching functionality."""

    def test_mirror_singleton_behavior(self):
        """Test that Mirror instances are singletons with same parameters."""
        mirror1 = Mirror("tests.fixtures")
        mirror2 = Mirror("tests.fixtures")

        # Same parameters should return same instance
        self.assertIs(mirror1, mirror2, "Same parameters should return same Mirror instance")

    def test_mirror_different_parameters_create_different_instances(self):
        """Test that different parameters create different Mirror instances."""
        mirror1 = Mirror("tests.fixtures")
        mirror2 = Mirror("tests.fixtures", placeholder="$ref")

        # Different parameters should create different instances
        self.assertIsNot(mirror1, mirror2, "Different parameters should create different instances")

    def test_reflect_cached_by_default(self):
        """Test that reflect() caches results by default."""
        mirror = Mirror("tests.fixtures")

        # First call
        config1 = mirror.reflect("tests/configs/simple.json", TestConfig)

        # Second call should return same cached object
        config2 = mirror.reflect("tests/configs/simple.json", TestConfig)

        self.assertIs(config1, config2, "Default behavior should cache reflections")

    def test_reflect_cached_explicit(self):
        """Test that reflect(cached=True) caches results."""
        mirror = Mirror("tests.fixtures")

        # First call with explicit caching
        config1 = mirror.reflect("tests/configs/simple.json", TestConfig, cached=True)

        # Second call should return same cached object
        config2 = mirror.reflect("tests/configs/simple.json", TestConfig, cached=True)

        self.assertIs(config1, config2, "Explicit cached=True should cache reflections")

    def test_reflect_not_cached(self):
        """Test that reflect(cached=False) creates fresh instances."""
        mirror = Mirror("tests.fixtures")

        # First call without caching
        config1 = mirror.reflect("tests/configs/simple.json", TestConfig, cached=False)

        # Second call should return different object
        config2 = mirror.reflect("tests/configs/simple.json", TestConfig, cached=False)

        self.assertIsNot(config1, config2, "cached=False should create fresh instances")

    def test_reflect_mixed_caching(self):
        """Test mixing cached and non-cached calls."""
        mirror = Mirror("tests.fixtures")

        # First call cached
        config1 = mirror.reflect("tests/configs/simple.json", TestConfig, cached=True)

        # Second call not cached
        config2 = mirror.reflect("tests/configs/simple.json", TestConfig, cached=False)

        # Third call cached (should return same as first)
        config3 = mirror.reflect("tests/configs/simple.json", TestConfig, cached=True)

        self.assertIsNot(config1, config2, "Cached and non-cached should be different")
        self.assertIs(config1, config3, "Cached calls should return same object")

    def test_reflect_raw_cached_by_default(self):
        """Test that reflect_raw() caches results by default."""
        mirror = Mirror("tests.fixtures")

        # First call
        raw1 = mirror.reflect_raw("tests/configs/simple.json")

        # Second call should return same cached object
        raw2 = mirror.reflect_raw("tests/configs/simple.json")

        self.assertIs(raw1, raw2, "Default behavior should cache raw reflections")

    def test_reflect_raw_not_cached(self):
        """Test that reflect_raw(cached=False) creates fresh instances."""
        mirror = Mirror("tests.fixtures")

        # First call without caching
        raw1 = mirror.reflect_raw("tests/configs/simple.json", cached=False)

        # Second call should return different object
        raw2 = mirror.reflect_raw("tests/configs/simple.json", cached=False)

        self.assertIsNot(raw1, raw2, "cached=False should create fresh raw instances")

    def test_global_cache_across_mirror_instances(self):
        """Test that cache is shared across Mirror instances."""
        mirror1 = Mirror("tests.fixtures")
        mirror2 = Mirror("tests.fixtures")

        # First call on mirror1
        config1 = mirror1.reflect("tests/configs/simple.json", TestConfig)

        # Second call on mirror2 should return same cached object
        config2 = mirror2.reflect("tests/configs/simple.json", TestConfig)

        self.assertIs(config1, config2, "Cache should be shared across Mirror instances")

    def test_different_config_files_cached_separately(self):
        """Test that different config files are cached separately."""
        mirror = Mirror("tests.fixtures")

        # Different config files
        config1 = mirror.reflect("tests/configs/simple.json", TestConfig)
        config2 = mirror.reflect("tests/configs/database.json", DatabaseConfig)

        self.assertIsNot(config1, config2, "Different configs should be cached separately")

    def test_different_model_types_cached_separately(self):
        """Test that different model types are cached separately."""
        mirror = Mirror("tests.fixtures")

        # Same config, different model types
        config1 = mirror.reflect("tests/configs/simple.json", TestConfig)
        raw1 = mirror.reflect_raw("tests/configs/simple.json")

        self.assertIsNot(config1, raw1, "Different model types should be cached separately")

    def test_cached_vs_non_cached_behavior(self):
        """Test difference between cached and non-cached reflections."""
        mirror = Mirror("tests.fixtures")

        # Create cached reflection
        config1 = mirror.reflect("tests/configs/simple.json", TestConfig)

        # Create non-cached reflection
        config2 = mirror.reflect("tests/configs/simple.json", TestConfig, cached=False)

        self.assertIsNot(config1, config2, "Cached and non-cached should be different objects")

    def test_mirror_singleton_persistence(self):
        """Test that Mirror instances persist as singletons."""
        mirror1 = Mirror("tests.fixtures")
        config1 = mirror1.reflect("tests/configs/simple.json", TestConfig)

        # Create another Mirror with same parameters
        mirror2 = Mirror("tests.fixtures")
        config2 = mirror2.reflect("tests/configs/simple.json", TestConfig)

        self.assertIs(mirror1, mirror2, "Same parameters should return same Mirror instance")
        self.assertIs(config1, config2, "Cached reflections should be shared across singleton instances")

    def test_cache_key_uniqueness(self):
        """Test that cache keys are unique for different combinations."""
        mirror = Mirror("tests.fixtures")

        # Create different cached objects
        config1 = mirror.reflect("tests/configs/simple.json", TestConfig)
        config2 = mirror.reflect("tests/configs/database.json", DatabaseConfig)
        raw1 = mirror.reflect_raw("tests/configs/simple.json")
        raw2 = mirror.reflect_raw("tests/configs/database.json")

        # All should be different objects
        objects = [config1, config2, raw1, raw2]
        unique_ids = {id(obj) for obj in objects}

        self.assertEqual(len(unique_ids), 4, "All cached objects should be unique")

    def test_cached_parameter_is_keyword_only(self):
        """Test that cached parameter must be used as keyword argument."""
        mirror = Mirror("tests.fixtures")

        # This should work (keyword argument)
        mirror.reflect("tests/configs/simple.json", TestConfig, cached=True)

        # This should raise TypeError (positional argument)
        with self.assertRaises(TypeError):
            mirror.reflect("tests/configs/simple.json", TestConfig, True)  # type: ignore

    def test_caching_correctness(self):
        """Test that caching works correctly."""
        mirror = Mirror("tests.fixtures")

        # First call (not cached)
        config1 = mirror.reflect("tests/configs/simple.json", TestConfig)

        # Second call (cached) - should return same object instantly
        config2 = mirror.reflect("tests/configs/simple.json", TestConfig)

        # Cached call should return the exact same object
        self.assertIs(config1, config2, "Cached call should return same object instance")

        # Third call with cached=False should create new object
        config3 = mirror.reflect("tests/configs/simple.json", TestConfig, cached=False)

        # Non-cached call should create different object
        self.assertIsNot(config1, config3, "Non-cached call should create new object")

    def test_cache_survives_state_reset(self):
        """Test that cache survives internal state resets."""
        mirror = Mirror("tests.fixtures")

        # Create cached reflection
        config1 = mirror.reflect("tests/configs/simple.json", TestConfig)

        # Force state reset by calling reflect with different config
        mirror.reflect("tests/configs/database.json", DatabaseConfig, cached=False)

        # Original cached object should still be returned
        config2 = mirror.reflect("tests/configs/simple.json", TestConfig)

        self.assertIs(config1, config2, "Cache should survive internal state resets")


if __name__ == "__main__":
    unittest.main(verbosity=2)
