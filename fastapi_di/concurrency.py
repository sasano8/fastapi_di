from typing import Any, Callable, TypeVar
from contextlib import asynccontextmanager, contextmanager, AsyncExitStack
import functools
import asyncio

T = TypeVar("T")


async def run_in_threadpool(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    loop = asyncio.get_event_loop()
    # if contextvars is not None:  # pragma: no cover
    #     # Ensure we run in the same context
    #     child = functools.partial(func, *args, **kwargs)
    #     context = contextvars.copy_context()
    #     func = context.run
    #     args = (child,)
    # elif kwargs:  # pragma: no cover
    #     # loop.run_in_executor doesn't accept 'kwargs', so bind them in here
    #     func = functools.partial(func, **kwargs)

    func = functools.partial(func, **kwargs)
    return await loop.run_in_executor(None, func, *args)


@asynccontextmanager
async def contextmanager_in_threadpool(cm: Any) -> Any:
    try:
        yield await run_in_threadpool(cm.__enter__)
    except Exception as e:
        ok = await run_in_threadpool(cm.__exit__, type(e), e, None)
        if not ok:
            raise e
    else:
        await run_in_threadpool(cm.__exit__, None, None, None)
