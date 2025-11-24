from pydantic import BaseModel, Field

from modelmirror.reflection.reflection_registry import ReflectionRegistry


class ReflectionMetadata(BaseModel):
    instance: str | None = Field(default=None)
    registry: ReflectionRegistry
