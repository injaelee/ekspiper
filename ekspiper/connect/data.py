from typing import Generic, TypeVar

T = TypeVar("T")

class DataSource:
    def __aiter__(self):
        return self

    async def __anext__(self):
        raise NotImplementedError


class DataSink:
    async def put(self,
        entry: T,
    ):
        raise NotImplementedError