from typing import Any

from modelmirror.class_provider.class_reference import ClassReference


class ClassRegister:
    reference: ClassReference

    def __init_subclass__(cls, **kwargs: Any) -> None:
        reference = kwargs.pop("reference", None)
        super().__init_subclass__(**kwargs)
        if reference is None:
            raise ValueError(f"ClassRegister reference must be provided for class {cls.__name__!r}")
        cls.reference = reference
