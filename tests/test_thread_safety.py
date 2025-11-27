"""
Test suite to demonstrate thread safety issues in ModelMirror.

This test shows how concurrent usage of ModelMirror can lead to:
1. Race conditions in class modification
2. Shared state corruption
3. Inconsistent behavior across threads
"""

import unittest
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
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
        
        def create_mirror_and_reflect(thread_id: int):
            try:
                mirror = Mirror('tests.fixtures')
                # Simulate some work
                time.sleep(0.01)  # Small delay to increase chance of race conditions
                
                # Check the state of the class after Mirror creation
                init_method = StatefulService.__init__
                results.append({
                    'thread_id': thread_id,
                    'init_method': init_method,
                    'instance_count': StatefulService.get_instance_count()
                })
            except Exception as e:
                errors.append({'thread_id': thread_id, 'error': str(e)})
        
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
            first_init = results[0]['init_method']
            for result in results[1:]:
                self.assertIs(result['init_method'], first_init,
                             "All threads should see the same class")

    def test_concurrent_reflection_with_shared_singletons(self):
        """Test concurrent reflections that use shared singletons."""
        results = []
        errors = []
        
        def reflect_config(thread_id: int):
            try:
                mirror = Mirror('tests.fixtures')
                
                # Create a simple config that uses singletons with unique names
                config_data = {
                    "service": {
                        "$mirror": f"stateful_service:shared_singleton_{thread_id}",
                        "name": f"thread_{thread_id}"
                    }
                }
                
                # Write temporary config file
                import json
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(config_data, f)
                    temp_file = f.name
                
                try:
                    instances = mirror.reflect_raw(temp_file)
                    service = instances.get(StatefulService, f'$shared_singleton_{thread_id}')
                    
                    results.append({
                        'thread_id': thread_id,
                        'service_name': service.name,
                        'service_id': service.instance_id,
                        'service_object_id': id(service)
                    })
                finally:
                    os.unlink(temp_file)
                    
            except Exception as e:
                errors.append({'thread_id': thread_id, 'error': str(e)})
        
        # Run concurrent reflections
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(reflect_config, i) for i in range(10)]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    errors.append({'error': str(e)})
        
        self.assertEqual(len(errors), 0, "No errors should occur during concurrent reflections")
        
        # Analyze singleton behavior
        if results:
            # Check if singleton names are consistent
            singleton_objects = set(r['service_object_id'] for r in results)
            
            # Each thread should get its own singleton instance (unique names)
            self.assertEqual(len(singleton_objects), len(results), "Each thread should get its own singleton instance with unique names")

    def test_class_modification_thread_safety(self):
        """Test thread safety of class modifications."""
        modification_results = []
        
        def check_class_modification(thread_id: int):
            # Check initial state
            initial_init = ValidationSensitiveService.__init__
            
            # Create Mirror (which modifies classes)
            mirror = Mirror('tests.fixtures')
            
            # Check final state
            final_init = ValidationSensitiveService.__init__
            
            modification_results.append({
                'thread_id': thread_id,
                'initial_init': initial_init,
                'final_init': final_init,
                'was_modified': initial_init is not final_init
            })
        
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
            final_inits = [r['final_init'] for r in modification_results]
            unique_final_inits = set(id(init) for init in final_inits)
            
            self.assertEqual(len(unique_final_inits), 1,
                           "All threads should see the same final class")

    def test_registry_state_consistency_under_concurrency(self):
        """Test registry state consistency under concurrent access."""
        registry_states = []
        
        def capture_registry_state(thread_id: int):
            mirror = Mirror('tests.fixtures')
            
            # Test registry isolation by checking if Mirror works correctly
            try:
                # Simple test to verify registry is working
                config_data = {
                    "service": {
                        "$mirror": "stateful_service",
                        "name": f"registry_test_{thread_id}"
                    }
                }
                
                import json
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(config_data, f)
                    temp_file = f.name
                
                try:
                    instances = mirror.reflect_raw(temp_file)
                    service = instances.get(StatefulService)
                    
                    registry_states.append({
                        'thread_id': thread_id,
                        'registry_working': True,
                        'service_name': service.name if service else None
                    })
                finally:
                    os.unlink(temp_file)
                    
            except Exception as e:
                registry_states.append({
                    'thread_id': thread_id,
                    'registry_working': False,
                    'error': str(e)
                })
        
        # Concurrent registry access
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(capture_registry_state, i) for i in range(6)]
            
            for future in as_completed(futures):
                future.result()
        
        # Check for consistency
        valid_states = [s for s in registry_states if 'registry_working' in s]
        if valid_states:
            working_registries = [s['registry_working'] for s in valid_states]
            all_working = all(working_registries)
            
            self.assertTrue(all_working, "All registries should work correctly under concurrency")

    def test_singleton_lifecycle_thread_safety(self):
        """Test singleton lifecycle thread safety."""
        singleton_lifecycles = []
        
        # Create shared config file once
        config_data = {
            "service": {
                "$mirror": "stateful_service:lifecycle_test",
                "name": "shared_lifecycle_service"
            }
        }
        
        import json
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            shared_temp_file = f.name
        
        def test_singleton_lifecycle(thread_id: int):
            try:
                mirror = Mirror('tests.fixtures')
                
                # Use shared config file
                instances = mirror.reflect_raw(shared_temp_file)
                service = instances.get(StatefulService, '$lifecycle_test')
                
                singleton_lifecycles.append({
                    'thread_id': thread_id,
                    'service_id': service.instance_id if service else None,
                    'service_object_id': id(service) if service else None
                })
                    
            except Exception as e:
                singleton_lifecycles.append({
                    'thread_id': thread_id,
                    'error': str(e)
                })
        
        try:
            # Run concurrent singleton lifecycle tests
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(test_singleton_lifecycle, i) for i in range(5)]
                
                for future in as_completed(futures):
                    future.result()
            
            # Check that all threads got the same singleton
            valid_lifecycles = [s for s in singleton_lifecycles if 'service_object_id' in s]
            if valid_lifecycles:
                object_ids = set(s['service_object_id'] for s in valid_lifecycles)
                self.assertEqual(len(object_ids), 1, "All threads should get the same singleton instance")
        finally:
            # Clean up shared temp file
            os.unlink(shared_temp_file)


if __name__ == '__main__':
    unittest.main(verbosity=2)