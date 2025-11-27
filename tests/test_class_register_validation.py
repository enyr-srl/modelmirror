"""
Tests for ClassRegister validation behavior when no reference is provided.
"""

import unittest

from modelmirror.class_provider.class_reference import ClassReference
from modelmirror.class_provider.class_register import ClassRegister
from tests.fixtures.test_classes import SimpleService


class TestClassRegisterValidation(unittest.TestCase):
    """Test ClassRegister validation behavior."""

    def test_class_register_without_reference_attribute(self):
        """Test that ClassRegister raises ValueError when no reference attribute is provided."""
        with self.assertRaisesRegex(ValueError, "ClassRegister reference must be provided for class"):

            class InvalidRegister(ClassRegister):
                pass

    def test_class_register_with_none_reference(self):
        """Test that ClassRegister raises ValueError when reference attribute is None."""
        with self.assertRaisesRegex(ValueError, "ClassRegister reference must be provided for class"):

            class InvalidRegister(ClassRegister):
                reference = None  # type: ignore

    def test_class_register_with_valid_reference(self):
        """Test that ClassRegister works correctly when valid reference is provided."""

        # This should not raise any exception
        class ValidRegister(ClassRegister):
            reference = ClassReference(id="test_service", cls=SimpleService)

        # Verify the register was created successfully
        self.assertEqual(ValidRegister.reference.id, "test_service")
        self.assertEqual(ValidRegister.reference.cls, SimpleService)


if __name__ == "__main__":
    unittest.main()
