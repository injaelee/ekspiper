
class QueueSource:
    def __init__(self,
        async_queue: AsyncQueue,
    ):
        self.async_queue = async_queue

    def stop(self):
        self.is_stop = True
        self.populate_task.cancel()

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.is_stop and self.async_queue.empty():
            raise StopAsyncIteration

        return await self.async_queue.get()
