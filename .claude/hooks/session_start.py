"""SessionStart hook — 세션 부트스트랩 + dangling 세션 finalize + 의미적 inject.

수행:
  1. 직전 세션이 dangling(ended_at IS NULL + raw.jsonl 비어있지 않음)인 경우 backfill finalize
  2. session_id 발급 (UUIDv4 6자 hex)
  3. _workspace/_memory/sessions/{id}/ 부트스트랩 + raw.jsonl 빈 파일 생성
  4. observations.db 미존재 시 4개 테이블 + FTS5 초기화 + ensure_migrations 실행
  5. sessions 테이블 INSERT
  6. session_id를 _memory/.current_session에 기록
  7. _workspace/_telemetry/{date}.jsonl에 라이프사이클 이벤트 append
  8. 의미적 carry-over inject (단계 C):
     a. 직전 1~3개 세션의 dharness_event category 카운트
     b. 작업 중단점 (git status --short)
     c. 최신 daily_summary (있으면)
     모두 deterministic — LLM 호출 없음. 토큰 budget 2000자.
  9. stdout으로 hookSpecificOutput.additionalContext JSON 송출

Digest/cluster/daily_summary 자동 생성은 단계 D 이후 통합 (manual LLM trigger only).
"""

from __future__ import annotations

import calendar
import json
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid

from _schema import (
    DB_PATH,
    DDL,
    DRAFTS_DIR,
    MEMORY_ROOT,
    REPO_ROOT,
    TELEMETRY_DIR,
    ensure_migrations,
    write_session_id,
)
from session_end import flatten_to_transcript

INJECT_BUDGET = 2000
DAILY_SUMMARY_MAX_CHARS = 600
GIT_STATUS_MAX_LINES = 12
PRIOR_SESSIONS = 3
PENDING_DRAFTS_MAX = 5


def backfill_dangling_sessions(conn: sqlite3.Connection, now_iso: str) -> list[str]:
    """ended_at IS NULL + raw.jsonl 비어있지 않은 세션을 transcript 평탄화·UPDATE finalize."""
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
    row = conn.execute(
        "SELECT date, summary FROM daily_summaries ORDER BY date DESC LIMIT 1"
    ).fetchone()
    if not row:
        return None
    return row[0], row[1]


def fetch_prior_sessions(conn: sqlite3.Connection, current_id: str, n: int) -> list[dict]:
    """직전 N개 세션의 dharness_event category 카운트.

    반환: [{session_id, date, started_at, categories: {category: count}}, ...]
    가장 최근 세션이 첫 번째.
    """
    rows = conn.execute("""
        SELECT session_id, date, started_at
        FROM sessions
        WHERE session_id != ?
        ORDER BY started_at DESC
        LIMIT ?
    """, (current_id, n)).fetchall()
    out: list[dict] = []
    for sid, date, started_at in rows:
        cur = conn.execute("""
            SELECT category, COUNT(*) AS n
            FROM observations
            WHERE session_id = ? AND section = 'dharness_event' AND category IS NOT NULL
            GROUP BY category
            ORDER BY n DESC
        """, (sid,))
        cats = {row[0]: row[1] for row in cur.fetchall()}
        out.append({
            "session_id": sid,
            "date": date,
            "started_at": started_at,
            "categories": cats,
        })
    return out


def fetch_pending_drafts(limit: int) -> list[str]:
    """_workspace/_drafts/ 안의 미적용 draft 파일들 (filename에서 sid 추출)."""
    if not DRAFTS_DIR.exists():
        return []
    out: list[str] = []
    for p in sorted(DRAFTS_DIR.glob("*.md"))[:limit]:
        stem = p.stem  # {date}_{sid}
        date, _, sid = stem.partition("_")
        if sid:
            out.append(f"{date} {sid}")
        else:
            out.append(stem)
    return out


def fetch_git_status_short(max_lines: int) -> list[str]:
    """git status --short 출력. git 호출 실패 / repo 아님이면 빈 리스트."""
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=2,
            encoding="utf-8",
            errors="replace",
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []
    if result.returncode != 0:
        return []
    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    return lines[:max_lines]


def format_inject(
    session_id: str,
    project_name: str,
    prior: list[dict],
    git_lines: list[str],
    summary: tuple[str, str] | None,
    pending_drafts: list[str],
    budget: int,
) -> str:
    """직전 세션 사실 set + git status + daily_summary + 미적용 draft를 한 string으로 패킹."""
    parts: list[str] = [f"[CM] session_id={session_id} (project={project_name})."]

    if prior:
        prior_chunks: list[str] = []
        for sess in prior:
            cats = sess["categories"]
            if not cats:
                cats_str = "(no dharness_event)"
            else:
                top = list(cats.items())[:5]
                cats_str = " / ".join(f"{c}:{n}" for c, n in top)
            label = f"{sess['date']} {sess['session_id']}"
            prior_chunks.append(f"  · {label} — {cats_str}")
        parts.append(
            f"[CM] 직전 {len(prior)} 세션 dharness_event:\n" + "\n".join(prior_chunks)
        )

    if pending_drafts:
        chunks = "\n".join(f"  · {d}" for d in pending_drafts)
        parts.append(
            f"[CM] 미적용 CLAUDE.md draft {len(pending_drafts)}건 — apply: "
            f"/cm-claudemd-apply <sid>, discard: /cm-claudemd-discard\n{chunks}"
        )

    if git_lines:
        git_block = "\n".join(f"  {ln}" for ln in git_lines)
        parts.append(f"[CM] 작업 중단점 (git status --short):\n{git_block}")

    if summary:
        date, summary_text = summary
        if len(summary_text) > DAILY_SUMMARY_MAX_CHARS:
            summary_text = summary_text[: DAILY_SUMMARY_MAX_CHARS - 1] + "…"
        parts.append(f"[CM] 최근 요약 ({date}):\n{summary_text}")

    out = "\n".join(parts)
    if len(out) > budget:
        out = out[: budget - 1] + "…"
    return out


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
    prior_sessions: list[dict] = []
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(DDL)
        try:
            ensure_migrations(conn)
        except Exception as e:
            print(f"[CM SessionStart] migration skipped: {e}", file=sys.stderr)
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
        try:
            prior_sessions = fetch_prior_sessions(conn, session_id, PRIOR_SESSIONS)
        except Exception as e:
            print(f"[CM SessionStart] prior sessions lookup skipped: {e}", file=sys.stderr)

    write_session_id(session_id)

    git_lines = fetch_git_status_short(GIT_STATUS_MAX_LINES)
    pending_drafts = fetch_pending_drafts(PENDING_DRAFTS_MAX)

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

    additional_context = format_inject(
        session_id=session_id,
        project_name=REPO_ROOT.name,
        prior=prior_sessions,
        git_lines=git_lines,
        summary=latest_summary,
        pending_drafts=pending_drafts,
        budget=INJECT_BUDGET,
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
