"""CM hook 공용 인프라 — DDL 단일 정의 + session_id 파일 기반 전달.

DDL은 본 모듈이 단일 진실 원천이다. observations/sessions/clusters/daily_summaries
4개 테이블 + observations_fts FTS5 가상 테이블을 정의한다.

session_id는 SessionStart hook 시점에 파일에 기록되고, PostToolUse/SessionEnd
hook이 같은 파일에서 읽는다. hook은 별도 프로세스이므로 환경 변수로는 전달되지 않는다.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

for _stream in (sys.stdin, sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

def _walk_up_for_workspace() -> Path:
    """Plugin install 시 CLAUDE_PROJECT_DIR이 항상 set되어 이 fallback은 미사용.
    dharness self-use에서 manual `py plugins/cm-harness/hooks/cm_commands.py status`
    같은 직접 호출 시에만 도달. _workspace/ 디렉토리를 가진 가장 가까운 조상으로 올라감.
    """
    here = Path(__file__).resolve()
    for p in [here.parent, *here.parents]:
        if (p / "_workspace").is_dir():
            return p
    return here.parents[3]  # last resort: dharness/ from plugins/cm-harness/hooks/


_env_root = os.environ.get("CLAUDE_PROJECT_DIR")
REPO_ROOT = (
    Path(_env_root).resolve()
    if _env_root and Path(_env_root).is_dir()
    else _walk_up_for_workspace()
)
MEMORY_ROOT = REPO_ROOT / "_workspace" / "_memory"
DB_PATH = MEMORY_ROOT / "observations" / "observations.db"
TELEMETRY_DIR = REPO_ROOT / "_workspace" / "_telemetry"
TOOL_OUTPUTS = REPO_ROOT / "_workspace" / "_tool_outputs"
SESSION_ID_FILE = MEMORY_ROOT / ".current_session"

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


def write_session_id(session_id: str) -> None:
    SESSION_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_ID_FILE.write_text(session_id, encoding="utf-8")


def read_session_id() -> str | None:
    if not SESSION_ID_FILE.exists():
        return None
    sid = SESSION_ID_FILE.read_text(encoding="utf-8").strip()
    return sid or None


def clear_session_id() -> None:
    if SESSION_ID_FILE.exists():
        SESSION_ID_FILE.unlink()
