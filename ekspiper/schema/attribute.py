from typing import Any, Dict, List, Set
import copy

class AttributeTypeMappingCollector:
    """
    Extracts and aggregates the key, data types pair given dictionaries.

    This is used to find the superset of the key to data types.
    Hierarchical keys are flatten with dots ".".

    Example)
    start_key:
    |_a_key: v
    |_b_key:
      |_c-key: []

    Results in:
      start_key            : <dict>
      start_key.a_key      : <str>
      start_key.b_key      : <dict>
      start_key.b_key.c_key: <list>
    """
    def __init__(self,
        data_type_mapping: str = None,
        init_attribute_mapping: Dict[str, Set[str]] = None,
    ):
        self.data_type_mapping = data_type_mapping

        if init_attribute_mapping:
            self.attribute_mapping = copy.deepcopy(
                init_attribute_mapping
            )
        else:
            self.attribute_mapping = {}

        # setup BigQuery Data Type
        self.bigquery_data_type_mapping = {
            int: "INTEGER",
            str: "STRING",
            dict: "RECORD",
        }

    def get_keys(self) -> List[Any]:
        return self.attribute_mapping.keys()

    def get(self,
        key,
    ) -> Any:
        return self.attribute_mapping.get(key)

    def get_mapping(self) -> Dict[str, Set[str]]:
        return self.attribute_mapping

    def _data_type_translation(self,
        data_type,
    ):
        if self.data_type_mapping == "google":
            return self.bigquery_data_type_mapping.get(
                data_type,
                "NOT FOUND:[{}]".format(data_type),
            )

        return data_type

    async def acollect_attributes(self,
        entry: Dict[str, Any]
    ):
        self.collect_attributes(entry)

    def collect_attributes(self,
        data_dict: Dict[str, Any],
    ):
        self._collect_attributes(
            prefix = "",
            data_dict = data_dict,
            attribute_mapping = self.attribute_mapping,
        )  

    def _collect_attributes(self,
        prefix: str,
        data_dict: Dict[str, Any],
        attribute_mapping: Dict[str, Set[str]],
    ):

        # extract out all the attributes
        for k, v in data_dict.items():

            attribute_name = prefix + k

            if type(v) == dict:
                self._collect_attributes(
                    prefix = attribute_name + ".",
                    data_dict = v,
                    attribute_mapping = attribute_mapping,
                )

            # assumption: there is no list of lists
            if type(v) == list:
                for entry in v:
                    if type(entry) == dict:
                        self._collect_attributes(
                            prefix = attribute_name + ".",
                            data_dict = entry,
                            attribute_mapping = attribute_mapping,
                        )
                    elif type(entry) == list:
                        if not attribute_mapping.get(attribute_name + ".list"):
                            attribute_mapping[attribute_name + ".list"] = set()

                        data_type = self._data_type_translation(dict)
                        attribute_mapping[attribute_name + ".list"].add(data_type)

                        for e in entry:
                            self._collect_attributes(
                                prefix = attribute_name + ".list.",
                                data_dict = e,
                                attribute_mapping = attribute_mapping,
                            )

            if not attribute_mapping.get(attribute_name):
                attribute_mapping[attribute_name] = set()

            data_type = self._data_type_translation(type(v))
            attribute_mapping[attribute_name].add(data_type)

    def print(self,
        delimeter = "\t",
    ):
        for k in sorted(self.attribute_mapping.keys()):
            v = self.attribute_mapping.get(k)
            print("{key}{delimeter}{value}".format(
                key = k,
                delimeter = delimeter,
                value = v,
            ))
