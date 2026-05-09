"""SessionEnd hook — transcript.md 생성 + sessions UPDATE + cm-digester+cm-curator 팀 호출 지시.

session-capture 스킬의 finalize 단계.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_ROOT = REPO_ROOT / "_workspace" / "_memory"
DB_PATH = MEMORY_ROOT / "observations" / "observations.db"
TELEMETRY_DIR = REPO_ROOT / "_workspace" / "_telemetry"


def flatten_to_transcript(raw_path: Path) -> tuple[str, set[str]]:
    """raw.jsonl을 사람이 읽을 수 있는 markdown으로 평탄화."""
    if not raw_path.exists():
        return "", set()
    lines = ["# Session Transcript\n"]
    tools_used: set[str] = set()
    for line in raw_path.read_text(encoding="utf-8").splitlines():
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
    return "".join(lines), tools_used


def main() -> int:
    session_id = os.environ.get("CM_SESSION_ID")
    if not session_id:
        print("[CM SessionEnd] CM_SESSION_ID 미설정 — finalize 스킵", file=sys.stderr)
        return 0

    sess_dir = MEMORY_ROOT / "sessions" / session_id
    raw_path = sess_dir / "raw.jsonl"
    transcript_path = sess_dir / "transcript.md"

    transcript, tools_used = flatten_to_transcript(raw_path)
    if transcript:
        transcript_path.write_text(transcript, encoding="utf-8")

    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    today = time.strftime("%Y-%m-%d", time.gmtime())
    raw_lines = sum(1 for _ in raw_path.open(encoding="utf-8")) if raw_path.exists() else 0

    if DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT started_at FROM sessions WHERE session_id=?", (session_id,)
            ).fetchone()
            duration_min = None
            if row and row[0]:
                started = time.mktime(time.strptime(row[0], "%Y-%m-%dT%H:%M:%SZ"))
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

    print(f"[CM SessionEnd] session_id={session_id} transcript={transcript_path.relative_to(REPO_ROOT)} ({raw_lines} events)")
    print("[CM SessionEnd] cm-orchestrator를 통해 cm-digester + cm-curator 팀을 호출하여 digest 생성과 클러스터링을 수행하라.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
