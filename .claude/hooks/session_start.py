"""SessionStart hook — 세션 부트스트랩 + dangling 세션 finalize + 의미적 inject.

수행:
  1. 직전 세션이 dangling(ended_at IS NULL + raw.jsonl 비어있지 않음)인 경우 backfill finalize
  2. session_id 발급 (UUIDv4 6자 hex)
  3. _workspace/_memory/sessions/{id}/ 부트스트랩 + raw.jsonl 빈 파일 생성
  4. observations.db 미존재 시 2개 테이블 + FTS5 초기화 + ensure_migrations 실행
  5. sessions 테이블 INSERT
  6. session_id를 _memory/.current_session에 기록
  7. _workspace/_telemetry/{date}.jsonl에 라이프사이클 이벤트 append
  8. 의미적 carry-over inject (4 블록, 모두 deterministic):
     a. 직전 N=3 세션의 dharness_event category 카운트
     b. 미적용 CLAUDE.md draft 목록
     c. 작업 중단점 (git status --short)
     LLM 호출 없음. 토큰 budget 2000자.
  9. stdout으로 hookSpecificOutput.additionalContext JSON 송출

daily_summary 블록은 결정적 모델 일관성을 위해 제거 (Tier 3B 무산).
R1 (2026-05-14): `daily_summaries` / `clusters` 테이블 + observations 4 컬럼 +
`sessions.digest_path` 모두 schema에서 제거 — ensure_migrations가 기존 DB도 정리.
"""

from __future__ import annotations

import calendar
import json
import sqlite3
import subprocess
import sys
import time
import uuid

from _schema import (
    DB_PATH,
    DDL,
    DRAFTS_DIR,
    HARNESS_ADAPT_THRESHOLD_FAILURES,
    HARNESS_ADAPT_THRESHOLD_INVOCATIONS,
    MEMORY_ROOT,
    REPO_ROOT,
    TELEMETRY_DIR,
    adapt_alert_due,
    count_events_since_last_adapt,
    ensure_migrations,
    read_last_adapt_ts,
    write_session_id,
)
from _transcript_utils import flatten_to_transcript

INJECT_BUDGET = 2000
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
            except ValueError as e:
                print(
                    f"[CM SessionStart] started_at parse failed (sid={sid}, value={started_at!r}): {e}",
                    file=sys.stderr,
                )
        conn.execute(
            "UPDATE sessions SET ended_at=?, duration_min=?, tools_used=? WHERE session_id=?",
            (now_iso, duration_min, json.dumps(sorted(tools_used)), sid),
        )
        finalized.append(sid)
    return finalized


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


def format_adapt_alert(counts: dict[str, int], last_adapt_ts: float) -> str | None:
    """Phase 10 adapt 권장 alert 블록. 임계값 미도달이면 None."""
    if not adapt_alert_due(counts):
        return None
    harness_n = counts.get("harness_invocation", 0)
    agent_n = counts.get("agent_invocation", 0)
    fail_n = counts.get("agent_failure", 0)
    if last_adapt_ts > 0.0:
        last_label = time.strftime("%Y-%m-%d", time.gmtime(last_adapt_ts))
    else:
        last_label = "최초 이후"
    triggers = []
    if harness_n + agent_n >= HARNESS_ADAPT_THRESHOLD_INVOCATIONS:
        triggers.append(
            f"invocations={harness_n + agent_n} (≥{HARNESS_ADAPT_THRESHOLD_INVOCATIONS})"
        )
    if fail_n >= HARNESS_ADAPT_THRESHOLD_FAILURES:
        triggers.append(f"failures={fail_n} (≥{HARNESS_ADAPT_THRESHOLD_FAILURES})")
    trigger_str = " · ".join(triggers)
    return (
        f"[CM] ⚠️ Phase 10 ADAPT 권장 — last adapt: {last_label} / 누적 {trigger_str}.\n"
        f"  · 실행: `/harness:harness-adapt` (변경안 제시→사용자 승인→적용)\n"
        f"  · skip: 다음 alert까지 누적 계속, 임계값 갱신 의도면 plugins/harness/skills/harness/references/runtime-adaptation.md 참조"
    )


def format_inject(
    session_id: str,
    project_name: str,
    prior: list[dict],
    git_lines: list[str],
    pending_drafts: list[str],
    adapt_alert: str | None,
    budget: int,
) -> str:
    """직전 세션 사실 set + 미적용 draft + git status를 한 string으로 패킹 (4 블록)."""
    parts: list[str] = [f"[CM] session_id={session_id} (project={project_name})."]

    if adapt_alert:
        parts.append(adapt_alert)

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

    out = "\n".join(parts)
    if len(out) > budget:
        out = out[: budget - 1] + "…"
    return out


def main() -> int:
    session_id = uuid.uuid4().hex[:6]
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    today = time.strftime("%Y-%m-%d", time.gmtime())

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    backfilled: list[str] = []
    prior_sessions: list[dict] = []
    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            conn.executescript(DDL)
            try:
                ensure_migrations(conn)
            except Exception as e:
                print(f"[CM SessionStart] migration skipped: {e}", file=sys.stderr)
            try:
                backfilled = backfill_dangling_sessions(conn, now_iso)
            except Exception as e:
                print(f"[CM SessionStart] dangling backfill skipped: {e}", file=sys.stderr)
            # session_id 충돌 시 더 긴 hex로 재발급. 충돌 확률은 6자 hex 기준 ~1e-6 이하.
            # INSERT 성공 후에만 sess_dir 생성 — orphan dir 방지.
            inserted = False
            for hex_len in (6, 8, 10, 14, 32):
                if hex_len != 6:
                    session_id = uuid.uuid4().hex if hex_len == 32 else uuid.uuid4().hex[:hex_len]
                result = conn.execute(
                    "INSERT OR IGNORE INTO sessions (session_id, date, started_at, project) VALUES (?, ?, ?, ?)",
                    (session_id, today, now_iso, REPO_ROOT.name),
                )
                if result.rowcount > 0:
                    inserted = True
                    break
            if not inserted:
                raise RuntimeError(
                    "session_id collision unresolved after 5 attempts (6/8/10/14/32 hex)"
                )
            try:
                prior_sessions = fetch_prior_sessions(conn, session_id, PRIOR_SESSIONS)
            except Exception as e:
                print(f"[CM SessionStart] prior sessions lookup skipped: {e}", file=sys.stderr)
    finally:
        conn.close()

    sess_dir = MEMORY_ROOT / "sessions" / session_id
    sess_dir.mkdir(parents=True, exist_ok=True)
    (sess_dir / "raw.jsonl").touch()

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

    try:
        adapt_counts = count_events_since_last_adapt()
        last_adapt_ts = read_last_adapt_ts()
        adapt_alert = format_adapt_alert(adapt_counts, last_adapt_ts)
    except Exception as e:
        print(f"[CM SessionStart] adapt alert skipped: {e}", file=sys.stderr)
        adapt_alert = None

    additional_context = format_inject(
        session_id=session_id,
        project_name=REPO_ROOT.name,
        prior=prior_sessions,
        git_lines=git_lines,
        pending_drafts=pending_drafts,
        adapt_alert=adapt_alert,
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
