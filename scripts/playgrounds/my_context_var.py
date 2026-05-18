import asyncio
from contextvars import ContextVar

ORIGIN: ContextVar[int] = ContextVar("ORIGIN", default=100)
SCOPE: ContextVar[int] = ContextVar("SCOPE", default=0)


async def show():
    print(f"ORIGIN={ORIGIN.get()}, SCOPE={SCOPE.get()}")


async def func_a():
    SCOPE.set(1)
    await show()


async def func_b():
    SCOPE.set(2)
    await show()


async def main():
    ORIGIN.set(100)
    await asyncio.gather(func_a(), func_b())


if __name__ == "__main__":
    asyncio.run(main())
