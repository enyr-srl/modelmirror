"""
Test factory classes for testing type instantiation.
"""

from typing import Optional, Type


class ServiceFactory:
    """Factory that creates services based on type references."""

    def __init__(self, name: str, creates_type: Type, related_factory: Optional[object] = None):
        self.name = name
        self.creates_type = creates_type
        self.related_factory = related_factory

    def create_service(self, *args, **kwargs):
        """Create an instance of the service class."""
        if self.creates_type:
            return self.creates_type(*args, **kwargs)
        return None


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
