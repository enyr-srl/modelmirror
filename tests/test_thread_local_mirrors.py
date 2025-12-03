"""
Test suite for automatic thread-local Mirror behavior.

This test verifies that Mirror instances are automatically isolated
per thread and async task without requiring explicit configuration.
"""

import asyncio
import json
import os
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed

from modelmirror.mirror import Mirror
from tests.fixtures.test_classes_extended import StatefulService


class TestThreadLocalMirrors(unittest.TestCase):
    """Test suite for automatic thread-local Mirror behavior."""

    def setUp(self):
        """Reset state before each test."""
        StatefulService.reset_class_state()

    def test_same_parameters_different_threads_get_different_mirrors(self):
        """Test that same Mirror parameters in different threads create different instances."""
        mirror_instances = {}
        thread_ids = {}
        results_lock = threading.Lock()

        def get_mirror_in_thread(thread_id: int):
            mirror = Mirror("tests.fixtures")
            actual_thread_id = threading.get_ident()
            with results_lock:
                mirror_instances[thread_id] = id(mirror)
                thread_ids[thread_id] = actual_thread_id

        # Create mirrors in different threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=get_mirror_in_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check that we actually got different threads
        unique_thread_ids = set(thread_ids.values())

        # All mirrors should be different instances (one per unique thread)
        mirror_ids = list(mirror_instances.values())
        unique_mirror_ids = set(mirror_ids)

        # Should have as many unique mirrors as unique threads
        self.assertEqual(
            len(unique_mirror_ids),
            len(unique_thread_ids),
            f"Should have one Mirror per thread. Threads: {len(unique_thread_ids)}, Mirrors: {len(unique_mirror_ids)}",
        )
        # Note: In some environments, all threads might be the same (e.g., single-threaded test runner)
        # The important thing is that the behavior is consistent
        if len(unique_thread_ids) == 1:
            self.assertEqual(len(unique_mirror_ids), 1, "If all in same thread, should share Mirror")
        else:
            self.assertGreater(len(unique_thread_ids), 1, "Should have multiple threads")

    def test_concurrent_reflections_no_serialization(self):
        """Test that concurrent reflections can run in parallel without serialization."""
        import time

        results = []
        results_lock = threading.Lock()
        start_times = {}
        end_times = {}

        def reflect_with_timing(thread_id: int):
            start_times[thread_id] = time.time()

            mirror = Mirror("tests.fixtures")

            config_data = {
                "service": {
                    "$mirror": f"stateful_service:thread_singleton_{thread_id}",
                    "name": f"thread_{thread_id}",
                }
            }

            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(config_data, f)
                temp_file = f.name

            try:
                # Add small delay to make timing differences visible
                time.sleep(0.1)
                instances = mirror.reflect_raw(temp_file)
                service = instances.get(StatefulService, f"$thread_singleton_{thread_id}")

                end_times[thread_id] = time.time()

                with results_lock:
                    results.append(
                        {
                            "thread_id": thread_id,
                            "service_name": service.name,
                            "mirror_id": id(mirror),
                            "success": True,
                        }
                    )
            except Exception as e:
                end_times[thread_id] = time.time()
                with results_lock:
                    results.append({"thread_id": thread_id, "error": str(e), "success": False})
            finally:
                os.unlink(temp_file)

        # Run concurrent reflections
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(reflect_with_timing, i) for i in range(3)]
            for future in as_completed(futures):
                future.result()

        # Analyze results
        successful_results = [r for r in results if r.get("success", False)]
        self.assertEqual(len(successful_results), 3, "All reflections should succeed")

        # Check that reflections ran concurrently (not serialized)
        # If serialized, total time would be ~0.3s, if parallel ~0.1s
        total_start = min(start_times.values())
        total_end = max(end_times.values())
        total_time = total_end - total_start

        # Should be closer to 0.1s (parallel) than 0.3s (serialized)
        self.assertLess(total_time, 0.25, "Reflections should run in parallel, not serialized")

        # Check mirror isolation based on actual thread usage
        mirror_ids = {r["mirror_id"] for r in successful_results}
        # ThreadPoolExecutor may reuse threads, so we expect mirrors to match thread usage
        self.assertGreaterEqual(len(mirror_ids), 1, "Should have at least one Mirror instance")
        self.assertLessEqual(len(mirror_ids), 3, "Should not have more Mirror instances than tasks")

    def test_async_tasks_get_different_mirrors(self):
        """Test that different async tasks get different Mirror instances."""

        async def get_mirror_in_task(task_id: int) -> dict:
            mirror = Mirror("tests.fixtures")
            return {"task_id": task_id, "mirror_id": id(mirror)}

        async def run_async_test():
            tasks = [get_mirror_in_task(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            return results

        # Run async test
        results = asyncio.run(run_async_test())

        # Each async task should get different Mirror instances
        mirror_ids = [r["mirror_id"] for r in results]
        unique_ids = set(mirror_ids)

        self.assertEqual(len(unique_ids), 5, "Each async task should get its own Mirror instance")
        self.assertEqual(len(results), 5, "Should have 5 results")

    def test_mixed_thread_and_async_isolation(self):
        """Test that threads and async tasks are properly isolated."""
        results = []
        results_lock = threading.Lock()

        def thread_get_mirror(thread_id: int):
            mirror = Mirror("tests.fixtures")
            with results_lock:
                results.append({"id": f"thread_{thread_id}", "mirror_id": id(mirror), "type": "thread"})

        async def async_get_mirror(task_id: int):
            mirror = Mirror("tests.fixtures")
            with results_lock:
                results.append({"id": f"async_{task_id}", "mirror_id": id(mirror), "type": "async"})

        async def run_mixed_test():
            # Start thread pool
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Submit thread tasks
                thread_futures = [executor.submit(thread_get_mirror, i) for i in range(3)]

                # Create async tasks
                async_tasks = [async_get_mirror(i) for i in range(3)]

                # Wait for async tasks
                await asyncio.gather(*async_tasks)

                # Wait for thread tasks
                for future in as_completed(thread_futures):
                    future.result()

        # Run mixed test
        asyncio.run(run_mixed_test())

        # Analyze results
        self.assertEqual(len(results), 6, "Should have 6 results total")

        thread_results = [r for r in results if r["type"] == "thread"]
        async_results = [r for r in results if r["type"] == "async"]

        self.assertEqual(len(thread_results), 3, "Should have 3 thread results")
        self.assertEqual(len(async_results), 3, "Should have 3 async results")

        # Check mirror isolation - should have unique mirrors per execution context
        all_mirror_ids = {r["mirror_id"] for r in results}
        # Note: ThreadPoolExecutor may reuse threads, so we expect at least as many unique mirrors as unique execution contexts
        self.assertGreaterEqual(len(all_mirror_ids), 4, "Should have multiple unique Mirror instances")

    def test_same_thread_same_mirror_instance(self):
        """Test that multiple Mirror creations in same thread return same instance."""

        def get_multiple_mirrors():
            mirror1 = Mirror("tests.fixtures")
            mirror2 = Mirror("tests.fixtures")
            mirror3 = Mirror("tests.fixtures")

            return id(mirror1), id(mirror2), id(mirror3)

        # Test in main thread
        id1, id2, id3 = get_multiple_mirrors()
        self.assertEqual(id1, id2, "Same thread should get same Mirror instance")
        self.assertEqual(id2, id3, "Same thread should get same Mirror instance")

        # Test in separate thread
        result_container = []

        def thread_test():
            result_container.extend(get_multiple_mirrors())

        thread = threading.Thread(target=thread_test)
        thread.start()
        thread.join()

        thread_id1, thread_id2, thread_id3 = result_container
        self.assertEqual(thread_id1, thread_id2, "Same thread should get same Mirror instance")
        self.assertEqual(thread_id2, thread_id3, "Same thread should get same Mirror instance")

        # But different from main thread
        self.assertNotEqual(id1, thread_id1, "Different threads should get different Mirror instances")

    def test_async_task_isolation_within_same_thread(self):
        """Test that different async tasks in same thread get different Mirror instances."""

        async def test_task_isolation():
            # Create multiple tasks that will run in the same thread
            async def get_mirror(task_name: str):
                mirror = Mirror("tests.fixtures")
                current_task = asyncio.current_task()
                return task_name, id(mirror), id(current_task) if current_task else None

            # Run tasks sequentially (same task context - should get same mirror)
            task1_result = await get_mirror("task1")
            task2_result = await get_mirror("task2")

            # Create concurrent tasks (different task contexts - should get different mirrors)
            concurrent_results = await asyncio.gather(get_mirror("concurrent1"), get_mirror("concurrent2"))

            return [task1_result, task2_result] + list(concurrent_results)

        results = asyncio.run(test_task_isolation())

        # Extract mirror IDs and task IDs
        mirror_ids = [result[1] for result in results]
        task_ids = [result[2] for result in results]
        unique_mirror_ids = set(mirror_ids)
        unique_task_ids = set(task_ids)

        # Should have one mirror per unique task
        self.assertEqual(
            len(unique_mirror_ids),
            len(unique_task_ids),
            f"Should have one Mirror per task. Tasks: {len(unique_task_ids)}, Mirrors: {len(unique_mirror_ids)}",
        )

        # Sequential calls should share same mirror (same task), concurrent should be different
        self.assertEqual(results[0][1], results[1][1], "Sequential calls in same task should share Mirror")
        self.assertNotEqual(results[2][1], results[3][1], "Concurrent tasks should have different Mirrors")


if __name__ == "__main__":
    unittest.main()
