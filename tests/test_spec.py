from fastapi_di.spec import check as spec_checking
import asyncio


def test_spec():
    asyncio.run(spec_checking())