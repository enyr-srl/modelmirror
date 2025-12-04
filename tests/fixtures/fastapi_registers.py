"""
FastAPI class registers.
"""

from modelmirror.class_provider.class_reference import ClassReference
from modelmirror.class_provider.class_register import ClassRegister

try:
    from fastapi import FastAPI

    from tests.fixtures.test_fastapi_classes import LifeSpan, StartupCallbacks, StartupStrategy

    class FastAPIRegister(ClassRegister):
        reference = ClassReference(id="fast-api", cls=FastAPI)

    class LifeSpanClassRegister(ClassRegister):
        reference = ClassReference(id="life-span", cls=LifeSpan)

    class StartupStrategyClassRegister(ClassRegister):
        reference = ClassReference(id="startup-strategy", cls=StartupStrategy)

    class StartupCallbacksClassRegister(ClassRegister):
        reference = ClassReference(id="startup-callbacks", cls=StartupCallbacks)

except ImportError:
    pass
