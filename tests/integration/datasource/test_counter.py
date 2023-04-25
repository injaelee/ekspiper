import unittest

from ekspiper.source.counter import PartitionedCounterDataSource


class PartitionedCounterDataSourceTest(unittest.IsolatedAsyncioTestCase):
    async def test_count_down_contiguous(self):
        data_source = PartitionedCounterDataSource(
            starting_count=100,
            shard_index=0,
            shard_size=1,
        )
        data_source.start()

        previous_value = 0
        itr_count = 0
        async for value in data_source:
            data_source.stop()
            if itr_count > 0:
                self.assertEqual(0, previous_value - value - 1)
            itr_count += 1
            previous_value = value

        self.assertTrue(itr_count > 1)

    async def test_count_down_partitioned(self):
        shard_index = 5
        data_source = PartitionedCounterDataSource(
            starting_count=100,
            shard_index=shard_index,
            shard_size=10,
        )
        data_source.start()

        itr_count = 0
        async for value in data_source:
            data_source.stop()
            self.assertTrue(value % shard_index == 0)
            itr_count += 1

        self.assertTrue(itr_count > 1)
