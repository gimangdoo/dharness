"""CM Dashboard Worker — dharness self-host 단일 프로젝트 SQLite 집계 + FastAPI 서빙.

dharness 한정 self-host. REPO_ROOT는 본 모듈 위치(worker/dashboard_server.py)에서
parents[1]로 결정적 계산 — projects.json 레지스트리/멀티 프로젝트 분기 폐지.

LLM 호출 없는 결정적 데이터 집계 — 본 모듈이 SQL과 view 명세의 단일 진실 원천.
정적 프론트엔드는 `worker/static/`에 mount되며 `/ui/`로 서빙된다 (없으면 mount 생략).
외부 origin(예: Vite dev server)에서 API를 호출할 수 있도록 localhost CORS를 허용한다.

실행: py worker/dashboard_server.py
바인딩: 127.0.0.1:8765 (외부 노출 없음)
"""

from __future__ import annotations

import html
import json
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "_workspace" / "_memory" / "observations" / "observations.db"
TELEMETRY_DIR = REPO_ROOT / "_workspace" / "_telemetry"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
CLAUDE_DIR = REPO_ROOT / ".claude"
SETTINGS = CLAUDE_DIR / "settings.json"
STATIC_DIR = Path(__file__).resolve().parent / "static"
CACHE_TTL_SEC = 300

