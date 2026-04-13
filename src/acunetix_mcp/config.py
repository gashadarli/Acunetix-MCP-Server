"""Configuration management for Acunetix MCP Server."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    ACUNETIX_BASE_URL: str = os.getenv("ACUNETIX_BASE_URL", "")
    ACUNETIX_API_KEY: str = os.getenv("ACUNETIX_API_KEY", "")
    VERIFY_SSL: bool = os.getenv("VERIFY_SSL", "false").lower() == "true"
    MCP_SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8000"))

    def validate(self):
        if not self.ACUNETIX_BASE_URL:
            raise ValueError(
                "ACUNETIX_BASE_URL is required. Set it in .env or as environment variable."
            )
        if not self.ACUNETIX_API_KEY:
            raise ValueError(
                "ACUNETIX_API_KEY is required. Set it in .env or as environment variable. "
                "Get your API key from Acunetix UI > Profile > API Key."
            )


config = Config()
config.validate()
