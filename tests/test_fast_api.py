"""
Test suite for real FastAPI integration.
"""

import json
import os
import tempfile
import unittest

from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    class FastAPIConfig(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        app: FastAPI

    class TestFastApi(unittest.TestCase):
        """Test real FastAPI integration."""

        def setUp(self):
            """Set up test fixtures."""
            self.mirror = Mirror("tests.fixtures")

        def test_fastapi_app_creation(self):
            """Test FastAPI app creation through ModelMirror."""
            config_data = {
                "app": {
                    "$mirror": "fastapi_app",
                    "title": "Test API",
                    "description": "Test FastAPI application",
                    "version": "1.0.0",
                }
            }

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(config_data, f)
                config_path = f.name

            try:
                config = self.mirror.reflect(config_path, FastAPIConfig)

                # Verify FastAPI app is created correctly
                self.assertIsInstance(config.app, FastAPI)
                self.assertEqual(config.app.title, "Test API")
                self.assertEqual(config.app.description, "Test FastAPI application")
                self.assertEqual(config.app.version, "1.0.0")

            finally:
                os.unlink(config_path)

        def test_fastapi_singleton_behavior(self):
            """Test FastAPI singleton behavior across reflections."""
            config_data = {"app": {"$mirror": "fastapi_app:main_app", "title": "Singleton API", "version": "2.0.0"}}

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(config_data, f)
                config_path = f.name

            try:
                # First reflection
                config1 = self.mirror.reflect(config_path, FastAPIConfig)
                app1 = config1.app

                # Second reflection with same singleton name
                config2 = self.mirror.reflect(config_path, FastAPIConfig)
                app2 = config2.app

                # Should be the same instance
                self.assertIs(app1, app2)

            finally:
                os.unlink(config_path)

        def test_fastapi_with_middleware_inline(self):
            """Test FastAPI with inline middleware configuration."""
            config_data = {"app": {"$mirror": "fastapi_app", "title": "API with Middleware"}}

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(config_data, f)
                config_path = f.name

            try:
                config = self.mirror.reflect(config_path, FastAPIConfig)

                # Add middleware after creation (only if CORSMiddleware is available)
                if CORSMiddleware is not None:
                    config.app.add_middleware(
                        CORSMiddleware,
                        allow_origins=["*"],
                        allow_credentials=True,
                        allow_methods=["*"],
                        allow_headers=["*"],
                    )

                    # Verify middleware is added
                    self.assertTrue(len(config.app.user_middleware) > 0)

            finally:
                os.unlink(config_path)

except ImportError:
    print("FastAPI is not installed. Skipping FastAPI tests.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
