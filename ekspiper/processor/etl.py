from .base import EntryProcessor
from collections import namedtuple
from ekspiper.schema.xrp import XRPLObjectSchema
from fluent import sender
from typing import Any, Dict, List
import copy
import logging


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


class XRPLTransactionTransformer(Transformer):
    def transform(self,
        data_entry: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        "Amount": {str, dict},
        "SendMax": {str, dict},
        "TakerGets": {str, dict},
        "TakerPays": {str, dict},
        "metaData.AffectedNodes.CreatedNode.NewFields.Balance": {str, dict},
        "metaData.AffectedNodes.CreatedNode.NewFields.TakerGets": {str, dict},
        "metaData.AffectedNodes.CreatedNode.NewFields.TakerPays": {str, dict},
        "metaData.AffectedNodes.DeletedNode.FinalFields.Balance": {str, dict},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TakerGets": {str, dict},
        "metaData.AffectedNodes.DeletedNode.FinalFields.TakerPays": {str, dict},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.TakerGets": {str, dict},
        "metaData.AffectedNodes.DeletedNode.PreviousFields.TakerPays": {str, dict},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.Balance": {str, dict},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TakerGets": {str, dict},
        "metaData.AffectedNodes.ModifiedNode.FinalFields.TakerPays": {str, dict},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.Balance": {str, dict},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.TakerGets": {str, dict},
        "metaData.AffectedNodes.ModifiedNode.PreviousFields.TakerPays": {str, dict},
        "metaData.DeliveredAmount": {str, dict},
        "metaData.delivered_amount": {str, dict},
        """
        working_data_entry = copy.deepcopy(data_entry)

        for k in ["Amount", "SendMax", "TakerGets", "TakerPays"]:

            if k not in working_data_entry:
                continue

            if type(working_data_entry.get(k)) is not dict:
                working_data_entry[k] = {
                    "currency": "XRP",
                    "issuer": "",
                    "value": data_entry[k],
                }

        meta_data_dict = working_data_entry.get("metaData", {})
        if not meta_data_dict:
            return working_data_entry

        for k in ["DeliveredAmount", "delivered_amount"]:
            if k not in meta_data_dict:
                continue

            if type(meta_data_dict[k]) is not dict:
                working_data_entry[k] = {
                    "currency": "XRP",
                    "issuer": "",
                    "value": meta_data_dict[k],
                }

        affected_nodes = meta_data_dict.get("AffectedNodes", [])
        if not affected_nodes:
            return working_data_entry


        for node_dict in affected_nodes:
            for k, kk in [
                ("CreatedNode", "NewFields"),
                ("DeletedNode", "FinalFields"),
                ("ModifiedNode", "FinalFields"),
                ("ModifiedNode", "PreviousFields"),
            ]:
                if k not in node_dict:
                    continue

                for kkk in ["Balance", "TakerGets", "TakerPays"]:
                    if kk not in node_dict[k] or kkk not in node_dict[k][kk]:
                        continue

                    if type(node_dict[k][kk][kkk]) != dict:
                        node_dict[k][kk][kkk] = {
                            "currency": "XRP",
                            "issuer": "",
                            "value": node_dict[k][kk][kkk],
                        }

        return working_data_entry

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