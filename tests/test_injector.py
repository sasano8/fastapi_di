from fastapi_di import DI
from fastapi import Depends
import pytest

context_val = 0


def get_db():
    try:
        yield "db"
    except:
        raise
    finally:
        global context_val
        context_val = 1


@pytest.mark.asyncio
async def test_basic():
    app = DI()

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

    @app.task()
    async def func_context_manager(db=Depends(get_db)):
        return db

    assert await func.do() == 1
    assert await func.do(value=2) == 2
    assert await func2.do(user_id=3) == 3
    assert await func_context_manager.do() == "db"

    print(repr(app))
