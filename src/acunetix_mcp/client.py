"""Async Acunetix REST API client used by MCP tools."""

from __future__ import annotations

from typing import Any, Mapping

import httpx

from .config import Settings, load_settings, mask_secret


JsonDict = dict[str, Any]


def _sanitize(value: Any, secret: str | None) -> Any:
    """Recursively redact secrets from structured response/error values."""
    if isinstance(value, str):
        return mask_secret(value, secret)
    if isinstance(value, list):
        return [_sanitize(item, secret) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize(item, secret) for item in value)
    if isinstance(value, Mapping):
        sanitized: JsonDict = {}
        for key, item in value.items():
            if str(key).lower() in {"x-auth", "authorization", "api_key", "api-key"}:
                sanitized[str(key)] = "***REDACTED***"
            else:
                sanitized[str(key)] = _sanitize(item, secret)
        return sanitized
    return value


class AcunetixClient:
    """Small typed wrapper around the Acunetix REST API.

    The client intentionally exposes HTTP verbs only to internal tool modules.
    No generic MCP proxy tool is registered.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self._transport = transport

    def _settings(self) -> Settings:
        settings = self.settings or load_settings()
        settings.validate()
        return settings

    def _timeout(self, settings: Settings) -> httpx.Timeout:
        return httpx.Timeout(settings.request_timeout_seconds)

    def _http_client(self, settings: Settings) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers={
                "X-Auth": settings.acunetix_api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            verify=settings.acunetix_verify_ssl,
            timeout=self._timeout(settings),
            transport=self._transport,
        )

    def _parse_body(self, response: httpx.Response, settings: Settings) -> Any:
        if not response.content:
            return None
        try:
            return _sanitize(response.json(), settings.acunetix_api_key)
        except ValueError:
            return _sanitize(response.text, settings.acunetix_api_key)

    def _handle_response(self, response: httpx.Response, settings: Settings) -> JsonDict:
        body = self._parse_body(response, settings)
        result: JsonDict = {
            "success": 200 <= response.status_code < 300,
            "status_code": response.status_code,
        }

        if result["success"]:
            result["data"] = body
            location = response.headers.get("Location")
            if location:
                result["location"] = _sanitize(location, settings.acunetix_api_key)
            return result

        result["error"] = {
            "message": self._error_message(body, response.status_code),
            "details": body,
        }
        return result

    @staticmethod
    def _error_message(body: Any, status_code: int) -> str:
        if isinstance(body, Mapping):
            for key in ("message", "reason", "error", "description"):
                if key in body and body[key]:
                    return str(body[key])
        if isinstance(body, str) and body.strip():
            return body.strip()
        return f"Acunetix API returned HTTP {status_code}"

    def _exception_result(self, exc: Exception, settings: Settings | None = None) -> JsonDict:
        secret = settings.acunetix_api_key if settings else None
        return {
            "success": False,
            "status_code": None,
            "error": {
                "message": _sanitize(str(exc), secret),
                "type": exc.__class__.__name__,
            },
        }

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
    ) -> JsonDict:
        settings: Settings | None = None
        try:
            settings = self._settings()
            clean_path = path if path.startswith("/") else f"/{path}"
            clean_params = {
                key: value
                for key, value in (params or {}).items()
                if value is not None and value != ""
            }
            async with self._http_client(settings) as client:
                response = await client.request(
                    method=method.upper(),
                    url=f"{settings.api_base_url}{clean_path}",
                    params=clean_params,
                    json=body,
                )
            return self._handle_response(response, settings)
        except (ValueError, httpx.HTTPError) as exc:
            return self._exception_result(exc, settings)

    async def get(self, path: str, params: Mapping[str, Any] | None = None) -> JsonDict:
        return await self.request("GET", path, params=params)

    async def post(
        self,
        path: str,
        body: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> JsonDict:
        return await self.request("POST", path, params=params, body=body)

    async def put(self, path: str, body: Mapping[str, Any] | None = None) -> JsonDict:
        return await self.request("PUT", path, body=body)

    async def patch(self, path: str, body: Mapping[str, Any] | None = None) -> JsonDict:
        return await self.request("PATCH", path, body=body)

    async def delete(self, path: str, body: Mapping[str, Any] | None = None) -> JsonDict:
        return await self.request("DELETE", path, body=body)

    async def health(self) -> JsonDict:
        """Check configuration and authenticated read-only API reachability."""
        settings: Settings | None = None
        try:
            settings = self._settings()
        except ValueError as exc:
            return {
                "success": False,
                "configured": False,
                "error": {"message": str(exc), "type": exc.__class__.__name__},
            }

        result = await self.get("/target_groups", params={"l": 1})
        health: JsonDict = {
            "success": bool(result.get("success")),
            "configured": True,
            "api_base_url": settings.api_base_url,
            "verify_ssl": settings.acunetix_verify_ssl,
            "read_only": settings.read_only,
            "api_status_code": result.get("status_code"),
        }
        if not result.get("success"):
            health["error"] = result.get("error")
        return health


acunetix = AcunetixClient()
