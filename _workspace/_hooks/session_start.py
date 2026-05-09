"""SessionStart hook — session-capture 스킬의 결정적 부분 실행.

수행:
  1. session_id 발급 (UUIDv4 6자 hex)
  2. _workspace/_memory/sessions/{id}/ 부트스트랩 + raw.jsonl 빈 파일 생성
  3. observations.db 미존재 시 4개 테이블 + FTS5 초기화
  4. sessions 테이블 INSERT
  5. _workspace/_telemetry/{date}.jsonl에 session_capture_init 이벤트 append
  6. stdout으로 cm-injector 호출 지시 + CM_SESSION_ID 출력 (Claude Code가 추가 컨텍스트로 흡수)

LLM 호출 없음. 빠르게 종료해야 SessionStart 지연이 없다.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_ROOT = REPO_ROOT / "_workspace" / "_memory"
DB_PATH = MEMORY_ROOT / "observations" / "observations.db"
TELEMETRY_DIR = REPO_ROOT / "_workspace" / "_telemetry"

DDL = """
CREATE TABLE IF NOT EXISTS observations (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL, date TEXT NOT NULL,
  section TEXT NOT NULL, content TEXT NOT NULL, tags TEXT,
  embedding BLOB, completed INTEGER DEFAULT 0, cluster_id TEXT,
  created_at TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
  content, session_id, tags,
  content='observations', content_rowid='rowid'
);
CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY, date TEXT NOT NULL, started_at TEXT NOT NULL,
  ended_at TEXT, duration_min INTEGER, tools_used TEXT,
  digest_path TEXT, project TEXT
);
CREATE TABLE IF NOT EXISTS clusters (
  cluster_id TEXT PRIMARY KEY, theme TEXT NOT NULL, confidence REAL NOT NULL,
  member_count INTEGER NOT NULL DEFAULT 0, tags TEXT, embedding BLOB,
  promoted_path TEXT, created_at TEXT NOT NULL, last_updated TEXT NOT NULL,
  last_accessed TEXT
);
CREATE TABLE IF NOT EXISTS daily_summaries (
  date TEXT PRIMARY KEY, summary TEXT NOT NULL,
  session_ids TEXT NOT NULL, generated_at TEXT NOT NULL
);
"""


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
        conn.execute(
            "INSERT OR IGNORE INTO sessions (session_id, date, started_at, project) VALUES (?, ?, ?, ?)",
            (session_id, today, now_iso, REPO_ROOT.name),
        )

    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    telemetry_path = TELEMETRY_DIR / f"{today}.jsonl"
    with open(telemetry_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "ts": now_iso, "type": "session_capture_init",
            "session_id": session_id, "project": REPO_ROOT.name,
        }) + "\n")

    os.environ["CM_SESSION_ID"] = session_id

    print(f"[CM SessionStart] session_id={session_id} (project={REPO_ROOT.name})")
    print("[CM SessionStart] cm-orchestrator 스킬을 통해 cm-injector를 호출하여 직전 세션 요약을 주입하라.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
