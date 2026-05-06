# Acunetix MCP Server

Production-oriented, model-agnostic MCP server for the Acunetix REST API.
It exposes typed MCP tools for AI clients instead of a dangerous raw HTTP proxy.

```
AI Client
  -> MCP transport layer
      -> typed MCP tools
          -> policy and audit layer
              -> Acunetix API client
                  -> Acunetix REST API
```

Supported clients include Claude Desktop, Gemini CLI, ChatGPT remote MCP, Codex,
OpenClaw, local MCP runners, and other MCP-compatible clients.

## Tool Coverage

The server registers fixed MCP tools for every operation documented in
`Acunetix-API-Documentation.yaml`. The current coverage report is:

```text
documented_operations: 161
implemented_operations: 161
missing_operations: 0
registered_tools: 168
```

Common read-only tools:

- `acunetix_health`
- `list_targets`
- `get_target`
- `list_target_groups`
- `get_target_group`
- `list_scans`
- `get_scan_status`
- `list_scanning_profiles`
- `list_vulnerabilities`
- `get_vulnerability`
- `list_report_templates`
- `list_reports`
- `get_report`
- `list_users`
- `get_user`
- `list_roles`
- `list_wafs`
- `list_workers`
- `download_report`

Common action tools:

- `create_target`
- `start_scan`
- `stop_scan`
- `generate_report`
- `create_user`
- `update_user`
- `delete_user`
- `update_vulnerability_status`

Action tools are blocked by default because `ACUNETIX_READ_ONLY=true`. To allow
them, set `ACUNETIX_READ_ONLY=false`; callers must still pass
`confirmation=true` unless `ACUNETIX_REQUIRE_CONFIRMATION=false` is set.

There is no generic `acunetix_request(method, path, body)` proxy tool.

The broad OpenAPI coverage tools use a consistent argument shape:

```json
{
  "path_params": {"user_id": "11111111-1111-1111-1111-111111111111"},
  "query": {"q": "text:admin"},
  "body": {"enabled": true},
  "limit": 50,
  "offset": "cursor-value",
  "confirmation": true
}
```

For example:

- "get user list" maps to `list_users` and calls `GET /users`.
- "show WAFs" maps to `list_wafs` and calls `GET /wafs`.
- "download report descriptor X" maps to `download_report` and calls
  `GET /reports/download/{descriptor}`.
- "update vulnerability status" maps to `update_vulnerability_status`, requires
  confirmation, and calls `PUT /vulnerabilities/{vuln_id}/status`.

## Configuration

Copy the examples and fill in your own secret locally:

```bash
cp .env.example .env
cp config.example.yaml config.yaml
```

Environment variables override `config.yaml`.

Key settings:

```env
ACUNETIX_BASE_URL=https://10.0.244.136/
ACUNETIX_API_KEY=replace-with-your-api-key
ACUNETIX_VERIFY_SSL=false
ACUNETIX_READ_ONLY=true
ACUNETIX_REQUIRE_CONFIRMATION=true
ACUNETIX_TARGET_ALLOWLIST=
MCP_TRANSPORT=stdio
MCP_SERVER_PORT=8080
```

`ACUNETIX_BASE_URL` may be either the Acunetix root URL or the full API base URL.
The server normalizes `https://host/` to `https://host/api/v1`.

Never place real API keys in source code, tests, README snippets, or committed
config. `.env` and `config.yaml` are ignored by Git.

## Docker

Build:

```bash
docker compose build
```

Run with Docker Compose:

```bash
ACUNETIX_API_KEY="$ACUNETIX_API_KEY" docker compose up
```

Run stdio mode in Docker for local MCP clients:

```bash
docker run --rm -i \
  -e ACUNETIX_BASE_URL="https://10.0.244.136/" \
  -e ACUNETIX_API_KEY="$ACUNETIX_API_KEY" \
  -e ACUNETIX_VERIFY_SSL="false" \
  acunetix-mcp:latest \
  --transport stdio
```

Run HTTP mode:

