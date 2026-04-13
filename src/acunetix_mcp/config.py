"""Configuration management for Acunetix MCP Server.

Config is loaded from environment variables (or a .env file).
Validation is LAZY — it only runs when the HTTP client is first used,
so importing this module never crashes the server on startup.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Acunetix MCP Server configuration.

    All values come from environment variables:
      ACUNETIX_BASE_URL  — full API base URL, e.g. https://10.0.244.136/api/v1
      ACUNETIX_API_KEY   — API key from Acunetix UI > Profile > API Key
      VERIFY_SSL         — 'true' | 'false' (default: false for self-signed certs)
      MCP_SERVER_HOST    — bind host for HTTP transport (default: 0.0.0.0)
      MCP_SERVER_PORT    — bind port for HTTP transport (default: 8000)
    """

    ACUNETIX_BASE_URL: str = os.getenv("ACUNETIX_BASE_URL", "")
    ACUNETIX_API_KEY: str = os.getenv("ACUNETIX_API_KEY", "")
    VERIFY_SSL: bool = os.getenv("VERIFY_SSL", "false").lower() == "true"
    MCP_SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8000"))

    def validate(self) -> None:
        """Raise ValueError if required configuration is missing."""
        if not self.ACUNETIX_BASE_URL:
            raise ValueError(
                "ACUNETIX_BASE_URL is not set. "
                "Add it to your .env file or pass it as an environment variable.\n"
                "Example: ACUNETIX_BASE_URL=https://10.0.244.136/api/v1"
            )
        if not self.ACUNETIX_API_KEY:
            raise ValueError(
                "ACUNETIX_API_KEY is not set. "
                "Get your key from Acunetix UI → Profile → API Key, "
                "then add it to your .env file.\n"
                "Example: ACUNETIX_API_KEY=1986ad8c..."
            )


# Singleton — used across the whole package.
# validate() is NOT called here; the client calls it lazily on first use.
config = Config()
