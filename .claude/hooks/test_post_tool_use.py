"""PostToolUse hook 단위 테스트.

실행:
    py .claude/hooks/test_post_tool_use.py

stdlib unittest, 외부 의존성 0. tmp 디렉토리 + fresh DB에서 raw.jsonl append,
10KB threshold split, agent telemetry emit, dharness_event INSERT를 검증한다.
"""

from __future__ import annotations

import io
import json
import sqlite3
import sys
import time
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

from _test_fixtures import HookTestBase
import _schema


def _run_with_stdin(hook_module, payload: dict) -> int:
    """stdin에 JSON payload 주입 후 main() 호출."""
    stderr = io.StringIO()
    orig_stdin = sys.stdin
    sys.stdin = io.StringIO(json.dumps(payload))
    try:
        with redirect_stderr(stderr):
            rc = hook_module.main()
    finally:
        sys.stdin = orig_stdin
    return rc


class Serialize(HookTestBase):
    def test_str_passthrough(self):
        ptu = self.hooks["post_tool_use"]
        self.assertEqual(ptu._serialize("hello"), "hello")

    def test_none_returns_empty(self):
        ptu = self.hooks["post_tool_use"]
        self.assertEqual(ptu._serialize(None), "")

    def test_dict_json_encoded(self):
        ptu = self.hooks["post_tool_use"]
        out = ptu._serialize({"a": 1, "b": "값"})
        self.assertIn('"값"', out)  # ensure_ascii=False

    def test_unserializable_falls_back_to_str(self):
        ptu = self.hooks["post_tool_use"]
        class Weird:
            def __repr__(self): return "<weird>"
        out = ptu._serialize(Weird())
        self.assertEqual(out, "<weird>")


class AgentFailureReason(HookTestBase):
    def test_is_error_true(self):
        ptu = self.hooks["post_tool_use"]
        self.assertEqual(ptu._agent_failure_reason({"is_error": True}, "{}"), "is_error")

    def test_is_error_with_message(self):
        ptu = self.hooks["post_tool_use"]
        self.assertEqual(
            ptu._agent_failure_reason({"is_error": True, "error": "boom"}, "{}"), "boom"
        )

    def test_type_error(self):
        ptu = self.hooks["post_tool_use"]
        self.assertEqual(ptu._agent_failure_reason({"type": "error"}, "{}"), "error")

    def test_error_field_truthy(self):
        ptu = self.hooks["post_tool_use"]
        self.assertEqual(ptu._agent_failure_reason({"error": "boom"}, "{}"), "boom")

    def test_string_error_prefix(self):
        ptu = self.hooks["post_tool_use"]
        self.assertEqual(
            ptu._agent_failure_reason("Error: nope", "Error: nope"), "Error: nope"
        )

    def test_inner_content_error_prefix(self):
        ptu = self.hooks["post_tool_use"]
        self.assertEqual(ptu._agent_failure_reason(
            {"content": "Error: bad input"}, '{"content": "Error: bad input"}'
        ), "Error: bad input")

    def test_reason_truncated_200(self):
        ptu = self.hooks["post_tool_use"]
        reason = ptu._agent_failure_reason({"error": "x" * 500}, "{}")
        self.assertEqual(len(reason), 200)

    def test_success_returns_none(self):
        ptu = self.hooks["post_tool_use"]
        self.assertIsNone(ptu._agent_failure_reason({"ok": True}, '{"ok": true}'))


