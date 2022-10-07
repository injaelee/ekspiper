import unittest
from ekspiper.schema.attribute import AttributeTypeMappingCollector


class CollectorTestCases(unittest.TestCase):
    def test_good(self):
        structured_data_entries = [
            # 1
            {
                "dict-1": {
                    "boolean-n-string-1": True,
                    "string-1": "1D0BD042421251CAEA1F6D3C52B8F357FFDF90626A4738CC70DCD6291FFF1275",
                    "int-1": 0,
                    "float-1": 705695142.,
                },
            },
            # 1.1 with dupe types
            {
                "dict-1": {
                    "boolean-n-string-1": "string",
                    "string-1": "1D0BD042421251CAEA1F6D3C52B8F357FFDF90626A4738CC70DCD6291FFF1275",
                    "int-1": 0,
                    "float-1": 705695142.,
                },
            },
            # 2
            {
                "dict-2": {
                    "string-1": "SEC",
                    "list-1": [
                        {
                            "string-1": "string"
                        }
                    ]
                },
            },
        ]
        type_mapping_collector = AttributeTypeMappingCollector()
        for data_entry in structured_data_entries:
            type_mapping_collector.collect_attributes(data_entry)

        answer_dict = {
            "dict-1": {dict},
            "dict-1.boolean-n-string-1": {str, bool},
            "dict-1.float-1": {float},
            "dict-1.int-1": {int},
            "dict-1.string-1": {str},
            "dict-2": {dict},
            "dict-2.list-1": {list},
            "dict-2.list-1.string-1": {str},
            "dict-2.string-1": {str},
        }
        attribute_type_mapping = type_mapping_collector.get_mapping()
        for key, type_set in answer_dict.items():
            self.assertIsNotNone(attribute_type_mapping.get(key), "No key exists for key '{key}'".format(key = key))
            self.assertEqual(attribute_type_mapping.get(key), type_set, "Not equal for key '{key}'".format(key = key))

        # number of keys must match
        self.assertEqual(len(answer_dict), len(attribute_type_mapping))

    def test_nested(self):
        structured_data_entries = [
            # 1
            {
                "nested-list-1": [
                    {"AuthAccount": {"Account": "rMKXGCbJ5d8LbrqthdG46q3f969MVK2Qeg"}},
                    {"AuthAccount": {"Account": "rBepJuTLFJt3WmtLXYAxSjtBWAeQxVbncv"}}
                ],
            },
        ]
        type_mapping_collector = AttributeTypeMappingCollector()
        for data_entry in structured_data_entries:
            type_mapping_collector.collect_attributes(data_entry)

        attribute_type_mapping = type_mapping_collector.get_mapping()
        print(attribute_type_mapping)