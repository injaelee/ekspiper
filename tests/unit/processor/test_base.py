from ekspiper.processor.base import RetryWrapper
import unittest


class RetryWrapperTest(unittest.IsolatedAsyncioTestCase):
    async def test_retries(self):
        called = 2
        async def wrappable_func(input: int) -> str:
            nonlocal called
            called -= 1
            if called > 0:
                raise ValueError("simulated value error")
            return str(":{}:".format(input))

        retry_wrapper = RetryWrapper[int, str]()
        output = await retry_wrapper.aretry(
            121,
            func_handler = wrappable_func,
        )

        print("Output gathered '{}'".format(output))

