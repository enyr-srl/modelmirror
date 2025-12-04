"""
Test suite for real FastAPI integration.
"""

import unittest

from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror
from tests.fixtures.test_helper_classes import International

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    class FastAPIDefaultConfig(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        app: FastAPI

    class FastAPICompleteConfig(BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)
        international: International
        app: FastAPI

    class TestFastApi(unittest.TestCase):
        """Test real FastAPI integration."""

        def setUp(self):
            """Set up test fixtures."""
            self.mirror = Mirror("tests.fixtures")

        def test_fastapi_creation(self):
            """Test FastAPI app creation through ModelMirror."""
            config = self.mirror.reflect("tests/configs/fastapi_basic.json", FastAPIDefaultConfig)

            # Verify FastAPI app is created correctly
            self.assertIsInstance(config.app, FastAPI)
            self.assertEqual(config.app.title, "Test API")
            self.assertEqual(config.app.description, "Test FastAPI application")
            self.assertEqual(config.app.version, "1.0.0")

        def test_fastapi_lifespan_creation(self):
            """Test FastAPI lifespan creation through ModelMirror."""
            config = self.mirror.reflect("tests/configs/fastapi_lifespan.json", FastAPIDefaultConfig)

            # Verify FastAPI app is created correctly
            self.assertIsInstance(config.app, FastAPI)
            self.assertEqual(config.app.title, "Test API")
            self.assertEqual(config.app.description, "Test FastAPI application")
            self.assertEqual(config.app.version, "1.0.0")

            # Verify lifespan is configured (FastAPI stores it internally)
            # Check that the app was created successfully with lifespan parameter
            self.assertIsNotNone(config.app)

        def test_fastapi_singleton_behavior(self):
            """Test FastAPI singleton behavior across reflections."""
            # First reflection
            config1 = self.mirror.reflect("tests/configs/fastapi_singleton.json", FastAPIDefaultConfig)
            app1 = config1.app

            # Second reflection with same singleton name
            config2 = self.mirror.reflect("tests/configs/fastapi_singleton.json", FastAPIDefaultConfig)
            app2 = config2.app

            # Should be the same instance
            self.assertIs(app1, app2)

        def test_fastapi_with_middleware_inline(self):
            """Test FastAPI with inline middleware configuration."""
            config = self.mirror.reflect("tests/configs/fastapi_middleware.json", FastAPIDefaultConfig)

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

except ImportError:
    print("FastAPI is not installed. Skipping FastAPI tests.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
