"""raw.jsonl → transcript.md 평탄화 유틸.

session_start.py(dangling backfill)와 session_end.py(정상 finalize) 양쪽에서
공유한다. session_end.py에 두면 session_start.py가 session_end.py를 import해야
하는 결합이 생기므로 별도 모듈로 분리.
"""

from __future__ import annotations

import json
from pathlib import Path


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
        if kind == "tool_call":
            tool = evt.get("tool", "?")
            tools_used.add(tool)
            lines.append(f"\n- {ts} tool_call: {tool}\n")
        elif kind == "tool_result":
            tool = evt.get("tool", "?")
            tools_used.add(tool)
            lines.append(f"- {ts} tool_result: {tool} ({evt.get('output_size', 0)}b)\n")
    return "".join(lines), tools_used, raw_count
