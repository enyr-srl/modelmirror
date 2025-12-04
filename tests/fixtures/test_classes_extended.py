"""
Additional test classes for testing state isolation and proper behavior.
"""

from typing import Dict, List


class TestService:
    """Service for testing state isolation."""

    def __init__(self, name: str, value: int = 42):
        self.name = name
        self.value = value

    def get_info(self) -> str:
        return f"{self.name}: {self.value}"


class MutableDefaultService:
    """Service with mutable default parameters to test corruption."""

    def __init__(self, name: str, config: Dict[str, str] | None = None, items: List[str] | None = None):
        self.name = name
        self.config = config or {"default": "value"}
        self.items = items or ["default"]

    def add_config(self, key: str, value: str):
        self.config[key] = value

    def add_item(self, item: str):
        self.items.append(item)


class StatefulService:
    """Service that maintains internal state to test isolation."""

    _instance_count = 0
    _shared_data: Dict[str, str] = {}

    def __init__(self, name: str):
        StatefulService._instance_count += 1
        self.name = name
        self.instance_id = StatefulService._instance_count

    @classmethod
    def get_instance_count(cls) -> int:
        return cls._instance_count

    @classmethod
    def get_shared_data(cls) -> Dict:
        return cls._shared_data

    @classmethod
    def reset_class_state(cls):
        cls._instance_count = 0
        cls._shared_data.clear()


class ValidationSensitiveService:
    """Service that behaves differently with/without Pydantic validation."""

    def __init__(self, name: str, port: int):
        # This will behave differently if Pydantic validation is added
        self.name = name
        self.port = port

        # Store whether validation was applied
        self.validation_applied = hasattr(type(self).__init__, "__wrapped__")

    def is_validated(self) -> bool:
        return self.validation_applied