class EmitAgentTelemetry(HookTestBase):
    """P1 회귀 — Agent + Task 둘 다 telemetry emit 해야 한다."""

    def _read_telemetry(self) -> list[dict]:
        today = time.strftime("%Y-%m-%d", time.gmtime())
        path = _schema.TELEMETRY_DIR / f"{today}.jsonl"
        if not path.exists():
            return []
        return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]

    def test_task_emits_agent_invocation(self):
        ptu = self.hooks["post_tool_use"]
        ptu._emit_agent_telemetry(
            "Task", {"subagent_type": "Explore", "description": "find x"},
            {"ok": True}, '{"ok": true}', "sid1", "2026-05-23T00:00:00Z",
            time.strftime("%Y-%m-%d", time.gmtime()),
        )
        events = self._read_telemetry()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "agent_invocation")
        self.assertEqual(events[0]["subagent_type"], "Explore")

    def test_agent_emits_agent_invocation(self):
        """P1 picture — `Agent` tool name도 매칭되어야 함."""
        ptu = self.hooks["post_tool_use"]
        ptu._emit_agent_telemetry(
            "Agent", {"subagent_type": "general-purpose", "description": "do y"},
            {"ok": True}, '{"ok": true}', "sid2", "2026-05-23T00:00:00Z",
            time.strftime("%Y-%m-%d", time.gmtime()),
        )
        events = self._read_telemetry()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "agent_invocation")

    def test_non_agent_tool_skipped(self):
        ptu = self.hooks["post_tool_use"]
        ptu._emit_agent_telemetry(
            "Bash", {}, "", "", "sid3", "2026-05-23T00:00:00Z",
            time.strftime("%Y-%m-%d", time.gmtime()),
        )
        self.assertEqual(self._read_telemetry(), [])

    def test_failure_emits_two_events(self):
        ptu = self.hooks["post_tool_use"]
        ptu._emit_agent_telemetry(
            "Agent", {"subagent_type": "Explore", "description": "x"},
            {"is_error": True}, '{"is_error":true}', "sid4",
            "2026-05-23T00:00:00Z", time.strftime("%Y-%m-%d", time.gmtime()),
        )
        events = self._read_telemetry()
        types = [e["type"] for e in events]
        self.assertIn("agent_invocation", types)
        self.assertIn("agent_failure", types)
        fail = next(e for e in events if e["type"] == "agent_failure")
        self.assertEqual(fail["error"], "is_error")
        self.assertIs(fail["retry_succeeded"], False)

    def test_description_truncated_120(self):
        ptu = self.hooks["post_tool_use"]
        ptu._emit_agent_telemetry(
            "Task", {"description": "x" * 200}, {}, "{}", "sid5",
            "2026-05-23T00:00:00Z", time.strftime("%Y-%m-%d", time.gmtime()),
        )
        events = self._read_telemetry()
        self.assertEqual(len(events[0]["description"]), 120)


class MainSkipNoSessionId(HookTestBase):
    def test_returns_0_without_session_id(self):
        """SessionStart 미실행 (current_session 파일 부재) — 전체 skip."""
        ptu = self.hooks["post_tool_use"]
        # session_id 파일 없음.
        rc = _run_with_stdin(ptu, {"tool_name": "Read", "tool_input": {}})
        self.assertEqual(rc, 0)


class MainMalformedStdin(HookTestBase):
    """PT3 (2026-05-27): JSONDecodeError fallback (`payload = {}`) 경로 회귀.

    malformed stdin은 host 세션을 깨뜨리지 않고 silent skip 해야 한다. session_id
    파일 부재면 즉시 return 0 (orphan capture 방지).
    """

    def _run_with_raw_stdin(self, raw: str) -> int:
        import io
        from contextlib import redirect_stderr
        ptu = self.hooks["post_tool_use"]
        stderr = io.StringIO()
        orig_stdin = sys.stdin
        sys.stdin = io.StringIO(raw)
        try:
            with redirect_stderr(stderr):
                rc = ptu.main()
        finally:
            sys.stdin = orig_stdin
        return rc

    def test_empty_stdin_returns_0(self):
        # payload = {} (sys.stdin.read() == "" → "" or "{}" → {}).
        rc = self._run_with_raw_stdin("")
        self.assertEqual(rc, 0)

    def test_malformed_json_returns_0(self):
        # `payload = {}` fallback. session_id 미설정 → return 0.
        rc = self._run_with_raw_stdin("{ this is not valid json")
        self.assertEqual(rc, 0)

    def test_malformed_json_with_session_id_returns_0(self):
        """session_id 파일이 있어도 payload empty → tool_name='unknown' 경로 회귀."""
        self.write_session_id("ptmal1")
        (_schema.MEMORY_ROOT / "sessions" / "ptmal1").mkdir(parents=True)
        (_schema.MEMORY_ROOT / "sessions" / "ptmal1" / "raw.jsonl").touch()
        rc = self._run_with_raw_stdin("garbage payload")
        self.assertEqual(rc, 0)
        # raw.jsonl에 tool='unknown' 라인 1건 박제 (silent skip 아닌 안전 기록).
        raw = (_schema.MEMORY_ROOT / "sessions" / "ptmal1" / "raw.jsonl").read_text(encoding="utf-8")
        self.assertIn('"tool": "unknown"', raw)


