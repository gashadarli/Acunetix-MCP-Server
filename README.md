# Acunetix MCP Server

Full-coverage MCP (Model Context Protocol) server for **Acunetix Scanner API** — 149+ tools covering every endpoint. Works with **Claude**, **ChatGPT**, **Gemini**, and **OpenClaw**.

## Features

- ✅ **149+ MCP tools** — 1:1 coverage of the entire Acunetix REST API
- ✅ **Docker-ready** — Multi-stage production build
- ✅ **Streamable HTTP transport** — Compatible with all MCP clients
- ✅ **Async** — Non-blocking, high-performance httpx client
- ✅ **Self-signed SSL support** — Works with on-premise Acunetix

## API Coverage

| Domain | Tools | Description |
|--------|-------|-------------|
| Targets | 25 | Create, configure, delete scan targets |
| Scans | 10 | Schedule, abort, resume, trigger scans |
| Vulnerabilities | 11 | List, filter, update status, recheck |
| Scan Results | 18 | Crawl data, statistics, technologies |
| Reports | 13 | Generate, download PDF/HTML reports |
| Users | 8 | User CRUD, enable/disable |
| Target Groups | 9 | Group and organize targets |
| User Groups | 9 | Access control management |
| Scanning Profiles | 5 | Custom scan type configuration |
| Workers | 10 | Distributed engine management |
| Issue Trackers | 15 | Jira, GitHub, GitLab, Azure DevOps |
| WAFs | 7 | WAF export integrations |
| Roles | 6 | RBAC roles and permissions |
| Agents | 3 | Registration token management |
| Excluded Hours | 5 | Scan scheduling blackout windows |

## Quick Start

### Docker (Recommended)

```bash
# 1. Clone and configure
cd Acunetix-MCP-Server
cp .env.example .env
# Edit .env with your Acunetix URL and API key

# 2. Build and run
docker compose up -d

# 3. Verify
curl http://localhost:8000/health
```

### Local Development

```bash
pip install -e .
acunetix-mcp-server
```

## Configuration

Edit `.env`:

```env
ACUNETIX_BASE_URL=https://10.10.10.10/api/v1
ACUNETIX_API_KEY=your-api-key-here
VERIFY_SSL=false
MCP_SERVER_PORT=8000
```

## MCP Client Configuration

### Claude Desktop / Cursor / OpenClaw

Add to your MCP client config:

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

### Gemini / ChatGPT (OpenAI) with MCP support

```json
{
  "servers": [
    {
      "name": "acunetix",
      "url": "http://localhost:8000/mcp",
      "transport": "streamable-http"
    }
  ]
}
```

## Example Usage (via AI)

Ask your AI assistant:

- *"Acunetix-də bütün targetləri göstər"*
- *"https://example.com üçün Full Scan başlat"*
- *"Kritik zəiflikləri siyahıla"*
- *"Ən son scan-ın nəticələrini göstər"*
- *"Executive Summary report yarat"*
- *"Bu zəifliyi 'false_positive' kimi işarələ"*

## Architecture

```
AI Client (Claude/GPT/Gemini/OpenClaw)
         │ MCP Protocol (HTTP SSE)
         ▼
Acunetix MCP Server (FastMCP, Port 8000)
         │ HTTPS REST API
         ▼
Acunetix Scanner (https://10.10.10.10)
```

## Health Check

```bash
curl http://localhost:8000/health
```

## API Key

To get your API key from Acunetix:
1. Log in to Acunetix
2. Go to **Profile** (top right) → **API Key**
3. Copy the key
