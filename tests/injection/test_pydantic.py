from typing import Annotated
from pydantic import BaseModel, Field


class TestPydantic(BaseModel):
    model_config = {"extra": "forbid"}
    test_param: Annotated[str, Field(min_length=3, max_length=10)]

    def __init__(self, test_p_p: str, test_param: str):
        super().__init__(test_param=test_param) # this is the call to the base model __init__
        self.__test_p_p = test_p_p

    def say_hello(self):
        print(f"Hello, {self.test_param} {self.__test_p_p}!")