class MainPersistsAndClassifies(HookTestBase):
    def test_small_output_appends_raw_only(self):
        ptu = self.hooks["post_tool_use"]
        self.write_session_id("test01")
        (_schema.MEMORY_ROOT / "sessions" / "test01").mkdir(parents=True)
        (_schema.MEMORY_ROOT / "sessions" / "test01" / "raw.jsonl").touch()
        rc = _run_with_stdin(ptu, {
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/x.txt"},
            "tool_response": "small",
        })
        self.assertEqual(rc, 0)
        raw = (_schema.MEMORY_ROOT / "sessions" / "test01" / "raw.jsonl").read_text(encoding="utf-8")
        self.assertIn('"tool": "Read"', raw)
        # tool_output_captured emit 안 됨 (10KB 미만).
        today = time.strftime("%Y-%m-%d", time.gmtime())
        tel_path = _schema.TELEMETRY_DIR / f"{today}.jsonl"
        tel_text = tel_path.read_text(encoding="utf-8") if tel_path.exists() else ""
        self.assertNotIn("tool_output_captured", tel_text)

    def test_large_output_captures_raw_file(self):
        ptu = self.hooks["post_tool_use"]
        self.write_session_id("test02")
        (_schema.MEMORY_ROOT / "sessions" / "test02").mkdir(parents=True)
        (_schema.MEMORY_ROOT / "sessions" / "test02" / "raw.jsonl").touch()
        # PT4 (2026-05-27): non-repeating payload — 압축/dedup이 우연히 통과하지 않게.
        big = "".join(chr(0x30 + (i % 64)) for i in range(11 * 1024))
        rc = _run_with_stdin(ptu, {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
            "tool_response": big,
        })
        self.assertEqual(rc, 0)
        # _tool_outputs/test02 디렉토리에 1 파일 박제.
        outputs = list((_schema.TOOL_OUTPUTS / "test02").glob("*"))
        self.assertEqual(len(outputs), 1)
        self.assertTrue(outputs[0].suffix == ".log")  # Bash → .log
        # PT4: content == 원본 raw payload (truncate/compress/encoding loss 없음).
        captured = outputs[0].read_text(encoding="utf-8")
        self.assertEqual(len(captured), len(big),
                         f"length mismatch: captured={len(captured)} original={len(big)}")
        self.assertEqual(captured, big, "captured content ≠ original payload")
        # telemetry tool_output_captured emit 확인.
        today = time.strftime("%Y-%m-%d", time.gmtime())
        tel = (_schema.TELEMETRY_DIR / f"{today}.jsonl").read_text(encoding="utf-8")
        self.assertIn("tool_output_captured", tel)

    def test_dharness_event_persisted(self):
        ptu = self.hooks["post_tool_use"]
        self.write_session_id("test03")
        (_schema.MEMORY_ROOT / "sessions" / "test03").mkdir(parents=True)
        (_schema.MEMORY_ROOT / "sessions" / "test03" / "raw.jsonl").touch()
        rc = _run_with_stdin(ptu, {
            "tool_name": "Edit",
            "tool_input": {"file_path": "plugins/harness/skills/harness/SKILL.md"},
            "tool_response": "ok",
        })
        self.assertEqual(rc, 0)
        with sqlite3.connect(_schema.DB_PATH) as conn:
            rows = conn.execute(
                "SELECT category, artifact_kind FROM observations "
                "WHERE session_id='test03' AND section='dharness_event'"
            ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "harness_skill_edit")
        self.assertEqual(rows[0][1], "skill")


if __name__ == "__main__":
    unittest.main(verbosity=2)
