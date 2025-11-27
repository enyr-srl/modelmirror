"""
Test suite for class isolation and proper scanning behavior.
"""

import inspect
import unittest

from modelmirror.class_provider.class_scanner import ClassScanner
from modelmirror.mirror import Mirror
from tests.fixtures.test_classes import SimpleService


class TestClassIsolation(unittest.TestCase):
    """Test verifying proper class isolation and scanning behavior."""

    def setUp(self):
        """Store original class state."""
        self.original_init = SimpleService.__init__
        self.original_signature = str(inspect.signature(self.original_init))

    def test_class_scanner_preserves_original_classes(self):
        """Test that ClassScanner preserves original class definitions."""

        # Create ClassScanner and scan
        scanner = ClassScanner("tests.fixtures")
        scanner.scan()

        # Check if class was modified
        modified_init = SimpleService.__init__

        # Classes should NOT be modified globally
        is_modified = (self.original_init is not modified_init) or hasattr(modified_init, "__wrapped__")

        self.assertFalse(is_modified, "ClassScanner should preserve original classes")

    def test_multiple_scanners_see_same_original_class(self):
        """Test that multiple scanners see the same original class."""
        # First scanner
        scanner1 = ClassScanner("tests.fixtures")
        scanner1.scan()
        init_after_scanner1 = SimpleService.__init__

        # Second scanner
        scanner2 = ClassScanner("tests.fixtures")
        scanner2.scan()
        init_after_scanner2 = SimpleService.__init__

        # Scanners should see the same unmodified class
        self.assertIs(init_after_scanner1, init_after_scanner2, "Multiple scanners should see the same original class")

    def test_mirror_instances_share_original_classes(self):
        """Test that multiple Mirror instances share original classes."""
        # Create first Mirror
        Mirror("tests.fixtures")
        init_after_mirror1 = SimpleService.__init__

        # Create second Mirror
        Mirror("tests.fixtures")
        init_after_mirror2 = SimpleService.__init__

        # Mirrors should see the same unmodified class
        self.assertIs(
            init_after_mirror1, init_after_mirror2, "Multiple Mirror instances should see the same original class"
        )

    def test_pydantic_validation_isolation(self):
        """Test that Pydantic validation is properly isolated."""
        # Create Mirror with isolated scanner
        Mirror("tests.fixtures")

        # Try to create instance with parameters
        validation_error_occurred = False
        try:
            # This should work since validation is properly isolated
            SimpleService(name="123")
        except Exception:
            validation_error_occurred = True

        # Validation should be properly isolated
        self.assertFalse(validation_error_occurred, "Validation should be properly isolated")

    def test_class_preservation_across_instances(self):
        """Test that class definitions are preserved across instance creation."""
        # Create instance before Mirror
        SimpleService("before_mirror")

        # Create Mirror with isolated scanner
        Mirror("tests.fixtures")

        # Create instance after Mirror
        SimpleService("after_mirror")

        # The class should be preserved
        current_init = SimpleService.__init__
        is_modified = (self.original_init is not current_init) or hasattr(current_init, "__wrapped__")

        self.assertFalse(is_modified, "Class should be preserved")

    def test_cleanup_mechanism_available(self):
        """Test that automatic cleanup mechanism works correctly."""
        # Store original state
        original_init = SimpleService.__init__

        # Create Mirror with isolated scanner
        mirror = Mirror("tests.fixtures")

        # Class should be preserved
        modified_init = SimpleService.__init__
        is_modified = original_init is not modified_init

        # Check for ReflectionEngine (automatic cleanup)
        has_private_reset = hasattr(mirror, "_Mirror__engine")

        self.assertFalse(is_modified, "Class should be preserved")
        self.assertTrue(has_private_reset, "Automatic cleanup mechanism should be available")


if __name__ == "__main__":
    unittest.main(verbosity=2)
