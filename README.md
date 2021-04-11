# fastapi_di
I extracted the dependency injection process from fastapi.
Dependency injection by fastapi_di is only available in the async environment.

# setup
``` shell
poetry install fastapi_di
```
# getting started
Dependency injection is done by decorating the function and calling do as follows.


``` Python
import asyncio
from fastapi import Depends
from fastapi_di import DI

di = DI()


def get_db():
    yield {1: {"id": 1, "name": "bob", "memo": ""}}


@di.task()
async def update_user(db=Depends(get_db), *, user_id: int, memo: str):
    record = db[user_id]
    record["memo"] = memo
    return record


async def main():
    return await update_user.do(user_id=1, memo="test")


result = asyncio.run(main())
print(result)
# => {'id': 1, 'name': 'bob', 'memo': 'test'}}
```