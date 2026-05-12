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

import calendar
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

for _stream in (sys.stdin, sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_ROOT = REPO_ROOT / "_workspace" / "_memory"
DB_PATH = MEMORY_ROOT / "observations" / "observations.db"
TELEMETRY_DIR = REPO_ROOT / "_workspace" / "_telemetry"
TOOL_OUTPUTS = REPO_ROOT / "_workspace" / "_tool_outputs"
DRAFTS_DIR = REPO_ROOT / "_workspace" / "_drafts"
DRAFTS_APPLIED = DRAFTS_DIR / "applied"
DRAFTS_DISCARDED = DRAFTS_DIR / "discarded"
SESSION_ID_FILE = MEMORY_ROOT / ".current_session"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
LAST_ADAPT_FILE = TELEMETRY_DIR / "_last_adapt"

# Phase 10 자동 adapt 알림 임계값. invocation/failure 누적이 이 값 도달 시
# SessionStart inject에 `/harness:harness-adapt` 권장 블록 추가.
HARNESS_ADAPT_THRESHOLD_INVOCATIONS = 10
HARNESS_ADAPT_THRESHOLD_FAILURES = 2

# CLAUDE.md draft 사유 컬럼 placeholder (session_end.py 생성, cm_commands.py 치환).
DRAFT_REASON_PLACEHOLDER = "(apply 전 작성 — 사유/맥락)"

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

# user_version=0: 컬럼 추가 전. user_version=1: category/artifact_kind/phase + 인덱스 적용 후.
SCHEMA_VERSION = 1


def ensure_migrations(conn: sqlite3.Connection) -> list[str]:
    """누락된 컬럼을 ALTER TABLE로 추가. PRAGMA user_version으로 빠른 short-circuit.

    매 hook 프로세스마다 호출되지만, 첫 번째 PRAGMA user_version 조회로 대부분 즉시 반환.
    SCHEMA_VERSION 미만일 때만 PRAGMA table_info → ALTER 흐름 진입.
    """
    current_version = conn.execute("PRAGMA user_version").fetchone()[0]
    if current_version >= SCHEMA_VERSION:
        return []

    cur = conn.execute("PRAGMA table_info(observations)")
    existing = {row[1] for row in cur.fetchall()}
    if not existing:
        # 빈 DB — DDL이 이미 최신 컬럼을 만들었음. version만 갱신.
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
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
    conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
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


# ---------------------------- adapt counter helpers ----------------------------

# Phase 10 자동 adapt 알림 카운터. `_workspace/_telemetry/*.jsonl`을 ascending 스캔해
# `_last_adapt` mtime 이후의 `harness_invocation` / `agent_invocation` / `agent_failure`
# 이벤트를 카운트한다. `_last_adapt`는 `/harness:harness-adapt` 완료 시 touch.

_COUNTED_TYPES = {"harness_invocation", "agent_invocation", "agent_failure"}


def read_last_adapt_ts() -> float:
    """`_last_adapt` mtime을 epoch float로 반환. 미존재 시 0.0 (= epoch 시작)."""
    if not LAST_ADAPT_FILE.exists():
        return 0.0
    try:
        return LAST_ADAPT_FILE.stat().st_mtime
    except OSError:
        return 0.0


def touch_last_adapt() -> None:
    """`/harness:harness-adapt` 완료 표지. 카운터 reset 트리거."""
    LAST_ADAPT_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_ADAPT_FILE.write_text(
        time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), encoding="utf-8"
    )


def _iter_telemetry_files_since(since_ts: float) -> list[Path]:
    """since_ts 이후 mtime 또는 today 파일만 반환 (소팅된 list)."""
    if not TELEMETRY_DIR.exists():
        return []
    out: list[Path] = []
    today = time.strftime("%Y-%m-%d", time.gmtime())
    for p in sorted(TELEMETRY_DIR.glob("*.jsonl")):
        try:
            if p.stat().st_mtime >= since_ts or p.stem == today:
                out.append(p)
        except OSError:
            continue
    return out


def _iso_to_epoch(iso: str) -> float | None:
    """`YYYY-MM-DDTHH:MM:SSZ` → epoch float. 실패 시 None."""
    if not iso:
        return None
    try:
        return float(calendar.timegm(time.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")))
    except (ValueError, TypeError):
        return None


def count_events_since_last_adapt() -> dict[str, int]:
    """`_last_adapt` 이후 telemetry 이벤트 카운트. 키: harness_invocation /
    agent_invocation / agent_failure. 신뢰 못하는 라인은 silent skip."""
    counts = {t: 0 for t in _COUNTED_TYPES}
    since_ts = read_last_adapt_ts()
    for path in _iter_telemetry_files_since(since_ts):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        evt = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    t = evt.get("type")
                    if t not in _COUNTED_TYPES:
                        continue
                    if since_ts > 0.0:
                        evt_ts = _iso_to_epoch(evt.get("ts", ""))
                        # `_last_adapt` 동일 초 이벤트는 reset *직전* 도착으로 간주
                        # — `<= since_ts`이면 skip.
                        if evt_ts is None or evt_ts <= since_ts:
                            continue
                    counts[t] += 1
        except OSError:
            continue
    return counts


def adapt_alert_due(counts: dict[str, int]) -> bool:
    """카운트가 임계값 도달 시 True. invocation OR failure 어느 한쪽 도달이면 trigger."""
    total_invocations = counts.get("harness_invocation", 0) + counts.get("agent_invocation", 0)
    failures = counts.get("agent_failure", 0)
    return (
        total_invocations >= HARNESS_ADAPT_THRESHOLD_INVOCATIONS
        or failures >= HARNESS_ADAPT_THRESHOLD_FAILURES
    )


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
