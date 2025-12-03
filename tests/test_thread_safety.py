"""
Test suite to demonstrate thread safety issues in ModelMirror.

This test shows how concurrent usage of ModelMirror can lead to:
1. Race conditions in class modification
2. Shared state corruption
3. Inconsistent behavior across threads
"""

import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel, ConfigDict

from modelmirror.mirror import Mirror
from tests.fixtures.test_classes_extended import StatefulService, ValidationSensitiveService


class ThreadTestConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    stateful_service: StatefulService


class TestThreadSafety(unittest.TestCase):
    """Test suite demonstrating thread safety issues in ModelMirror."""

    def setUp(self):
        """Reset state before each test."""
        StatefulService.reset_class_state()

    def test_concurrent_mirror_creation_race_condition(self):
        """Test race conditions when creating Mirror instances concurrently."""
        results = []
        errors = []
        results_lock = threading.Lock()

        def create_mirror_and_reflect(thread_id: int):
            try:
                Mirror("tests.fixtures")
                # Simulate some work
                time.sleep(0.01)  # Small delay to increase chance of race conditions

                # Check the state of the class after Mirror creation
                init_method = StatefulService.__init__
                with results_lock:
                    results.append(
                        {
                            "thread_id": thread_id,
                            "init_method": init_method,
                            "instance_count": StatefulService.get_instance_count(),
                        }
                    )
            except Exception as e:
                with results_lock:
                    errors.append({"thread_id": thread_id, "error": str(e)})

        # Create multiple threads that create Mirror instances concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_mirror_and_reflect, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Analyze results
        self.assertEqual(len(errors), 0, "No errors should occur during concurrent Mirror creation")

        # Check if all threads see the same class
        if results:
            first_init = results[0]["init_method"]
            for result in results[1:]:
                self.assertIs(result["init_method"], first_init, "All threads should see the same class")

    def test_concurrent_reflection_with_shared_singletons(self):
        """Test concurrent reflections that use shared singletons."""
        results = []
        errors = []
        results_lock = threading.Lock()

        # Create shared config files once
        import json
        import os
        import tempfile

        config_files = []
        for i in range(10):
            config_data = {
                "service": {
                    "$mirror": f"stateful_service:shared_singleton_{i}",
                    "name": f"thread_{i}",
                }
            }
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(config_data, f)
                config_files.append(f.name)

        def reflect_config(thread_id: int):
            try:
                mirror = Mirror("tests.fixtures")
                temp_file = config_files[thread_id]

                instances = mirror.reflect_raw(temp_file)
                service = instances.get(StatefulService, f"$shared_singleton_{thread_id}")

                with results_lock:
                    results.append(
                        {
                            "thread_id": thread_id,
                            "service_name": service.name,
                            "service_id": service.instance_id,
                            "service_object_id": id(service),
                        }
                    )

            except Exception as e:
                with results_lock:
                    errors.append({"thread_id": thread_id, "error": str(e)})

        try:
            # Run concurrent reflections
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(reflect_config, i) for i in range(10)]

                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        with results_lock:
                            errors.append({"error": str(e)})

            if errors:
                print(f"Errors occurred: {errors}")
            self.assertEqual(len(errors), 0, "No errors should occur during concurrent reflections")

            # Analyze singleton behavior
            if results:
                # Check that we got results from all threads
                self.assertEqual(len(results), 10, "Should get results from all 10 threads")

                # Check if singleton names are consistent with thread IDs
                for result in results:
                    expected_name = f"thread_{result['thread_id']}"
                    self.assertEqual(
                        result["service_name"],
                        expected_name,
                        f"Thread {result['thread_id']} should have correct service name",
                    )

                # Each thread should get its own singleton instance (unique names)
                singleton_objects = {r["service_object_id"] for r in results}
                self.assertEqual(
                    len(singleton_objects),
                    len(results),
                    "Each thread should get its own singleton instance with unique names",
                )
        finally:
            # Clean up config files
            for config_file in config_files:
                try:
                    os.unlink(config_file)
                except Exception:
                    pass

    def test_class_modification_thread_safety(self):
        """Test thread safety of class modifications."""
        modification_results = []
        results_lock = threading.Lock()

        def check_class_modification(thread_id: int):
            # Check initial state
            initial_init = ValidationSensitiveService.__init__

            # Create Mirror (which modifies classes)
            Mirror("tests.fixtures")

            # Check final state
            final_init = ValidationSensitiveService.__init__

            with results_lock:
                modification_results.append(
                    {
                        "thread_id": thread_id,
                        "initial_init": initial_init,
                        "final_init": final_init,
                        "was_modified": initial_init is not final_init,
                    }
                )

        # Run concurrent class modifications
        threads = []
        for i in range(5):
            thread = threading.Thread(target=check_class_modification, args=(i,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Check consistency
        if modification_results:
            final_inits = [r["final_init"] for r in modification_results]
            unique_final_inits = {id(init) for init in final_inits}

            self.assertEqual(len(unique_final_inits), 1, "All threads should see the same final class")

    def test_registry_state_consistency_under_concurrency(self):
        """Test registry state consistency under concurrent access."""
        registry_states = []
        results_lock = threading.Lock()

        # Create config files upfront
        import json
        import os
        import tempfile

        config_files = []
        for i in range(6):
            config_data = {"service": {"$mirror": "stateful_service", "name": f"registry_test_{i}"}}
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(config_data, f)
                config_files.append(f.name)

        def capture_registry_state(thread_id: int):
            try:
                mirror = Mirror("tests.fixtures")
                temp_file = config_files[thread_id]

                instances = mirror.reflect_raw(temp_file)
                service = instances.get(StatefulService)

                with results_lock:
                    registry_states.append(
                        {
                            "thread_id": thread_id,
                            "registry_working": True,
                            "service_name": service.name if service else None,
                        }
                    )

            except Exception as e:
                with results_lock:
                    registry_states.append({"thread_id": thread_id, "registry_working": False, "error": str(e)})

        try:
            # Concurrent registry access
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(capture_registry_state, i) for i in range(6)]

                for future in as_completed(futures):
                    future.result()

            # Check for consistency
            valid_states = [s for s in registry_states if "registry_working" in s]
            if valid_states:
                working_registries = [s["registry_working"] for s in valid_states]
                all_working = all(working_registries)

                self.assertTrue(all_working, "All registries should work correctly under concurrency")
        finally:
            # Clean up config files
            for config_file in config_files:
                try:
                    os.unlink(config_file)
                except Exception:
                    pass

    def test_different_parser_instances_create_different_mirrors(self):
        """Test that different parser instances create different Mirror instances."""
        from modelmirror.parser.default_code_link_parser import DefaultCodeLinkParser
        from modelmirror.parser.default_model_link_parser import DefaultModelLinkParser

        # Create different parser instances with different configurations
        parser1 = DefaultCodeLinkParser("$mirror")
        parser2 = DefaultCodeLinkParser("$ref")

        mirror1 = Mirror("tests.fixtures", parser1, DefaultModelLinkParser())
        mirror2 = Mirror("tests.fixtures", parser2, DefaultModelLinkParser())

        # Different parser configurations should create different Mirror instances
        self.assertNotEqual(
            id(mirror1), id(mirror2), "Different parser instances should create different Mirror instances"
        )

    def test_same_parser_instances_create_same_mirror(self):
        """Test that same parser instances create the same Mirror instance in same thread."""
        from modelmirror.parser.default_code_link_parser import DefaultCodeLinkParser
        from modelmirror.parser.default_model_link_parser import DefaultModelLinkParser

        # Create shared parser instances
        shared_code_parser = DefaultCodeLinkParser()
        shared_model_parser = DefaultModelLinkParser()

        # Same parser instances in same thread should create same Mirror
        mirror1 = Mirror("tests.fixtures", shared_code_parser, shared_model_parser)
        mirror2 = Mirror("tests.fixtures", shared_code_parser, shared_model_parser)

        self.assertEqual(
            id(mirror1), id(mirror2), "Same parser instances in same thread should create same Mirror instance"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
