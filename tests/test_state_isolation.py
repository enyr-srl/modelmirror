"""
Test suite for proper state isolation in ModelMirror.
"""

import inspect
import unittest

from pydantic import BaseModel, ConfigDict

from modelmirror.class_provider.class_scanner import ClassScanner
from modelmirror.mirror import Mirror


class TestService:
    """Test service for state isolation testing."""

    def __init__(self, name: str, value: int = 42):
        self.name = name
        self.value = value


class TestServiceWithComplexDefaults:
    """Service with complex default parameters for testing."""

    def __init__(self, name: str, config: dict | None = None, items: list | None = None):
        self.name = name
        self.config = config or {"default": True}
        self.items = items or ["default_item"]


class TestConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    service: TestService


class TestStateIsolation(unittest.TestCase):
    """Test suite verifying proper state isolation in ModelMirror."""

    def setUp(self):
        """Reset any global state before each test."""
        # Store original __init__ methods to verify modification
        self.original_test_service_init = TestService.__init__
        self.original_complex_service_init = TestServiceWithComplexDefaults.__init__

    def test_class_scanner_preserves_original_classes(self):
        """Test that ClassScanner preserves original class __init__ methods."""
        # Check original state
        original_init = TestService.__init__

        # Create first scanner - this should NOT modify the class with the fix
        scanner1 = ClassScanner("tests.fixtures")
        scanner1.scan()

        # Verify the class was NOT modified
        modified_init = TestService.__init__
        self.assertIs(original_init, modified_init, "ClassScanner should preserve __init__ method")

        # Create second scanner - class should remain unmodified
        scanner2 = ClassScanner("tests.fixtures")
        scanner2.scan()

        # Both scanners should see the same unmodified class
        self.assertIs(TestService.__init__, original_init, "Second scanner should see original class")

    def test_multiple_mirror_instances_share_original_classes(self):
        """Test that multiple Mirror instances share original classes."""
        # Create first Mirror instance
        Mirror("tests.fixtures")

        # Store the unmodified __init__ method
        init_after_mirror1 = TestService.__init__

        # Create second Mirror instance
        Mirror("tests.fixtures")

        # Both mirrors should see the same original class
        self.assertIs(
            TestService.__init__, init_after_mirror1, "Multiple Mirror instances should see original classes"
        )
        self.assertIs(TestService.__init__, self.original_test_service_init, "Classes should remain original")

    def test_pydantic_validation_isolation(self):
        """Test that Pydantic validation is properly isolated."""
        # Create Mirror instance with isolated scanner
        Mirror("tests.fixtures")

        # Try to create TestService with parameters
        # This should work since validation is properly isolated
        try:
            TestService(name="123")
            validation_added = False
        except Exception:
            validation_added = True

        # Create second Mirror instance
        Mirror("tests.fixtures")

        # The validation should be properly isolated
        try:
            TestService(name="123")
            validation_still_present = False
        except Exception:
            validation_still_present = True

        self.assertFalse(validation_added, "Validation should be properly isolated")
        self.assertFalse(validation_still_present, "Validation should remain isolated")

    def test_default_parameter_preservation(self):
        """Test that mutable default parameters are properly preserved."""
        # Create first instance with default parameters
        service1 = TestServiceWithComplexDefaults("test1")

        # Modify the mutable defaults
        service1.config["modified"] = True
        service1.items.append("modified_item")

        # Create Mirror with isolated scanner
        Mirror("tests.fixtures")

        # Create second instance - defaults should be clean
        service2 = TestServiceWithComplexDefaults("test2")

        # Defaults should be preserved (correct Python behavior)
        self.assertEqual(service2.config, {"default": True}, "Default config should be preserved")
        self.assertEqual(service2.items, ["default_item"], "Default items should be preserved")

    def test_registry_isolation_between_mirror_instances(self):
        """Test that Mirror instances have proper isolation."""
        # Create first Mirror
        Mirror("tests.fixtures")

        # Get registered classes from first mirror
        scanner1 = ClassScanner("tests.fixtures")
        classes1 = scanner1.scan()

        # Create second Mirror
        Mirror("tests.fixtures")

        # Get registered classes from second mirror
        scanner2 = ClassScanner("tests.fixtures")
        classes2 = scanner2.scan()

        # Classes should be properly isolated

        # Both should find the same number of classes
        self.assertEqual(len(classes1), len(classes2), "Both scanners should find the same number of classes")

    def test_concurrent_mirror_usage_isolation(self):
        """Test that concurrent Mirror usage is properly isolated."""
        # Create two Mirror instances
        Mirror("tests.fixtures")
        Mirror("tests.fixtures")

        # Both should see original classes
        self.assertIs(
            TestService.__init__, self.original_test_service_init, "Both mirrors should see original classes"
        )

    def test_class_preservation_inspection(self):
        """Test that classes are preserved by ClassScanner."""
        # Get original method signature
        original_signature = inspect.signature(TestService.__init__)

        # Create Mirror with isolated scanner
        Mirror("tests.fixtures")

        # Get signature after Mirror creation
        after_signature = inspect.signature(TestService.__init__)

        # Signatures should be identical
        self.assertEqual(str(original_signature), str(after_signature), "Signatures should be preserved")

        # Check if the method was preserved
        self.assertIs(
            TestService.__init__, self.original_test_service_init, "Class __init__ method should be preserved"
        )

    def test_mirror_reset_mechanism_available(self):
        """Test that Mirror has reset mechanism available."""
        # Create Mirror
        mirror = Mirror("tests.fixtures")

        # Automatic cleanup should be available via ReflectionEngine
        self.assertTrue(hasattr(mirror, "_Mirror__engine"), "Mirror should have ReflectionEngine for state management")

        # Class should remain original
        self.assertIs(TestService.__init__, self.original_test_service_init, "Class should remain original")

    def test_multiple_package_scanning_isolation(self):
        """Test that scanning multiple packages maintains proper isolation."""
        # Create mirrors for same package
        Mirror("tests.fixtures")
        Mirror("tests.fixtures")

        # Both mirrors should see original classes
        self.assertIs(
            TestService.__init__,
            self.original_test_service_init,
            "Classes should remain original after multiple scans",
        )


class TestIsolationVerification(unittest.TestCase):
    """Test cases that verify proper isolation behavior."""

    def test_isolation_successful(self):
        """Test that demonstrates proper isolation is working."""
        original_init = TestService.__init__

        # Create multiple Mirror instances
        mirrors = [Mirror("tests.fixtures") for _ in range(3)]

        # Class should remain unmodified
        self.assertIs(
            TestService.__init__, original_init, "Class should remain unmodified after multiple Mirror instances"
        )

        # Automatic cleanup should be available via ReflectionEngine
        for mirror in mirrors:
            self.assertTrue(
                hasattr(mirror, "_Mirror__engine"), "Mirror should have ReflectionEngine for state management"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
