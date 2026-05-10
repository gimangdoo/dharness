"""SessionStart hook — session-capture 스킬의 결정적 부분 실행.

수행:
  1. session_id 발급 (UUIDv4 6자 hex)
  2. _workspace/_memory/sessions/{id}/ 부트스트랩 + raw.jsonl 빈 파일 생성
  3. observations.db 미존재 시 4개 테이블 + FTS5 초기화 (스키마는 _schema.py)
  4. sessions 테이블 INSERT
  5. session_id를 _memory/.current_session에 기록 (다른 hook이 읽음)
  6. _workspace/_telemetry/{date}.jsonl에 session_capture_init + harness_invocation 이벤트 append
  7. stdout으로 hookSpecificOutput.additionalContext JSON 송출 (Claude Code 컨트랙트)

LLM 호출 없음. 빠르게 종료해야 SessionStart 지연이 없다.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import sys
import time
import uuid

from _schema import DDL, DB_PATH, MEMORY_ROOT, REPO_ROOT, TELEMETRY_DIR, write_session_id


def main() -> int:
    session_id = uuid.uuid4().hex[:6]
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    today = time.strftime("%Y-%m-%d", time.gmtime())

    sess_dir = MEMORY_ROOT / "sessions" / session_id
    sess_dir.mkdir(parents=True, exist_ok=True)
    (sess_dir / "raw.jsonl").touch()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(DDL)
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

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": (
                f"[CM] session_id={session_id} (project={REPO_ROOT.name}). "
                "cm-orchestrator 스킬을 통해 cm-injector를 호출하여 직전 세션 요약을 주입하라."
            ),
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
