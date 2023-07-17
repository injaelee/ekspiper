import pyarrow as pa
import logging

from typing import Dict, List, Set
from collections import namedtuple

IntermediateNode = namedtuple("IntermediateNode", ["prefix", "name", "obj"])
logger = logging.getLogger(__name__)


class ParquetSchemaGenerator:
    def __init__(self):
        self.to_data_type: Dict[type, pa.DataType] = {
            int: pa.int32(),
            float: pa.float32(),
            str: pa.string(),
            bool: pa.bool_(),
        }

    def _type_to_data_type(self,
                           python_type: type,
                           ) -> pa.DataType:
        return self.to_data_type.get(python_type)

    def build_from_stack(self,
                         obj_stack: List[IntermediateNode],
                         ) -> List[pa.field]:
        built_fields: List[pa.field] = []
        named_google_schema_fields: Dict[str, List[pa.field]] = {}

        while len(obj_stack) > 0:
            current_node = obj_stack.pop()

            # parent found: create the parent
            if current_node.obj in {list, dict}:  # prev_node and current_node.name == prev_node.prefix:

                key_name = current_node.name[len(current_node.prefix):]

                # remove the '.' if there is one
                key_name = key_name[1:] if key_name[0] == '.' else key_name

                google_schema_fields = named_google_schema_fields.get(current_node.name, [])
                if current_node.obj == dict:
                    type = pa.struct(named_google_schema_fields.get(current_node.name, []))
                else:
                    type = pa.list_(pa.string() if not google_schema_fields else pa.struct(google_schema_fields))

                obj_stack.append(IntermediateNode(
                    prefix=current_node.prefix,
                    name=current_node.name,
                    obj=pa.field(
                        key_name,
                        type)
                ))

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

        return built_fields

    def build(self,
              schema_dict: Dict[str, Set[type]],
              ) -> [pa.field]:

        obj_stack: List[IntermediateNode] = []

        for full_key in sorted(schema_dict.keys()):
            tokens = full_key.split(".")

            prefix_key = ".".join(tokens[:-1])

            key = tokens[-1]
            logger.debug(f"{prefix_key} - {key}")

            data_type_set = schema_dict.get(full_key)

            if data_type_set.intersection({dict, list}):
                obj = list if list in data_type_set else dict
            else:
                python_type = next(iter(data_type_set))
                bg_data_type = self._type_to_data_type(
                    python_type=python_type,
                )
                obj = pa.field(key, bg_data_type)

            obj_stack.append(IntermediateNode(
                prefix=prefix_key,
                name=full_key,
                obj=obj,
            ))

        built_fields: List[pa.field] = self.build_from_stack(
            obj_stack=obj_stack,
        )
        return built_fields
