"""SessionEnd hook — transcript.md 생성 + sessions UPDATE + CLAUDE.md draft 적재.

session_id는 _memory/.current_session 파일에서 읽는다.

주의: SessionEnd 시점에 .current_session 파일을 *지우지 않는다*. SessionEnd와 다음
SessionStart 사이의 짧은 인터벌에 PostToolUse 훅이 발동되면 파일이 비어있을 때
session_id="unknown"으로 도구 출력이 떨어지는 누수가 발생하기 때문. 다음 SessionStart의
write_session_id()가 새 ID로 덮어쓰는 것에 의존한다.

단계 D: 이번 세션의 dharness_event를 모아 CLAUDE.md "변경 이력" 표 행 draft를
`_workspace/_drafts/{date}_{sid}.md`에 적재한다. 자동 적용은 하지 않으며, 사용자가
다음 세션에서 `/cm-claudemd-apply <sid>` 또는 `/cm-claudemd-discard`로 게이트한다.
"""

from __future__ import annotations

import calendar
import json
import sqlite3
import sys
import time
from pathlib import Path

from _schema import (
    DB_PATH,
    DRAFT_REASON_PLACEHOLDER,
    DRAFTS_DIR,
    MEMORY_ROOT,
    REPO_ROOT,
    TELEMETRY_DIR,
    read_session_id,
)

DRAFT_TARGETS_MAX = 8


def flatten_to_transcript(raw_path: Path) -> tuple[str, set[str], int]:
    """raw.jsonl을 사람이 읽을 수 있는 markdown으로 평탄화."""
    if not raw_path.exists():
        return "", set(), 0
    lines = ["# Session Transcript\n"]
    tools_used: set[str] = set()
    raw_count = 0
    for line in raw_path.read_text(encoding="utf-8").splitlines():
        raw_count += 1
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = evt.get("kind")
        ts = evt.get("ts", "")
        if kind == "user_message":
            lines.append(f"\n## {ts} — User\n{evt.get('content', '')}\n")
        elif kind == "assistant_message":
            lines.append(f"\n## {ts} — Assistant\n{evt.get('content', '')}\n")
        elif kind == "tool_call":
            tool = evt.get("tool", "?")
            tools_used.add(tool)
            lines.append(f"\n- {ts} tool_call: {tool}\n")
        elif kind == "tool_result":
            tool = evt.get("tool", "?")
            tools_used.add(tool)
            lines.append(f"- {ts} tool_result: {tool} ({evt.get('output_size', 0)}b)\n")
    return "".join(lines), tools_used, raw_count


def _collect_session_events(conn: sqlite3.Connection, session_id: str) -> dict:
    """이번 세션의 dharness_event를 category/artifact_kind별로 집계 + 변경된 file path 추출."""
    cur = conn.execute("""
        SELECT category, artifact_kind, content
        FROM observations
        WHERE session_id = ? AND section = 'dharness_event'
        ORDER BY rowid ASC
    """, (session_id,))
    cat_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    targets: list[str] = []
    seen_targets: set[str] = set()
    for category, artifact_kind, content in cur.fetchall():
        if category:
            cat_counts[category] = cat_counts.get(category, 0) + 1
        if artifact_kind:
            kind_counts[artifact_kind] = kind_counts.get(artifact_kind, 0) + 1
        if artifact_kind == "git":
            continue
        if content and " " in content:
            target = content.split(" ", 1)[1].strip()
            if target and target not in seen_targets:
                seen_targets.add(target)
                targets.append(target)
    return {
        "categories": cat_counts,
        "kinds": kind_counts,
        "targets": targets,
        "total": sum(cat_counts.values()),
    }


