from .protocols import F, FuncMimicry
from .utils import get_dependant, solve_dependencies
from .concurrency import AsyncExitStack


class DummyRequest:
    def __init__(self, stack):
        self.scope = {"fastapi_astack": stack}


class Task(FuncMimicry[F]):
    def __init__(self, func: F):
        super().__init__(func)
        self.dependant = get_dependant(call=self)

    @property
    def do(self) -> F:
        """inject dependency and call."""
        return self._do

    async def _do(self, **kwargs):
        dependant = self.dependant
        async with AsyncExitStack() as stack:
            request = DummyRequest(stack=stack)
            values, errors, dependency_cache = await solve_dependencies(
                request=request, dependant=dependant, body=kwargs
            )
            values.update(kwargs)
            result = await self(**values)
        return result
