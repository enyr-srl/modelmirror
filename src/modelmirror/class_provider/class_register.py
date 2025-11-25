from typing import Any

from modelmirror.class_provider.class_reference import ClassReference


class ClassRegister:
    reference: ClassReference

    def __init_subclass__(cls, *, reference: ClassReference, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.reference = reference
