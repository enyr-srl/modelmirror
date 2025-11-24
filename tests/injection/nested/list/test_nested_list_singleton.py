from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

from tests.injection.test import Test


class TestNestedListSingleton(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')
    test_param: Annotated[str, Field(min_length=3, max_length=10)]
    test_singleton: Test
    tests: list[Test]

    def say_hello(self):
        for test in self.tests:
            test.say_hello()
