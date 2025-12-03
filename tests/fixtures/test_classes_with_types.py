"""
Test classes that accept Type parameters for testing type references.
"""

from typing import Optional, Type


class ServiceWithTypeRef:
    """Service that accepts a type reference as a parameter."""

    def __init__(self, name: str, service_type: Type):
        self.name = name
        self.service_type = service_type


class CircularServiceA:
    """Service for testing circular type dependencies."""

    def __init__(self, name: str, service_b_type: Optional[Type] = None):
        self.name = name
        self.service_b_type = service_b_type


class CircularServiceB:
    """Service for testing circular type dependencies."""

    def __init__(self, name: str, service_a_type: Optional[Type] = None):
        self.name = name
        self.service_a_type = service_a_type
