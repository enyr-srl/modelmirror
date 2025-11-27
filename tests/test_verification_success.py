"""
Test to verify that ModelMirror proper isolation is working correctly.
"""

import unittest
from modelmirror.mirror import Mirror
from tests.fixtures.test_classes import SimpleService, DatabaseService


class TestIsolationVerification(unittest.TestCase):
    """Test that verifies proper isolation is working correctly."""

    def test_isolation_working_correctly(self):
        """Verify that proper state isolation is working."""
        
        
        # Store original class state
        original_simple_init = SimpleService.__init__
        original_db_init = DatabaseService.__init__
        
        
        # Create Mirror instances
        mirror1 = Mirror('tests.fixtures')
        mirror2 = Mirror('tests.fixtures')
        
        # Check that original classes are unchanged
        current_simple_init = SimpleService.__init__
        current_db_init = DatabaseService.__init__
        
        
        # Verify no global modifications
        classes_unchanged = (
            original_simple_init is current_simple_init and
            original_db_init is current_db_init
        )
        
        
        # Test that original classes still work normally
        try:
            service = SimpleService("test")
            db = DatabaseService("localhost", 5432, "testdb")
            classes_work_normally = True
        except Exception as e:
            classes_work_normally = False
        
        # Check for automatic cleanup mechanism availability
        has_reset = hasattr(mirror1, '_Mirror__reset_state')
                
        # Assertions to verify proper isolation
        self.assertIs(original_simple_init, current_simple_init,
                     "SimpleService should not be modified globally")
        self.assertIs(original_db_init, current_db_init,
                     "DatabaseService should not be modified globally")
        self.assertTrue(classes_work_normally,
                       "Original classes should work normally")
        self.assertTrue(has_reset,
                       "Automatic cleanup mechanism should be available")


if __name__ == '__main__':
    unittest.main(verbosity=2)