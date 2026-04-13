"""Async HTTP client wrapper for Acunetix API."""

import base64
import warnings
from typing import Any, Dict, Optional

import httpx

from .config import config

# Suppress SSL warnings for self-signed certificates
warnings.filterwarnings("ignore", message="Unverified HTTPS request")


class AcunetixClient:
    """Async HTTP client for Acunetix Scanner API."""

    def __init__(self):
        self.base_url = config.ACUNETIX_BASE_URL.rstrip("/")
        self.headers = {
            "X-Auth": config.ACUNETIX_API_KEY,
            "Content-Type": "application/json",
        }
        self.verify_ssl = config.VERIFY_SSL

    def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers=self.headers,
            verify=self.verify_ssl,
            timeout=60.0,
        )

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform an async GET request."""
        async with self._get_client() as client:
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
        """Perform an async POST request."""
        async with self._get_client() as client:
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
        """Perform an async PATCH request."""
        async with self._get_client() as client:
            response = await client.patch(
                f"{self.base_url}{path}",
                json=body,
            )
            return self._handle_response(response)

    async def put(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform an async PUT request."""
        async with self._get_client() as client:
            response = await client.put(
                f"{self.base_url}{path}",
                json=body,
            )
            return self._handle_response(response)

    async def delete(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform an async DELETE request."""
        async with self._get_client() as client:
            response = await client.request(
                method="DELETE",
                url=f"{self.base_url}{path}",
                json=body,
            )
            return self._handle_response(response)

    async def download(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Download a binary file and return it as base64-encoded data."""
        async with self._get_client() as client:
            response = await client.get(
                f"{self.base_url}{path}",
                params={k: v for k, v in (params or {}).items() if v is not None},
            )
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "application/octet-stream")
                content_disposition = response.headers.get("content-disposition", "")
                filename = ""
                if "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[-1].strip('" ')
                return {
                    "success": True,
                    "data": {
                        "content_base64": base64.b64encode(response.content).decode(),
                        "content_type": content_type,
                        "filename": filename,
                        "size_bytes": len(response.content),
                    },
                }
            else:
                try:
                    error_data = response.json()
                except Exception:
                    error_data = {"message": response.text}
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": error_data,
                }

    async def upload_init(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Initiate a file upload (step 1 of 2-step upload process).

        Returns a temporary upload URL where the actual file should be POSTed.
        """
        return await self.post(path, body=body)

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response and return parsed JSON or status info."""
        if response.status_code in (200, 201):
            try:
                return {"success": True, "data": response.json()}
            except Exception:
                return {"success": True, "data": response.text}
        elif response.status_code in (204, 203):
            return {"success": True, "data": None, "message": "Operation completed successfully"}
        elif response.status_code == 302:
            return {
                "success": True,
                "data": None,
                "location": response.headers.get("Location"),
                "message": "Redirect",
            }
        else:
            try:
                error_data = response.json()
            except Exception:
                error_data = {"message": response.text}
            return {
                "success": False,
                "status_code": response.status_code,
                "error": error_data,
            }


# Singleton client instance
acunetix = AcunetixClient()
