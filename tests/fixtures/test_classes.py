"""
Test classes for ModelMirror JSON configuration testing.
These classes represent various service patterns commonly used in applications.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SimpleService:
    """Basic service with single parameter."""

    def __init__(self, name: str):
        self.name = name

    def get_name(self) -> str:
        return self.name


class DatabaseService:
    """Database service with multiple configuration parameters."""

    def __init__(self, host: str, port: int, database_name: str):
        self.host = host
        self.port = port
        self.database_name = database_name

    def connect(self) -> str:
        return f"Connected to {self.database_name} at {self.host}:{self.port}"


class UserService:
    """Service that depends on another service (DatabaseService)."""

    def __init__(self, database: DatabaseService, cache_enabled: bool = True):
        self.database = database
        self.cache_enabled = cache_enabled

    def get_user(self, user_id: int) -> str:
        connection = self.database.connect()
        return f"User {user_id} from {connection} (cache: {self.cache_enabled})"


class ConfigurableService(BaseModel):
    """Pydantic-based service for validation testing."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    service: SimpleService
    timeout: int = Field(ge=1, le=300)
    retries: int = Field(ge=0, le=10)


class ComplexService:
    """Service with multiple dependencies and nested structures."""

    def __init__(self, database: DatabaseService, user_service: UserService, config: Dict[str, str]):
        self.database = database
        self.user_service = user_service
        self.config = config

    def process(self) -> str:
        return f"Processing with {self.database.connect()}"


class ServiceWithDefaults:
    """Service that has default parameter values."""

    def __init__(self, name: str, timeout: int = 30, retries: int = 3):
        self.name = name
        self.timeout = timeout
        self.retries = retries


class ServiceWithOptionals:
    """Service with optional parameters."""

    def __init__(self, name: str, optional_param: Optional[str] = None):
        self.name = name
        self.optional_param = optional_param


class ListService:
    """Service that takes a list of other services."""

    def __init__(self, name: str, services: List[SimpleService]):
        self.name = name
        self.services = services

    def get_service_count(self) -> int:
        return len(self.services)


class DictService:
    """Service that takes a dictionary of other services."""

    def __init__(self, name: str, service_map: Dict[str, SimpleService]):
        self.name = name
        self.service_map = service_map

    def get_service(self, key: str) -> Optional[SimpleService]:
        return self.service_map.get(key)


class NestedService:
    """Service with deeply nested dependencies."""

    def __init__(self, outer_service: ComplexService, metadata: Dict[str, Any]):
        self.outer_service = outer_service
        self.metadata = metadata


class ValidationService(BaseModel):
    """Service with strict validation rules."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    name: str = Field(min_length=1, max_length=50)
    port: int = Field(ge=1, le=65535)
    enabled: bool = True
