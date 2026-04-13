"""Issue Tracker integration MCP tools."""

from typing import Any, Dict, Optional
import fastmcp

from ..client import acunetix


def register_issue_tracker_tools(mcp: fastmcp.FastMCP):

    @mcp.tool()
    async def get_issue_trackers() -> Dict[str, Any]:
        """
        Get all configured Issue Tracker integrations.
        Supported trackers: Jira, GitHub Issues, GitLab, Azure DevOps (TFS), Bugzilla, etc.
        """
        return await acunetix.get("/issue_trackers")

    @mcp.tool()
    async def create_issue_tracker(
        name: str,
        tracker_type: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a new Issue Tracker integration.
        tracker_type: 'jira', 'github', 'gitlab', 'tfsonprem', 'tfsonline', 'bugzilla'
        config: Tracker-specific configuration (URL, credentials, project mappings).
        """
        return await acunetix.post(
            "/issue_trackers",
            body={"name": name, "platform": tracker_type, **config},
        )

    @mcp.tool()
    async def get_issue_tracker(issue_tracker_id: str) -> Dict[str, Any]:
        """
        Get details of a specific Issue Tracker integration.
        """
        return await acunetix.get(f"/issue_trackers/{issue_tracker_id}")

    @mcp.tool()
    async def update_issue_tracker(
        issue_tracker_id: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Modify an existing Issue Tracker integration configuration.
        """
        return await acunetix.patch(f"/issue_trackers/{issue_tracker_id}", body=config)

    @mcp.tool()
    async def delete_issue_tracker(issue_tracker_id: str) -> Dict[str, Any]:
        """
        Delete an Issue Tracker integration.
        """
        return await acunetix.delete(f"/issue_trackers/{issue_tracker_id}")

    @mcp.tool()
    async def check_issue_tracker_connection(issue_tracker_id: str) -> Dict[str, Any]:
        """
        Test the connection to a saved Issue Tracker integration.
        """
        return await acunetix.get(f"/issue_trackers/{issue_tracker_id}/check_connection")

    @mcp.tool()
    async def get_issue_tracker_projects(issue_tracker_id: str) -> Dict[str, Any]:
        """
        Get available Projects from a configured Issue Tracker.
        """
        return await acunetix.get(f"/issue_trackers/{issue_tracker_id}/projects")

    @mcp.tool()
    async def get_issue_tracker_issue_types(
        issue_tracker_id: str,
        project_id: str,
    ) -> Dict[str, Any]:
        """
        Get Issue Types for a specific Project in an Issue Tracker.
        """
        return await acunetix.get(
            f"/issue_trackers/{issue_tracker_id}/projects/{project_id}/issue_types"
        )

    @mcp.tool()
    async def get_issue_tracker_custom_fields(issue_tracker_id: str) -> Dict[str, Any]:
        """
        Get custom fields available in an Issue Tracker.
        """
        return await acunetix.get(f"/issue_trackers/{issue_tracker_id}/custom_fields")

    @mcp.tool()
    async def get_issue_tracker_collections(issue_tracker_id: str) -> Dict[str, Any]:
        """
        Get Collections from a TFS/Azure DevOps Issue Tracker.
        """
        return await acunetix.get(f"/issue_trackers/{issue_tracker_id}/collections")

    @mcp.tool()
    async def check_issue_tracker_connection_test(
        tracker_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Test connection to an Issue Tracker without saving it first.
        tracker_config: Full issue tracker configuration object.
        """
        return await acunetix.post("/issue_trackers/check_connection", body=tracker_config)

    @mcp.tool()
    async def get_issue_tracker_projects_test(
        tracker_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Get Projects from an Issue Tracker using a config without saving it.
        """
        return await acunetix.post("/issue_trackers/check_projects", body=tracker_config)

    @mcp.tool()
    async def get_issue_tracker_issue_types_test(
        tracker_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Get Issue Types from an Issue Tracker using a config without saving it.
        """
        return await acunetix.post("/issue_trackers/check_issue_types", body=tracker_config)

    @mcp.tool()
    async def get_issue_tracker_collections_test(
        tracker_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Get TFS Collections from an Issue Tracker using a config without saving it.
        """
        return await acunetix.post("/issue_trackers/collections", body=tracker_config)

    @mcp.tool()
    async def get_issue_tracker_custom_fields_test(
        tracker_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Get Custom Fields from an Issue Tracker using a config without saving it.
        """
        return await acunetix.post("/issue_trackers/custom_fields", body=tracker_config)

    @mcp.tool()
    async def get_issue_tracker_issue_types_by_query(
        issue_tracker_id: str,
        project_id: str,
    ) -> Dict[str, Any]:
        """
        Get Issue Types for a specific Project via query parameter.
        This is an alternative to get_issue_tracker_issue_types that uses
        a query parameter instead of a path parameter for the project ID.
        """
        return await acunetix.get(
            f"/issue_trackers/{issue_tracker_id}/projects/issue_types",
            params={"project_id": project_id},
        )
