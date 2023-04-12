import asyncio


class AsyncTimedIterable:
    def __init__(self, iterable, timeout=0):
        class AsyncTimedIterator:
            def __init__(self):
                self._iterator = iterable.__aiter__()

            async def __anext__(self):
                try:
                    result = await asyncio.wait_for(self._iterator.__anext__(), int(timeout))
                    # if you want to stop the iteration just raise StopAsyncIteration using some conditions (when the
                    # last chunk arrives, for example)
                    if not result:
                        raise StopAsyncIteration
                    return result
                except asyncio.TimeoutError as e:
                    raise e

        self._factory = AsyncTimedIterator

    def __aiter__(self):
        return self._factory()
