from fastapi_di.manager import FastInjection
from fastapi import Depends


async def check():
    app = FastInjection()

    @app.on_event("startup")
    def test():
        pass

    def get_user_id():
        import random

        return random.random()

    @app.task()
    async def func(value=1):
        return value

    @app.task()
    async def func2(user_id: int = Depends(get_user_id)):
        return user_id

    values, errors, dependency_cache = await func2.resolve_dependency()
    print(f"{values=} {errors=} {dependency_cache=}")

    assert await func.do() == 1
    assert await func.do(value=2) == 2
    assert await func2.do(user_id=3) == 3

    print(repr(app))