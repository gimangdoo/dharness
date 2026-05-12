"""PostToolUse hook — raw.jsonl append + 10KB 초과 시 _tool_outputs/에 원본 보존
+ dharness 도메인 이벤트 분류 후 observations 테이블에 INSERT.

stdin으로 도구 결과 메타데이터를 받는다 (Claude Code hook payload).
session_id는 _memory/.current_session 파일에서 읽는다 (hook 간 별도 프로세스이므로 환경변수 불가).

10KB 초과 출력은 `_workspace/_tool_outputs/{session_id}/{ts}_{tool}_{n}.{ext}`에
원본 그대로 저장되며, 별도 압축/요약 처리는 하지 않는다.

도메인 분류는 _schema.classify_dharness_event가 담당. file path/git subcommand 기반
deterministic — LLM 호출 없음. 분류된 이벤트는 observations 테이블에 section='dharness_event'로
INSERT (단계 B 이후).
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
import uuid

from _schema import (
    DB_PATH,
    MEMORY_ROOT,
    REPO_ROOT,
    TELEMETRY_DIR,
    TOOL_OUTPUTS,
    classify_dharness_event,
    ensure_migrations,
    read_session_id,
)

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


def _persist_dharness_event(
    session_id: str,
    event: dict,
    tool_name: str,
    now_iso: str,
    today: str,
) -> None:
    """observations 테이블에 dharness_event INSERT. DB 미존재면 silent skip."""
    if not DB_PATH.exists():
        return
    obs_id = f"{session_id}-{uuid.uuid4().hex[:8]}"
    try:
        conn = sqlite3.connect(DB_PATH)
        try:
            with conn:
                ensure_migrations(conn)
                conn.execute(
                    """
                    INSERT INTO observations
                      (id, session_id, date, section, content, tags, completed, created_at,
                       category, artifact_kind, phase)
                    VALUES (?, ?, ?, 'dharness_event', ?, ?, 0, ?, ?, ?, NULL)
                    """,
                    (
                        obs_id,
                        session_id,
                        today,
                        event["content"],
                        json.dumps(event["tags"]),
                        now_iso,
                        event["category"],
                        event["artifact_kind"],
                    ),
                )
        finally:
            conn.close()
    except sqlite3.Error as e:
        print(f"[CM PostToolUse] dharness_event INSERT 실패: {e}", file=sys.stderr)


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        payload = {}

    session_id = read_session_id() or "unknown"
    tool_name = payload.get("tool_name") or payload.get("tool") or "unknown"
    tool_input = payload.get("tool_input") or {}
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

    if session_id != "unknown":
        event = classify_dharness_event(tool_name, tool_input)
        if event:
            _persist_dharness_event(session_id, event, tool_name, now_iso, today)

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
