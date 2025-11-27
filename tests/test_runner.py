"""
Comprehensive test runner for ModelMirror JSON configuration tests.

This module runs all test suites and provides a summary of results.
"""

import sys
import unittest
from io import StringIO


def run_all_tests():
    """Run all test suites and return results."""

    # Import all test modules
    from tests.test_comprehensive_integration import TestComprehensiveIntegration
    from tests.test_json_configurations import TestJSONConfigurations
    from tests.test_json_edge_cases import TestJSONEdgeCases
    from tests.test_json_validation import TestJSONValidation

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestJSONConfigurations))
    suite.addTests(loader.loadTestsFromTestCase(TestJSONEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestJSONValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestComprehensiveIntegration))

    # Run tests with detailed output
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2, buffer=True)

    result = runner.run(suite)

    # Print results
    output = stream.getvalue()
    print(output)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  - {test}")

    success_rate = (
        ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        if result.testsRun > 0
        else 0
    )
    print(f"\nSuccess rate: {success_rate:.1f}%")

    return result.wasSuccessful()


def run_specific_suite(suite_name):
    """Run a specific test suite."""

    suite_map = {
        "configurations": "tests.test_json_configurations.TestJSONConfigurations",
        "edge_cases": "tests.test_json_edge_cases.TestJSONEdgeCases",
        "validation": "tests.test_json_validation.TestJSONValidation",
        "integration": "tests.test_comprehensive_integration.TestComprehensiveIntegration",
    }

    if suite_name not in suite_map:
        print(f"Unknown test suite: {suite_name}")
        print(f"Available suites: {', '.join(suite_map.keys())}")
        return False

    # Import and run specific suite
    module_path = suite_map[suite_name]
    parts = module_path.split(".")
    module_name = ".".join(parts[:-1])
    class_name = parts[-1]

    module = __import__(module_name, fromlist=[class_name])
    test_class = getattr(module, class_name)

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(test_class)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        suite_name = sys.argv[1]
        success = run_specific_suite(suite_name)
    else:
        success = run_all_tests()

    sys.exit(0 if success else 1)
