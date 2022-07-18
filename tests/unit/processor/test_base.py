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

        value_passed = 121
        expected_value = f":{value_passed}:"
        retry_wrapper = RetryWrapper[int, str]()
        output = await retry_wrapper.aretry(
            value_passed,
            func_handler = wrappable_func,
            is_mute_stacktrace = True,
            base_sleep_s = 0,
            sleep_multiplier = 0,
        )

        self.assertEqual(expected_value, output)
