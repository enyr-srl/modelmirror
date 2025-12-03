"""
Test factory classes for testing type instantiation.
"""

from typing import Optional, Type


class ServiceFactory:
    """Factory that creates services based on type references."""

    def __init__(self, service_class: Type, dependency_service: Optional[object] = None):
        self.service_class = service_class
        self.dependency_service = dependency_service

    def create_service(self, *args, **kwargs):
        """Create an instance of the service class."""
        return self.service_class(*args, **kwargs)


class DependentService:
    """Service that depends on other services."""

    def __init__(self, name: str, dependency: Optional[object] = None):
        self.name = name
        self.dependency = dependency


class CircularDependentService:
    """Service for testing circular dependencies with types."""

    def __init__(self, name: str, circular_type: Optional[Type] = None):
        self.name = name
        self.circular_type = circular_type
