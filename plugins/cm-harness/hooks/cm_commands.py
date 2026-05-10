"""/cm-harness:cm-* 슬래시 커맨드 결정적 핸들러.

사용법 (dharness self-use, repo root에서):
    python plugins/cm-harness/hooks/cm_commands.py status
    python plugins/cm-harness/hooks/cm_commands.py sessions [--limit N]
    python plugins/cm-harness/hooks/cm_commands.py clusters [--min-confidence X.XX]
    python plugins/cm-harness/hooks/cm_commands.py dashboard
    python plugins/cm-harness/hooks/cm_commands.py init
    python plugins/cm-harness/hooks/cm_commands.py reset --confirm

/cm-harness:cm-curate는 LLM 작업이므로 plugins/cm-harness/commands/cm-curate.md가
cm-curator 에이전트를 직접 호출한다. 이 스크립트는 결정적 작업만 처리한다.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
import urllib.error
import urllib.request

from _schema import DB_PATH, DDL, MEMORY_ROOT, REPO_ROOT, TELEMETRY_DIR, TOOL_OUTPUTS

DASHBOARD_URL = "http://127.0.0.1:8765/"
COUNT_TABLES = ("observations", "sessions", "clusters", "daily_summaries")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_db() -> bool:
    if DB_PATH.exists():
        return True
    print("observations.db 미존재 — /cm-harness:cm-init 먼저 실행하세요.")
    return False


def cmd_status() -> int:
    if not _ensure_db():
        return 1
    with _connect() as conn:
        counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in COUNT_TABLES}
        recent = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE date(started_at) >= date('now', '-7 days')"
        ).fetchone()[0]
        digested = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE date(started_at) >= date('now', '-7 days') AND digest_path IS NOT NULL"
        ).fetchone()[0]
        promoted = conn.execute("SELECT COUNT(*) FROM clusters WHERE promoted_path IS NOT NULL").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM observations WHERE section='do' AND completed=0").fetchone()[0]

    print(f"📊 CM 상태 ({REPO_ROOT.name})")
    print(f"  observations:     {counts['observations']}")
    print(f"  sessions:         {counts['sessions']} (최근 7일: {recent}, digest: {digested})")
    print(f"  clusters:         {counts['clusters']} (승격 {promoted})")
    print(f"  daily_summaries:  {counts['daily_summaries']}")
    print(f"  pending Do:       {pending}")
    return 0


def cmd_sessions(limit: int) -> int:
    if not _ensure_db():
        return 1
    with _connect() as conn:
        rows = conn.execute("""
            SELECT session_id, date, duration_min,
                   CASE WHEN digest_path IS NOT NULL THEN '✓' ELSE '·' END AS d,
                   tools_used
            FROM sessions ORDER BY date DESC, started_at DESC LIMIT ?
        """, (limit,)).fetchall()
    print(f"📅 최근 {len(rows)}개 세션")
    for r in rows:
        dur = f"{r['duration_min']}m" if r['duration_min'] else "—"
        print(f"  {r['date']} {r['session_id']} {dur:>5} {r['d']} tools={r['tools_used'] or '[]'}")
    return 0


def cmd_clusters(min_conf: float) -> int:
    if not _ensure_db():
        return 1
    with _connect() as conn:
        rows = conn.execute("""
            SELECT cluster_id, theme, confidence, member_count, last_accessed,
                   CAST(julianday('now') - julianday(last_accessed) AS INTEGER) AS days_since,
                   CASE WHEN promoted_path IS NOT NULL THEN '🏷️' ELSE '·' END AS p
            FROM clusters WHERE confidence >= ? ORDER BY confidence DESC
        """, (min_conf,)).fetchall()
    print(f"🧠 클러스터 {len(rows)}개 (confidence ≥ {min_conf})")
    for r in rows:
        ds = f"{r['days_since']}d" if r['days_since'] is not None else "—"
        print(f"  {r['p']} {r['confidence']:.2f} {r['cluster_id']} {r['theme'][:40]:40} (members={r['member_count']}, last={ds})")
    return 0


def cmd_dashboard() -> int:
    try:
        with urllib.request.urlopen(DASHBOARD_URL, timeout=1) as resp:
            if resp.status == 200:
                print(f"✅ Worker 실행 중: {DASHBOARD_URL}")
                return 0
    except (urllib.error.URLError, TimeoutError):
        pass
    print("Worker 미실행. 다음 명령으로 시작:")
    print("    python plugins/cm-harness/worker/dashboard_server.py")
    print("기본 포트 8765, 127.0.0.1만 바인딩 (외부 노출 없음).")
    return 1


def cmd_init() -> int:
    created = []
    # daily_summaries는 SQL 테이블에만 존재 (DB observations.db) — 디렉토리 불필요.
    for sub in ("sessions", "observations", "clusters"):
        p = MEMORY_ROOT / sub
        existed = p.exists()
        p.mkdir(parents=True, exist_ok=True)
        created.append((p, existed))
    for p in (TELEMETRY_DIR / "_rollback", TOOL_OUTPUTS):
        existed = p.exists()
        p.mkdir(parents=True, exist_ok=True)
        created.append((p, existed))

    db_existed = DB_PATH.exists()
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(DDL)
    created.append((DB_PATH, db_existed))

    for p, existed in created:
        marker = "(existing)" if existed else "(created)"
        print(f"  {'✅' if existed else '🆕'} {p.relative_to(REPO_ROOT)} {marker}")
    return 0


def cmd_reset(confirmed: bool) -> int:
    if not confirmed:
        print("⚠️  --confirm 플래그 없이는 실행 불가. /cm-harness:cm-reset 슬래시 커맨드 본문의 확인 절차를 따르세요.")
        return 1
    if MEMORY_ROOT.exists():
        shutil.rmtree(MEMORY_ROOT)
    if TOOL_OUTPUTS.exists():
        shutil.rmtree(TOOL_OUTPUTS)
    print("🗑️  _memory/, _tool_outputs/ 삭제됨")
    return cmd_init()


def main() -> int:
    parser = argparse.ArgumentParser(prog="cm")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    p_sessions = sub.add_parser("sessions"); p_sessions.add_argument("--limit", type=int, default=30)
    p_clusters = sub.add_parser("clusters"); p_clusters.add_argument("--min-confidence", type=float, default=0.0)
    sub.add_parser("dashboard")
    sub.add_parser("init")
    p_reset = sub.add_parser("reset"); p_reset.add_argument("--confirm", action="store_true")

    args = parser.parse_args()
    if args.cmd == "status":    return cmd_status()
    if args.cmd == "sessions":  return cmd_sessions(args.limit)
    if args.cmd == "clusters":  return cmd_clusters(args.min_confidence)
    if args.cmd == "dashboard": return cmd_dashboard()
    if args.cmd == "init":      return cmd_init()
    if args.cmd == "reset":     return cmd_reset(args.confirm)
    return 2


if __name__ == "__main__":
    sys.exit(main())