app = FastAPI(title="CM Dashboard")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(127\.0\.0\.1|localhost)(:\d+)?$",
    allow_methods=["GET"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/ui", StaticFiles(directory=STATIC_DIR, html=True), name="ui")

_cache: dict[str, tuple[float, tuple, object]] = {}


# ---------------------------- cache ----------------------------

def _project_mtimes() -> tuple:
    def _mt(p: Path) -> float:
        return p.stat().st_mtime if p.exists() else 0.0

    db_mtime = _mt(DB_PATH)
    tmt = max(
        (p.stat().st_mtime for p in TELEMETRY_DIR.glob("*.jsonl")),
        default=0.0,
    ) if TELEMETRY_DIR.exists() else 0.0
    return (db_mtime, tmt, _mt(CLAUDE_MD), _mt(SETTINGS))


def _cached(key: str, mtimes: tuple, builder):
    now = time.time()
    if key in _cache:
        ts, cached_mtimes, value = _cache[key]
        if cached_mtimes == mtimes and now - ts < CACHE_TTL_SEC:
            return value
    value = builder()
    _cache[key] = (now, mtimes, value)
    return value


# ---------------------------- DB ----------------------------

def _connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise HTTPException(503, "observations.db missing — start a Claude Code session to bootstrap")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _load_telemetry(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TEMP TABLE IF NOT EXISTS telemetry_tool_outputs (
            ts TEXT, tool TEXT, raw_size INTEGER,
            compressed_size INTEGER, ratio REAL
        )
    """)
    conn.execute("DELETE FROM telemetry_tool_outputs")
    if not TELEMETRY_DIR.exists():
        return
    rows = []
    for path in TELEMETRY_DIR.glob("*.jsonl"):
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if evt.get("type") != "tool_output_captured":
                    continue
                rows.append((
                    evt.get("ts"), evt.get("tool"),
                    evt.get("raw_size"), evt.get("compressed_size"),
                    evt.get("ratio"),
                ))
    if rows:
        conn.executemany(
            "INSERT INTO telemetry_tool_outputs VALUES (?, ?, ?, ?, ?)",
            rows,
        )


def _telemetry_tool_timeline() -> list[dict]:
    if not TELEMETRY_DIR.exists():
        return []
    bucket: dict[tuple[str, str], int] = {}
    for path in TELEMETRY_DIR.glob("*.jsonl"):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue
            if evt.get("type") != "tool_output_captured":
                continue
            ts = evt.get("ts", "")[:10]
            tool = evt.get("tool", "?")
            bucket[(ts, tool)] = bucket.get((ts, tool), 0) + 1
    return [
        {"date": d, "tool": t, "count": n}
        for (d, t), n in sorted(bucket.items())
    ]


# ---------------------------- views ----------------------------

def view_sessions() -> list[dict]:
    def build():
        with closing(_connect()) as conn:
            cur = conn.execute("""
                SELECT s.session_id, s.date, s.started_at, s.ended_at,
                       s.duration_min, s.tools_used, s.project,
                       SUM(CASE WHEN o.section='do' AND o.completed=0 THEN 1 ELSE 0 END) AS pending_count,
                       SUM(CASE WHEN o.section='warn' THEN 1 ELSE 0 END) AS warn_count,
                       CASE WHEN s.digest_path IS NOT NULL THEN 1 ELSE 0 END AS has_digest
                FROM sessions s
                LEFT JOIN observations o ON s.session_id = o.session_id
                GROUP BY s.session_id
                ORDER BY s.date DESC, s.started_at DESC
                LIMIT 30
            """)
            return [dict(r) for r in cur]
    return _cached("sessions", _project_mtimes(), build)


def view_clusters() -> list[dict]:
    def build():
        with closing(_connect()) as conn:
            cur = conn.execute("""
                SELECT cluster_id, theme, confidence, member_count,
                       promoted_path, last_accessed,
                       CAST(julianday('now') - julianday(last_accessed) AS INTEGER) AS days_since_access
                FROM clusters
                ORDER BY confidence DESC
            """)
            return [dict(r) for r in cur]
    return _cached("clusters", _project_mtimes(), build)


def view_compression() -> list[dict]:
    def build():
        with closing(_connect()) as conn:
            _load_telemetry(conn)
            cur = conn.execute("""
                SELECT tool,
                       COUNT(*) AS call_count,
                       AVG(raw_size) AS avg_raw,
                       AVG(compressed_size) AS avg_compressed,
                       AVG(ratio) AS avg_ratio
                FROM telemetry_tool_outputs
                WHERE date(ts) >= date('now', '-30 days')
                GROUP BY tool
                ORDER BY call_count DESC
            """)
            return [dict(r) for r in cur]
    return _cached("compression", _project_mtimes(), build)


def view_pending() -> list[dict]:
    def build():
        with closing(_connect()) as conn:
            cur = conn.execute("""
                SELECT content, session_id, date, tags
                FROM observations
                WHERE section='do' AND completed=0
                ORDER BY date DESC
            """)
            return [dict(r) for r in cur]
    return _cached("pending", _project_mtimes(), build)


def view_tool_timeline() -> list[dict]:
    return _cached(
        "tool_timeline",
        _project_mtimes(),
        _telemetry_tool_timeline,
    )


def view_rollup() -> dict:
    def build():
        out = {"name": REPO_ROOT.name, "path": str(REPO_ROOT)}
        try:
            with closing(_connect()) as conn:
                row = conn.execute("""
                    SELECT COUNT(*) AS sessions,
                           MIN(date) AS first_date,
                           MAX(date) AS last_date,
                           COALESCE(SUM(duration_min), 0) AS total_min
                    FROM sessions
                """).fetchone()
                out["sessions"] = row["sessions"] or 0
                out["first_date"] = row["first_date"]
                out["last_date"] = row["last_date"]
                out["total_minutes"] = row["total_min"] or 0
                out["clusters"] = conn.execute("SELECT COUNT(*) FROM clusters").fetchone()[0]
                out["pending"] = conn.execute(
                    "SELECT COUNT(*) FROM observations WHERE section='do' AND completed=0"
                ).fetchone()[0]
                out["status"] = "ok"
        except HTTPException:
            out.update({"sessions": 0, "clusters": 0, "pending": 0, "status": "no_db"})
        return out
    return _cached("rollup", _project_mtimes(), build)


# ---------------------------- inventory scanner ----------------------------

YAML_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(text: str) -> dict:
    """경량 YAML frontmatter 파서 (상위 키만 string으로 추출)."""
    m = YAML_FRONTMATTER_RE.match(text)
    if not m:
        return {}
    out: dict[str, str] = {}
    block = m.group(1)
    current_key: str | None = None
    buf: list[str] = []
    for line in block.splitlines():
        if re.match(r"^[A-Za-z_][A-Za-z0-9_-]*\s*:", line):
            if current_key is not None:
                out[current_key] = " ".join(b for b in buf if b).strip()
            key, _, rest = line.partition(":")
            current_key = key.strip()
            head = rest.strip()
            if head in ("|", ">", "|-", ">-"):
                head = ""
            buf = [head] if head else []
        elif current_key is not None:
            buf.append(line.strip())
    if current_key is not None:
        out[current_key] = " ".join(b for b in buf if b).strip()
    return out


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(REPO_ROOT))
    except ValueError:
        return str(p)


def scan_inventory() -> dict:
    """dharness 산출물 스캔: .claude/{skills,agents,commands} + plugins/harness/{skills,commands}."""
    skills: list[dict] = []
    agents: list[dict] = []
    commands: list[dict] = []

    skill_globs = [
        CLAUDE_DIR / "skills",
        REPO_ROOT / "plugins" / "harness" / "skills",
    ]
    for skills_dir in skill_globs:
        if not skills_dir.exists():
            continue
        for skill_md in skills_dir.glob("*/SKILL.md"):
            try:
                text = skill_md.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            fm = _parse_frontmatter(text)
            skills.append({
                "name": fm.get("name") or skill_md.parent.name,
                "description": fm.get("description", "")[:240],
                "path": _rel(skill_md),
            })

    agents_dir = CLAUDE_DIR / "agents"
    if agents_dir.exists():
        for agent_md in agents_dir.glob("*.md"):
            try:
                text = agent_md.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            fm = _parse_frontmatter(text)
            agents.append({
                "name": fm.get("name") or agent_md.stem,
                "description": fm.get("description", "")[:240],
                "tools": fm.get("tools", ""),
                "model": fm.get("model", ""),
                "path": _rel(agent_md),
            })

    command_globs = [
        CLAUDE_DIR / "commands",
        REPO_ROOT / "plugins" / "harness" / "commands",
    ]
    for cmd_dir in command_globs:
        if not cmd_dir.exists():
            continue
        for cmd_md in cmd_dir.glob("*.md"):
            try:
                text = cmd_md.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            fm = _parse_frontmatter(text)
            commands.append({
                "name": cmd_md.stem,
                "description": fm.get("description", "")[:240],
                "path": _rel(cmd_md),
            })

    hooks: list[dict] = []
    mcp: list[dict] = []
    for settings_path in (SETTINGS, CLAUDE_DIR / "settings.local.json"):
        if not settings_path.exists():
            continue
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for event, configs in (settings.get("hooks") or {}).items():
            if not isinstance(configs, list):
                continue
            for cfg in configs:
                for h in (cfg.get("hooks") or []):
                    hooks.append({
                        "event": event,
                        "matcher": cfg.get("matcher", ""),
                        "type": h.get("type", ""),
                        "command": (h.get("command", "") or "")[:240],
                        "source": settings_path.name,
                    })
        for name, cfg in (settings.get("mcpServers") or {}).items():
            mcp.append({
                "name": name,
                "command": cfg.get("command", "") if isinstance(cfg, dict) else "",
                "args": cfg.get("args", []) if isinstance(cfg, dict) else [],
            })

    return {
        "skills": sorted(skills, key=lambda s: s["name"]),
        "agents": sorted(agents, key=lambda a: a["name"]),
        "commands": sorted(commands, key=lambda c: c["name"]),
        "hooks": hooks,
        "mcp": mcp,
        "totals": {
            "skills": len(skills),
            "agents": len(agents),
            "commands": len(commands),
            "hooks": len(hooks),
            "mcp": len(mcp),
        },
    }


# ---------------------------- roadmap parser ----------------------------

ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def _split_row(line: str) -> list[str]:
    inner = line.strip().strip("|")
    return [c.strip() for c in inner.split("|")]


def parse_roadmap() -> list[dict]:
    """CLAUDE.md에서 markdown 표 추출 + 직전 heading을 표 제목으로."""
    if not CLAUDE_MD.exists():
        return []
    try:
        lines = CLAUDE_MD.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    tables: list[dict] = []
    last_heading = ""
    last_heading_level = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        h = HEADING_RE.match(line)
        if h:
            last_heading_level = len(h.group(1))
            last_heading = h.group(2)
            i += 1
            continue
        if (
            ROW_RE.match(line)
            and i + 1 < len(lines)
            and SEP_RE.match(lines[i + 1])
        ):
            header = _split_row(line)
            j = i + 2
            rows = []
            while j < len(lines) and ROW_RE.match(lines[j]) and not SEP_RE.match(lines[j]):
                rows.append(_split_row(lines[j]))
                j += 1
            tables.append({
                "title": last_heading,
                "heading_level": last_heading_level,
                "header": header,
                "rows": rows,
                "row_count": len(rows),
            })
            i = j
            continue
        i += 1
    return tables


# ---------------------------- API ----------------------------

@app.get("/api/rollup")
def api_rollup() -> JSONResponse:
    return JSONResponse(view_rollup())


@app.get("/api/sessions")
def api_sessions() -> JSONResponse:
    return JSONResponse(view_sessions())


@app.get("/api/clusters")
def api_clusters() -> JSONResponse:
    return JSONResponse(view_clusters())


@app.get("/api/compression")
def api_compression() -> JSONResponse:
    return JSONResponse(view_compression())


@app.get("/api/pending")
def api_pending() -> JSONResponse:
    return JSONResponse(view_pending())


@app.get("/api/tool-timeline")
def api_tool_timeline() -> JSONResponse:
    return JSONResponse(view_tool_timeline())


@app.get("/api/inventory")
def api_inventory() -> JSONResponse:
    return JSONResponse(_cached("inventory", _project_mtimes(), scan_inventory))


@app.get("/api/roadmap")
def api_roadmap() -> JSONResponse:
    return JSONResponse(_cached("roadmap", _project_mtimes(), parse_roadmap))


# ---------------------------- minimal HTML index ----------------------------

@app.get("/", response_class=HTMLResponse)
def landing() -> str:
    """프론트엔드(/ui/) 미설치 시 보이는 minimal API 인덱스."""
    if (STATIC_DIR / "index.html").exists():
        return (
            '<!doctype html><meta charset="utf-8">'
            '<title>CM Dashboard</title>'
            '<meta http-equiv="refresh" content="0;url=/ui/">'
            'Redirecting to <a href="/ui/">/ui/</a>...'
        )
    routes = [
        "/api/rollup",
        "/api/sessions",
        "/api/clusters",
        "/api/compression",
        "/api/pending",
        "/api/tool-timeline",
        "/api/inventory",
        "/api/roadmap",
    ]
    route_list = "".join(f"<li><code>{html.escape(r)}</code></li>" for r in routes)
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>CM Dashboard (API)</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:920px;margin:2em auto;padding:0 1em;color:#222}}
code{{background:#f3f3f3;padding:.1em .3em;border-radius:3px}}
.note{{color:#666;font-size:.9em}}
</style></head>
<body>
<h1>CM Dashboard — {html.escape(REPO_ROOT.name)}</h1>
<p class="note">dharness self-host. Frontend not installed. Drop static build into
<code>{html.escape(str(STATIC_DIR))}</code> to serve UI at <code>/ui/</code>.
Build at: {html.escape(time.strftime("%Y-%m-%d %H:%M:%S"))}</p>

<h2>Endpoints</h2>
<ul>{route_list}</ul>
</body></html>"""


def main() -> None:
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
