import unittest
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd


class ParquetCollectorTest(unittest.TestCase):
    """
    Use pandas and pyarrow to convert everything to a parquet file
    write to the parquet file locally?
    read the file line by line and emit it to a file on S3?

    """
    @staticmethod
    def test_table_create_from_transaction():
        data_1 = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }

        data_2 = {
            "key1": "value4",
            "key2": "value5",
            "key3": "value6"
        }

        transaction_1 = {'Account': 'rDvSaLnMDnGxtp1DPgH3HS9ad2eH7RhnF6', 'Fee': '10', 'Flags': 2147483648, 'OfferSequence': 80141563, 'Sequence': 80141564, 'SigningPubKey': '0342E083EA762D91D621714C39413A594B974D8A9A71E8824174D76F73E0C56CDA', 'TakerGets': {'currency': 'XRP', 'issuer': '', 'value': '110807678'}, 'TakerPays': {'currency': '534F4C4F00000000000000000000000000000000', 'issuer': 'rsoLo2S1kiGeCcn6hCUXVrCpGMWLrRrLZz', 'value': '542.52046355'}, 'TransactionType': 'OfferCreate', 'TxnSignature': '304402201838CDEFF339DD3FDAE99F97DDBB3778635562CE7064A5159FE39445B133076C02206348F18C9B688FE9B824AB798E4F0454BADAF690A846D98139567DCD649398D4', 'hash': 'F079D13BD9F3F0373C40D8F92AFF1F8D719E729B6559D1E69ACFC89ADBA065E5', 'metaData': {'AffectedNodes': [{'ModifiedNode': {'FinalFields': {'Account': 'rDvSaLnMDnGxtp1DPgH3HS9ad2eH7RhnF6', 'Balance': {'currency': 'XRP', 'issuer': '', 'value': '132807667'}, 'Flags': 0, 'OwnerCount': 4, 'Sequence': 80141565}, 'LedgerEntryType': 'AccountRoot', 'LedgerIndex': '15B31D321AECBD7C84B4298338640956BD1219DBB58014022885B1A11C7E0093', 'PreviousFields': {'Balance': {'currency': 'XRP', 'issuer': '', 'value': '132807677'}, 'Sequence': 80141564}, 'PreviousTxnID': '1617EE207656E2A3727E61A176D1CB1190CF911DC72292C7F44C83CBCB1775FF', 'PreviousTxnLgrSeq': 80604099}}, {'CreatedNode': {'LedgerEntryType': 'Offer', 'LedgerIndex': '1B31A7B2C556592C2C3599E63DF6510BB6D4C03E021BA7B6C32C523533873575', 'NewFields': {'Account': 'rDvSaLnMDnGxtp1DPgH3HS9ad2eH7RhnF6', 'BookDirectory': 'C73FAC6C294EBA5B9E22A8237AAE80725E85372510A6CA794F1164EF970C4568', 'Sequence': 80141564, 'TakerGets': {'currency': 'XRP', 'issuer': '', 'value': '110807678'}, 'TakerPays': {'currency': '534F4C4F00000000000000000000000000000000', 'issuer': 'rsoLo2S1kiGeCcn6hCUXVrCpGMWLrRrLZz', 'value': '542.52046355'}}}}, {'DeletedNode': {'FinalFields': {'Account': 'rDvSaLnMDnGxtp1DPgH3HS9ad2eH7RhnF6', 'BookDirectory': 'C73FAC6C294EBA5B9E22A8237AAE80725E85372510A6CA794F11690514F39C22', 'BookNode': '0', 'Flags': 0, 'OwnerNode': '0', 'PreviousTxnID': '1617EE207656E2A3727E61A176D1CB1190CF911DC72292C7F44C83CBCB1775FF', 'PreviousTxnLgrSeq': 80604099, 'Sequence': 80141563, 'TakerGets': {'currency': 'XRP', 'issuer': '', 'value': '110807688'}, 'TakerPays': {'currency': '534F4C4F00000000000000000000000000000000', 'issuer': 'rsoLo2S1kiGeCcn6hCUXVrCpGMWLrRrLZz', 'value': '543.01807816'}}, 'LedgerEntryType': 'Offer', 'LedgerIndex': '4D6E956D640206DC377305F498B2CBD5931F40633A11713F2D2A8CC713C7A1B9'}}, {'ModifiedNode': {'FinalFields': {'Flags': 0, 'IndexNext': '0', 'IndexPrevious': '0', 'Owner': 'rDvSaLnMDnGxtp1DPgH3HS9ad2eH7RhnF6', 'RootIndex': '708FCD38B4D25B1BE6310B0C853A768905C00189CA03402225CA6F0D72503719'}, 'LedgerEntryType': 'DirectoryNode', 'LedgerIndex': '708FCD38B4D25B1BE6310B0C853A768905C00189CA03402225CA6F0D72503719'}}, {'CreatedNode': {'LedgerEntryType': 'DirectoryNode', 'LedgerIndex': 'C73FAC6C294EBA5B9E22A8237AAE80725E85372510A6CA794F1164EF970C4568', 'NewFields': {'ExchangeRate': '4f1164ef970c4568', 'RootIndex': 'C73FAC6C294EBA5B9E22A8237AAE80725E85372510A6CA794F1164EF970C4568', 'TakerPaysCurrency': '534F4C4F00000000000000000000000000000000', 'TakerPaysIssuer': '1EB3EAA3AD86242E1D51DC502DD6566BD39E06A6'}}}, {'DeletedNode': {'FinalFields': {'ExchangeRate': '4f11690514f39c22', 'Flags': 0, 'RootIndex': 'C73FAC6C294EBA5B9E22A8237AAE80725E85372510A6CA794F11690514F39C22', 'TakerGetsCurrency': '0000000000000000000000000000000000000000', 'TakerGetsIssuer': '0000000000000000000000000000000000000000', 'TakerPaysCurrency': '534F4C4F00000000000000000000000000000000', 'TakerPaysIssuer': '1EB3EAA3AD86242E1D51DC502DD6566BD39E06A6'}, 'LedgerEntryType': 'DirectoryNode', 'LedgerIndex': 'C73FAC6C294EBA5B9E22A8237AAE80725E85372510A6CA794F11690514F39C22'}}], 'TransactionIndex': 26, 'TransactionResult': 'tesSUCCESS'}, '_LedgerIndex': 80604100}

        # Convert the list of dictionaries to a pandas DataFrame
        df = pd.DataFrame([transaction_1])

        # Load the existing Parquet file (if it exists)
        try:
            existing_table = pq.read_table('data.parquet')
        except FileNotFoundError:
            existing_table = None

        # Convert the pandas DataFrame to a PyArrow Table
        table = pa.Table.from_pandas(df)

        # Append the new data to the existing table (if it exists)
        if existing_table is not None:
            table = pa.concat_tables([existing_table, table])

        # Write the updated table to the Parquet file
        pq.write_table(table, 'data.parquet')


