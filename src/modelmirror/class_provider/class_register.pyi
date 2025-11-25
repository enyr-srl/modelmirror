from typing import Any

from .class_reference import ClassReference

class ClassRegister:
    reference: ClassReference
    def __init_subclass__(cls, *, reference: ClassReference, **kwargs: Any) -> None: ...
