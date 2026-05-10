"""CM hook 공용 인프라 — DDL 단일 정의 + session_id 파일 기반 전달 + 도메인 분류기.

DDL은 본 모듈이 단일 진실 원천이다. observations/sessions/clusters/daily_summaries
4개 테이블 + observations_fts FTS5 가상 테이블을 정의한다.

session_id는 SessionStart hook 시점에 파일에 기록되고, PostToolUse/SessionEnd
hook이 같은 파일에서 읽는다. hook은 별도 프로세스이므로 환경 변수로는 전달되지 않는다.

dharness self-host 한정 — REPO_ROOT는 본 모듈 위치(.claude/hooks/_schema.py)에서
parents[2]로 결정적 계산. ${CLAUDE_PROJECT_DIR} 의존 없음, walk-up fallback 없음.

도메인 분류기(classify_dharness_event)는 file path 기반 deterministic 매핑으로
PostToolUse 시점에 dharness 진화 이벤트를 추출한다. LLM 호출 없음.
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

for _stream in (sys.stdin, sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


REPO_ROOT = Path(__file__).resolve().parents[2]
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
  created_at TEXT NOT NULL,
  category TEXT,
  artifact_kind TEXT,
  phase TEXT
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
CREATE INDEX IF NOT EXISTS observations_category_idx ON observations(category);
CREATE INDEX IF NOT EXISTS observations_artifact_kind_idx ON observations(artifact_kind);
"""


_MIGRATIONS: tuple[tuple[str, str], ...] = (
    ("category", "TEXT"),
    ("artifact_kind", "TEXT"),
    ("phase", "TEXT"),
)


def ensure_migrations(conn: sqlite3.Connection) -> list[str]:
    """기존 observations 테이블에 누락된 컬럼을 ALTER TABLE로 추가. 추가된 컬럼명 반환."""
    cur = conn.execute("PRAGMA table_info(observations)")
    existing = {row[1] for row in cur.fetchall()}
    if not existing:
        return []
    added: list[str] = []
    for col, typ in _MIGRATIONS:
        if col not in existing:
            conn.execute(f"ALTER TABLE observations ADD COLUMN {col} {typ}")
            added.append(col)
    if added:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS observations_category_idx ON observations(category)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS observations_artifact_kind_idx ON observations(artifact_kind)"
        )
    return added


# ---------------------------- domain classifier ----------------------------

# (regex, category, artifact_kind). 첫 매칭 채택. 데이터 경로/캐시는 None 분류.
_FILE_RULES: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (re.compile(r"^_workspace/"), "", ""),  # data path — skip
    (re.compile(r"__pycache__/"), "", ""),
    (re.compile(r"\.git/"), "", ""),
    (re.compile(r"^plugins/harness/skills/harness/SKILL\.md$"), "harness_skill_edit", "skill"),
    (re.compile(r"^plugins/harness/skills/harness/references/.+\.md$"), "harness_reference_edit", "reference"),
    (re.compile(r"^plugins/harness/commands/.+\.md$"), "harness_command_edit", "command"),
    (re.compile(r"^plugins/harness/\.claude-plugin/plugin\.json$"), "harness_manifest_edit", "plugin_manifest"),
    (re.compile(r"^plugins/harness/"), "harness_other_edit", "harness"),
    (re.compile(r"^\.claude/hooks/_schema\.py$"), "cm_schema_edit", "schema"),
    (re.compile(r"^\.claude/hooks/.+\.py$"), "cm_hook_edit", "hook"),
    (re.compile(r"^\.claude/skills/[^/]+/SKILL\.md$"), "cm_skill_edit", "skill"),
    (re.compile(r"^\.claude/skills/"), "cm_skill_other_edit", "skill"),
    (re.compile(r"^\.claude/commands/.+\.md$"), "cm_command_edit", "command"),
    (re.compile(r"^\.claude/settings.*\.json$"), "cm_settings_edit", "settings"),
    (re.compile(r"^\.claude/agents/.+\.md$"), "cm_agent_edit", "agent"),
    (re.compile(r"^worker/static/"), "cm_worker_static_edit", "worker_static"),
    (re.compile(r"^worker/README\.md$"), "cm_doc_edit", "doc"),
    (re.compile(r"^worker/requirements\.txt$"), "cm_deps_edit", "deps"),
    (re.compile(r"^worker/.+\.py$"), "cm_worker_edit", "worker"),
    (re.compile(r"^CLAUDE\.md$"), "claudemd_edit", "claude_md"),
    (re.compile(r"^\.claude-plugin/marketplace\.json$"), "marketplace_edit", "plugin_manifest"),
    (re.compile(r"^README\.md$"), "readme_edit", "doc"),
    (re.compile(r"^\.gitignore$"), "gitignore_edit", "config"),
)

_GIT_SUBCOMMAND_RE = re.compile(r"^\s*git\s+(\S+)")
_GIT_RELEVANT = {
    "commit": ("git_commit", "git"),
    "add": ("git_add", "git"),
    "rm": ("git_rm", "git"),
    "mv": ("git_mv", "git"),
    "push": ("git_push", "git"),
    "pull": ("git_pull", "git"),
    "checkout": ("git_checkout", "git"),
    "merge": ("git_merge", "git"),
    "rebase": ("git_rebase", "git"),
    "reset": ("git_reset", "git"),
    "tag": ("git_tag", "git"),
}

_FILE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def _to_rel(file_path: str | None) -> str | None:
    if not file_path:
        return None
    try:
        p = Path(file_path)
        if p.is_absolute():
            p = p.resolve().relative_to(REPO_ROOT)
        return str(p).replace("\\", "/")
    except (ValueError, OSError):
        return None


def classify_dharness_event(tool_name: str, tool_input: dict) -> dict | None:
    """tool_input에서 dharness 도메인 이벤트 추출. 미해당이면 None.

    반환: {category, artifact_kind, content, tags(list[str])}
    """
    if tool_name in _FILE_TOOLS:
        rel = _to_rel(tool_input.get("file_path"))
        if not rel:
            return None
        for pattern, category, artifact_kind in _FILE_RULES:
            if pattern.search(rel):
                if not category:
                    return None  # explicit skip
                return {
                    "category": category,
                    "artifact_kind": artifact_kind,
                    "content": f"{tool_name} {rel}",
                    "tags": [tool_name.lower(), category, artifact_kind],
                }
        return None
    if tool_name == "Bash":
        command = tool_input.get("command", "") or ""
        m = _GIT_SUBCOMMAND_RE.match(command)
        if not m:
            return None
        sub = m.group(1)
        mapped = _GIT_RELEVANT.get(sub)
        if not mapped:
            return None
        category, artifact_kind = mapped
        head = command.strip().splitlines()[0]
        if len(head) > 200:
            head = head[:199] + "…"
        return {
            "category": category,
            "artifact_kind": artifact_kind,
            "content": head,
            "tags": ["bash", category, artifact_kind],
        }
    return None


# ---------------------------- session id helpers ----------------------------

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
