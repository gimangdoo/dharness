#!/usr/bin/env python3
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
    _get_conn,
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
        conn = _get_conn()
        try:
            with conn:
                ensure_migrations(conn)
                conn.execute(
                    """
                    INSERT INTO observations
                      (id, session_id, date, section, content, tags, created_at,
                       category, artifact_kind)
                    VALUES (?, ?, ?, 'dharness_event', ?, ?, ?, ?, ?)
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


def _agent_failure_reason(tool_response: object, serialized: str) -> str | None:
    """Task tool 응답에서 실패 사유 추출. 실패 아니면 None.

    failure 시그니처: is_error=True / type=='error' / 'Error:' prefix /
    error 필드 비어있지 않음. Task 응답이 dict일 때는 metadata 우선,
    string fallback (마지막 보루). 반환값은 telemetry `error` 필드에 박제(≤200자)."""
    if isinstance(tool_response, dict):
        if tool_response.get("is_error") is True:
            err = tool_response.get("error") or tool_response.get("message")
            return str(err)[:200] if err else "is_error"
        if tool_response.get("type") == "error":
            err = tool_response.get("error") or tool_response.get("message")
            return str(err)[:200] if err else "error"
        if tool_response.get("error"):
            return str(tool_response["error"])[:200]
        # Task 응답의 일반적인 구조 — content 또는 result 안에 error indicator
        for key in ("content", "result"):
            inner = tool_response.get(key)
            if isinstance(inner, str) and inner.lstrip().lower().startswith("error:"):
                return inner.strip()[:200]
    if isinstance(serialized, str):
        stripped = serialized.lstrip()
        if stripped[:64].lower().startswith("error:"):
            return stripped[:200]
        if '"is_error":true' in serialized:
            return "is_error"
    return None


def _emit_agent_telemetry(
    tool_name: str,
    tool_input: dict,
    tool_response: object,
    serialized: str,
    session_id: str,
    now_iso: str,
    today: str,
) -> None:
    """Task/Agent tool 결과 시 agent_invocation 1건 + 실패면 agent_failure 1건 emit.

    실측(2026-05-23 review): Claude Code hook payload는 sub-agent 호출 시 `Agent`
    tool name을 emit (raw.jsonl 검증). `Task`만 매칭 시 telemetry 영구 누락.
    """
    if tool_name not in ("Task", "Agent"):
        return
    subagent_type = tool_input.get("subagent_type") or "general-purpose"
    description = tool_input.get("description") or ""
    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    path = TELEMETRY_DIR / f"{today}.jsonl"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "ts": now_iso, "type": "agent_invocation",
            "session_id": session_id, "subagent_type": subagent_type,
            "description": description[:120],
        }) + "\n")
        reason = _agent_failure_reason(tool_response, serialized)
        if reason is not None:
            fh.write(json.dumps({
                "ts": now_iso, "type": "agent_failure",
                "session_id": session_id, "subagent_type": subagent_type,
                "description": description[:120],
                "error": reason,
                # PostToolUse는 최종 tool_response만 관측 — agent_failure는 재시도가
                # 모두 소진된 terminal failure 시에만 emit되므로 retry_succeeded는 항상
                # False (recovered retry는 이 hook 지점에서 관측 불가).
                "retry_succeeded": False,
            }) + "\n")


def _main_impl() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        payload = {}

    session_id = read_session_id()
    if not session_id:
        # SessionStart 미실행 — capture 전체 skip. orphan persistence 방지.
        return 0
    tool_name = payload.get("tool_name") or payload.get("tool") or "unknown"
    tool_input = payload.get("tool_input") or {}
    tool_response = payload.get("tool_response") or payload.get("output") or ""
    serialized = _serialize(tool_response)
    output_size = len(serialized.encode("utf-8"))
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    today = time.strftime("%Y-%m-%d", time.gmtime())

    try:
        _emit_agent_telemetry(
            tool_name, tool_input, tool_response, serialized,
            session_id, now_iso, today,
        )
    except Exception as e:
        print(f"[CM PostToolUse] agent telemetry skipped: {e}", file=sys.stderr)

    sess_dir = MEMORY_ROOT / "sessions" / session_id
    if sess_dir.exists():
        # IO 오류를 국소화 — append 실패가 이후 dharness_event INSERT·capture를
        # 통째로 drop시키지 않도록 (전역 swallow의 generic hook_crash보다 정밀).
        try:
            with open(sess_dir / "raw.jsonl", "a", encoding="utf-8") as fh:
                fh.write(json.dumps({
                    "ts": now_iso, "kind": "tool_result",
                    "tool": tool_name, "output_size": output_size,
                }) + "\n")
        except OSError as e:
            print(f"[CM PostToolUse] raw.jsonl append skipped: {e}", file=sys.stderr)

    event = classify_dharness_event(tool_name, tool_input)
    if event:
        _persist_dharness_event(session_id, event, tool_name, now_iso, today)

    if output_size <= THRESHOLD_BYTES:
        return 0

    raw_dir = TOOL_OUTPUTS / session_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    ext = {"WebFetch": "html", "Read": "txt", "Bash": "log"}.get(tool_name, "txt")
    # PO1 (2026-05-27): seq counter (raw_dir.glob "*" O(N)) 제거 — uuid 단독으로 고유성 충분.
    # filename은 time.time_ns()로 정렬 가능 (ascending = capture order).
    raw_path = raw_dir / f"{time.time_ns()}_{tool_name.lower()}_{uuid.uuid4().hex[:8]}.{ext}"
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


def main() -> int:
    """Hook entry — uncaught 예외는 host 세션을 깨뜨리지 않도록 swallow + hook_crash telemetry.

    Capture 실패는 관측성 손실이지 세션 정확성 손실이 아니다. 항상 0 반환.
    """
    try:
        return _main_impl()
    except Exception as e:
        try:
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            today = time.strftime("%Y-%m-%d", time.gmtime())
            TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
            with open(TELEMETRY_DIR / f"{today}.jsonl", "a", encoding="utf-8") as fh:
                fh.write(json.dumps({
                    "ts": now_iso, "type": "hook_crash",
                    "handler": "post_tool_use.py",
                    "error": f"{type(e).__name__}: {e}"[:500],
                }) + "\n")
        except Exception:
            pass
        print(f"[CM PostToolUse] hook crash swallowed: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
