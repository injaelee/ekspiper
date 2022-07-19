from ekspiper.processor.attribute import AttributeCollectionProcessor
import unittest


class AttributeCollectionProcessorTest(unittest.IsolatedAsyncioTestCase):
    async def test_collection_diff(self):
        processor = AttributeCollectionProcessor()

        expected_values = [
            ["attribute_a", "{<class 'str'>}"],
        ]
        values = await processor.aprocess({
            "attribute_a": "a",
        })
        self.assertEqual(1, len(values))
        
        values = await processor.aprocess({
            "attribute_a": "aa",
        })
        # there are no new attributes introduced, 
        # hence 0 output
        self.assertEqual(0, len(values))

        values = await processor.aprocess({
            "attribute_b": "b",
            "attribute_c": 1,
        })
        expected_values.extend([
            ["attribute_b", "{<class 'str'>}"],
            ["attribute_c", "{<class 'int'>}"]
        ])
        # there are two new attributes,
        # hence a total of 3 because it includes the
        # 1st one as well
        self.assertEqual(3, len(values))
        
        for av, ev in zip(values, expected_values):
            actual_value = av.split("\t")[1:]
            self.assertEqual(ev, actual_value)
