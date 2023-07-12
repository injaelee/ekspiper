import os
import unittest
from ekspiper.collector.output import CaspianCollector


class CaspianCollectorTest(unittest.IsolatedAsyncioTestCase):

    # This test requires the key to be set as an env variable
    async def test_collect_output(self):
        caspian_bronze_key = os.environ['CASPIAN_BRONZE_KEY']
        t_1 = {"OtherField": [{"value": "hmmm"}]}
        t_2 = {"OtherField2": "hi"}
        t_3 = {"Memos": [{"Memo": {"MemoData": "data1"}}]}
        t_4 = {"Memos": [{"Memo": {"MemoData": "data2", "MemoType": "stringtype", "multiple": {"issuer": 5}}}]}

        c = CaspianCollector(key=caspian_bronze_key)
        response = await c.acollect_output(t_1)
        self.assertNotEqual(response.status_code, 400)
        self.assertEqual(response.status_code, 200)
        response = await c.acollect_output(t_2)
        self.assertNotEqual(response.status_code, 400)
        self.assertEqual(response.status_code, 200)
        response = await c.acollect_output(t_3)
        self.assertNotEqual(response.status_code, 400)
        self.assertEqual(response.status_code, 200)
        response = await c.acollect_output(t_4)
        self.assertNotEqual(response.status_code, 400)
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
