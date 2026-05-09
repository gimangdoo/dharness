"""PostToolUse hook — raw.jsonl 이벤트 append + 10KB 초과 시 cm-compressor 트리거 안내.

stdin으로 도구 결과 메타데이터를 받는다 (Claude Code hook payload).
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_ROOT = REPO_ROOT / "_workspace" / "_memory"
TOOL_OUTPUTS = REPO_ROOT / "_workspace" / "_tool_outputs"
TELEMETRY_DIR = REPO_ROOT / "_workspace" / "_telemetry"

THRESHOLD_BYTES = 10 * 1024  # 10KB


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        payload = {}

    session_id = os.environ.get("CM_SESSION_ID", "unknown")
    tool_name = payload.get("tool_name") or payload.get("tool") or "unknown"
    tool_response = payload.get("tool_response") or payload.get("output") or ""
    output_size = len(tool_response.encode("utf-8")) if isinstance(tool_response, str) else 0
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    today = time.strftime("%Y-%m-%d", time.gmtime())

    sess_dir = MEMORY_ROOT / "sessions" / session_id
    if sess_dir.exists():
        with open(sess_dir / "raw.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ts": now_iso, "kind": "tool_result",
                "tool": tool_name, "output_size": output_size,
            }) + "\n")

    if output_size <= THRESHOLD_BYTES:
        return 0  # passthrough

    n = sum(1 for _ in (TOOL_OUTPUTS / session_id).glob("*")) if (TOOL_OUTPUTS / session_id).exists() else 0
    raw_dir = TOOL_OUTPUTS / session_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    ext = {"WebFetch": "html", "Read": "txt", "Bash": "log"}.get(tool_name, "txt")
    raw_path = raw_dir / f"{int(time.time())}_{tool_name.lower()}_{n+1:03d}.{ext}"
    raw_path.write_text(tool_response if isinstance(tool_response, str) else str(tool_response), encoding="utf-8")

    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    with open(TELEMETRY_DIR / f"{today}.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "ts": now_iso, "type": "tool_output_captured",
            "session_id": session_id, "tool": tool_name,
            "raw_size": output_size, "compressed_size": None, "ratio": None,
            "raw_path": str(raw_path.relative_to(REPO_ROOT)),
        }) + "\n")

    print(f"[CM PostToolUse] {tool_name} 출력 {output_size}bytes 캡처됨: {raw_path.relative_to(REPO_ROOT)}")
    print("[CM PostToolUse] cm-orchestrator를 통해 cm-compressor를 호출하여 압축 요약을 생성하라.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
