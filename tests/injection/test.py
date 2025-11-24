from typing import Annotated
from pydantic import Field


class Test:
    def __init__(self, test_param: Annotated[str, Field(min_length=3, max_length=10)]):
        self.test_param = test_param

    def say_hello(self):
        print(f"Hello, {self.test_param}!")
