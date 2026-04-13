# Acunetix MCP Server — Full Rewrite Plan

## Problem Summary

OpenClaw (və digər MCP clientlər) Acunetix MCP serverə qoşula bilmir. `web_fetch` ilə private IP-lərə (localhost/10.x.x.x) birbaşa gedə bilmir, MCP server körpü rolunu oynamalıdır. **Hazırkı implementation tamamilə səhvdir** — aşağıda 5 kritik bug var.

## Diaqnoz: Mövcud Kodda 5 Kritik Problem

### 🔴 Bug 1: Yalnız HTTP Transport — stdio yoxdur

**Əsas problem budur.** OpenClaw və əksər MCP clientlər `stdio` transport istifadə edir — yəni server-i subprocess kimi işlədib stdin/stdout ilə JSON-RPC danışır. Hazırkı kod **yalnız** `streamable-http` transport ilə işləyir (`uvicorn` + HTTP port 8000).

- [server.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/server.py#L110): `mcp.http_app(transport="streamable-http")` — yalnız HTTP
- OpenClaw MCP client `stdio` subprocess-ə ehtiyac duyur, HTTP endpoint-ə yox
- Claude Desktop də default olaraq `stdio` istifadə edir

### 🔴 Bug 2: Config Import Zamanı Crash

[config.py L29](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/config.py#L29): `config.validate()` **modul import edilən anda** çağırılır. Bu o deməkdir ki:

- `.env` faylı yoxdursa və ya env var-lar set deyilsə, **server import-da crash edir**
- MCP client subprocess-i başlatarkən env var-ları `command` config içində keçirir, amma `config.validate()` bunu görmədən əvvəl artıq crash edə bilər
- Test-lər belə buna workaround qoyub: `os.environ.setdefault(...)` import-dan əvvəl

### 🔴 Bug 3: Tool Name-lərdə Namespace Prefixi Yoxdur

Hazırkı tool adları: `get_targets`, `schedule_scan`, `get_vulnerabilities` — bunlar jenerikdir. Başqa MCP serv istirahətləri ilə (məsələn Jira MCP) conflict yarada bilər.

Düzgün format (Jira MCP kimi): `acunetix__list_targets`, `acunetix__start_scan`

### 🟡 Bug 4: `starlette` dependency bəyan edilməyib

[server.py L13-14](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/server.py#L13-L14): `from starlette.responses import JSONResponse` — amma `starlette` nə `requirements.txt`-də, nə `pyproject.toml`-da yoxdur. FastMCP onu transitive dependency kimi gətirir, amma bu etibarsızdır.

### 🟡 Bug 5: 149+ Tool — Çox Şişirdilmiş

OpenClaw/Claude kimi LLM-lər 149+ tool-dan effektiv istifadə edə bilmir:
- Tool discovery zamanı çox böyük payload olur
- LLM confused olur, yanlış tool çağırır
- Praktikada 15-20 tool kifayətdir

---

## Proposed Architecture

```
┌───────────────────────────────┐
│ AI Client                     │
│ (OpenClaw / Claude / Cursor)  │
│                               │
│ stdio subprocess kimi         │
│ server-i başladır             │
└──────────┬────────────────────┘
           │ stdin/stdout (JSON-RPC)
           ▼
┌───────────────────────────────┐
│ Acunetix MCP Server           │
│ (Python + FastMCP)            │
│                               │
│ Transport: stdio (default)    │
│    və ya  HTTP (--http flag)  │
│                               │
│ Tools: acunetix__*            │
└──────────┬────────────────────┘
           │ HTTPS + X-Auth header
           ▼
┌───────────────────────────────┐
│ Acunetix Scanner              │
│ https://10.0.244.136/api/v1   │
└───────────────────────────────┘
```

---

## Proposed Changes

### Core Infrastructure

---

#### [MODIFY] [config.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/config.py)

- **Lazy validation**: `validate()` artıq modul import zamanı çağırılmayacaq, yalnız client ilk dəfə istifadə ediləndə çağırılacaq
- Env var adları eyni qalacaq: `ACUNETIX_BASE_URL`, `ACUNETIX_API_KEY`, `VERIFY_SSL`

```python
# BEFORE (crash on import)
config = Config()
config.validate()   # ← server import-da crash edir

# AFTER (lazy validation)
config = Config()
# validate() çağırılmır, client istifadə zamanı yoxlayacaq
```

---

#### [MODIFY] [client.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/client.py)

- İlk HTTP çağırışda `config.validate()` çağırılacaq (lazy init)
- API key-i response/error message-lərdə heç vaxt göstərməyəcəyik
- Error handling daha anlaşıqlı olacaq

---

#### [MODIFY] [server.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/server.py)

**Əsas dəyişiklik**: Dual-transport support

```python
def main():
    import sys
    
    if "--http" in sys.argv:
        # HTTP/SSE transport (Docker, remote clients)
        mcp.run(transport="streamable-http", host="0.0.0.0", port=config.MCP_SERVER_PORT)
    else:
        # Default: stdio transport (OpenClaw, Claude Desktop, Cursor)
        mcp.run(transport="stdio")
```

- `starlette` import-ları silinəcək (artıq manual Starlette routing lazım deyil)
- Health check FastMCP-nin öz HTTP handler-i ilə həll ediləcək
- `mcp.run()` istifadə olunacaq — FastMCP-nin built-in transport switching-i

---

### Tool Modules — Namespace + Sadələşdirmə

> [!IMPORTANT]  
> **Seçim lazımdır**: 149+ tool-u saxlayaq, yoxsa 15-20 core tool-a endirək?
> 
> **Variant A (Tövsiyə)**: 15-20 əsas tool — LLM-lər üçün ideal, tool discovery sürətli, daha az confusion  
> **Variant B**: Bütün 149+ tool — tam API coverage, amma LLM-lər bunlardan effektiv istifadə edə bilmir

Aşağıdakı plan **Variant A** üzrədir. İstəsəniz Variant B ilə davam edə bilərik (yalnız namespace prefixi əlavə edərik, tool sayını dəyişmərik).

---

#### [MODIFY] [tools/targets.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/tools/targets.py)

Mövcud ~28 tool → **3 core tool**:

| Yeni Tool Adı | Köhnə Tool | Məqsəd |
|---|---|---|
| `acunetix__list_targets` | `get_targets` | Bütün targetləri listləmək, search + pagination |
| `acunetix__get_target` | `get_target` | Tək target-in detallı məlumatı |
| `acunetix__add_target` | `add_target` | Yeni target yaratmaq |

---

#### [MODIFY] [tools/scans.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/tools/scans.py)

Mövcud ~11 tool → **5 core tool**:

| Yeni Tool Adı | Köhnə Tool | Məqsəd |
|---|---|---|
| `acunetix__list_scans` | `get_scans` | Scan-ları listləmək, filter + pagination |
| `acunetix__start_scan` | `schedule_scan` | Yeni scan başlatmaq |
| `acunetix__get_scan_status` | `get_scan` | Scan statusunu yoxlamaq |
| `acunetix__abort_scan` | `abort_scan` | Scan-ı dayandırmaq |
| `acunetix__get_scan_results` | `get_scan_result_history` | Scan nəticələri |

---

#### [MODIFY] [tools/vulnerabilities.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/tools/vulnerabilities.py)

Mövcud ~10 tool → **4 core tool**:

| Yeni Tool Adı | Köhnə Tool | Məqsəd |
|---|---|---|
| `acunetix__list_vulnerabilities` | `get_vulnerabilities` | Zəiflikləri listləmək |
| `acunetix__get_vulnerability` | `get_vulnerability_details` | Tək zəifliyin detalları |
| `acunetix__update_vulnerability_status` | `set_vulnerability_status` | Status dəyişmək |
| `acunetix__list_vulnerability_types` | `get_vulnerability_types` | Zəiflik tipləri |

---

#### [MODIFY] [tools/reports.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/tools/reports.py)

Mövcud ~13 tool → **4 core tool**:

| Yeni Tool Adı | Köhnə Tool | Məqsəd |
|---|---|---|
| `acunetix__list_reports` | `get_reports` | Report-ları listləmək |
| `acunetix__generate_report` | `generate_new_report` | Yeni report yaratmaq |
| `acunetix__get_report` | `get_report` | Report detalları və download linki |
| `acunetix__list_report_templates` | `get_report_templates` | Mövcud report template-ləri |

---

#### [MODIFY] [tools/results.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/tools/results.py)

Mövcud ~18 tool → **2 core tool**:

| Yeni Tool Adı | Köhnə Tool | Məqsəd |
|---|---|---|
| `acunetix__get_scan_result` | `get_scan_result` | Scan sessiyanın detalları |
| `acunetix__get_scan_statistics` | `get_scan_statistics` | Statistikalar (vuln count, duration) |

---

#### [DELETE] Silinəcək fayllar (Variant A seçilərsə)

Bu tool modulları tamamilə silinəcək — çox niş/nadir istifadə olunan endpointlərdir:

- [tools/users.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/tools/users.py) — User management nadir lazım olur
- [tools/groups.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/tools/groups.py) — Group management
- [tools/scanning_profiles.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/tools/scanning_profiles.py) — Profile adları artıq scan tool-a daxildir
- [tools/workers.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/tools/workers.py) — Worker management
- [tools/issue_trackers.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/tools/issue_trackers.py) — Issue tracker config
- [tools/wafs.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/tools/wafs.py) — WAF config
- [tools/agents.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/tools/agents.py) — Agent registration
- [tools/excluded_hours.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/tools/excluded_hours.py) — Excluded hours
- [tools/roles.py](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/src/acunetix_mcp/tools/roles.py) — RBAC roles

> [!WARNING]
> **Variant B** seçilərsə, bu fayllar silinməyəcək, yalnız tool adlarına `acunetix__` prefixi əlavə ediləcək.

---

### Docker & Configuration

#### [MODIFY] [Dockerfile](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/Dockerfile)

- `ENTRYPOINT` dəyişəcək: `acunetix-mcp-server --http` (Docker zamanı HTTP transport istifadə)
- Health check eyni qalacaq

#### [MODIFY] [docker-compose.yml](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/docker-compose.yml)

- Minimal dəyişiklik, environment variables eyni

#### [MODIFY] [README.md](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/README.md)

Tam yenidən yazılacaq:
- **OpenClaw/Claude Desktop stdio config** nümunələri
- **Docker HTTP config** nümunəsi
- Tool listesi və izahları
- Troubleshooting bölməsi

#### [MODIFY] [pyproject.toml](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/pyproject.toml)

- `starlette` dependency silinəcək (artıq lazım deyil)
- `uvicorn` optional olacaq (yalnız HTTP transport üçün)

#### [MODIFY] [tests/](file:///Users/gashadarli/Documents/Acunetix-MCP-Server/tests)

- Tool count dəyişəcək
- Tool adları yenilənəcək
- stdio transport testi əlavə olunacaq

---

## MCP Client Configuration Nümunələri

### OpenClaw / Claude Desktop (stdio — default)

```json
{
  "mcpServers": {
    "acunetix": {
      "command": "python",
      "args": ["-m", "acunetix_mcp.server"],
      "cwd": "/path/to/Acunetix-MCP-Server",
      "env": {
        "ACUNETIX_BASE_URL": "https://10.0.244.136/api/v1",
        "ACUNETIX_API_KEY": "your-api-key-here",
        "VERIFY_SSL": "false"
      }
    }
  }
}
```

### Docker ilə HTTP Transport

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

## Open Questions

> [!IMPORTANT]
> **Variant seçimi**: 149+ tool qalsın (**Variant B** — yalnız namespace düzəlişi) yoxsa 15-20 core tool-a endirək (**Variant A** — tövsiyə olunan)? Bu LLM-in effektivliyinə ciddi təsir edir.

> [!IMPORTANT]
> **Scanning Profiles tool**: `acunetix__list_scanning_profiles` tool əlavə edək ki, LLM hansı scan profillərinin mövcud olduğunu öyrənə bilsin? Bu hazırkı plan-da yoxdur amma faydalı ola bilər.

---

## Verification Plan

### Automated Tests

1. **Smoke test** — Server import olunur, tool-lar register olunur:
   ```bash
   cd /Users/gashadarli/Documents/Acunetix-MCP-Server
   python -m pytest tests/test_smoke.py -v
   ```

2. **stdio transport test** — Server subprocess kimi başladılır:
   ```bash
   echo '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"capabilities":{}}}' | python -m acunetix_mcp.server
   ```

3. **Tool list verification** — Bütün tool-ların `acunetix__` prefixi var:
   ```bash
   python -c "
   import os; os.environ['ACUNETIX_BASE_URL']='https://test/api/v1'; os.environ['ACUNETIX_API_KEY']='test'
   import asyncio; from acunetix_mcp.server import mcp
   tools = asyncio.run(mcp.list_tools())
   for t in tools: assert t.name.startswith('acunetix__'), f'Bad name: {t.name}'
   print(f'✅ {len(tools)} tools, all namespaced')
   "
   ```

### Integration Tests (Əgər Acunetix instance mövcuddursa)

4. **Real API connection** — `list_targets` çağırışı:
   ```bash
   python -m pytest tests/test_integration.py -v -k test_get_targets
   ```

### Manual Verification

5. OpenClaw-da MCP server-i konfiqurasiya edib `acunetix__list_targets` çağırmaq
6. Claude Desktop-da eyni testi keçirmək
