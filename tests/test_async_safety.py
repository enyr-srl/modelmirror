"""
Test suite for async task safety in ModelMirror.

This test verifies that ModelMirror works correctly with asyncio tasks
and that reflection operations are properly isolated.
"""

import asyncio
import json
import os
import tempfile
import unittest

from modelmirror.mirror import Mirror
from tests.fixtures.test_classes_extended import StatefulService


class TestAsyncSafety(unittest.TestCase):
    """Test suite for async task safety in ModelMirror."""

    def setUp(self):
        """Reset state before each test."""
        StatefulService.reset_class_state()

    def test_concurrent_async_reflections_with_singletons(self):
        """Test concurrent async reflections that use singletons."""

        async def async_reflect_config(task_id: int) -> dict:
            try:
                mirror = Mirror("tests.fixtures")

                # Create config with unique singleton name
                config_data = {
                    "service": {
                        "$mirror": f"stateful_service:async_singleton_{task_id}",
                        "name": f"async_task_{task_id}",
                    }
                }

                # Create temporary config file
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    json.dump(config_data, f)
                    temp_file = f.name

                try:
                    instances = mirror.reflect_raw(temp_file)
                    service = instances.get(StatefulService, f"$async_singleton_{task_id}")

                    return {
                        "task_id": task_id,
                        "service_name": service.name,
                        "service_id": service.instance_id,
                        "service_object_id": id(service),
                        "success": True,
                    }
                finally:
                    os.unlink(temp_file)

            except Exception as e:
                return {"task_id": task_id, "error": str(e), "success": False}

        async def run_concurrent_reflections():
            # Create multiple async tasks
            tasks = [async_reflect_config(i) for i in range(10)]

            # Run all tasks concurrently
            results = await asyncio.gather(*tasks)

            return results

        # Run the async test
        results = asyncio.run(run_concurrent_reflections())

        # Analyze results
        successful_results = [r for r in results if r.get("success", False)]
        failed_results = [r for r in results if not r.get("success", False)]

        # Print any errors for debugging
        if failed_results:
            print(f"Failed results: {failed_results}")

        # All tasks should succeed
        self.assertEqual(len(failed_results), 0, "No errors should occur during concurrent async reflections")
        self.assertEqual(len(successful_results), 10, "All 10 tasks should succeed")

        # Each task should get its own singleton instance (unique names)
        if successful_results:
            # Check that each task got the correct service name
            for result in successful_results:
                expected_name = f"async_task_{result['task_id']}"
                self.assertEqual(
                    result["service_name"], expected_name, f"Task {result['task_id']} should have correct service name"
                )

            # Each task should get its own singleton instance
            singleton_objects = {r["service_object_id"] for r in successful_results}
            self.assertEqual(
                len(singleton_objects),
                len(successful_results),
                "Each async task should get its own singleton instance with unique names",
            )

    def test_mixed_thread_and_async_reflections(self):
        """Test mixing threading and async tasks."""
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = []
        results_lock = threading.Lock()

        def thread_reflect_config(thread_id: int):
            try:
                mirror = Mirror("tests.fixtures")

                config_data = {
                    "service": {
                        "$mirror": f"stateful_service:mixed_singleton_{thread_id}",
                        "name": f"mixed_thread_{thread_id}",
                    }
                }

                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    json.dump(config_data, f)
                    temp_file = f.name

                try:
                    instances = mirror.reflect_raw(temp_file)
                    service = instances.get(StatefulService, f"$mixed_singleton_{thread_id}")

                    with results_lock:
                        results.append(
                            {
                                "id": f"thread_{thread_id}",
                                "service_name": service.name,
                                "service_object_id": id(service),
                                "type": "thread",
                            }
                        )
                finally:
                    os.unlink(temp_file)

            except Exception as e:
                with results_lock:
                    results.append({"id": f"thread_{thread_id}", "error": str(e), "type": "thread"})

        async def async_reflect_config(task_id: int):
            try:
                mirror = Mirror("tests.fixtures")

                config_data = {
                    "service": {
                        "$mirror": f"stateful_service:mixed_async_singleton_{task_id}",
                        "name": f"mixed_async_{task_id}",
                    }
                }

                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    json.dump(config_data, f)
                    temp_file = f.name

                try:
                    instances = mirror.reflect_raw(temp_file)
                    service = instances.get(StatefulService, f"$mixed_async_singleton_{task_id}")

                    with results_lock:
                        results.append(
                            {
                                "id": f"async_{task_id}",
                                "service_name": service.name,
                                "service_object_id": id(service),
                                "type": "async",
                            }
                        )
                finally:
                    os.unlink(temp_file)

            except Exception as e:
                with results_lock:
                    results.append({"id": f"async_{task_id}", "error": str(e), "type": "async"})

        async def run_mixed_test():
            # Start thread pool
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Submit thread tasks
                thread_futures = [executor.submit(thread_reflect_config, i) for i in range(5)]

                # Create async tasks
                async_tasks = [async_reflect_config(i) for i in range(5)]

                # Wait for async tasks
                await asyncio.gather(*async_tasks)

                # Wait for thread tasks
                for future in as_completed(thread_futures):
                    future.result()

        # Run the mixed test
        asyncio.run(run_mixed_test())

        # Analyze results
        successful_results = [r for r in results if "error" not in r]
        failed_results = [r for r in results if "error" in r]

        if failed_results:
            print(f"Failed results: {failed_results}")

        # All operations should succeed
        self.assertEqual(len(failed_results), 0, "No errors should occur in mixed thread/async reflections")
        self.assertEqual(len(successful_results), 10, "All 10 operations should succeed")

        # Check that we have both thread and async results
        thread_results = [r for r in successful_results if r["type"] == "thread"]
        async_results = [r for r in successful_results if r["type"] == "async"]

        self.assertEqual(len(thread_results), 5, "Should have 5 thread results")
        self.assertEqual(len(async_results), 5, "Should have 5 async results")

        # All should have unique singleton instances
        all_object_ids = {r["service_object_id"] for r in successful_results}
        self.assertEqual(
            len(all_object_ids), len(successful_results), "Each operation should get its own singleton instance"
        )

    def test_sequential_async_calls_isolation(self):
        """Test that sequential async calls are properly isolated."""

        async def sequential_reflect_test():
            mirror = Mirror("tests.fixtures")
            results = []

            for i in range(5):
                config_data = {
                    "service": {
                        "$mirror": f"stateful_service:sequential_singleton_{i}",
                        "name": f"sequential_{i}",
                    }
                }

                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    json.dump(config_data, f)
                    temp_file = f.name

                try:
                    instances = mirror.reflect_raw(temp_file)
                    service = instances.get(StatefulService, f"$sequential_singleton_{i}")

                    results.append({"iteration": i, "service_name": service.name, "service_object_id": id(service)})
                finally:
                    os.unlink(temp_file)

            return results

        # Run sequential test
        results = asyncio.run(sequential_reflect_test())

        # Verify results
        self.assertEqual(len(results), 5, "Should have 5 results")

        # Each call should create its own singleton
        object_ids = {r["service_object_id"] for r in results}
        self.assertEqual(len(object_ids), 5, "Each sequential call should create its own singleton")

        # Verify service names
        for i, result in enumerate(results):
            expected_name = f"sequential_{i}"
            self.assertEqual(result["service_name"], expected_name, f"Iteration {i} should have correct service name")


if __name__ == "__main__":
    unittest.main(verbosity=2)
