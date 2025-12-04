"""
FastAPI class registers.
"""

from modelmirror.class_provider.class_reference import ClassReference
from modelmirror.class_provider.class_register import ClassRegister

try:
    from fastapi import FastAPI

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


if FASTAPI_AVAILABLE:

    class FastAPIRegister(ClassRegister):
        reference = ClassReference(id="fastapi_app", cls=FastAPI)
