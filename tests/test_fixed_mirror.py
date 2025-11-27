import unittest

from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror
from tests.fixtures.test_classes import DatabaseService, SimpleService


class SimpleConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    service: SimpleService


class TestFixedMirror(unittest.TestCase):
    """Test that the fixed Mirror doesn't pollute the global state"""

    def test_no_global_class_modification(self):
        """Test that original classes are not modified globally."""
        # Store original class
        original_init = SimpleService.__init__

        # Create fixed Mirror
        Mirror("tests.fixtures")

        # Original class should remain unchanged
        self.assertIs(SimpleService.__init__, original_init, "Original class should not be modified")
        self.assertFalse(
            hasattr(SimpleService.__init__, "__wrapped__"), "Original class should not have Pydantic wrapper"
        )

    def test_multiple_mirrors_are_isolated(self):
        """Test that multiple Mirror instances are properly isolated."""
        # Create multiple mirrors
        mirror1 = Mirror("tests.fixtures")
        mirror2 = Mirror("tests.fixtures")

        # Both should work independently without affecting each other
        config1 = mirror1.reflect("tests/configs/state_test_1.json", SimpleConfig)
        config2 = mirror2.reflect("tests/configs/state_test_2.json", SimpleConfig)

        self.assertEqual(config1.service.name, "first_service")
        self.assertEqual(config2.service.name, "second_service")
        self.assertIsNot(config1.service, config2.service)

    def test_automatic_reset_functionality(self):
        """Test that automatic reset properly clears state between reflections."""
        mirror = Mirror("tests.fixtures")

        # Load first config
        config1 = mirror.reflect("tests/configs/state_test_1.json", SimpleConfig)

        # Load different config (automatic reset happens)
        config2 = mirror.reflect("tests/configs/state_test_2.json", SimpleConfig)

        self.assertIsNot(config1.service, config2.service)

    def test_original_classes_still_work(self):
        """Test that original classes still work normally after Mirror usage."""
        # Create Mirror
        mirror = Mirror("tests.fixtures")
        mirror.reflect("tests/configs/state_test_1.json", SimpleConfig)

        # Original classes should still work normally
        service = SimpleService("test")
        self.assertEqual(service.name, "test")

        # Should accept any valid parameters (no global validation)
        db = DatabaseService("localhost", 5432, "testdb")
        self.assertEqual(db.host, "localhost")

    def test_no_multiple_wrapper_layers(self):
        """Test that multiple Mirror instances don't create wrapper layers."""
        original_init = SimpleService.__init__

        # Create multiple mirrors
        for _ in range(5):
            mirror = Mirror("tests.fixtures")
            mirror.reflect("tests/configs/state_test_1.json", SimpleConfig)

        # Original class should be unchanged
        self.assertIs(
            SimpleService.__init__, original_init, "Original class should remain unchanged after multiple mirrors"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
