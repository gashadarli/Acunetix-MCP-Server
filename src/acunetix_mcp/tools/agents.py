"""Agent registration token MCP tools."""

from typing import Any, Dict, Optional
import fastmcp

from ..client import acunetix


def register_agent_tools(mcp: fastmcp.FastMCP):

    @mcp.tool()
    async def get_agent_registration_token() -> Dict[str, Any]:
        """
        Get the current Agent Registration Token.
        This token is used to register new Acunetix scanning agents.
        """
        return await acunetix.get("/config/agents/registration_token")

    @mcp.tool()
    async def generate_agent_registration_token(
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate or regenerate an Agent Registration Token.
        If a token already exists, it will be replaced.
        description: Optional description for the token.
        """
        body: Dict[str, Any] = {}
        if description:
            body["description"] = description
        return await acunetix.post("/config/agents/registration_token", body=body)

    @mcp.tool()
    async def delete_agent_registration_token() -> Dict[str, Any]:
        """
        Delete the current Agent Registration Token.
        After deletion, no new agents can register until a new token is generated.
        """
        return await acunetix.delete("/config/agents/registration_token")
