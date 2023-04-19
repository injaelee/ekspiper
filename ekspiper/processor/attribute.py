from ekspiper.schema.attribute import AttributeTypeMappingCollector
from ekspiper.processor.base import EntryProcessor
from typing import Any, Dict, List, Set
import random
import time

class AttributeCollectionProcessor(EntryProcessor):
    def __init__(self,
        data_type_mapping: str = None,
        init_attribute_mapping: Dict[str, Set[str]] = None,
    ):
        self.attribute_type_mapping_collector = AttributeTypeMappingCollector(
            data_type_mapping = data_type_mapping,
            init_attribute_mapping = init_attribute_mapping,    
        )
        self.latest_key_count = len(
            self.attribute_type_mapping_collector.get_keys())

    # TODO: this only accounts for changes to the keys, not values. can be problematic when we have multiple datatypes
    #  for a single key, we wont register the change
    async def aprocess(self,
        entry: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        self.attribute_type_mapping_collector.collect_attributes(entry)

        values = []
        execution_id = "%d-%d" % (time.time(), random.randrange(0, 100_000_000))
        if self.latest_key_count != len(self.attribute_type_mapping_collector.get_keys()):
            self.latest_key_count = len(self.attribute_type_mapping_collector.get_keys())
            for k in sorted(self.attribute_type_mapping_collector.get_keys()):
                v = self.attribute_type_mapping_collector.get(k)
                values.append(f"{execution_id}\t{k}\t{v}")
        return values
