from .protocols import F, FuncMimicry
from .utils import get_dependant, solve_dependencies


class Task(FuncMimicry[F]):
    @property
    def do(self) -> F:
        """inject dependency and call."""
        return self._do

    async def _do(self, **kwargs):
        dependant = get_dependant(call=self)
        values, errors, dependency_cache = await solve_dependencies(
            dependant=dependant, body=kwargs
        )
        values.update(kwargs)
        return await self(**values)

    async def resolve_dependency(self, **kwargs):
        dependant = get_dependant(call=self)
        return await solve_dependencies(dependant=dependant)