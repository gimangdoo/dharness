"""SessionEnd hook — transcript.md 생성 + sessions UPDATE + cm-digester+cm-curator 팀 호출 지시.

session-capture 스킬의 finalize 단계.
session_id는 _memory/.current_session 파일에서 읽는다.
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
    MEMORY_ROOT,
    REPO_ROOT,
    TELEMETRY_DIR,
    clear_session_id,
    read_session_id,
)


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

    if DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT started_at FROM sessions WHERE session_id=?", (session_id,)
            ).fetchone()
            duration_min = None
            if row and row[0]:
                started = calendar.timegm(time.strptime(row[0], "%Y-%m-%dT%H:%M:%SZ"))
                duration_min = max(0, int((time.time() - started) / 60))
            conn.execute(
                "UPDATE sessions SET ended_at=?, duration_min=?, tools_used=? WHERE session_id=?",
                (now_iso, duration_min, json.dumps(sorted(tools_used)), session_id),
            )

    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    with open(TELEMETRY_DIR / f"{today}.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "ts": now_iso, "type": "session_capture_finalize",
            "session_id": session_id, "raw_lines": raw_lines,
            "transcript_size": transcript_path.stat().st_size if transcript_path.exists() else 0,
        }) + "\n")

    clear_session_id()

    print(
        f"[CM SessionEnd] session_id={session_id} transcript={transcript_path.relative_to(REPO_ROOT) if transcript_path.exists() else '(none)'} "
        f"({raw_lines} events) — cm-digester + cm-curator 팀 호출 권장.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
