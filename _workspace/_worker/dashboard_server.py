"""CM Dashboard Worker — 4개 뷰 SQLite 집계 + FastAPI 서빙.

LLM 호출 없는 결정적 데이터 집계. dashboard-render 스킬의 SQL 쿼리를 그대로 실행한다.

실행: python _workspace/_worker/dashboard_server.py
바인딩: 127.0.0.1:8765 (외부 노출 없음)
"""

from __future__ import annotations

import glob
import html
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "_workspace" / "_memory" / "observations" / "observations.db"
TELEMETRY_DIR = REPO_ROOT / "_workspace" / "_telemetry"
TELEMETRY_GLOB = str(TELEMETRY_DIR / "*.jsonl")
CACHE_TTL_SEC = 300

app = FastAPI(title="CM Dashboard")
_cache: dict[str, tuple[float, tuple[float, float], object]] = {}


def _data_mtimes() -> tuple[float, float]:
    db_mtime = DB_PATH.stat().st_mtime if DB_PATH.exists() else 0.0
    telemetry_mtime = max(
        (Path(p).stat().st_mtime for p in glob.glob(TELEMETRY_GLOB)),
        default=0.0,
    )
    return db_mtime, telemetry_mtime


def _cached(key: str, builder):
    now = time.time()
    mtimes = _data_mtimes()
    if key in _cache:
        ts, cached_mtimes, value = _cache[key]
        if cached_mtimes == mtimes and now - ts < CACHE_TTL_SEC:
            return value
    value = builder()
    _cache[key] = (now, mtimes, value)
    return value


def _connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise HTTPException(503, "observations.db not found: run /cm-init first")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _load_telemetry_into(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TEMP TABLE IF NOT EXISTS telemetry_tool_outputs (
            ts TEXT, tool TEXT, raw_size INTEGER,
            compressed_size INTEGER, ratio REAL
        )
    """)
    conn.execute("DELETE FROM telemetry_tool_outputs")
    rows = []
    for path in glob.glob(TELEMETRY_GLOB):
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if evt.get("type") != "tool_output_captured":
                    continue
                rows.append((
                    evt.get("ts"),
                    evt.get("tool"),
                    evt.get("raw_size"),
                    evt.get("compressed_size"),
                    evt.get("ratio"),
                ))
    if rows:
        conn.executemany(
            "INSERT INTO telemetry_tool_outputs VALUES (?, ?, ?, ?, ?)",
            rows,
        )


def view_sessions() -> list[dict]:
    def build():
        with closing(_connect()) as conn:
            cur = conn.execute("""
                SELECT s.session_id, s.date, s.duration_min,
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
    return _cached("sessions", build)


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
    return _cached("clusters", build)


def view_compression() -> list[dict]:
    def build():
        with closing(_connect()) as conn:
            _load_telemetry_into(conn)
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
    return _cached("compression", build)


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
    return _cached("pending", build)


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


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    sessions = view_sessions()
    clusters = view_clusters()
    compression = view_compression()
    pending = view_pending()

    def render_table(rows: list[dict]) -> str:
        if not rows:
            return "<p><em>(no rows)</em></p>"
        cols = list(rows[0].keys())
        head = "".join(f"<th>{html.escape(str(c))}</th>" for c in cols)
        body = "".join(
            "<tr>" + "".join(f"<td>{html.escape(str(r[c])) if r[c] is not None else ''}</td>" for c in cols) + "</tr>"
            for r in rows
        )
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>CM Dashboard</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:1100px;margin:2em auto;padding:0 1em}}
h2{{border-bottom:1px solid #ddd;padding-bottom:.3em;margin-top:2em}}
table{{border-collapse:collapse;width:100%;font-size:.9em}}
th,td{{border:1px solid #ddd;padding:.4em .6em;text-align:left}}
th{{background:#f5f5f5}}
</style></head>
<body>
<h1>CM Dashboard</h1>
<p>Auto-refresh: 5 min cache. Last build: {time.strftime("%Y-%m-%d %H:%M:%S")}</p>

<h2>📅 세션 타임라인 (최근 30개)</h2>
{render_table(sessions)}

<h2>🧠 메모리 클러스터 ({len(clusters)}개)</h2>
{render_table(clusters)}

<h2>📦 도구 출력 압축 통계 (최근 30일)</h2>
{render_table(compression)}

<h2>📋 미완료 작업 ({len(pending)}개)</h2>
{render_table(pending)}
</body></html>"""


def main() -> None:
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
