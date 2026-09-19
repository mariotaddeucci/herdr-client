"""Generate TypedDict models from the checked-in Herdr JSON Schema."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "herdr-api.schema.json"
OUTPUT_PATH = ROOT / "src/herdr_client/generated_types.py"
MAX_INLINE_TYPE_LENGTH = 76

PREFIXES = {
    "request": "Request",
    "success_response": "Response",
    "error_response": "Error",
    "event": "Event",
}

type SchemaPrimitive = bool | int | float | str | None
type SchemaValue = SchemaPrimitive | list[SchemaValue] | dict[str, SchemaValue]
type SchemaNode = bool | dict[str, SchemaValue]


def identifier(value: str) -> str:
    identifier = re.sub(r"[^a-zA-Z0-9_]", "_", value)
    if identifier != "" and identifier[0].isdigit():
        identifier = f"_{identifier}"
    return identifier


def pascal_name(value: str) -> str:
    parts = re.split(r"[^a-zA-Z0-9]+", value)
    return "".join(part[:1].upper() + part[1:] for part in parts if part != "")


def ref_name(ref: str) -> str:
    match = re.fullmatch(r"#/schemas/([^/]+)/\$defs/([^/]+)", ref)
    if match is None:
        return "JsonObject"
    section, name = match.groups()
    prefix = PREFIXES.get(section, "")
    return f"{prefix}{identifier(name)}"


def literal_value(value: object) -> str:
    return repr(value)


def literal_type(values: Sequence[object]) -> str:
    rendered = ", ".join(literal_value(value) for value in values)
    if len(rendered) <= MAX_INLINE_TYPE_LENGTH:
        return f"Literal[{rendered}]"
    return (
        "Literal[\n"
        + "".join(f"    {literal_value(value)},\n" for value in values)
        + "]"
    )


def union_types(types: list[str]) -> str:
    unique = list(dict.fromkeys(types))
    if len(unique) == 0:
        return "JsonObject"
    if len(unique) == 1:
        return unique[0]
    rendered = " | ".join(unique)
    if len(rendered) <= MAX_INLINE_TYPE_LENGTH:
        return rendered
    return (
        "(\n    "
        + unique[0]
        + "\n"
        + "\n".join(f"    | {item}" for item in unique[1:])
        + "\n)"
    )


def schema_object(value: object) -> dict[str, SchemaValue]:
    if not isinstance(value, dict):
        raise TypeError("schema value must be an object")
    return cast("dict[str, SchemaValue]", value)


def schema_node(value: object) -> SchemaNode:
    if isinstance(value, bool):
        return value
    return schema_object(value)


def schema_nodes(value: object) -> list[SchemaNode]:
    if not isinstance(value, list):
        raise TypeError("schema union must be an array")
    return [schema_node(cast(object, item)) for item in value]


def schema_objects(value: object) -> dict[str, dict[str, SchemaValue]]:
    values = schema_object(value)
    return {key: schema_object(item) for key, item in values.items()}


def required_string(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"schema field {field!r} must be a string")
    return value


def required_strings(value: object, field: str) -> set[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeError(f"schema field {field!r} must be an array of strings")
    return set(cast("list[str]", value))


def type_expr(node: SchemaNode) -> str:
    if isinstance(node, bool):
        return "JSONValue"
    if not isinstance(node, dict):
        return "JsonObject"
    reference = node.get("$ref")
    if reference is not None:
        return ref_name(required_string(reference, "$ref"))
    if "const" in node:
        return f"Literal[{literal_value(node['const'])}]"
    enum_values = node.get("enum")
    if enum_values is not None:
        if not isinstance(enum_values, list):
            raise TypeError("schema enum must be an array")
        return literal_type(enum_values)
    for union_key in ("oneOf", "anyOf"):
        variants = node.get(union_key)
        if variants is not None:
            return union_types([type_expr(item) for item in schema_nodes(variants)])

    return type_expr_for_schema(node)


def type_expr_for_schema(node: dict[str, SchemaValue]) -> str:
    schema_type = node.get("type")
    if isinstance(schema_type, list):
        types = [required_string(item, "type") for item in schema_type]
        return union_types([type_expr({"type": item}) for item in types])

    primitive_types = {
        "null": "None",
        "boolean": "bool",
        "integer": "int",
        "number": "int",
        "string": "str",
    }
    if schema_type in primitive_types:
        return primitive_types[schema_type]
    if schema_type == "array":
        return f"list[{type_expr(schema_node(node.get('items', {})))}]"
    if schema_type == "object":
        additional = node.get("additionalProperties")
        if isinstance(additional, dict):
            return f"dict[str, {type_expr(schema_node(additional))}]"
        return "JsonObject"
    return "JsonObject"


def render_object_class(
    class_name: str,
    properties: dict[str, SchemaNode],
    required_fields: set[str],
) -> list[str]:
    total = required_fields == set(properties)
    suffix = "" if total else ", total=False"
    lines = [f"class {class_name}(TypedDict{suffix}):"]
    if len(properties) == 0:
        lines.append("    pass")
    else:
        for field, field_schema in properties.items():
            field_name = identifier(field)
            field_type = type_expr(field_schema)
            if not total:
                marker = "Required" if field in required_fields else "NotRequired"
                field_type = f"{marker}[{field_type}]"
            lines.append(f"    {field_name}: {field_type}")
    lines.append("")
    return lines


def render_definition(
    name: str, definition: dict[str, SchemaValue], section: str
) -> list[str]:
    prefix = PREFIXES[section]
    class_name = f"{prefix}{identifier(name)}"
    variants_value = definition.get("oneOf")
    if variants_value is None:
        variants_value = definition.get("anyOf")
    if isinstance(variants_value, list) and len(variants_value) > 0:
        variants = schema_nodes(variants_value)
        lines: list[str] = []
        variant_names: list[str] = []
        for index, variant in enumerate(variants, start=1):
            if isinstance(variant, bool):
                variant_names.append(type_expr(variant))
                continue
            properties_value = variant.get("properties")
            if isinstance(properties_value, dict):
                variant_name = f"{class_name}Variant{index}"
                lines.extend(
                    render_object_class(
                        variant_name,
                        {
                            field: schema_node(field_schema)
                            for field, field_schema in schema_object(
                                properties_value
                            ).items()
                        },
                        required_strings(variant.get("required", []), "required"),
                    )
                )
                variant_names.append(variant_name)
            else:
                variant_names.append(type_expr(variant))
        lines.append(f"type {class_name} = {union_types(variant_names)}")
        lines.append("")
        return lines

    if "properties" not in definition or not isinstance(
        definition.get("properties"), dict
    ):
        return [f"type {class_name} = {type_expr(definition)}", ""]

    properties = {
        field: schema_node(field_schema)
        for field, field_schema in schema_object(definition["properties"]).items()
    }
    return render_object_class(
        class_name,
        properties,
        required_strings(definition.get("required", []), "required"),
    )


def render(schema: dict[str, SchemaValue]) -> str:
    lines = [
        "# This file is generated by tools/generate_models.py. Do not edit.",
        '"""Generated TypedDict models from the pinned Herdr JSON Schema."""',
        "",
        "from __future__ import annotations",
        "",
        "from collections.abc import Mapping",
        "from typing import Literal, NotRequired, Required, TypedDict",
        "",
        "type JSONScalar = bool | int | float | str | None",
        "type JSONValue = JSONScalar | list[JSONValue] | Mapping[str, JSONValue]",
        "type JsonObject = dict[str, JSONValue]",
        "",
    ]

    for section in ("request", "success_response", "error_response", "event"):
        section_schema = schema_objects(schema["schemas"]).get(section, {})
        definitions = schema_objects(section_schema.get("$defs", {}))
        if len(definitions) == 0:
            continue
        lines.append(f"# {section} definitions")
        lines.append("")
        for name, definition in definitions.items():
            lines.extend(render_definition(name, definition, section))
            lines.append("")

    lines.extend(["# Discriminated aliases", ""])
    for section, definition_name in (
        ("success_response", "ResponseResult"),
        ("event", "EventData"),
    ):
        section_schema = schema_objects(schema["schemas"]).get(section, {})
        definitions = schema_objects(section_schema.get("$defs", {}))
        definition = definitions.get(definition_name, {})
        for index, variant in enumerate(
            schema_nodes(definition.get("oneOf", [])), start=1
        ):
            if isinstance(variant, bool):
                continue
            properties = schema_object(variant.get("properties", {}))
            variant_type = schema_object(properties.get("type", {})).get("const")
            if isinstance(variant_type, str):
                alias_name = f"{definition_name}{pascal_name(variant_type)}"
                class_name = (
                    f"{PREFIXES[section]}{identifier(definition_name)}Variant{index}"
                )
                lines.append(f"type {alias_name} = {class_name}")
        lines.append("")

    request_methods: list[str] = []
    request_params: list[str] = []
    request_schema = schema_objects(schema["schemas"])["request"]
    for request_node in schema_nodes(request_schema["oneOf"]):
        if isinstance(request_node, bool):
            raise TypeError("request schema variant must be an object")
        properties = schema_object(request_node["properties"])
        method = required_string(schema_object(properties["method"])["const"], "const")
        params_ref = required_string(
            schema_object(properties["params"])["$ref"], "$ref"
        )
        request_methods.append(method)
        request_params.append(ref_name(params_ref))

    lines.extend(
        [
            "# Top-level schema unions",
            "",
            f"type RequestMethod = {literal_type(request_methods)}",
            f"type RequestParams = {union_types(request_params)}",
            "",
        ]
    )
    return "\n".join(lines)


def format_generated(source: str) -> str:
    completed = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--stdin-filename",
            str(OUTPUT_PATH),
            "-",
        ],
        input=source,
        capture_output=True,
        check=True,
        text=True,
    )
    return completed.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    check_argument = parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the generated artifact differs from the schema",
    )
    del check_argument
    args = parser.parse_args()
    decoded: object = json.loads(SCHEMA_PATH.read_text())
    schema = schema_object(decoded)
    output = format_generated(render(schema))

    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text() != output:
            raise SystemExit(f"generated models are stale: {OUTPUT_PATH}")
        return

    characters_written = OUTPUT_PATH.write_text(output)
    del characters_written


if __name__ == "__main__":
    main()
