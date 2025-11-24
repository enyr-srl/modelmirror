from typing import Type

from pydantic import BaseModel, Field


class ClassReference(BaseModel):
    schema_: str = Field(
        ...,
        alias="schema",
    )
    version: str
    cls: Type