```bash
docker run --rm \
  -p 8080:8080 \
  -e ACUNETIX_BASE_URL="https://10.0.244.136/" \
  -e ACUNETIX_API_KEY="$ACUNETIX_API_KEY" \
  -e ACUNETIX_VERIFY_SSL="false" \
  -e MCP_TRANSPORT="http" \
  acunetix-mcp:latest
```

HTTP endpoints:

- MCP streamable HTTP: `http://localhost:8080/mcp`
- Container health: `http://localhost:8080/health`

## Claude Desktop

Stdio configuration:

```json
{
  "mcpServers": {
    "acunetix": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "ACUNETIX_BASE_URL=https://10.0.244.136/",
        "-e", "ACUNETIX_API_KEY",
        "-e", "ACUNETIX_VERIFY_SSL=false",
        "acunetix-mcp:latest",
        "--transport", "stdio"
      ],
      "env": {
        "ACUNETIX_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Gemini CLI

Example MCP server entry:

```json
{
  "mcpServers": {
    "acunetix": {
      "command": "acunetix-mcp-server",
      "args": ["--transport", "stdio"],
      "env": {
        "ACUNETIX_BASE_URL": "https://10.0.244.136/",
        "ACUNETIX_API_KEY": "your-api-key-here",
        "ACUNETIX_VERIFY_SSL": "false"
      }
    }
  }
}
```

## ChatGPT Remote MCP / HTTP

Run the server where ChatGPT can reach it over HTTPS. For local testing:

```bash
docker run --rm -p 8080:8080 \
  -e MCP_TRANSPORT=http \
  -e ACUNETIX_BASE_URL="https://10.0.244.136/" \
  -e ACUNETIX_API_KEY="$ACUNETIX_API_KEY" \
  -e ACUNETIX_VERIFY_SSL=false \
  acunetix-mcp:latest
```

Configure the remote MCP URL as:

```text
https://your-public-host.example.com/mcp
```

For production remote access, put the container behind TLS and your normal
authentication or network access controls. Do not expose this service openly.

## Generic MCP Client

Local stdio:

```json
{
  "mcpServers": {
    "acunetix": {
      "command": "python",
      "args": ["-m", "acunetix_mcp.server", "--transport", "stdio"],
      "cwd": "/absolute/path/to/Acunetix-MCP-Server",
      "env": {
        "ACUNETIX_BASE_URL": "https://10.0.244.136/",
        "ACUNETIX_API_KEY": "your-api-key-here",
        "ACUNETIX_VERIFY_SSL": "false"
      }
    }
  }
}
```

HTTP:

```json
{
  "mcpServers": {
    "acunetix": {
      "type": "http",
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

## Tests

Install test dependencies:

```bash
pip install -e ".[dev]"
```

Run unit tests:

```bash
pytest -v
```

Print a coverage report from the registered MCP tools:

```bash
python -c "import asyncio, json; from acunetix_mcp.server import create_server; from acunetix_mcp.tools.openapi_coverage import coverage_report; tools=asyncio.run(create_server().list_tools()); print(json.dumps(coverage_report({t.name for t in tools}), indent=2))"
```

Run read-only integration tests only when you have a real Acunetix instance:

```bash
ACUNETIX_BASE_URL="https://10.0.244.136/" \
ACUNETIX_API_KEY="$ACUNETIX_API_KEY" \
ACUNETIX_VERIFY_SSL=false \
pytest tests/test_integration.py -v
```

Docker smoke checks:

```bash
docker compose build
ACUNETIX_API_KEY="$ACUNETIX_API_KEY" docker compose up
curl http://localhost:8080/health
python scripts/verify_mcp_http.py --url http://localhost:8080/mcp
```

## Security Notes

- API keys are sent only as the Acunetix `X-Auth` header.
- API keys are masked in normalized API errors and audit logs.
- Action tools are blocked in read-only mode by default.
- `start_scan` is protected by confirmation, target allowlist checks, and a
  scan-start concurrency limit.
- Delete operations are not exposed.
- Integration tests are read-only and skipped unless credentials are set.
