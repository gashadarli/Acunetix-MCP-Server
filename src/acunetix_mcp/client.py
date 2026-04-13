"""Async HTTP client wrapper for the Acunetix REST API.

Handles:
- Authentication via X-Auth header
- SSL verification toggle (off by default for self-signed certs)
- Lazy config validation (validated on first HTTP call, not on import)
- API key masking in error messages
- Consistent response envelope: {"success": bool, "data": ..., "error": ...}
"""

import warnings
from typing import Any, Dict, Optional

import httpx

from .config import config

# Suppress SSL warnings for self-signed certificates
warnings.filterwarnings("ignore", message="Unverified HTTPS request")


class AcunetixClient:
    """Async HTTP client for the Acunetix Scanner API."""

    _validated: bool = False

    def __init__(self) -> None:
        self.base_url: str = ""  # populated lazily after validation
        self.verify_ssl: bool = False

    def _lazy_init(self) -> None:
        """Validate config and set up client parameters on first use.

        Called automatically before every HTTP request.
        Raises ValueError with a human-friendly message if config is missing.
        """
        if not self._validated:
            config.validate()            # may raise ValueError
            self.base_url = config.ACUNETIX_BASE_URL.rstrip("/")
            self.verify_ssl = config.VERIFY_SSL
            AcunetixClient._validated = True

    def _http_client(self) -> httpx.AsyncClient:
        """Create a configured httpx async client."""
        return httpx.AsyncClient(
            headers={
                "X-Auth": config.ACUNETIX_API_KEY,
                "Content-Type": "application/json",
            },
            verify=self.verify_ssl,
            timeout=60.0,
        )

    def _safe_error(self, response: httpx.Response) -> Dict[str, Any]:
        """Parse an error response, masking the API key if it appears."""
        try:
            body = response.json()
        except Exception:
            body = {"message": response.text}

        # Safety: never expose the raw API key in tool output
        body_str = str(body)
        if config.ACUNETIX_API_KEY and config.ACUNETIX_API_KEY in body_str:
            body_str = body_str.replace(config.ACUNETIX_API_KEY, "***REDACTED***")
            body = {"message": body_str}

        return {
            "success": False,
            "status_code": response.status_code,
            "error": body,
        }

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Convert an httpx Response to a consistent result dict."""
        if response.status_code in (200, 201):
            try:
                return {"success": True, "data": response.json()}
            except Exception:
                return {"success": True, "data": response.text}
        elif response.status_code in (203, 204):
            return {"success": True, "data": None, "message": "Operation completed successfully"}
        elif response.status_code == 302:
            return {
                "success": True,
                "data": None,
                "location": response.headers.get("Location"),
                "message": "Redirect",
            }
        else:
            return self._safe_error(response)

    # ── Public HTTP methods ───────────────────────────────────────────────────

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform a GET request."""
        self._lazy_init()
        async with self._http_client() as client:
            response = await client.get(
                f"{self.base_url}{path}",
                params={k: v for k, v in (params or {}).items() if v is not None},
            )
            return self._handle_response(response)

    async def post(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform a POST request."""
        self._lazy_init()
        async with self._http_client() as client:
            response = await client.post(
                f"{self.base_url}{path}",
                json=body,
                params={k: v for k, v in (params or {}).items() if v is not None},
            )
            return self._handle_response(response)

    async def patch(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform a PATCH request."""
        self._lazy_init()
        async with self._http_client() as client:
            response = await client.patch(f"{self.base_url}{path}", json=body)
            return self._handle_response(response)

    async def put(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform a PUT request."""
        self._lazy_init()
        async with self._http_client() as client:
            response = await client.put(f"{self.base_url}{path}", json=body)
            return self._handle_response(response)

    async def delete(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform a DELETE request (with optional JSON body)."""
        self._lazy_init()
        async with self._http_client() as client:
            response = await client.request(
                method="DELETE",
                url=f"{self.base_url}{path}",
                json=body,
            )
            return self._handle_response(response)


# Module-level singleton — shared by all tool modules.
acunetix = AcunetixClient()
