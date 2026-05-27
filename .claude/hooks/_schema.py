"""CM hook 공용 인프라 — DDL 단일 정의 + session_id 파일 기반 전달 + 도메인 분류기.

DDL은 본 모듈이 단일 진실 원천이다. observations/sessions 2개 테이블 +
observations_fts FTS5 가상 테이블을 정의한다. (R1 2026-05-14: dead schema
`clusters` / `daily_summaries` / `observations.{embedding,completed,cluster_id,phase}` /
`sessions.digest_path` 제거.)

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
import os
import re
import shlex
import sqlite3
import sys
import time
from pathlib import Path

for _stream in (sys.stdin, sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


# REPO_ROOT 결정: ${CLAUDE_PROJECT_DIR} 우선 (Claude Code가 working dir을 결정적으로 전달),
# 미설정 시 본 모듈 위치(.claude/hooks/_schema.py)에서 parents[2]로 fallback.
_env_root = os.environ.get("CLAUDE_PROJECT_DIR")
if _env_root:
    REPO_ROOT = Path(_env_root).resolve()
else:
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
CHANGELOG_MD = REPO_ROOT / "CHANGELOG.md"
LAST_ADAPT_FILE = TELEMETRY_DIR / "_last_adapt"

# Phase 10 자동 adapt 알림 임계값. invocation/failure 누적이 이 값 도달 시
# SessionStart inject에 `/harness:harness-adapt` 권장 블록 추가.
# env var(`CM_ADAPT_THRESHOLD_INVOCATIONS` / `CM_ADAPT_THRESHOLD_FAILURES`)로 오버라이드 가능.


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return max(1, int(raw))
    except (TypeError, ValueError):
        return default


HARNESS_ADAPT_THRESHOLD_INVOCATIONS = _env_int("CM_ADAPT_THRESHOLD_INVOCATIONS", 10)
HARNESS_ADAPT_THRESHOLD_FAILURES = _env_int("CM_ADAPT_THRESHOLD_FAILURES", 2)

# CHANGELOG.md draft 사유 컬럼 placeholder (session_end.py 생성, cm_commands.py 치환).
DRAFT_REASON_PLACEHOLDER = "(apply 전 작성 — 사유/맥락)"

DDL = """
CREATE TABLE IF NOT EXISTS observations (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL, date TEXT NOT NULL,
  section TEXT NOT NULL, content TEXT NOT NULL, tags TEXT,
  created_at TEXT NOT NULL,
  category TEXT,
  artifact_kind TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
  content, session_id, tags,
  content='observations', content_rowid='rowid'
);
CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY, date TEXT NOT NULL, started_at TEXT NOT NULL,
  ended_at TEXT, duration_min INTEGER, tools_used TEXT,
  project TEXT
);
CREATE INDEX IF NOT EXISTS observations_category_idx ON observations(category);
CREATE INDEX IF NOT EXISTS observations_artifact_kind_idx ON observations(artifact_kind);
"""


_ADD_COLUMNS_V1: tuple[tuple[str, str], ...] = (
    ("category", "TEXT"),
    ("artifact_kind", "TEXT"),
)
_DROP_COLUMNS_V2_OBS: tuple[str, ...] = ("embedding", "completed", "cluster_id", "phase")
_DROP_TABLES_V2: tuple[str, ...] = ("clusters", "daily_summaries")

# user_version=0: 초기 (category/artifact_kind 미존재).
# user_version=1: v0 + category/artifact_kind/phase + 인덱스 적용 후.
# user_version=2: v1 - dead schema (clusters/daily_summaries 테이블 + observations 4 컬럼 +
#                 sessions.digest_path) 제거 (R1 2026-05-14).
SCHEMA_VERSION = 2

# ALTER TABLE DROP COLUMN은 SQLite 3.35.0(2021-03)+에서만 지원. 미만은 dead 컬럼 그대로 둠.
_SQLITE_SUPPORTS_DROP_COLUMN = sqlite3.sqlite_version_info >= (3, 35, 0)

# 세션 단위 migration marker. 파일명에 SCHEMA_VERSION이 박혀 있어 bump 시 자동 stale.
# 마커 존재 = 해당 버전 마이그레이션 이미 완료 — ensure_migrations short-circuit (락 회피).
MIGRATION_MARKER = MEMORY_ROOT / f".migration_v{SCHEMA_VERSION}"


def _get_conn(path: Path | None = None) -> sqlite3.Connection:
    """WAL + busy_timeout + synchronous=NORMAL 적용된 SQLite 연결.

    WAL: writer 활성 중에도 reader 동시 가능 — PostToolUse 쓰는 동안 /cm-status 읽기 가능.
    busy_timeout=5000ms: 짧은 락 경합 자동 재시도.
    synchronous=NORMAL: WAL 모드에서 안전한 fsync 정책.
    """
    conn = sqlite3.connect(path or DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _marker_current() -> bool:
    return MIGRATION_MARKER.exists()


def _mark_migration_current() -> None:
    try:
        MIGRATION_MARKER.parent.mkdir(parents=True, exist_ok=True)
        MIGRATION_MARKER.touch()
    except OSError:
        pass  # marker는 hot-path 최적화일 뿐 — 실패해도 정확성 영향 없음


def ensure_migrations(conn: sqlite3.Connection) -> list[str]:
    """누락 컬럼 ADD / dead 컬럼·테이블 DROP. PRAGMA user_version + marker로 short-circuit.

    Marker 존재 시 PRAGMA 조회 없이 즉시 반환 (post_tool_use hot-path 락 회피).
    Marker 미존재 + PRAGMA user_version 도달 시 marker 생성 후 반환.

    v0→v2: category/artifact_kind ADD COLUMN + dead schema DROP (phase는 ADD 없이 바로 skip).
    v1→v2: dead schema DROP만.
    v2: no-op.

    SQLite < 3.35: DROP COLUMN 미지원 — dead 컬럼은 그대로 두고 user_version도 bump하지 않음
    (다음 SQLite 업그레이드 후 재시도). DROP TABLE은 모든 버전 지원.
    """
    if _marker_current():
        return []
    current_version = conn.execute("PRAGMA user_version").fetchone()[0]
    if current_version >= SCHEMA_VERSION:
        _mark_migration_current()
        return []

    changed: list[str] = []
    drop_failures = 0
    obs_info = conn.execute("PRAGMA table_info(observations)").fetchall()
    obs_cols = {row[1] for row in obs_info}

    if not obs_cols:
        # 빈 DB — DDL이 최신 schema를 이미 만들었음. version만 갱신.
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        _mark_migration_current()
        return []

    # v0→v1: category/artifact_kind 누락 시 ADD COLUMN (phase는 v2에서 drop이므로 skip)
    for col, typ in _ADD_COLUMNS_V1:
        if col not in obs_cols:
            conn.execute(f"ALTER TABLE observations ADD COLUMN {col} {typ}")
            changed.append(f"add:{col}")
            obs_cols.add(col)
    if any(c.startswith("add:") for c in changed):
        conn.execute(
            "CREATE INDEX IF NOT EXISTS observations_category_idx ON observations(category)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS observations_artifact_kind_idx ON observations(artifact_kind)"
        )

    # v1→v2: dead 컬럼 DROP (SQLite 3.35+에서만)
    if _SQLITE_SUPPORTS_DROP_COLUMN:
        for col in _DROP_COLUMNS_V2_OBS:
            if col in obs_cols:
                try:
                    conn.execute(f"ALTER TABLE observations DROP COLUMN {col}")
                    changed.append(f"drop_col:obs.{col}")
                except sqlite3.OperationalError as e:
                    print(
                        f"[_schema] migration v1→v2 skip: DROP observations.{col} failed: {e}",
                        file=sys.stderr,
                    )
                    drop_failures += 1

        sess_info = conn.execute("PRAGMA table_info(sessions)").fetchall()
        sess_cols = {row[1] for row in sess_info}
        if "digest_path" in sess_cols:
            try:
                conn.execute("ALTER TABLE sessions DROP COLUMN digest_path")
                changed.append("drop_col:sess.digest_path")
            except sqlite3.OperationalError as e:
                print(
                    f"[_schema] migration v1→v2 skip: DROP sessions.digest_path failed: {e}",
                    file=sys.stderr,
                )
                drop_failures += 1
    else:
        # 구 SQLite — dead 컬럼은 그대로 두고 user_version도 bump하지 않음.
        # 다음 SQLite 업그레이드 후 재시도하도록 marker도 안 만듦.
        drop_failures += 1
        print(
            f"[_schema] SQLite {sqlite3.sqlite_version} < 3.35.0 — DROP COLUMN 미지원, "
            f"dead 컬럼 유지 + user_version bump 보류",
            file=sys.stderr,
        )

    # v1→v2: dead 테이블 DROP (모든 SQLite 지원)
    for tbl in _DROP_TABLES_V2:
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,)
        ).fetchone()
        if result:
            conn.execute(f"DROP TABLE {tbl}")
            changed.append(f"drop_table:{tbl}")

    # 모든 DROP COLUMN 성공 시에만 version bump + marker — partial migration은
    # 다음 hook에서 재시도 가능하도록 user_version 보류.
    if drop_failures == 0:
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        _mark_migration_current()
    return changed


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

# Bash shell separator 토큰들 — shlex 파싱 후 이 토큰 뒤에 `git`이 오면 새 명령.
_BASH_SEPARATORS = {";", "&&", "||", "|", "&", "\n"}
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
        chain_subs = _extract_git_subcommands(command)
        # _GIT_RELEVANT 매핑 가능 항목만 후보 (status/log 등 read-only는 제외)
        candidates = [s for s in chain_subs if s in _GIT_RELEVANT]
        if not candidates:
            return None
        # bash chain semantic 정합 — 마지막 매핑 가능 subcommand가 terminal action
        sub = candidates[-1]
        mapped = _GIT_RELEVANT[sub]
        category, artifact_kind = mapped
        head = command.strip().splitlines()[0]
        if len(head) > 200:
            head = head[:199] + "…"
        tags = ["bash", category, artifact_kind]
        # chain 사실 자체를 tag로 박제 (관측성) — 매핑 가능 subcommand 2개 이상일 때만
        if len(candidates) > 1:
            tags.append("git_chain")
        return {
            "category": category,
            "artifact_kind": artifact_kind,
            "content": head,
            "tags": tags,
        }
    return None


def _extract_git_subcommands(command: str) -> list[str]:
    """Bash command line에서 실제로 실행될 git subcommand만 추출.

    shlex로 토큰화하면 quoted/heredoc 내부의 `git` 키워드는 single token에 흡수돼
    false positive가 안 생긴다 (`echo "git commit"` → ['echo', 'git commit']).
    shlex.split이 실패하는 malformed quoting은 안전하게 빈 리스트 반환.

    chain 구분: `;`, `&&`, `||`, `|`, `&`, newline — 이들 뒤에 등장하는 `git`만 명령 시작.
    """
    try:
        tokens = shlex.split(command, comments=True, posix=True)
    except ValueError:
        return []
    subs: list[str] = []
    expect_git = True  # 명령 시작 위치
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in _BASH_SEPARATORS:
            expect_git = True
            i += 1
            continue
        if expect_git and tok == "git" and i + 1 < len(tokens):
            sub = tokens[i + 1]
            # subcommand 다음 토큰은 보통 옵션/인자 — 다음 separator까지 skip.
            subs.append(sub)
            j = i + 2
            while j < len(tokens) and tokens[j] not in _BASH_SEPARATORS:
                j += 1
            i = j
            expect_git = True
            continue
        # 명령의 첫 토큰이 git이 아니면 그 명령 전체 skip (다음 separator까지).
        j = i + 1
        while j < len(tokens) and tokens[j] not in _BASH_SEPARATORS:
            j += 1
        i = j
        expect_git = False
    return subs


# ---------------------------- adapt counter helpers ----------------------------

# Phase 10 자동 adapt 알림 카운터. `_workspace/_telemetry/*.jsonl`을 ascending 스캔해
# `_last_adapt` mtime 이후의 `harness_invocation` / `agent_invocation` / `agent_failure`
# 이벤트를 카운트한다. `_last_adapt` 파일은 `/harness:harness-adapt` 완료 시 shell
# (Set-Content / `date >`)로 직접 write — 본 모듈의 Python writer 없음.

_COUNTED_TYPES = {"harness_invocation", "agent_invocation", "agent_failure"}


def read_last_adapt_ts() -> float:
    """`_last_adapt` mtime을 epoch float로 반환. 미존재 시 0.0 (= epoch 시작)."""
    if not LAST_ADAPT_FILE.exists():
        return 0.0
    try:
        return LAST_ADAPT_FILE.stat().st_mtime
    except OSError:
        return 0.0


def touch_last_adapt() -> float:
    """`_last_adapt` 파일 mtime을 현재 epoch로 박제 (없으면 생성).

    PO5 (2026-05-27): manual shell touch doctrine 폐기 — `/cm-reset-adapt-counter`
    subcommand의 programmatic 진입점. 반환: 새 mtime epoch float.
    """
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    LAST_ADAPT_FILE.touch(exist_ok=True)
    now = time.time()
    os.utime(LAST_ADAPT_FILE, (now, now))
    return now


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
    agent_invocation / agent_failure. 신뢰 못하는 라인은 silent skip.

    encoding은 `utf-8-sig`로 BOM tolerantly strip — PowerShell 5.1의
    `Add-Content -Encoding utf8`가 BOM을 삽입하는 케이스 대응 (derived 프로젝트
    오케스트레이터가 흔히 사용)."""
    counts = {t: 0 for t in _COUNTED_TYPES}
    since_ts = read_last_adapt_ts()
    for path in _iter_telemetry_files_since(since_ts):
        try:
            with open(path, "r", encoding="utf-8-sig") as fh:
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
    """Atomic write — tmp 파일 작성 후 os.replace로 교체. PostToolUse가 동시에
    read해도 partial content 안 보임 (POSIX rename + Windows os.replace 모두 atomic).
    """
    SESSION_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = SESSION_ID_FILE.with_suffix(".tmp")
    tmp.write_text(session_id, encoding="utf-8")
    os.replace(tmp, SESSION_ID_FILE)


def read_session_id() -> str | None:
    if not SESSION_ID_FILE.exists():
        return None
    sid = SESSION_ID_FILE.read_text(encoding="utf-8").strip()
    return sid or None


def clear_session_id() -> None:
    if SESSION_ID_FILE.exists():
        SESSION_ID_FILE.unlink()
