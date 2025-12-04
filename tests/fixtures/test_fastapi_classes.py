"""
Class registers for extended testing classes.
"""

from dataclasses import dataclass, field
from typing import AsyncGenerator, Awaitable, Callable, List

try:
    from fastapi import FastAPI
    from fastapi.concurrency import asynccontextmanager

    @dataclass
    class ShutdownCallbacks:
        callbacks: List[Callable[[], Awaitable[None]]] = field(default_factory=list)

    class ShutdownStrategy:
        def __init__(self, callbacks: ShutdownCallbacks = ShutdownCallbacks()) -> None:
            self.__callbacks: ShutdownCallbacks = callbacks

        async def run(self) -> None:
            for callback in self.__callbacks.callbacks:
                await callback()

    @dataclass
    class StartupCallbacks:
        callbacks: List[Callable[[], Awaitable[None]]] = field(default_factory=list)

    class StartupStrategy:
        def __init__(self, callbacks: StartupCallbacks = StartupCallbacks()) -> None:
            self.__callbacks: StartupCallbacks = callbacks

        async def run(self) -> None:
            for callback in self.__callbacks.callbacks:
                await callback()

    class LifeSpan:
        def __init__(
            self,
            startup_strategy: StartupStrategy = StartupStrategy(),
            shutdown_strategy: ShutdownStrategy = ShutdownStrategy(),
        ) -> None:
            self.__startup_strategy: StartupStrategy = startup_strategy
            self.__shutdown_strategy: ShutdownStrategy = shutdown_strategy

        @asynccontextmanager
        async def __call__(self, app: FastAPI) -> AsyncGenerator:
            await self.__startup_strategy.run()
            yield
            await self.__shutdown_strategy.run()

except ImportError:
    pass
