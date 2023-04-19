import argparse
import json
from collections import namedtuple
from google.cloud import bigquery
from xrp import XRPLObjectSchema, XRPLTransactionSchema, XRPLLedgerSchema
from typing import Dict, List, Set
import datetime
import logging
import sys
import unittest

IntermediateNode = namedtuple("IntermediateNode", ["prefix", "name", "obj"])


logger = logging.getLogger(__name__)


class BigQuerySchemaBottomUpBuilder:
    def __init__(self):
        self.to_gcp_bq_data_type: Dict[type, str] = {
            int: "INTEGER",
            float: "FLOAT",
            str: "STRING",
            dict: "RECORD",
            list: "RECORD",
            bool: "BOOLEAN",
            datetime.datetime: "DATETIME",
            datetime.date: "DATE",
            datetime.time: "TIME",
        }

    def _type_to_data_type(self,
        python_type: type,
    ) -> str:
        return self.to_gcp_bq_data_type.get(python_type)

    def build_from_stack(self,
        obj_stack: List[IntermediateNode],
    ) -> List[bigquery.SchemaField]:

        built_fields: List[bigquery.SchemaField] = []
        named_google_schema_fields: Dict[str, List[bigquery.SchemaField]] = {}

        prev_node = None
        while len(obj_stack) > 0:
            current_node = obj_stack.pop()

            # parent found: create the parent
            if current_node.obj in {list, dict}: #prev_node and current_node.name == prev_node.prefix:

                key_name = current_node.name[len(current_node.prefix):]

                # remove the '.' if there is one
                key_name = key_name[1:] if key_name[0] == '.' else key_name

                google_schema_fields = named_google_schema_fields.get(current_node.name, [])

                obj_stack.append(IntermediateNode(
                    prefix = current_node.prefix,
                    name = current_node.name,
                    obj = bigquery.SchemaField(
                        key_name,
                        "RECORD" if google_schema_fields else "STRING",
                        mode = "NULLABLE" if current_node.obj == dict else "REPEATED",
                        fields = named_google_schema_fields.get(current_node.name, []),
                )))

                if current_node.name in named_google_schema_fields:
                    del named_google_schema_fields[current_node.name]

            # build up the sibling list
            elif current_node.prefix:
                google_schema_fields = named_google_schema_fields.get(
                    current_node.prefix,
                    []
                )
                google_schema_fields.append(current_node.obj)
                named_google_schema_fields[current_node.prefix] = google_schema_fields

            else:

                built_fields.append(current_node.obj)

            prev_node = current_node

        return built_fields

    def build(self,
        schema_dict: Dict[str, Set[type]],
    ) -> List[bigquery.SchemaField]:

        obj_stack: List[IntermediateNode] = []

        # build the object stack
        for full_key in sorted(schema_dict.keys()):
            tokens = full_key.split(".")

            # prefix key is the canonical name without the key
            prefix_key = ".".join(tokens[:-1])

            # the key name is the last token
            key = tokens[-1]
            logger.debug(f"{prefix_key} - {key}")

            data_type_set = schema_dict.get(full_key)

            if data_type_set.intersection({dict, list}):
                obj = list if list in data_type_set else dict
            else:
                python_type = next(iter(data_type_set))
                bg_data_type = self._type_to_data_type(
                    python_type = python_type,
                )
                obj = bigquery.SchemaField(
                    key,
                    bg_data_type,
                    mode = "NULLABLE",
                )

            obj_stack.append(IntermediateNode(
                prefix = prefix_key,
                name = full_key,
                obj = obj,
            ))


        built_fields: List[bigquery.SchemaField] = self.build_from_stack(
            obj_stack = obj_stack,
        )
        return built_fields


class BigQueryTableBuilder:
    def build(self,
        project_name: str,
        dataset_name: str,
        table_name: str,
        schema: List[bigquery.SchemaField],
    ):
        # set up the 'GOOGLE_APPLICATION_CREDENTIALS' env variable
        client = bigquery.Client()

        table_id = f"{project_name}.{dataset_name}.{table_name}"
        table = bigquery.Table(
            table_id,
            schema = schema,
        )
        table = client.create_table(table)  # Make an API request.
        print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")


class BigQueryTableUpdater:
    def update(self,
        project_name: str,
        dataset_name: str,
        table_name: str,
        schema: List[bigquery.SchemaField],
    ):
        # set up the 'GOOGLE_APPLICATION_CREDENTIALS' env variable
        client = bigquery.Client()

        table_id = f"{project_name}.{dataset_name}.{table_name}"
        table = bigquery.Table(
            table_id,
            schema = schema,
        )

        #column_names = [x.name for x in table.schema]
        table = client.update_table(table, ['schema'])  # Make an API request.
        print(f"Updated table {table.project}.{table.dataset_id}.{table.table_id}")


