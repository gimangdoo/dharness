"""/cm-* 슬래시 커맨드 결정적 핸들러 (dharness self-host).

사용법 (repo root에서):
    py .claude/hooks/cm_commands.py status
    py .claude/hooks/cm_commands.py sessions [--limit N]
    py .claude/hooks/cm_commands.py dashboard
    py .claude/hooks/cm_commands.py reset --confirm

결정적 작업만 처리한다. Cluster/digest 생성은 워커 잡(worker/) 책임.
DB·디렉토리 부트스트랩은 SessionStart 훅 또는 reset 시 자동 수행되므로 별도 init 명령 없음.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
import urllib.error
import urllib.request

from _schema import DB_PATH, DDL, MEMORY_ROOT, REPO_ROOT, TOOL_OUTPUTS

DASHBOARD_URL = "http://127.0.0.1:8765/"
COUNT_TABLES = ("observations", "sessions", "clusters", "daily_summaries")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_db() -> bool:
    if DB_PATH.exists():
        return True
    print("observations.db 미존재 — 새 Claude Code 세션을 시작하면 SessionStart 훅이 자동 생성합니다.")
    return False


def _init_storage() -> list[tuple]:
    """디렉토리 + DB 스키마 부트스트랩. cmd_reset이 wipe 후 호출."""
    created = []
    for sub in ("sessions", "observations", "clusters"):
        p = MEMORY_ROOT / sub
        existed = p.exists()
        p.mkdir(parents=True, exist_ok=True)
        created.append((p, existed))
    existed = TOOL_OUTPUTS.exists()
    TOOL_OUTPUTS.mkdir(parents=True, exist_ok=True)
    created.append((TOOL_OUTPUTS, existed))

    db_existed = DB_PATH.exists()
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(DDL)
    created.append((DB_PATH, db_existed))
    return created


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


def cmd_dashboard() -> int:
    try:
        with urllib.request.urlopen(DASHBOARD_URL, timeout=1) as resp:
            if resp.status == 200:
                print(f"✅ Worker 실행 중: {DASHBOARD_URL}")
                return 0
    except (urllib.error.URLError, TimeoutError):
        pass
    print("Worker 미실행. 다음 명령으로 시작:")
    print("    py worker/dashboard_server.py")
    print("기본 포트 8765, 127.0.0.1만 바인딩 (외부 노출 없음).")
    return 1


def cmd_reset(confirmed: bool) -> int:
    if not confirmed:
        print("⚠️  --confirm 플래그 없이는 실행 불가. /cm-reset 슬래시 커맨드 본문의 확인 절차를 따르세요.")
        return 1
    if MEMORY_ROOT.exists():
        shutil.rmtree(MEMORY_ROOT)
    if TOOL_OUTPUTS.exists():
        shutil.rmtree(TOOL_OUTPUTS)
    print("🗑️  _memory/, _tool_outputs/ 삭제됨")
    for p, existed in _init_storage():
        marker = "(existing)" if existed else "(created)"
        print(f"  {'✅' if existed else '🆕'} {p.relative_to(REPO_ROOT)} {marker}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="cm")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    p_sessions = sub.add_parser("sessions"); p_sessions.add_argument("--limit", type=int, default=30)
    sub.add_parser("dashboard")
    p_reset = sub.add_parser("reset"); p_reset.add_argument("--confirm", action="store_true")

    args = parser.parse_args()
    if args.cmd == "status":    return cmd_status()
    if args.cmd == "sessions":  return cmd_sessions(args.limit)
    if args.cmd == "dashboard": return cmd_dashboard()
    if args.cmd == "reset":     return cmd_reset(args.confirm)
    return 2


if __name__ == "__main__":
    sys.exit(main())
