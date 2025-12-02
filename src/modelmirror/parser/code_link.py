from dataclasses import dataclass
from typing import Any


@dataclass
class CodeLink:
    id: str
    params: dict[str, Any]
    instance: str | None = None
