from pydantic import BaseModel


class BaseCounter(BaseModel):
    name: str
    value: int


class CounterInDb(BaseCounter): ...
