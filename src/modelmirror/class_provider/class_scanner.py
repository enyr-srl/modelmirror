"""
Isolated class scanner that creates copies instead of modifying classes globally.
"""

import importlib
import pkgutil
from typing import Dict, Type

from pydantic import BaseModel, validate_call

from modelmirror.class_provider.class_reference import ClassReference
from modelmirror.class_provider.class_register import ClassRegister


class IsolatedClassReference(BaseModel):
    id: str
    cls: Type
    original_cls: Type


class ClassScanner:
    """Scanner that creates isolated class copies instead of global modifications."""

    def __init__(self, package_name: str):
        self.__package_name = package_name
        self.__original_classes: Dict[str, Type] = {}
        self.__isolated_classes: Dict[str, Type] = {}

    def scan(self) -> list[IsolatedClassReference]:
        """Scan and create isolated class copies with validation."""
        self.__import_all_modules(self.__package_name)
        subclasses = self.__all_subclasses(ClassRegister)
        classes_reference: list[IsolatedClassReference] = []

        for cls in subclasses:
            if not cls.__module__.startswith(self.__package_name):
                continue

            class_reference: ClassReference | None = getattr(cls, "reference", None)
            if not class_reference:
                continue

            if self.__is_duplicate(class_reference, classes_reference):
                raise Exception(f"Duplicate class registration with id {class_reference.id}")

            # Create isolated copy instead of modifying original
            isolated_class = self.__create_isolated_class(class_reference.cls)
            isolated_reference = IsolatedClassReference(
                id=class_reference.id, cls=isolated_class, original_cls=class_reference.cls
            )

            classes_reference.append(isolated_reference)

        return classes_reference

    def __create_isolated_class(self, original_class: Type) -> Type:
        """Create an isolated copy of the class with validation."""
        class_name = f"Isolated{original_class.__name__}"

        # Store original for potential restoration
        self.__original_classes[class_name] = original_class

        # Create isolated class with validation
        class IsolatedClass(original_class):
            pass

        IsolatedClass.__name__ = class_name
        IsolatedClass.__qualname__ = class_name

        # Add validation to the isolated class only
        init_method = original_class.__init__
        if init_method:
            setattr(
                IsolatedClass,
                "__init__",
                validate_call(config={"arbitrary_types_allowed": True, "extra": "forbid"})(init_method),
            )

        self.__isolated_classes[class_name] = IsolatedClass
        return IsolatedClass

    def __is_duplicate(self, reference: ClassReference, existing: list[IsolatedClassReference]) -> bool:
        return any(ref.id == reference.id for ref in existing)

    def __import_all_modules(self, package_name: str):
        package = importlib.import_module(package_name)
        for _, name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            try:
                importlib.import_module(name)
            except Exception:
                continue
            if is_pkg:
                self.__import_all_modules(name)

    def __all_subclasses(self, cls: type):
        subclasses = set(cls.__subclasses__())
        for subclass in cls.__subclasses__():
            subclasses.update(self.__all_subclasses(subclass))
        return subclasses
