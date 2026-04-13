"""Target management MCP tools."""

from typing import Any, Dict, List, Optional
import fastmcp

from ..client import acunetix


def register_target_tools(mcp: fastmcp.FastMCP):

    @mcp.tool()
    async def get_targets(
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        query: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a list of all Scan Targets.
        Use query parameter to filter (e.g., 'text:example.com').
        """
        return await acunetix.get(
            "/targets",
            params={"c": cursor, "l": limit, "q": query, "s": sort},
        )

    @mcp.tool()
    async def add_target(
        address: str,
        description: Optional[str] = None,
        type: Optional[str] = "default",
        criticality: Optional[int] = 10,
    ) -> Dict[str, Any]:
        """
        Create a new Scan Target.
        address: URL of the target (e.g., https://example.com)
        type: Target type (default, network)
        criticality: 0=none, 10=low, 20=medium, 30=high, 40=critical
        """
        body: Dict[str, Any] = {"address": address, "type": type, "criticality": criticality}
        if description:
            body["description"] = description
        return await acunetix.post("/targets", body=body)

    @mcp.tool()
    async def add_targets(
        targets: List[Dict[str, Any]],
        groups: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create multiple Scan Targets at once.
        targets: List of target objects, each with 'address', optional 'description', 'type', 'criticality'
        groups: Optional list of target group IDs to add targets to
        """
        body: Dict[str, Any] = {"targets": targets}
        if groups:
            body["groups"] = groups
        return await acunetix.post("/targets/add", body=body)

    @mcp.tool()
    async def get_target(target_id: str) -> Dict[str, Any]:
        """
        Get details of a specific Scan Target by its ID.
        """
        return await acunetix.get(f"/targets/{target_id}")

    @mcp.tool()
    async def update_target(
        target_id: str,
        address: Optional[str] = None,
        description: Optional[str] = None,
        type: Optional[str] = None,
        criticality: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Modify an existing Scan Target.
        """
        body: Dict[str, Any] = {}
        if address is not None:
            body["address"] = address
        if description is not None:
            body["description"] = description
        if type is not None:
            body["type"] = type
        if criticality is not None:
            body["criticality"] = criticality
        return await acunetix.patch(f"/targets/{target_id}", body=body)

    @mcp.tool()
    async def remove_target(target_id: str) -> Dict[str, Any]:
        """
        Delete a Scan Target and all its associated resources (scans, reports, vulnerabilities).
        WARNING: This is irreversible!
        """
        return await acunetix.delete(f"/targets/{target_id}")

    @mcp.tool()
    async def remove_targets(target_ids: List[str]) -> Dict[str, Any]:
        """
        Delete multiple Scan Targets at once.
        WARNING: This is irreversible! All associated resources will be deleted.
        """
        return await acunetix.post("/targets/delete", body={"target_id_list": target_ids})

    @mcp.tool()
    async def get_target_configuration(target_id: str) -> Dict[str, Any]:
        """
        Get the full configuration of a Scan Target (login, proxy, auth, etc.).
        """
        return await acunetix.get(f"/targets/{target_id}/configuration")

    @mcp.tool()
    async def configure_target(
        target_id: str,
        configuration: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Modify a Scan Target's configuration. Partial configuration merges with existing.
        Common config fields: login (credentials), proxy, sensor, custom_headers,
        user_agent, excluded_paths, scan_speed, case_sensitive, limit_crawler_scope,
        authentication.
        """
        return await acunetix.patch(
            f"/targets/{target_id}/configuration", body=configuration
        )

    @mcp.tool()
    async def get_allowed_hosts(target_id: str) -> Dict[str, Any]:
        """
        Get list of Allowed Hosts for a Scan Target (additional hosts within scope).
        """
        return await acunetix.get(f"/targets/{target_id}/allowed_hosts")

    @mcp.tool()
    async def add_allowed_host(
        target_id: str,
        allowed_target_id: str,
    ) -> Dict[str, Any]:
        """
        Add an Allowed Host to a Scan Target's scope.
        allowed_target_id: The target ID of the host to allow.
        """
        return await acunetix.post(
            f"/targets/{target_id}/allowed_hosts",
            body={"target_id": allowed_target_id},
        )

    @mcp.tool()
    async def remove_allowed_host(
        target_id: str,
        allowed_target_id: str,
    ) -> Dict[str, Any]:
        """
        Remove an Allowed Host from a Scan Target.
        """
        return await acunetix.delete(
            f"/targets/{target_id}/allowed_hosts/{allowed_target_id}"
        )

    @mcp.tool()
    async def get_continuous_scan_status(target_id: str) -> Dict[str, Any]:
        """
        Get the Continuous Scan status of a Target.
        """
        return await acunetix.get(f"/targets/{target_id}/continuous_scan")

    @mcp.tool()
    async def set_continuous_scan_status(
        target_id: str,
        enabled: bool,
    ) -> Dict[str, Any]:
        """
        Enable or disable Continuous Scan for a Target.
        """
        return await acunetix.post(
            f"/targets/{target_id}/continuous_scan",
            body={"enabled": enabled},
        )

    @mcp.tool()
    async def reset_sensor_secret(
        target_id: str,
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Reset the AcuSensor secret for a Target.
        """
        body: Dict[str, Any] = {}
        if secret:
            body["sensor_secret"] = secret
        return await acunetix.post(f"/targets/{target_id}/sensor/reset", body=body)

    @mcp.tool()
    async def get_excluded_paths(target_id: str) -> Dict[str, Any]:
        """
        Get the list of excluded paths for a Scan Target.
        """
        return await acunetix.get(f"/targets/{target_id}/configuration/exclusions")

    @mcp.tool()
    async def update_excluded_paths(
        target_id: str,
        paths: List[str],
    ) -> Dict[str, Any]:
        """
        Update the excluded paths list for a Scan Target.
        paths: List of path patterns to exclude (e.g., ['/admin', '/logout'])
        """
        return await acunetix.post(
            f"/targets/{target_id}/configuration/exclusions",
            body={"paths": paths},
        )

    @mcp.tool()
    async def get_login_sequence(target_id: str) -> Dict[str, Any]:
        """
        Get the Login Sequence file info for a Scan Target.
        """
        return await acunetix.get(
            f"/targets/{target_id}/configuration/login_sequence"
        )

    @mcp.tool()
    async def delete_login_sequence(target_id: str) -> Dict[str, Any]:
        """
        Delete and unset the Login Sequence for a Scan Target.
        """
        return await acunetix.delete(
            f"/targets/{target_id}/configuration/login_sequence"
        )

    @mcp.tool()
    async def get_client_certificate(target_id: str) -> Dict[str, Any]:
        """
        Get the Client Certificate info for a Scan Target.
        """
        return await acunetix.get(
            f"/targets/{target_id}/configuration/client_certificate"
        )

    @mcp.tool()
    async def delete_client_certificate(target_id: str) -> Dict[str, Any]:
        """
        Delete and unset the Client Certificate for a Scan Target.
        """
        return await acunetix.delete(
            f"/targets/{target_id}/configuration/client_certificate"
        )

    @mcp.tool()
    async def get_imported_files(target_id: str) -> Dict[str, Any]:
        """
        Get list of imported files (Burp, Fiddler, HTTP Archive, etc.) for a Scan Target.
        """
        return await acunetix.get(f"/targets/{target_id}/configuration/imports")

    @mcp.tool()
    async def delete_imported_file(
        target_id: str,
        import_id: str,
    ) -> Dict[str, Any]:
        """
        Delete an imported file from a Scan Target configuration.
        """
        return await acunetix.delete(
            f"/targets/{target_id}/configuration/imports/{import_id}"
        )

    @mcp.tool()
    async def targets_cvs_export(
        query: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Export targets list in CSV format.
        """
        return await acunetix.get(
            "/targets/cvs_export", params={"q": query, "s": sort}
        )

    @mcp.tool()
    async def list_target_groups(target_id: str) -> Dict[str, Any]:
        """
        Get all Target Groups that include a specific Target.
        """
        return await acunetix.get(f"/targets/{target_id}/target_groups")

    @mcp.tool()
    async def get_workers_assigned_to_target(target_id: str) -> Dict[str, Any]:
        """
        Get the Workers assigned to a specific Target.
        """
        return await acunetix.get(f"/targets/{target_id}/configuration/workers")

    @mcp.tool()
    async def assign_workers_to_target(
        target_id: str,
        worker_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Assign Workers to a Target (up to one Worker-type per Target).
        """
        return await acunetix.post(
            f"/targets/{target_id}/configuration/workers",
            body={"worker_id_list": worker_ids},
        )

    @mcp.tool()
    async def upload_login_sequence(
        target_id: str,
        filename: str,
    ) -> Dict[str, Any]:
        """
        Initiate a Login Sequence upload for a Target (step 1 of 2).
        Returns a temporary upload URL where the .lsr file should be POSTed
        using application/octet-stream Content-Type.
        After upload, call configure_target to apply the login sequence.
        """
        return await acunetix.upload_init(
            f"/targets/{target_id}/configuration/login_sequence",
            body={"name": filename},
        )

    @mcp.tool()
    async def download_login_sequence(target_id: str) -> Dict[str, Any]:
        """
        Download the Login Sequence file (.lsr) of a Target.
        Returns the file as base64-encoded data.
        """
        return await acunetix.download(
            f"/targets/{target_id}/configuration/login_sequence/download"
        )

    @mcp.tool()
    async def upload_client_certificate(
        target_id: str,
        filename: str,
        password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initiate a Client Certificate upload for a Target (step 1 of 2).
        Returns a temporary upload URL where the PKCS12 certificate file
        should be POSTed using application/octet-stream Content-Type.
        After upload, call configure_target to apply the certificate.
        password: Optional password for the PKCS12 certificate.
        """
        body: Dict[str, Any] = {"name": filename}
        if password:
            body["password"] = password
        return await acunetix.upload_init(
            f"/targets/{target_id}/configuration/client_certificate",
            body=body,
        )

    @mcp.tool()
    async def upload_import_file(
        target_id: str,
        filename: str,
    ) -> Dict[str, Any]:
        """
        Initiate an Import File upload for a Target (step 1 of 2).
        Supports: Acunetix HTTP Sniffer, Fiddler SAZ, Burp State/Export XML,
        HTTP Archive (HAR), and Plain Text formats.
        Returns a temporary upload URL where the file should be POSTed
        using application/octet-stream Content-Type (max 1MB per request).
        After upload, call configure_target to apply the import.
        """
        return await acunetix.upload_init(
            f"/targets/{target_id}/configuration/imports",
            body={"name": filename},
        )

    @mcp.tool()
    async def download_sensor(
        sensor_type: str,
        sensor_secret: str,
    ) -> Dict[str, Any]:
        """
        Download the AcuSensor file for a Target.
        sensor_type: Type of sensor (e.g., 'java', 'php', 'aspnet', 'nodejs')
        sensor_secret: The sensor secret from the target configuration.
        Returns the sensor file as base64-encoded data.
        """
        return await acunetix.download(
            f"/targets/sensors/{sensor_type}/{sensor_secret}"
        )
