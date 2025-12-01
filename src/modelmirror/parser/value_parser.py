from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import final


@dataclass
class ParsedValue:
    id: str
    instance: str | None = None


@dataclass
class FormatValidation:
    is_valid: bool
    reason: str = ""


class ValueParser(ABC):
    __name__: str

    def __init__(self):
        self.__name__ = f"{self.__class__.__name__}"

    @abstractmethod
    def _parse(self, value: str) -> ParsedValue:
        raise NotImplementedError

    @abstractmethod
    def _validate(self, value: str) -> FormatValidation:
        raise NotImplementedError

    @final
    def parse(self, value: str) -> ParsedValue:
        if not isinstance(value, str):
            raise ValueError(f"Reference must be a string. Error in reference: '{value!r}")
        format_validation = self._validate(value)
        if format_validation.is_valid:
            return self._parse(value)
        raise ValueError(format_validation.reason)
