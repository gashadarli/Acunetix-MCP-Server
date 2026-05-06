"""Register fixed MCP tools for every operation in the Acunetix OpenAPI spec."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import fastmcp
import yaml

from ..audit import audit_event
from ..client import acunetix
from ..policy import PolicyEngine, policy_error
from .common import validate_limit, validate_uuid


HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
MUTATING_METHODS = {"post", "put", "patch", "delete"}
SPEC_RESOURCE = "Acunetix-API-Documentation.yaml"


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    name: str
    location: str
    required: bool = False
    kind: str | None = None
    fmt: str | None = None


@dataclass(frozen=True, slots=True)
class OperationSpec:
    method: str
    path: str
    operation_id: str
    tool_name: str
    summary: str
    description: str
    parameters: tuple[ParameterSpec, ...]
    has_body: bool

    @property
    def path_parameters(self) -> tuple[ParameterSpec, ...]:
        return tuple(p for p in self.parameters if p.location == "path")

    @property
    def query_parameters(self) -> tuple[ParameterSpec, ...]:
        return tuple(p for p in self.parameters if p.location == "query")


def load_openapi_spec() -> dict[str, Any]:
    import importlib.resources as resources

    with resources.files("acunetix_mcp").joinpath(SPEC_RESOURCE).open(
        "r",
        encoding="utf-8",
    ) as handle:
        return yaml.safe_load(handle)


def _resolve_ref(spec: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    ref = item.get("$ref")
    if not ref:
        return item
    if not ref.startswith("#/"):
        return item
    current: Any = spec
    for part in ref[2:].split("/"):
        current = current[part]
    return current


def _operation_id(method: str, path: str, operation: dict[str, Any]) -> str:
    raw = operation.get("operationId")
    if raw:
        return _snake(raw)
    text = f"{method}_{path.strip('/') or 'root'}"
    text = text.replace("{", "").replace("}", "")
    return _snake(text.replace("/", "_"))


def _snake(value: str) -> str:
    value = re.sub(r"[^0-9a-zA-Z]+", "_", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return re.sub(r"_+", "_", value).strip("_").lower()


def _singular(noun: str) -> str:
    irregular = {
        "children": "child",
        "indices": "index",
        "statuses": "status",
    }
    if noun in irregular:
        return irregular[noun]
    if noun.endswith("ies"):
        return noun[:-3] + "y"
    if noun.endswith("sses"):
        return noun[:-2]
    if noun.endswith("s") and not noun.endswith("ss"):
        return noun[:-1]
    return noun


def _friendly_name(method: str, path: str, operation_id: str) -> str:
    method = method.lower()
    pieces = [part for part in path.strip("/").split("/") if part and not part.startswith("{")]
    resource = pieces[-1] if pieces else "root"
    singular = _singular(resource)
    has_path_params = "{" in path

    if method == "get" and not has_path_params:
        return f"list_{resource}"
    if method == "get" and operation_id.startswith("get_"):
        return operation_id
    if method == "post" and operation_id.startswith(("add_", "create_")):
        return f"create_{operation_id.split('_', 1)[1]}"
    if method == "delete" and operation_id.startswith(("remove_", "delete_")):
        return f"delete_{operation_id.split('_', 1)[1]}"
    if operation_id.startswith("remove_"):
        return f"delete_{operation_id.split('_', 1)[1]}"
    if operation_id == "generate_new_report":
        return "generate_report"
    if method in {"put", "patch"} and not operation_id.startswith(("update_", "set_", "configure_")):
        return f"update_{singular}"
    return operation_id


def build_operation_catalog() -> list[OperationSpec]:
    spec = load_openapi_spec()
    operations: list[OperationSpec] = []
    used_names: dict[str, int] = {}

    for path, path_item in sorted(spec.get("paths", {}).items()):
        path_item = path_item or {}
        path_params = [_resolve_ref(spec, p) for p in path_item.get("parameters", [])]
        for method, operation in sorted(path_item.items()):
            if method.lower() not in HTTP_METHODS:
                continue
            method = method.lower()
            operation = operation or {}
            operation_id = _operation_id(method, path, operation)
            base_name = _friendly_name(method, path, operation_id)
            tool_name = base_name
            if tool_name in used_names:
                used_names[base_name] += 1
                domain = path.strip("/").split("/", 1)[0] or "root"
                tool_name = f"{base_name}__{_snake(domain)}_{used_names[base_name]}"
            else:
                used_names[base_name] = 1

            raw_params = path_params + [
                _resolve_ref(spec, p) for p in operation.get("parameters", [])
            ]
            parameters: list[ParameterSpec] = []
            has_body = False
            for param in raw_params:
                location = param.get("in")
                name = param.get("name")
                if not name or not location:
                    continue
                if location == "body":
                    has_body = True
                    continue
                schema = param.get("schema") or {}
                parameters.append(
                    ParameterSpec(
                        name=name,
                        location=location,
                        required=bool(param.get("required")),
                        kind=param.get("type") or schema.get("type"),
                        fmt=param.get("format") or schema.get("format"),
                    )
                )

            operations.append(
                OperationSpec(
                    method=method,
                    path=path,
                    operation_id=operation_id,
                    tool_name=tool_name,
                    summary=operation.get("summary") or operation_id,
                    description=operation.get("description") or "",
                    parameters=tuple(parameters),
                    has_body=has_body,
                )
            )

    return operations


def coverage_report(registered_tool_names: set[str]) -> dict[str, Any]:
    catalog = build_operation_catalog()
    covered = [op for op in catalog if op.tool_name in registered_tool_names]
    missing = [op for op in catalog if op.tool_name not in registered_tool_names]
    return {
        "documented_operations": len(catalog),
        "implemented_operations": len(covered),
        "missing_operations": len(missing),
        "missing": [
            {"method": op.method.upper(), "path": op.path, "tool": op.tool_name}
            for op in missing
        ],
    }


def register_openapi_tools(
    mcp: fastmcp.FastMCP,
    *,
    skip_names: set[str] | None = None,
) -> list[OperationSpec]:
    skip_names = skip_names or set()
    registered: list[OperationSpec] = []
    for operation in build_operation_catalog():
        if operation.tool_name in skip_names:
            continue
        _register_operation_tool(mcp, operation)
        registered.append(operation)
    return registered


def _register_operation_tool(mcp: fastmcp.FastMCP, operation: OperationSpec) -> None:
    description = _tool_description(operation)

    @mcp.tool(name=operation.tool_name, description=description)
    async def openapi_operation_tool(
        path_params: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: str | None = None,
        confirmation: bool = False,
    ) -> dict[str, Any]:
        return await _call_operation(
            operation,
            path_params=path_params,
            query=query,
            body=body,
            limit=limit,
            offset=offset,
            confirmation=confirmation,
        )


def _tool_description(operation: OperationSpec) -> str:
    path_params = ", ".join(p.name for p in operation.path_parameters) or "none"
    query_params = ", ".join(p.name for p in operation.query_parameters) or "none"
    parts = [
        f"{operation.summary}.",
        f"Maps to {operation.method.upper()} {operation.path}.",
        f"Path parameters: {path_params}.",
        f"Query parameters may be passed in query; documented query parameters: {query_params}.",
    ]
    if operation.has_body:
        parts.append("Request body is passed as body.")
    if operation.method in MUTATING_METHODS:
        parts.append("This mutating operation is policy-protected and requires confirmation when configured.")
    return " ".join(parts)


async def _call_operation(
    operation: OperationSpec,
    *,
    path_params: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    limit: int | None = None,
    offset: str | None = None,
    confirmation: bool = False,
) -> dict[str, Any]:
    path_params = dict(path_params or {})
    query_params = dict(query or {})

    path = operation.path
    for param in operation.path_parameters:
        if param.name not in path_params:
            return _validation_error(f"Missing required path parameter: {param.name}")
        value = str(path_params[param.name])
        if param.fmt == "uuid" or param.name.endswith("_id"):
            error = validate_uuid(value, param.name)
            if error:
                return error
        path = path.replace("{" + param.name + "}", value)

    if limit is not None:
        query_params["l"] = validate_limit(limit)
    elif "l" in query_params:
        query_params["l"] = validate_limit(query_params.get("l"))
    if offset is not None:
        query_params["c"] = offset

    if operation.method in MUTATING_METHODS:
        policy = PolicyEngine()
        decision = policy.check_action(operation.tool_name, confirmed=confirmation)
        audit_event(
            operation.tool_name,
            allowed=decision.allowed,
            reason=decision.reason,
            details={
                "method": operation.method.upper(),
                "path": operation.path,
                "path_params": path_params,
            },
        )
        if not decision.allowed:
            return policy_error(decision)

    if operation.method == "get":
        return await acunetix.get(path, params=query_params)
    if operation.method == "post":
        return await acunetix.post(path, body=body, params=query_params)
    if operation.method == "put":
        return await acunetix.put(path, body=body)
    if operation.method == "patch":
        return await acunetix.patch(path, body=body)
    if operation.method == "delete":
        return await acunetix.delete(path, body=body)
    return _validation_error(f"Unsupported method: {operation.method}")


def _validation_error(message: str) -> dict[str, Any]:
    return {
        "success": False,
        "error": {
            "message": message,
            "type": "ValidationError",
        },
    }
