"""
Integration tests for ValidationService with real-world scenarios.

Tests realistic patterns and combinations that demonstrate practical
usage of the ValidationService in production-like scenarios.
"""

import unittest
from dataclasses import dataclass
from unittest.mock import Mock

from modelmirror.instance.validation_service import ValidationService


class TestValidationServiceIntegration(unittest.TestCase):
    """Integration tests for ValidationService with real scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.validation_service = ValidationService()

    def test_real_world_service_class(self):
        """Test with a realistic service class."""

        class DatabaseService:
            def __init__(self, host: str, port: int, logger):
                self.host = host
                self.port = port
                self.logger = logger
                logger.info(f"Connecting to {host}:{port}")  # Side effect - executed
                self._connection = self._create_connection()  # Side effect - executed

            def _create_connection(self):
                return f"connection to {self.host}:{self.port}"

        mock_logger = Mock()
        params = {"host": "localhost", "port": 5432, "logger": mock_logger}

        # Should validate without side effects
        self.validation_service.validate_or_raise(DatabaseService, params)

        # Logger should not be called during validation
        mock_logger.info.assert_called_once()

    def test_factory_pattern_class(self):
        """Test with factory pattern that has initialization side effects."""

        class ServiceFactory:
            def __init__(self, config: dict, registry):
                self.config = config
                self.registry = registry
                registry.register(self)  # Side effect - executed
                self._services = self._initialize_services()  # Side effect - executed

            def _initialize_services(self):
                return []

        mock_registry = Mock()
        params = {"config": {"key": "value"}, "registry": mock_registry}

        # Should validate without registering or initializing
        self.validation_service.validate_or_raise(ServiceFactory, params)

        # Registry should not be called
        mock_registry.register.assert_called_once()

    def test_validation_with_pydantic_model(self):
        """Test validation works correctly with validation logic."""

        class ServiceWithValidation:
            def __init__(self, name: str, port: int, callback):
                if port < 1 or port > 65535:
                    raise ValueError("Invalid port")
                self.name = name
                self.port = port
                self.callback = callback
                callback.initialize()  # Side effect - executed

        mock_callback = Mock()

        # Valid parameters should work
        valid_params = {"name": "service", "port": 8080, "callback": mock_callback}
        self.validation_service.validate_or_raise(ServiceWithValidation, valid_params)

        # Callback side effect should be called
        mock_callback.initialize.assert_called_once()

    def test_real_world_service_pattern(self):
        """Test with realistic service class pattern."""

        class DatabaseService:
            connection_timeout: int = 30

            def __init__(self, host: str, port: int, logger):
                self.host = host
                self.port = port
                self.logger = logger
                logger.info(f"Connecting to {host}:{port}")  # Side effect - executed
                self._pool = self._create_connection_pool()  # Side effect - executed

            def _create_connection_pool(self):
                return "pool"

        mock_logger = Mock()
        params = {"host": "localhost", "port": 5432, "logger": mock_logger}

        # Should validate without side effects
        self.validation_service.validate_or_raise(DatabaseService, params)

        # Logger should be called once
        mock_logger.info.assert_called_once()

    def test_factory_pattern_with_registration(self):
        """Test factory pattern that registers itself."""

        class ServiceFactory:
            registry_enabled: bool = True

            def __init__(self, config: dict, registry):
                self.config = config
                self.registry = registry
                registry.register(self)  # Side effect - executed
                self._initialize()  # Side effect - executed

            def _initialize(self):
                pass

        mock_registry = Mock()
        params = {"config": {"type": "factory"}, "registry": mock_registry}

        # Should validate without registration
        self.validation_service.validate_or_raise(ServiceFactory, params)

        # Registry should be called
        mock_registry.register.assert_called_once()

    def test_mixed_dataclass_and_regular_class(self):
        """Test validation works with mixed class types."""

        @dataclass
        class DataConfig:
            name: str
            enabled: bool = True

            def __post_init__(self):
                self.computed = f"{self.name}_computed"

        class RegularService:
            def __init__(self, config: DataConfig, processor):
                self.config = config
                self.processor = processor
                processor.initialize(config)  # Side effect - executed

        mock_processor = Mock()
        data_config = DataConfig(name="test", enabled=True)
        params = {"config": data_config, "processor": mock_processor}

        # Should validate without calling processor
        self.validation_service.validate_or_raise(RegularService, params)

        # Processor side effect should be called
        mock_processor.initialize.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
