import asyncio

class QueueSource:
    def __init__(self,
        async_queue: asyncio.Queue,
    ):
        self.async_queue = async_queue
        self.is_stop = False

    def stop(self):
        self.is_stop = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.is_stop and self.async_queue.empty():
            raise StopAsyncIteration

        return await self.async_queue.get()
