from typing import TYPE_CHECKING
from .protocols import F, FuncMimicry
from .utils import get_dependant

if TYPE_CHECKING:
    from .manager import FastInjection


class DummyRequest:
    def __init__(self, stack):
        self.scope = {"fastapi_astack": stack}


class Task(FuncMimicry[F]):
    def __init__(self, func: F):
        super().__init__(func)
        self.dependant = get_dependant(call=self)

    def depend_on(self, di: "FastInjection"):
        self.di = di

    @property
    def do(self) -> F:
        """inject dependency and call."""
        return self._do

    async def _do(self, **kwargs):
        return await self.di.do(self, **kwargs)
