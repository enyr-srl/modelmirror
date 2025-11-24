import importlib
import pkgutil

from pydantic import validate_call

from modelmirror.class_provider.class_reference import ClassReference
from modelmirror.class_provider.class_register import ClassRegister


class ClassScanner:
    def __init__(self, package_name: str):
        self.__package_name = package_name
        self.__base_class = ClassRegister
        self.__classes_reference: list[ClassReference] = []

    def scan(self) -> list[ClassReference]:
        self.__import_all_modules(self.__package_name)
        subclasses = self.__all_subclasses(self.__base_class)
        for cls in subclasses:
            # filter by module prefix
            if not cls.__module__.startswith(self.__package_name):
                continue

            class_reference = getattr(cls, "reference", None)
            if class_reference:
                reference: ClassReference = class_reference
                if self.__is_present(reference):
                    raise Exception(
                        f"Duplicate class registration with schema {reference.schema_} and version {reference.version}"
                    )
                self.__set_init_decorator(reference)
                self.__classes_reference.append(reference)
        return self.__classes_reference

    def __set_init_decorator(self, cls_reference: ClassReference):
        init_method = cls_reference.cls.__dict__.get("__init__")
        if init_method:
            cls_reference.cls.__init__ = validate_call(config={"arbitrary_types_allowed": True, "extra": "forbid"})(
                init_method
            )

    def __is_present(self, reference: ClassReference):
        for class_reference in self.__classes_reference:
            if class_reference.schema_ == reference.schema_ and class_reference.version == reference.version:
                return True
        return False

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
