from pydantic import BaseModel, Field


class ReflectionRegistry(BaseModel):
    schema_: str = Field(
        ...,
        alias="schema",
    )
    version: str