class SchemaBuilderTest(unittest.TestCase):
    def test_google(self):
        schema = {
            "Account": {str},
            "Amendment": {str},
            "Amount": {str, dict},
            "Amount.currency": {str},
            "Amount.issuer": {str},
            "Amount.value": {str},
            "Amount.objs": {list},
            "Amount.objs.name": {str},
            "Amount.objs.value": {int},
            "ListStrings": {list},
        }
        bg_query_schema_builder = BigQuerySchemaBottomUpBuilder()
        bg_schema_fields = bg_query_schema_builder.build(
            schema_dict = schema,
        )

        expected_schema_fields = [
            bigquery.SchemaField("ListStrings", "STRING", mode = "REPEATED"),
            bigquery.SchemaField("Amount", "RECORD", mode = "NULLABLE", fields = [
                bigquery.SchemaField("value", "STRING", mode = "NULLABLE"),
                bigquery.SchemaField("objs", "RECORD", mode = "REPEATED", fields = [
                    bigquery.SchemaField("value", "INTEGER", mode = "NULLABLE"),
                    bigquery.SchemaField("name", "STRING", mode = "NULLABLE"),
                ]),
                bigquery.SchemaField("issuer", "STRING", mode = "NULLABLE"),
                bigquery.SchemaField("currency", "STRING", mode = "NULLABLE"),
            ]),
            bigquery.SchemaField("Amendment", "STRING", mode = "NULLABLE"),
            bigquery.SchemaField("Account", "STRING", mode = "NULLABLE")
        ]

        # recursive function to determine equal content and structure
        def equal_schema_fields(
            assertion: unittest.TestCase,
            expected_fields: List[bigquery.SchemaField],
            actual_fields: List[bigquery.SchemaField],
        ) -> bool:
            assertion.assertEqual(len(expected_fields), len(actual_fields))
            for expected_field in expected_fields:
                matched = False
                for actual_field in actual_fields:
                    if expected_field.name == actual_field.name:
                        matched = True
                        assertion.assertEqual(
                            expected_field.field_type,
                            actual_field.field_type,
                        )
                        equal_schema_fields(
                            assertion,
                            expected_field.fields,
                            actual_field.fields,
                        )
                        break
                assertion.assertTrue(
                    matched, "Missing field in actual fields: %s" % expected_field)

        equal_schema_fields(self, expected_schema_fields, bg_schema_fields)


def update_bigquery_table(
    project_name: str,
    dataset_name: str,
    table_name: str,
    schema: Dict[str, Set[str]],
):
    bg_query_schema_builder = BigQuerySchemaBottomUpBuilder()
    bg_schema_fields = bg_query_schema_builder.build(
        schema_dict = schema,
    )

    bg_query_schema_updater = BigQueryTableUpdater()
    bg_schema_fields = bg_query_schema_updater.update(
        project_name = project_name,
        dataset_name = dataset_name,
        table_name = table_name,
        schema = bg_schema_fields,
    )


def build_bigquery_table(
    project_name: str,
    dataset_name: str,
    table_name: str,
    schema: Dict[str, Set[str]],
):
    bg_query_schema_builder = BigQuerySchemaBottomUpBuilder()
    bg_schema_fields = bg_query_schema_builder.build(
        schema_dict = schema,
    )

    bq_table_builder = BigQueryTableBuilder()
    bq_table_builder.build(
        project_name = project_name,
        dataset_name = dataset_name,
        table_name = table_name,
        schema = bg_schema_fields,
    )


def print_schema(
    schema: Dict[str, Set[str]],
):
    bg_query_schema_builder = BigQuerySchemaBottomUpBuilder()
    bg_schema_fields = bg_query_schema_builder.build(
        schema_dict = schema,
    )
    for f in bg_schema_fields:
        print(f)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument(
        "-p", "--project",
        help = "specify the project name",
        type = str,
        default = "ripplex-ilee-pipeline",
    )
    arg_parser.add_argument(
        "-d", "--dataset",
        help = "specify dataset name",
        type = str,
        default = "raw_xrpl_data",
    )
    arg_parser.add_argument(
        "-t", "--table",
        help = "specify the table name",
        type = str,
        default = "xrpl_ledger_objects",
    )
    arg_parser.add_argument(
        "-s", "--schema",
        help = "specify the schema type",
        type = str,
        choices=["", "object", "transaction", "ledger"],
        default = "",
    )
    arg_parser.add_argument(
        "-ps", "--print",
        help = "print the specified schema",
        action="store_true",
    )
    arg_parser.add_argument(
        "-u", "--update",
        help = "update the table with the schema",
        action="store_true",
    )

    cli_args = arg_parser.parse_args()

    schema_dict = {
        "ledger": XRPLLedgerSchema.SCHEMA,
        "transaction": XRPLTransactionSchema.SCHEMA,
        "object": XRPLObjectSchema.SCHEMA,
    }

    schema = schema_dict.get(cli_args.schema)
    if not schema:
        sys.exit("[ERROR] Specify a valid schema. Given '%s'." % cli_args.schema)

    logger.warning("Using schema: ")
    print_schema(schema)

    if cli_args.print:
        print_schema(schema)

    elif cli_args.update:
        update_bigquery_table(
            project_name = cli_args.project,
            dataset_name = cli_args.dataset,
            table_name = cli_args.table,
            schema = schema,
        )

    else:
        build_bigquery_table(
            project_name = cli_args.project,
            dataset_name = cli_args.dataset,
            table_name = cli_args.table,
            schema = schema,
        )