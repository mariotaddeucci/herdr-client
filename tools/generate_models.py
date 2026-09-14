"""Generate TypedDict models from the checked-in Herdr JSON Schema."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "herdr-api.schema.json"
OUTPUT_PATH = ROOT / "src/herdr_client/generated_types.py"

_PREFIXES = {
    "request": "Request",
    "success_response": "Response",
    "error_response": "Error",
    "event": "Event",
}


def _identifier(value: str) -> str:
    identifier = re.sub(r"[^a-zA-Z0-9_]", "_", value)
    if identifier and identifier[0].isdigit():
        identifier = f"_{identifier}"
    return identifier


def _pascal_name(value: str) -> str:
    parts = re.split(r"[^a-zA-Z0-9]+", value)
    return "".join(part[:1].upper() + part[1:] for part in parts if part)


def _ref_name(ref: str) -> str:
    match = re.fullmatch(r"#/schemas/([^/]+)/\$defs/([^/]+)", ref)
    if match is None:
        return "JsonObject"
    section, name = match.groups()
    prefix = _PREFIXES.get(section, "")
    return f"{prefix}{_identifier(name)}"


def _literal(value: object) -> str:
    return repr(value)


def _literal_type(values: list[object]) -> str:
    rendered = ", ".join(_literal(value) for value in values)
    if len(rendered) <= 76:
        return f"Literal[{rendered}]"
    return "Literal[\n" + "".join(f"    {_literal(value)},\n" for value in values) + "]"


def _union(types: list[str]) -> str:
    unique = list(dict.fromkeys(types))
    if not unique:
        return "JsonObject"
    if len(unique) == 1:
        return unique[0]
    rendered = " | ".join(unique)
    if len(rendered) <= 76:
        return rendered
    return (
        "(\n    "
        + unique[0]
        + "\n"
        + "\n".join(f"    | {item}" for item in unique[1:])
        + "\n)"
    )


def _type_expr(node: dict[str, Any] | bool) -> str:
    if isinstance(node, bool):
        return "JSONValue"
    if not isinstance(node, dict):
        return "JsonObject"
    if "$ref" in node:
        return _ref_name(node["$ref"])
    if "const" in node:
        return f"Literal[{_literal(node['const'])}]"
    if "enum" in node:
        return _literal_type(node["enum"])
    for union_key in ("oneOf", "anyOf"):
        if union_key in node:
            return _union([_type_expr(item) for item in node[union_key]])

    return _type_expr_for_schema(node)


def _type_expr_for_schema(node: dict[str, Any]) -> str:
    schema_type = node.get("type")
    if isinstance(schema_type, list):
        return _union([_type_expr({"type": item}) for item in schema_type])

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
        return f"list[{_type_expr(node.get('items', {}))}]"
    if schema_type == "object":
        additional = node.get("additionalProperties")
        if isinstance(additional, dict):
            return f"dict[str, {_type_expr(additional)}]"
        return "JsonObject"
    return "JsonObject"


def _render_object_class(
    class_name: str, properties: dict[str, Any], required_fields: set[str]
) -> list[str]:
    total = required_fields == set(properties)
    suffix = "" if total else ", total=False"
    lines = [f"class {class_name}(TypedDict{suffix}):"]
    if not properties:
        lines.append("    pass")
    else:
        for field, field_schema in properties.items():
            field_name = _identifier(field)
            field_type = _type_expr(field_schema)
            if not total:
                marker = "Required" if field in required_fields else "NotRequired"
                field_type = f"{marker}[{field_type}]"
            lines.append(f"    {field_name}: {field_type}")
    lines.append("")
    return lines


def _render_definition(
    name: str, definition: dict[str, Any], section: str
) -> list[str]:
    prefix = _PREFIXES[section]
    class_name = f"{prefix}{_identifier(name)}"
    variants = definition.get("oneOf") or definition.get("anyOf")
    if isinstance(variants, list) and variants:
        lines: list[str] = []
        variant_names: list[str] = []
        for index, variant in enumerate(variants, start=1):
            properties = variant.get("properties")
            if isinstance(properties, dict):
                variant_name = f"{class_name}Variant{index}"
                lines.extend(
                    _render_object_class(
                        variant_name,
                        properties,
                        set(variant.get("required", ())),
                    )
                )
                variant_names.append(variant_name)
            else:
                variant_names.append(_type_expr(variant))
        lines.append(f"type {class_name} = {_union(variant_names)}")
        lines.append("")
        return lines

    if "properties" not in definition or not isinstance(
        definition.get("properties"), dict
    ):
        return [f"type {class_name} = {_type_expr(definition)}", ""]

    properties = definition["properties"]
    return _render_object_class(
        class_name, properties, set(definition.get("required", ()))
    )


def render(schema: dict[str, Any]) -> str:
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
        definitions = schema["schemas"].get(section, {}).get("$defs", {})
        if not definitions:
            continue
        lines.append(f"# {section} definitions")
        lines.append("")
        for name, definition in definitions.items():
            lines.extend(_render_definition(name, definition, section))
            lines.append("")

    lines.extend(["# Discriminated aliases", ""])
    for section, definition_name in (
        ("success_response", "ResponseResult"),
        ("event", "EventData"),
    ):
        definition = (
            schema["schemas"].get(section, {}).get("$defs", {}).get(definition_name, {})
        )
        for index, variant in enumerate(definition.get("oneOf", ()), start=1):
            variant_type = variant.get("properties", {}).get("type", {}).get("const")
            if isinstance(variant_type, str):
                alias_name = f"{definition_name}{_pascal_name(variant_type)}"
                class_name = (
                    f"{_PREFIXES[section]}{_identifier(definition_name)}Variant{index}"
                )
                lines.append(f"type {alias_name} = {class_name}")
        lines.append("")

    request_methods = []
    request_params = []
    for request in schema["schemas"]["request"]["oneOf"]:
        properties = request["properties"]
        method = properties["method"]["const"]
        params_ref = properties["params"]["$ref"]
        request_methods.append(method)
        request_params.append(_ref_name(params_ref))

    lines.extend(
        [
            "# Top-level schema unions",
            "",
            f"type RequestMethod = {_literal_type(request_methods)}",
            f"type RequestParams = {_union(request_params)}",
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
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the generated artifact differs from the schema",
    )
    args = parser.parse_args()
    schema = json.loads(SCHEMA_PATH.read_text())
    output = format_generated(render(schema))

    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text() != output:
            raise SystemExit(f"generated models are stale: {OUTPUT_PATH}")
        return

    OUTPUT_PATH.write_text(output)


if __name__ == "__main__":
    main()
