"""SessionStart hook — 세션 부트스트랩 + 직전 dangling 세션 finalize + daily_summary inject.

수행:
  1. 직전 세션이 dangling(ended_at IS NULL + raw.jsonl 비어있지 않음)인 경우 backfill finalize
     (이전 SessionEnd 훅이 발동되지 않고 종료된 세션 복구)
  2. session_id 발급 (UUIDv4 6자 hex)
  3. _workspace/_memory/sessions/{id}/ 부트스트랩 + raw.jsonl 빈 파일 생성
  4. observations.db 미존재 시 4개 테이블 + FTS5 초기화 (스키마는 _schema.py)
  5. sessions 테이블 INSERT
  6. session_id를 _memory/.current_session에 기록 (다른 hook이 읽음)
  7. _workspace/_telemetry/{date}.jsonl에 session_capture_init + harness_invocation 이벤트 append
  8. 최신 daily_summary가 있으면 첫 줄을 additionalContext로 inject (순수 데이터 주입)
  9. stdout으로 hookSpecificOutput.additionalContext JSON 송출 (Claude Code 컨트랙트)

LLM 호출도, LLM에 대한 instruction도 emit하지 않는다. 빠르게 종료.

Digest/cluster/daily_summary 생성은 별도 워커 잡(worker/dashboard_server.py 통합 예정)이
담당한다. 이 훅은 *읽기/주입*만 한다.
"""

from __future__ import annotations

import calendar
import json
import shutil
import sqlite3
import sys
import time
import uuid

from _schema import DDL, DB_PATH, MEMORY_ROOT, REPO_ROOT, TELEMETRY_DIR, write_session_id
from session_end import flatten_to_transcript

DAILY_SUMMARY_INJECT_MAX_CHARS = 800


def backfill_dangling_sessions(conn: sqlite3.Connection, now_iso: str) -> list[str]:
    """ended_at IS NULL + raw.jsonl 비어있지 않은 세션을 transcript 평탄화·UPDATE finalize.

    이전 세션의 SessionEnd 훅이 발동되지 않은 채 다음 SessionStart가 발생하면
    이전 세션이 영원히 ended_at=NULL로 남는다. 이 함수가 차순회 시 복구한다.
    """
    finalized: list[str] = []
    rows = conn.execute(
        "SELECT session_id, started_at FROM sessions WHERE ended_at IS NULL"
    ).fetchall()
    for sid, started_at in rows:
        sess_dir = MEMORY_ROOT / "sessions" / sid
        raw_path = sess_dir / "raw.jsonl"
        if not raw_path.exists() or raw_path.stat().st_size == 0:
            continue
        try:
            transcript, tools_used, raw_lines = flatten_to_transcript(raw_path)
        except Exception:
            continue
        if raw_lines == 0:
            continue
        transcript_path = sess_dir / "transcript.md"
        if transcript:
            transcript_path.write_text(transcript, encoding="utf-8")
        duration_min: int | None = None
        if started_at:
            try:
                started = calendar.timegm(time.strptime(started_at, "%Y-%m-%dT%H:%M:%SZ"))
                duration_min = max(0, int((time.time() - started) / 60))
            except ValueError:
                pass
        conn.execute(
            "UPDATE sessions SET ended_at=?, duration_min=?, tools_used=? WHERE session_id=?",
            (now_iso, duration_min, json.dumps(sorted(tools_used)), sid),
        )
        finalized.append(sid)
    return finalized


def fetch_latest_daily_summary(conn: sqlite3.Connection) -> tuple[str, str] | None:
    """가장 최근 daily_summary 1건의 (date, summary)를 반환. 없으면 None."""
    row = conn.execute(
        "SELECT date, summary FROM daily_summaries ORDER BY date DESC LIMIT 1"
    ).fetchone()
    if not row:
        return None
    return row[0], row[1]


def main() -> int:
    session_id = uuid.uuid4().hex[:6]
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    today = time.strftime("%Y-%m-%d", time.gmtime())

    sess_dir = MEMORY_ROOT / "sessions" / session_id
    sess_dir.mkdir(parents=True, exist_ok=True)
    (sess_dir / "raw.jsonl").touch()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    backfilled: list[str] = []
    latest_summary: tuple[str, str] | None = None
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(DDL)
        try:
            backfilled = backfill_dangling_sessions(conn, now_iso)
        except Exception as e:
            print(f"[CM SessionStart] dangling backfill skipped: {e}", file=sys.stderr)
        result = conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id, date, started_at, project) VALUES (?, ?, ?, ?)",
            (session_id, today, now_iso, REPO_ROOT.name),
        )
        if result.rowcount == 0:
            shutil.rmtree(sess_dir, ignore_errors=True)
            session_id = uuid.uuid4().hex[:8]
            sess_dir = MEMORY_ROOT / "sessions" / session_id
            sess_dir.mkdir(parents=True, exist_ok=True)
            (sess_dir / "raw.jsonl").touch()
            conn.execute(
                "INSERT INTO sessions (session_id, date, started_at, project) VALUES (?, ?, ?, ?)",
                (session_id, today, now_iso, REPO_ROOT.name),
            )
        try:
            latest_summary = fetch_latest_daily_summary(conn)
        except Exception as e:
            print(f"[CM SessionStart] daily_summary lookup skipped: {e}", file=sys.stderr)

    write_session_id(session_id)

    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    telemetry_path = TELEMETRY_DIR / f"{today}.jsonl"
    with open(telemetry_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "ts": now_iso, "type": "session_capture_init",
            "session_id": session_id, "project": REPO_ROOT.name,
        }) + "\n")
        fh.write(json.dumps({
            "ts": now_iso, "type": "harness_invocation",
            "event": "SessionStart", "handler": "session_start.py",
            "session_id": session_id,
        }) + "\n")
        if backfilled:
            fh.write(json.dumps({
                "ts": now_iso, "type": "session_backfill_finalize",
                "session_id": session_id, "backfilled": backfilled,
            }) + "\n")

    additional_context = f"[CM] session_id={session_id} (project={REPO_ROOT.name})."
    if latest_summary:
        date, summary = latest_summary
        if len(summary) > DAILY_SUMMARY_INJECT_MAX_CHARS:
            summary = summary[: DAILY_SUMMARY_INJECT_MAX_CHARS - 1] + "…"
        additional_context += f"\n[CM] 최근 요약 ({date}):\n{summary}"

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional_context,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
