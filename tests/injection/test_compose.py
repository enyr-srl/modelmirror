from tests.injection.test import Test


class TestCompose:
    def __init__(self, test_param: str, test_1: Test):
        self.test_param = test_param
        self.test_1 = test_1

    def say_hello(self):
        print("Hello from Test2")
