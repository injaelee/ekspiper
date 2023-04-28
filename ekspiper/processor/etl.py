import copy
import logging
from collections import namedtuple
from typing import Any, Dict, List

from ekspiper.schema.xrp import XRPLTransactionSchema
from .base import EntryProcessor

logger = logging.getLogger(__name__)


class Validator:

    def validate(self,
                 data_entry: Dict[str, Any],
                 ) -> Dict[str, Any]:
        return data_entry


class Transformer:

    def transform(self,
                  data_entry: Dict[str, Any],
                  ) -> Dict[str, Any]:
        return data_entry


class ETLTemplateProcessor(EntryProcessor):

    def __init__(self,
                 validator: Validator,
                 transformer: Transformer,
                 ):
        self.validator = validator
        self.transformer = transformer

    async def aprocess(self,
                       data_entry: Any,
                       ) -> List[Any]:
        validated_entry = self.validator.validate(data_entry)
        if not validated_entry:
            logger.warn("There were NO valid attributes")
        return [self.transformer.transform(validated_entry)]


class GenericValidator(Validator):
    def __init__(self,
                 schema: Dict[str, Any],
                 ):
        self.schema = schema

    def validate(self,
                 data_entry: Dict[str, Any],
                 ) -> Dict[str, Any]:
        """
        Validate the data types
        """

        # make a deep copy to not touch the orginal
        working_data_entry = copy.deepcopy(data_entry)

        se = namedtuple("se", ["key", "entry_dict", "prefix"])
        keys_stack = []
        for key in working_data_entry.keys():
            keys_stack.append(se(key, working_data_entry, ""))

        while keys_stack:
            (current_key, entry_dict, key_prefix) = keys_stack.pop()

            full_key = (key_prefix + "." if key_prefix else "") + current_key

            allowed_data_type_set = self.schema.get(full_key, [])

            # check whether the key is defined within the schema
            # case sensitive
            if not allowed_data_type_set:
                logger.warning(
                    "removing key['%s'] that is not defined in the schema: %s",
                    full_key,
                    entry_dict[current_key],
                )
                # remove the key
                del entry_dict[current_key]
                continue

            # check whether the data entry is allowed
            if type(entry_dict[current_key]) not in allowed_data_type_set:
                logger.warning(
                    "removing key['%s'] that is the wrong data type: %s",
                    full_key,
                    entry_dict[current_key],
                )
                del entry_dict[current_key]
                continue

            if type(entry_dict[current_key]) == dict:
                current_dict = entry_dict[current_key]
                # push to the stack for evaluation
                for key in current_dict.keys():
                    keys_stack.append(se(key, current_dict, full_key))

        return working_data_entry


class XRPLObjectTransformer(Transformer):
    def transform(self,
                  data_entry: Dict[str, Any],
                  ) -> Dict[str, Any]:
        """
        For the dual types, ie. dict + str, consolidate
        to a single type, say, dict.

        "Balance": {str, dict},
        "SendMax": {str, dict},
        "TakerGets": {str, dict},
        "TakerPays": {str, dict},

        Convert these to dict.
        - currency
        - issuer
        - value
        """
        # make a deep copy to not touch the orginal
        working_data_entry = copy.deepcopy(data_entry)

        for k in ["Balance", "SendMax", "TakerGets", "TakerPays"]:

            if k not in working_data_entry:
                continue

            if type(working_data_entry.get(k)) is not dict:
                working_data_entry[k] = {
                    "currency": "XRP",
                    "issuer": "",
                    "value": data_entry[k],
                }

        return working_data_entry


class XRPLGenericTransformer(Transformer):
    def __init__(self, schema=XRPLTransactionSchema.SCHEMA):
        self.toTransform = set()

        for key, value in schema.items():
            if len(value) > 1:
                self.toTransform.add(key)

    def transform(self,
                  data_entry: Dict[str, Any],
                  ) -> Dict[str, Any]:
        """
        turns all string data entries with double types into dictionaries based on schema

        a: "str"
        b.c: "str"

        {
          a: "val"
          b: {
            c: "val2"
            d: {
              e: "ha"
            }
          }
        }

        :param data_entry: data to transform
        :return: the new data entry
        """
        working_data_entry = copy.deepcopy(data_entry)
        self.flatten_lists(working_data_entry)

        for k in self.toTransform:
            path = k.split(".")
            self.transform_helper(path, working_data_entry)

        return working_data_entry

    def flatten_lists(self, data):
        """
        data: {
          paths: [[{currency, issuer, type}]]
        } ->
        data {
          paths: [{list: [{currency, issuer, type}]}]
        }

        flattens nested lists -> adds a `list` field within nested lists to support bigquery
        """
        if type(data) is not dict:
            return

        for key, value in data.items():
            if type(value) is dict:
                self.flatten_lists(value)
            elif type(value) is list:
                transformed_list = []
                for d in value:
                    if type(d) is list:
                        a_list = {'list': copy.deepcopy(d)}
                        transformed_list.append(a_list)

                if len(transformed_list) > 0:
                    data[key] = transformed_list

                for d in data[key]:
                    self.flatten_lists(d)

    def transform_helper(self, path, data):
        val = data
        p = path[0]

        for i in range(len(path) - 1):
            if val is not None and p in val:
                if type(val[p]) is list:
                    for d in val[p]:
                        self.transform_helper(path[i + 1:len(path)], d)
                    return
                else:
                    val = val[p]
                    p = path[i + 1]
            else:
                break

        if p in val and type(val[p]) is not dict:
            logger.info("transforming path: " + str(path))
            val[p] = {
                "currency": "XRP",
                "issuer": "",
                "value": val[p],
            }


class XRPLObjectTransformer(Transformer):
    def transform(self,
                  data_entry: Dict[str, Any],
                  ) -> Dict[str, Any]:
        """
        "Amount": {str, dict},
        "Balance": {str, dict},
        "SendMax": {str, dict},
        "TakerGets": {str, dict},
        "TakerPays": {str, dict},
        """
        working_data_entry = copy.deepcopy(data_entry)
        for k in ["Amount", "Balance", "SendMax", "TakerGets", "TakerPays"]:

            if k not in working_data_entry:
                continue

            if type(working_data_entry.get(k)) is not dict:
                working_data_entry[k] = {
                    "currency": "XRP",
                    "issuer": "",
                    "value": data_entry[k],
                }

        return working_data_entry
