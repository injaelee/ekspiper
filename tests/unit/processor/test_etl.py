from ekspiper.schema.xrp import XRPLObjectSchema
from ekspiper.processor.etl import (
    XRPLTransactionTransformer, 
    GenericValidator,
    XRPLObjectTransformer,
)
import unittest


class ETLTests(unittest.TestCase):

    def test_validator_ledgerobj(self):
        test_dict = {
            "TakerGets": {
                "currency": "value as dict",
                "issuer": "value as dict",
                "value": "value as dict",
                "notInSchema": "value not in schema",
            },
            "NotInTheSchema": "Hello Not Here",
            "SignerEntries": [
                "signer_01",
                "signer_02"
            ],
        }

        validator = GenericValidator(XRPLObjectSchema.SCHEMA)
        validated_dict = validator.validate(
            data_entry = test_dict,
        )

        # make sure that the one that is not in the schema is removed
        self.assertIsNotNone(test_dict.get("TakerGets", {}).get("notInSchema"))
        self.assertIsNone(validated_dict.get("TakerGets", {}).get("notInSchema"))

        # same here
        self.assertIsNotNone(test_dict.get("NotInTheSchema"))
        self.assertIsNone(validated_dict.get("NotInTheSchema"))

        # check the values of those that remain after the validation
        for key in ["currency", "issuer", "value"]:
            self.assertEqual(
                test_dict.get("TakerGets", {}).get(key),
                validated_dict.get("TakerGets", {}).get(key),
            )

        # check whether the values that remain
        self.assertEqual(
            len(test_dict.get("SignerEntries")), 
            len(validated_dict.get("SignerEntries")),
        )
        for expected, actual in zip(
            test_dict.get("SignerEntries"),
            validated_dict.get("SignerEntries"),
        ):
            self.assertEqual(expected, actual)

        # there should be only two keys available in the validated
        self.assertEqual(2, len(validated_dict))

    def test_transformer_ledgerobj(self):
        test_dict = {
            "TakerGets": {
                "notInSchema": "value not in schema",
                "currency": "value as dict1",
                "issuer": "value as dict2",
                "value": "value as dict3",
            },
            "Balance": "1000002",
            "SendMax": {
                "currency": "value as dict4",
                "issuer": "value as dict5",
                "value": "value as dict6",
            },
            "TakerPays": "101010"
        }
        
        transformer = XRPLObjectTransformer()
        transformed_dict = transformer.transform(test_dict)
        
        for k in ["TakerGets", "SendMax", "TakerGets"]:
            for mk in ["currency", "issuer", "value"]:
                self.assertEqual(
                    test_dict.get(k, {}).get(mk),
                    transformed_dict.get(k, {}).get(mk),
                )

        self.assertIsNotNone(
            transformed_dict.get("TakerGets",{}).get("notInSchema")
        )

        for k in ["Balance", "TakerPays"]:
            self.assertEqual(
                test_dict.get(k, None),
                transformed_dict.get(k, {}).get("value"),
            )
            self.assertEqual(
                "",
                transformed_dict.get(k, {}).get("issuer"),
            )
            self.assertEqual(
                "XRP",
                transformed_dict.get(k, {}).get("currency"),
            )

    def test_transformer_txns(self):
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
        test_dict = {
            "Paths": [[{'currency': 'USD', 'issuer': 'rK4ghh5jbUvEaV4ytV9h3M6JU5YVDv4E76', 'type': 48}]],
            "Amount": "100",
            "SendMax":  {
                "currency": "XRP",
                "issuer": "NoChange",
                "value": "200"
            },
            "TakerGets": "300",
            "TakerPays": "400",
            "metaData": {
                "AffectedNodes": [
                    {
                        "ModifiedNode": {
                            "FinalFields": {
                                "Balance": "100100",
                                "Paths": [[{'currency': 'USD', 'issuer': 'rK4ghh5jbUvEaV4ytV9h3M6JU5YVDv4E76', 'type': 48}]],
                            },
                            "LedgerEntryType": "Type",
                            "LedgerIndex": "AAAAA",
                            "PreviousFields": {
                                "Balance": "100000",
                            },
                            "PreviousTxnID": "AAAAA",
                            "PreviousTxnLgrSeq": 71698271
                        }
                    },{
                        "DeletedNode": {
                            "FinalFields": {
                                "Balance": "100100",
                            },
                            "LedgerEntryType": "Type",
                            "LedgerIndex": "AAAAA",
                            "PreviousFields": {
                                "Balance": "100000",
                            },
                            "PreviousTxnID": "AAAAA",
                            "PreviousTxnLgrSeq": 71698271
                        }
                    },{
                        "CreatedNode": {
                            "NewFields": {
                                "Balance": "400100",
                                "TakerGets": "400200",
                                "TakerPays": "400300",
                            },
                        }
                    }
                ]
        }  }

        answer_dict = {
            "Paths":[
                {
                    "list":[
                        {
                            "currency":"USD",
                            "issuer":"rK4ghh5jbUvEaV4ytV9h3M6JU5YVDv4E76",
                            "type":48
                        }
                    ]
                }
            ],
            "Amount":{
                "currency":"XRP",
                "issuer":"",
                "value":"100"
            },
            "SendMax":{
                "currency":"XRP",
                "issuer":"NoChange",
                "value":"200"
            },
            "TakerGets":{
                "currency":"XRP",
                "issuer":"",
                "value":"300"
            },
            "TakerPays":{
                "currency":"XRP",
                "issuer":"",
                "value":"400"
            },
            "metaData":{
                "AffectedNodes":[
                    {
                        "ModifiedNode":{
                            "FinalFields":{
                                "Balance":{
                                    "currency":"XRP",
                                    "issuer":"",
                                    "value":"100100"
                                },
                                "Paths":[
                                    {
                                        "list":[
                                            {
                                                "currency":"USD",
                                                "issuer":"rK4ghh5jbUvEaV4ytV9h3M6JU5YVDv4E76",
                                                "type":48
                                            }
                                        ]
                                    }
                                ]
                            },
                            "LedgerEntryType":"Type",
                            "LedgerIndex":"AAAAA",
                            "PreviousFields":{
                                "Balance":{
                                    "currency":"XRP",
                                    "issuer":"",
                                    "value":"100000"
                                }
                            },
                            "PreviousTxnID":"AAAAA",
                            "PreviousTxnLgrSeq":71698271
                        }
                    },
                    {
                        "DeletedNode":{
                            "FinalFields":{
                                "Balance":{
                                    "currency":"XRP",
                                    "issuer":"",
                                    "value":"100100"
                                }
                            },
                            "LedgerEntryType":"Type",
                            "LedgerIndex":"AAAAA",
                            "PreviousFields":{
                                "Balance":{
                                    "currency":"XRP",
                                    "issuer":"",
                                    "value":"100000"
                                }
                            },
                            "PreviousTxnID":"AAAAA",
                            "PreviousTxnLgrSeq":71698271
                        }
                    },
                    {
                        "CreatedNode":{
                            "NewFields":{
                                "Balance":{
                                    "currency":"XRP",
                                    "issuer":"",
                                    "value":"400100"
                                },
                                "TakerGets":{
                                    "currency":"XRP",
                                    "issuer":"",
                                    "value":"400200"
                                },
                                "TakerPays":{
                                    "currency":"XRP",
                                    "issuer":"",
                                    "value":"400300"
                                }
                            }
                        }
                    }
                ]
            }
        }

        transformer = XRPLTransactionTransformer()
        transformed_dict = transformer.transform(test_dict)
        print(transformed_dict)

        assert transformed_dict is not test_dict
        self.assertDictEqual(transformed_dict, answer_dict)
