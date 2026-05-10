"""CM Dashboard Worker — multi-project SQLite 집계 + FastAPI 서빙.

옵션 A 채택: 각 프로젝트는 자기 `_workspace/_memory/observations.db`를 보유한다.
대시보드는 `_workspace/projects.json`(수동 레지스트리)을 읽어 여러 프로젝트의 데이터를
독립적으로 조회한다 — cross-project SQL JOIN 없음. dharness 본체는 read-only.

LLM 호출 없는 결정적 데이터 집계. dashboard-render 스킬의 SQL을 그대로 실행한다.
정적 프론트엔드는 `_workspace/_worker/static/`에 mount되며 `/ui/`로 서빙된다
(없으면 mount 생략). 외부 origin(예: Vite dev server)에서 API를 호출할 수 있도록
localhost CORS를 허용한다.

실행: python _workspace/_worker/dashboard_server.py
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

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "_workspace" / "projects.json"
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


# ---------------------------- registry ----------------------------

def load_registry() -> list[dict]:
    """projects.json 로드. 없거나 비면 dharness 단일 fallback."""
    raw_projects: list[dict] = []
    if REGISTRY_PATH.exists():
        try:
            data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
            raw_projects = data.get("projects") or []
        except (json.JSONDecodeError, OSError):
            raw_projects = []
    if not raw_projects:
        raw_projects = [{"name": REPO_ROOT.name, "path": str(REPO_ROOT)}]

    out: list[dict] = []
    for p in raw_projects:
        path_str = p.get("path")
        if not path_str:
            continue
        path = Path(path_str).resolve()
        out.append({
            "name": p.get("name") or path.name,
            "path": str(path),
            "exists": path.exists(),
            "db": str(path / "_workspace" / "_memory" / "observations" / "observations.db"),
            "telemetry_dir": str(path / "_workspace" / "_telemetry"),
            "claude_md": str(path / "CLAUDE.md"),
            "claude_dir": str(path / ".claude"),
            "commands_dir": str(path / "commands"),
            "settings": str(path / ".claude" / "settings.json"),
        })
    return out


def find_project(name: str) -> dict:
    for p in load_registry():
        if p["name"] == name:
            return p
    raise HTTPException(404, f"project not found: {name}")


# ---------------------------- cache ----------------------------

def _project_mtimes(proj: dict) -> tuple:
    def _mt(p: str) -> float:
        path = Path(p)
        return path.stat().st_mtime if path.exists() else 0.0

    db_mtime = _mt(proj["db"])
    tdir = Path(proj["telemetry_dir"])
    tmt = max(
        (p.stat().st_mtime for p in tdir.glob("*.jsonl")),
        default=0.0,
    ) if tdir.exists() else 0.0
    return (db_mtime, tmt, _mt(proj["claude_md"]), _mt(proj["settings"]))


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

def _connect(proj: dict) -> sqlite3.Connection:
    db = Path(proj["db"])
    if not db.exists():
        raise HTTPException(503, f"observations.db missing for project={proj['name']}")
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn


def _load_telemetry(conn: sqlite3.Connection, proj: dict) -> None:
    conn.execute("""
        CREATE TEMP TABLE IF NOT EXISTS telemetry_tool_outputs (
            ts TEXT, tool TEXT, raw_size INTEGER,
            compressed_size INTEGER, ratio REAL
        )
    """)
    conn.execute("DELETE FROM telemetry_tool_outputs")
    tdir = Path(proj["telemetry_dir"])
    if not tdir.exists():
        return
    rows = []
    for path in tdir.glob("*.jsonl"):
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


def _telemetry_tool_timeline(proj: dict, days: int = 30) -> list[dict]:
    """일자별 도구 호출 횟수 (timeline용)."""
    tdir = Path(proj["telemetry_dir"])
    if not tdir.exists():
        return []
    bucket: dict[tuple[str, str], int] = {}
    for path in tdir.glob("*.jsonl"):
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


# ---------------------------- views (per-project) ----------------------------

def view_sessions(proj: dict) -> list[dict]:
    def build():
        with closing(_connect(proj)) as conn:
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
    return _cached(f"{proj['name']}:sessions", _project_mtimes(proj), build)


def view_clusters(proj: dict) -> list[dict]:
    def build():
        with closing(_connect(proj)) as conn:
            cur = conn.execute("""
                SELECT cluster_id, theme, confidence, member_count,
                       promoted_path, last_accessed,
                       CAST(julianday('now') - julianday(last_accessed) AS INTEGER) AS days_since_access
                FROM clusters
                ORDER BY confidence DESC
            """)
            return [dict(r) for r in cur]
    return _cached(f"{proj['name']}:clusters", _project_mtimes(proj), build)


def view_compression(proj: dict) -> list[dict]:
    def build():
        with closing(_connect(proj)) as conn:
            _load_telemetry(conn, proj)
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
    return _cached(f"{proj['name']}:compression", _project_mtimes(proj), build)


def view_pending(proj: dict) -> list[dict]:
    def build():
        with closing(_connect(proj)) as conn:
            cur = conn.execute("""
                SELECT content, session_id, date, tags
                FROM observations
                WHERE section='do' AND completed=0
                ORDER BY date DESC
            """)
            return [dict(r) for r in cur]
    return _cached(f"{proj['name']}:pending", _project_mtimes(proj), build)


def view_tool_timeline(proj: dict) -> list[dict]:
    return _cached(
        f"{proj['name']}:tool_timeline",
        _project_mtimes(proj),
        lambda: _telemetry_tool_timeline(proj),
    )


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


def scan_inventory(proj: dict) -> dict:
    """프로젝트의 .claude/, commands/ 디렉토리에서 산출물 스캔."""
    root = Path(proj["path"])
    claude_dir = Path(proj["claude_dir"])
    commands_dir = Path(proj["commands_dir"])

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(root))
        except ValueError:
            return str(p)

    skills: list[dict] = []
    if claude_dir.exists():
        for skill_md in (claude_dir / "skills").glob("*/SKILL.md"):
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

    agents: list[dict] = []
    if claude_dir.exists():
        for agent_md in (claude_dir / "agents").glob("*.md"):
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

    commands: list[dict] = []
    if commands_dir.exists():
        for cmd_md in commands_dir.glob("*.md"):
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
    settings_path = Path(proj["settings"])
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            settings = {}
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


def parse_roadmap(proj: dict) -> list[dict]:
    """CLAUDE.md에서 markdown 표 추출 + 직전 heading을 표 제목으로."""
    cmd = Path(proj["claude_md"])
    if not cmd.exists():
        return []
    try:
        lines = cmd.read_text(encoding="utf-8", errors="replace").splitlines()
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


# ---------------------------- API: projects ----------------------------

@app.get("/api/projects")
def api_projects() -> JSONResponse:
    out = []
    for p in load_registry():
        rollup = {
            "name": p["name"], "path": p["path"],
            "exists": p["exists"],
        }
        try:
            with closing(_connect(p)) as conn:
                row = conn.execute("""
                    SELECT COUNT(*) AS sessions,
                           MIN(date) AS first_date,
                           MAX(date) AS last_date,
                           COALESCE(SUM(duration_min), 0) AS total_min
                    FROM sessions
                """).fetchone()
                rollup["sessions"] = row["sessions"] or 0
                rollup["first_date"] = row["first_date"]
                rollup["last_date"] = row["last_date"]
                rollup["total_minutes"] = row["total_min"] or 0
                rollup["clusters"] = conn.execute(
                    "SELECT COUNT(*) FROM clusters"
                ).fetchone()[0]
                rollup["pending"] = conn.execute(
                    "SELECT COUNT(*) FROM observations WHERE section='do' AND completed=0"
                ).fetchone()[0]
                rollup["status"] = "ok"
        except HTTPException:
            rollup.update({
                "sessions": 0, "clusters": 0, "pending": 0,
                "status": "no_db",
            })
        out.append(rollup)
    return JSONResponse(out)


@app.get("/api/projects/{name}/sessions")
def api_p_sessions(name: str) -> JSONResponse:
    return JSONResponse(view_sessions(find_project(name)))


@app.get("/api/projects/{name}/clusters")
def api_p_clusters(name: str) -> JSONResponse:
    return JSONResponse(view_clusters(find_project(name)))


@app.get("/api/projects/{name}/compression")
def api_p_compression(name: str) -> JSONResponse:
    return JSONResponse(view_compression(find_project(name)))


@app.get("/api/projects/{name}/pending")
def api_p_pending(name: str) -> JSONResponse:
    return JSONResponse(view_pending(find_project(name)))


@app.get("/api/projects/{name}/tool-timeline")
def api_p_tool_timeline(name: str) -> JSONResponse:
    return JSONResponse(view_tool_timeline(find_project(name)))


@app.get("/api/projects/{name}/inventory")
def api_p_inventory(name: str) -> JSONResponse:
    proj = find_project(name)
    return JSONResponse(_cached(
        f"{name}:inventory",
        _project_mtimes(proj),
        lambda: scan_inventory(proj),
    ))


@app.get("/api/projects/{name}/roadmap")
def api_p_roadmap(name: str) -> JSONResponse:
    proj = find_project(name)
    return JSONResponse(_cached(
        f"{name}:roadmap",
        _project_mtimes(proj),
        lambda: parse_roadmap(proj),
    ))


# ---------------------------- API: backward-compat (default project) ----------------------------

def _default_project() -> dict:
    return load_registry()[0]


def _resolve(project: str | None) -> dict:
    return find_project(project) if project else _default_project()


@app.get("/api/sessions")
def api_sessions(project: str | None = Query(default=None)) -> JSONResponse:
    return JSONResponse(view_sessions(_resolve(project)))


@app.get("/api/clusters")
def api_clusters(project: str | None = Query(default=None)) -> JSONResponse:
    return JSONResponse(view_clusters(_resolve(project)))


@app.get("/api/compression")
def api_compression(project: str | None = Query(default=None)) -> JSONResponse:
    return JSONResponse(view_compression(_resolve(project)))


@app.get("/api/pending")
def api_pending(project: str | None = Query(default=None)) -> JSONResponse:
    return JSONResponse(view_pending(_resolve(project)))


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
    projects = load_registry()
    rows = "".join(
        f"<tr><td>{html.escape(p['name'])}</td><td>{html.escape(p['path'])}</td>"
        f"<td>{'yes' if p['exists'] else 'missing'}</td></tr>"
        for p in projects
    )
    routes = [
        "/api/projects",
        "/api/projects/{name}/sessions",
        "/api/projects/{name}/clusters",
        "/api/projects/{name}/compression",
        "/api/projects/{name}/pending",
        "/api/projects/{name}/tool-timeline",
        "/api/projects/{name}/inventory",
        "/api/projects/{name}/roadmap",
    ]
    route_list = "".join(f"<li><code>{html.escape(r)}</code></li>" for r in routes)
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>CM Dashboard (API)</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:920px;margin:2em auto;padding:0 1em;color:#222}}
table{{border-collapse:collapse;width:100%;font-size:.9em;margin:.5em 0}}
th,td{{border:1px solid #ddd;padding:.4em .6em;text-align:left}}
th{{background:#f5f5f5}}
code{{background:#f3f3f3;padding:.1em .3em;border-radius:3px}}
.note{{color:#666;font-size:.9em}}
</style></head>
<body>
<h1>CM Dashboard — API</h1>
<p class="note">Frontend not installed. Drop static build into
<code>{html.escape(str(STATIC_DIR))}</code> to serve UI at <code>/ui/</code>.
Build at: {html.escape(time.strftime("%Y-%m-%d %H:%M:%S"))}</p>

<h2>Registered projects ({len(projects)})</h2>
<table><thead><tr><th>name</th><th>path</th><th>status</th></tr></thead>
<tbody>{rows or '<tr><td colspan="3"><em>(none)</em></td></tr>'}</tbody></table>
<p class="note">Edit <code>_workspace/projects.json</code> to register more.</p>

<h2>Endpoints</h2>
<ul>{route_list}</ul>
</body></html>"""


def main() -> None:
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
