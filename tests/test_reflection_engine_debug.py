"""
Debug tests for ReflectionEngine type resolution.
"""

import json
import os
import tempfile
import unittest

from modelmirror.mirror import Mirror
from tests.fixtures.test_classes import SimpleService


class TestReflectionEngineDebug(unittest.TestCase):
    """Debug tests for ReflectionEngine type resolution."""

    def setUp(self):
        """Set up test fixtures."""
        self.mirror = Mirror("tests.fixtures")

    def test_debug_registered_classes_attributes(self):
        """Debug what attributes are available on registered classes."""
        # Access the reflection engine's registered classes
        engine = self.mirror._Mirror__engine
        registered_classes = engine._ReflectionEngine__registered_classes

        simple_service_ref = None
        for ref in registered_classes:
            if ref.id == "simple_service":
                simple_service_ref = ref
                break

        self.assertIsNotNone(simple_service_ref, "SimpleService reference not found")

        # Debug what attributes exist
        print(f"Class reference attributes: {dir(simple_service_ref)}")
        print(f"cls: {simple_service_ref.cls}")
        print(f"cls name: {simple_service_ref.cls.__name__}")

        # Check if original_cls exists
        if hasattr(simple_service_ref, "original_cls"):
            print(f"original_cls: {simple_service_ref.original_cls}")
            print(f"original_cls name: {simple_service_ref.original_cls.__name__}")
        else:
            print("original_cls attribute does not exist")

        # Check what getattr returns
        original_or_cls = getattr(simple_service_ref, "original_cls", simple_service_ref.cls)
        print(f"getattr result: {original_or_cls}")
        print(f"getattr result name: {original_or_cls.__name__}")

        # Compare with actual SimpleService
        print(f"SimpleService: {SimpleService}")
        print(f"Are they equal? {original_or_cls == SimpleService}")
        print(f"Are they the same object? {original_or_cls is SimpleService}")

    def test_debug_type_resolution_flow(self):
        """Debug the type resolution flow step by step."""
        config_data = {
            "service_with_type": {
                "$mirror": "service_with_type_ref",
                "name": "TestService",
                "service_type": "$simple_service$",
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            # Access internal components for debugging
            engine = self.mirror._Mirror__engine

            # Check model link parser
            model_link = engine._ReflectionEngine__model_link_parser.parse("$simple_service$")
            print(f"Parsed model link: {model_link}")
            print(f"Model link type: {model_link.type if model_link else 'None'}")
            print(f"Model link id: {model_link.id if model_link else 'None'}")

            # Test the actual reflection
            instances = self.mirror.reflect_raw(config_path)
            from tests.fixtures.test_classes_with_types import ServiceWithTypeRef

            service = instances.get(ServiceWithTypeRef)
            print(f"Resolved service_type: {service.service_type}")
            print(f"Resolved service_type name: {service.service_type.__name__}")

        finally:
            os.unlink(config_path)

    def test_debug_class_scanner_behavior(self):
        """Debug how class scanner creates isolated classes."""
        from modelmirror.class_provider.class_scanner import ClassScanner

        scanner = ClassScanner("tests.fixtures")
        references = scanner.scan()

        simple_service_ref = None
        for ref in references:
            if ref.id == "simple_service":
                simple_service_ref = ref
                break

        self.assertIsNotNone(simple_service_ref)

        print(f"Scanner created class: {simple_service_ref.cls}")
        print(f"Scanner class name: {simple_service_ref.cls.__name__}")
        print(f"Scanner class module: {simple_service_ref.cls.__module__}")

        # Check all attributes
        for attr in dir(simple_service_ref):
            if not attr.startswith("_"):
                value = getattr(simple_service_ref, attr)
                print(f"{attr}: {value}")


if __name__ == "__main__":
    unittest.main()
