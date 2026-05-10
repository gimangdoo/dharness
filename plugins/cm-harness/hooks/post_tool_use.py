"""PostToolUse hook — raw.jsonl 이벤트 append + 10KB 초과 시 _tool_outputs/에 보존.

stdin으로 도구 결과 메타데이터를 받는다 (Claude Code hook payload).
session_id는 _memory/.current_session 파일에서 읽는다 (hook 간 별도 프로세스이므로 환경변수 불가).

10KB 초과 출력은 `_workspace/_tool_outputs/{session_id}/{ts}_{tool}_{n}.{ext}`에
원본 그대로 저장되며, 별도 압축/요약 처리는 하지 않는다 (필요 시 워커가 후처리).
"""

from __future__ import annotations

import json
import sys
import time

from _schema import MEMORY_ROOT, REPO_ROOT, TELEMETRY_DIR, TOOL_OUTPUTS, read_session_id

THRESHOLD_BYTES = 10 * 1024


def _serialize(tool_response: object) -> str:
    if isinstance(tool_response, str):
        return tool_response
    if tool_response is None:
        return ""
    try:
        return json.dumps(tool_response, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(tool_response)


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        payload = {}

    session_id = read_session_id() or "unknown"
    tool_name = payload.get("tool_name") or payload.get("tool") or "unknown"
    tool_response = payload.get("tool_response") or payload.get("output") or ""
    serialized = _serialize(tool_response)
    output_size = len(serialized.encode("utf-8"))
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
        return 0

    raw_dir = TOOL_OUTPUTS / session_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    n = sum(1 for _ in raw_dir.glob("*"))
    ext = {"WebFetch": "html", "Read": "txt", "Bash": "log"}.get(tool_name, "txt")
    raw_path = raw_dir / f"{time.time_ns()}_{tool_name.lower()}_{n+1:03d}.{ext}"
    raw_path.write_text(serialized, encoding="utf-8")

    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    with open(TELEMETRY_DIR / f"{today}.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "ts": now_iso, "type": "tool_output_captured",
            "session_id": session_id, "tool": tool_name,
            "raw_size": output_size, "compressed_size": None, "ratio": None,
            "raw_path": str(raw_path.relative_to(REPO_ROOT)),
        }) + "\n")

    print(
        f"[CM PostToolUse] {tool_name} 출력 {output_size}bytes 캡처: "
        f"{raw_path.relative_to(REPO_ROOT)}.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
