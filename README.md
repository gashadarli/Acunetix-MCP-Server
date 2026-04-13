# Acunetix MCP Server

MCP (Model Context Protocol) server for the **Acunetix Web Vulnerability Scanner API**.

Allows AI assistants (OpenClaw, Claude, Cursor, Gemini) to interact with Acunetix through
structured tool calls — without ever making raw HTTP requests to private/internal addresses
themselves. The MCP server acts as the authenticated bridge.

## Why this exists

AI runtimes block direct HTTP calls to private IPs (`10.x.x.x`, `localhost`, etc.).
The MCP server runs locally (or in Docker) with access to your Acunetix instance,
and the AI calls structured tools instead:

```
AI client  ──(MCP tools)──▶  acunetix-mcp  ──(HTTPS + X-Auth)──▶  Acunetix
```

## Available Tools (19 total)

All tool names are prefixed with `acunetix__` to avoid conflicts with other MCP servers.

| Tool | Description |
|------|-------------|
| `acunetix__list_targets` | List / search scan targets |
| `acunetix__get_target` | Detailed info for one target |
| `acunetix__add_target` | Create a new scan target |
| `acunetix__list_scans` | List scans (filter by target/status) |
| `acunetix__start_scan` | Start a scan immediately |
| `acunetix__get_scan_status` | Poll status of a running/completed scan |
| `acunetix__abort_scan` | Stop a running scan |
| `acunetix__get_scan_results` | Scan session history |
| `acunetix__list_scanning_profiles` | Available scan profile IDs |
| `acunetix__list_vulnerabilities` | List vulnerabilities (filter by severity/status) |
| `acunetix__get_vulnerability` | Full details + remediation for one finding |
| `acunetix__update_vulnerability_status` | Mark open / fixed / false_positive / ignored |
| `acunetix__list_vulnerability_types` | Vulnerability type breakdown |
| `acunetix__list_report_templates` | Available report format templates |
| `acunetix__generate_report` | Generate a PDF/HTML report |
| `acunetix__list_reports` | List generated reports |
| `acunetix__get_report` | Report details + download descriptor |
| `acunetix__get_scan_result` | One scan session's metadata |
| `acunetix__get_scan_statistics` | Vuln counts, URLs scanned, timing |

---

## Quick Start

### 1. Configure

```bash
cp .env.example .env
# Edit .env with your Acunetix URL and API key
```

```env
ACUNETIX_BASE_URL=https://10.0.244.136/api/v1
ACUNETIX_API_KEY=1986ad8c...
VERIFY_SSL=false
```

> **Get your API key**: Acunetix UI → top-right menu → **Profile** → **API Key**

### 2. Install

```bash
pip install -e .
```

### 3. Verify it works

```bash
# Quick sanity check — should print 19 tools, all starting with acunetix__
ACUNETIX_BASE_URL=https://10.0.244.136/api/v1 \
ACUNETIX_API_KEY=your-key \
python -c "
import asyncio, os
from acunetix_mcp.server import mcp
tools = asyncio.run(mcp.list_tools())
for t in tools:
    print(t.name)
print()
print(f'Total: {len(tools)} tools')
"
```

---

## MCP Client Configuration

### OpenClaw / Claude Desktop / Cursor (stdio — recommended)

The server runs as a **subprocess** — no port, no Docker needed.

**Option A — using installed package** (`pip install -e .` was run):

```json
{
  "mcpServers": {
    "acunetix": {
      "command": "acunetix-mcp-server",
      "env": {
        "ACUNETIX_BASE_URL": "https://10.0.244.136/api/v1",
        "ACUNETIX_API_KEY": "your-api-key-here",
        "VERIFY_SSL": "false"
      }
    }
  }
}
```

**Option B — using Python directly** (no install needed):

```json
{
  "mcpServers": {
    "acunetix": {
      "command": "python",
      "args": ["-m", "acunetix_mcp.server"],
      "cwd": "/absolute/path/to/Acunetix-MCP-Server",
      "env": {
        "ACUNETIX_BASE_URL": "https://10.0.244.136/api/v1",
        "ACUNETIX_API_KEY": "your-api-key-here",
        "VERIFY_SSL": "false"
      }
    }
  }
}
```

**Option C — using uv** (auto dependency management):

```json
{
  "mcpServers": {
    "acunetix": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/absolute/path/to/Acunetix-MCP-Server",
        "acunetix-mcp-server"
      ],
      "env": {
        "ACUNETIX_BASE_URL": "https://10.0.244.136/api/v1",
        "ACUNETIX_API_KEY": "your-api-key-here",
        "VERIFY_SSL": "false"
      }
    }
  }
}
```

> **Config file locations:**
> - **Claude Desktop** macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
> - **Claude Desktop** Windows: `%APPDATA%\Claude\claude_desktop_config.json`
> - **Cursor**: `.cursor/mcp.json` in your project, or `~/.cursor/mcp.json` globally
> - **OpenClaw**: check Settings → MCP Servers

---

### Docker / HTTP Transport

Use this if you want the server running as a persistent HTTP service
(e.g., shared team instance, or an MCP client that only supports HTTP URLs).

```bash
# Build and start
docker compose up -d

# Verify
curl http://localhost:8000/mcp
```

MCP client config (HTTP URL mode):

```json
{
  "mcpServers": {
    "acunetix": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

---

## Example AI Conversations

Once configured, ask your AI assistant:

- *"List all Acunetix targets"*
- *"Search for targets containing 'azincloud'"*
- *"Start a Full Scan on target `<uuid>`"*
- *"What's the status of scan `<uuid>`?"*
- *"Show me all high and critical vulnerabilities"*
- *"Mark vulnerability `<uuid>` as false positive"*
- *"Generate an Executive Summary report for the last scan"*

---

## Typical Scan Workflow

```
1. acunetix__list_targets
       │ find target_id
       ▼
2. acunetix__start_scan(target_id)
       │ get scan_id
       ▼
3. acunetix__get_scan_status(scan_id)   ← poll until status == "completed"
       │ get result_id from current_result
       ▼
4. acunetix__get_scan_statistics(scan_id, result_id)
       │ see severity counts
       ▼
5. acunetix__list_vulnerabilities(target_id=..., severity="high")
       │ triage findings
       ▼
6. acunetix__generate_report(template_id, "scan", [scan_id])
```

---

## Transport Modes

| Mode | When to use | How |
|------|-------------|-----|
| **stdio** (default) | OpenClaw, Claude Desktop, Cursor | Config with `command` key |
| **HTTP** (`--http`) | Docker, shared/remote setups | Config with `url` key |

Run HTTP mode manually:
```bash
acunetix-mcp-server --http
acunetix-mcp-server --http --port 9000
```

---

## Troubleshooting

**Server not found / "command not found"**
→ Run `pip install -e .` first, or use the Python direct Option B above.

**"ACUNETIX_BASE_URL is not set"**
→ Pass env vars in your MCP client config (see examples above), or create a `.env` file.

**SSL certificate error**
→ Set `VERIFY_SSL=false` in env vars (Acunetix on-prem uses self-signed certs by default).

**"Connection refused" / "Cannot connect"**
→ Verify Acunetix is running and the URL/port is correct. Test directly:
```bash
curl -k -H "X-Auth: your-api-key" https://10.0.244.136/api/v1/targets
```

**OpenClaw says "fetch request" failed**
→ This is the exact problem this MCP server solves. OpenClaw cannot call `10.x.x.x`
directly. Configure the MCP server using the stdio config above — OpenClaw will call
`acunetix__list_targets` (the tool), not the raw Acunetix URL.
