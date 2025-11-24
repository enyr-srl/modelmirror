from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

from tests.injection.test import Test


class TestNestedDict(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')
    test_param: Annotated[str, Field(min_length=3, max_length=10)]
    test_p_p: Test

    def say_hello(self):
        print(f"Hello, {self.test_param} {self.test_p_p.test_param}!")
