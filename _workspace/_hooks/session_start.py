"""SessionStart hook — session-capture 스킬의 결정적 부분 실행.

수행:
  1. 직전 세션이 dangling(ended_at IS NULL + raw.jsonl 비어있지 않음)인 경우 backfill finalize
     (이전 SessionEnd 훅이 발동되지 않고 종료된 세션 복구)
  2. session_id 발급 (UUIDv4 6자 hex)
  3. _workspace/_memory/sessions/{id}/ 부트스트랩 + raw.jsonl 빈 파일 생성
  4. observations.db 미존재 시 4개 테이블 + FTS5 초기화 (스키마는 _schema.py)
  5. sessions 테이블 INSERT
  6. session_id를 _memory/.current_session에 기록 (다른 hook이 읽음)
  7. _workspace/_telemetry/{date}.jsonl에 session_capture_init + harness_invocation 이벤트 append
  8. digest 누락 세션 목록을 additionalContext에 포함시켜 cm-orchestrator가 cm-digester
     backfill을 cm-injector 전에 수행하도록 지시
  9. stdout으로 hookSpecificOutput.additionalContext JSON 송출 (Claude Code 컨트랙트)

LLM 호출 없음. 빠르게 종료해야 SessionStart 지연이 없다.
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

DIGEST_BACKFILL_LIMIT = 5


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


def find_digest_backfill_candidates(conn: sqlite3.Connection, limit: int) -> list[str]:
    """종료되었지만 digest_path가 NULL인 세션 목록 (최신순, limit개)."""
    rows = conn.execute(
        "SELECT session_id FROM sessions "
        "WHERE ended_at IS NOT NULL AND digest_path IS NULL "
        "ORDER BY ended_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [r[0] for r in rows]


def main() -> int:
    session_id = uuid.uuid4().hex[:6]
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    today = time.strftime("%Y-%m-%d", time.gmtime())

    sess_dir = MEMORY_ROOT / "sessions" / session_id
    sess_dir.mkdir(parents=True, exist_ok=True)
    (sess_dir / "raw.jsonl").touch()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    backfilled: list[str] = []
    digest_pending: list[str] = []
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
            digest_pending = find_digest_backfill_candidates(conn, DIGEST_BACKFILL_LIMIT)
        except Exception as e:
            print(f"[CM SessionStart] digest_pending lookup skipped: {e}", file=sys.stderr)

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

    additional_context = (
        f"[CM] session_id={session_id} (project={REPO_ROOT.name}). "
        "cm-orchestrator 스킬을 통해 cm-injector를 호출하여 직전 세션 요약을 주입하라."
    )
    if digest_pending:
        sids_str = ", ".join(digest_pending)
        additional_context += (
            f" [CM Backfill] digest 누락 세션 {len(digest_pending)}건: {sids_str}. "
            "cm-injector 호출 *전*에 cm-orchestrator를 통해 cm-digester를 각 세션에 순차 호출하고, "
            "마지막에 cm-curator를 1회 호출하여 daily_summaries를 갱신하라. "
            "transcript 경로: _workspace/_memory/sessions/{sid}/transcript.md. "
            "토큰 예산을 고려해 가장 최근 1~3건만 처리해도 됨."
        )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional_context,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