def generate_draft(
    conn: sqlite3.Connection,
    session_id: str,
    today: str,
    duration_min: int | None,
) -> Path | None:
    """이번 세션의 변경 이력 draft를 _workspace/_drafts/{date}_{sid}.md에 작성.

    이벤트가 0건이면 draft 생성하지 않는다 (잡음 방지).
    """
    summary = _collect_session_events(conn, session_id)
    if summary["total"] == 0:
        return None

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    cats = summary["categories"]
    kinds = summary["kinds"]
    targets = summary["targets"]

    summary_chunks = " / ".join(f"{c}:{n}" for c, n in sorted(cats.items(), key=lambda x: -x[1]))

    targets_for_table = targets[:DRAFT_TARGETS_MAX]
    targets_table = ", ".join(f"`{t}`" for t in targets_for_table)
    if len(targets) > DRAFT_TARGETS_MAX:
        targets_table += f" (+{len(targets) - DRAFT_TARGETS_MAX} more)"

    row = f"| {today} | dharness_event 자동 draft — {summary_chunks} | {targets_table} | {DRAFT_REASON_PLACEHOLDER} |"

    targets_full_md = "\n".join(f"- `{t}`" for t in targets)
    cats_md = "\n".join(f"- {c}: {n}" for c, n in sorted(cats.items(), key=lambda x: -x[1]))
    kinds_md = "\n".join(f"- {k}: {n}" for k, n in sorted(kinds.items(), key=lambda x: -x[1]))
    duration_str = f"{duration_min}m" if duration_min is not None else "—"

    body = f"""---
session_id: {session_id}
date: {today}
duration_min: {duration_min if duration_min is not None else 0}
status: pending
total_events: {summary['total']}
---

# CLAUDE.md 변경 이력 draft — 세션 `{session_id}`

자동 생성된 행 (apply 전 사유/맥락을 채워주세요).

## 표 행 (apply 시 CLAUDE.md "변경 이력" 표에 삽입됨)

```
{row}
```

## 카테고리 카운트

{cats_md}

## artifact_kind 카운트

{kinds_md}

## 변경 대상 (전체 {len(targets)}개)

{targets_full_md}

## 메타

- session_id: `{session_id}`
- 종료 시각: {today} (UTC)
- duration: {duration_str}
- 총 dharness_event: {summary['total']}

## 적용 / 폐기

- `/cm-claudemd-apply {session_id}` — 위 행을 CLAUDE.md "변경 이력" 표에 추가 (사유 placeholder 유지)
- `/cm-claudemd-apply {session_id} 사유 한 줄` — 사유 인자를 즉시 치환 (markdown table 안전 처리 내장 — `\\|` escape, 줄바꿈 → 공백)
- `/cm-claudemd-discard {session_id}` — 이 draft 폐기 (보관: `_workspace/_drafts/discarded/`)
"""

    draft_path = DRAFTS_DIR / f"{today}_{session_id}.md"
    draft_path.write_text(body, encoding="utf-8")
    return draft_path


def main() -> int:
    session_id = read_session_id()
    if not session_id:
        print("[CM SessionEnd] session_id 미설정 — finalize 스킵", file=sys.stderr)
        return 0

    sess_dir = MEMORY_ROOT / "sessions" / session_id
    raw_path = sess_dir / "raw.jsonl"
    transcript_path = sess_dir / "transcript.md"

    transcript, tools_used, raw_lines = flatten_to_transcript(raw_path)
    if transcript:
        transcript_path.write_text(transcript, encoding="utf-8")

    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    today = time.strftime("%Y-%m-%d", time.gmtime())

    duration_min: int | None = None
    draft_path: Path | None = None
    if DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT started_at FROM sessions WHERE session_id=?", (session_id,)
            ).fetchone()
            if row and row[0]:
                try:
                    started = calendar.timegm(time.strptime(row[0], "%Y-%m-%dT%H:%M:%SZ"))
                    duration_min = max(0, int((time.time() - started) / 60))
                except ValueError:
                    duration_min = None
            conn.execute(
                "UPDATE sessions SET ended_at=?, duration_min=?, tools_used=? WHERE session_id=?",
                (now_iso, duration_min, json.dumps(sorted(tools_used)), session_id),
            )
            try:
                draft_path = generate_draft(conn, session_id, today, duration_min)
            except sqlite3.Error as e:
                print(f"[CM SessionEnd] draft 생성 실패: {e}", file=sys.stderr)

    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    with open(TELEMETRY_DIR / f"{today}.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "ts": now_iso, "type": "session_capture_finalize",
            "session_id": session_id, "raw_lines": raw_lines,
            "transcript_size": transcript_path.stat().st_size if transcript_path.exists() else 0,
        }) + "\n")
        if draft_path:
            fh.write(json.dumps({
                "ts": now_iso, "type": "claudemd_draft_created",
                "session_id": session_id,
                "draft_path": str(draft_path.relative_to(REPO_ROOT)),
            }) + "\n")

    print(
        f"[CM SessionEnd] session_id={session_id} transcript={transcript_path.relative_to(REPO_ROOT) if transcript_path.exists() else '(none)'} "
        f"({raw_lines} events) finalized."
        + (f" draft={draft_path.relative_to(REPO_ROOT)}" if draft_path else ""),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
