"""SessionStart hook 단위 테스트.

실행:
    py .claude/hooks/test_session_start.py

stdlib unittest, 외부 의존성 0. tmp 디렉토리에 fresh DB를 부트스트랩하고
session_start 핵심 함수를 격리 호출한다.
"""

from __future__ import annotations

import io
import json
import sqlite3
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from _test_fixtures import HookTestBase
import _schema


class BackfillDanglingSessions(HookTestBase):
    def test_dangling_session_with_raw_finalized(self):
        """ended_at IS NULL + raw.jsonl 비어있지 않은 세션은 finalize 된다."""
        ss = self.hooks["session_start"]
        sid = "abc123"
        self.insert_session(sid, started_at="2026-05-23T00:00:00Z", ended_at=None)
        sess_dir = _schema.MEMORY_ROOT / "sessions" / sid
        sess_dir.mkdir(parents=True)
        (sess_dir / "raw.jsonl").write_text(
            json.dumps({"ts": "2026-05-23T00:01:00Z", "kind": "tool_result",
                        "tool": "Read", "output_size": 100}) + "\n",
            encoding="utf-8",
        )
        with sqlite3.connect(_schema.DB_PATH) as conn:
            finalized = ss.backfill_dangling_sessions(conn, "2026-05-23T01:00:00Z")
        self.assertEqual(finalized, [sid])
        with sqlite3.connect(_schema.DB_PATH) as conn:
            row = conn.execute(
                "SELECT ended_at, tools_used FROM sessions WHERE session_id=?", (sid,)
            ).fetchone()
        self.assertEqual(row[0], "2026-05-23T01:00:00Z")
        self.assertIn("Read", row[1])

    def test_dangling_session_with_empty_raw_skipped(self):
        """raw.jsonl 부재/빈 파일이면 finalize 대상 아님."""
        ss = self.hooks["session_start"]
        sid = "def456"
        self.insert_session(sid, ended_at=None)
        sess_dir = _schema.MEMORY_ROOT / "sessions" / sid
        sess_dir.mkdir(parents=True)
        (sess_dir / "raw.jsonl").touch()
        with sqlite3.connect(_schema.DB_PATH) as conn:
            finalized = ss.backfill_dangling_sessions(conn, "2026-05-23T01:00:00Z")
        self.assertEqual(finalized, [])

    def test_completed_session_untouched(self):
        """ended_at 있는 세션은 무시된다."""
        ss = self.hooks["session_start"]
        sid = "ghi789"
        self.insert_session(sid, ended_at="2026-05-22T00:00:00Z")
        with sqlite3.connect(_schema.DB_PATH) as conn:
            finalized = ss.backfill_dangling_sessions(conn, "2026-05-23T01:00:00Z")
        self.assertEqual(finalized, [])


class FetchPriorSessions(HookTestBase):
    def test_categories_aggregated_per_session(self):
        ss = self.hooks["session_start"]
        self.insert_session("old111", started_at="2026-05-20T00:00:00Z", date="2026-05-20")
        self.insert_observation("old111", "harness_skill_edit", "skill")
        self.insert_observation("old111", "harness_skill_edit", "skill",
                                content="Edit plugins/harness/skills/harness/references/x.md")
        self.insert_observation("old111", "git_commit", "git",
                                content="Bash git commit ...")
        self.insert_session("new222", started_at="2026-05-21T00:00:00Z", date="2026-05-21")
        self.insert_observation("new222", "cm_hook_edit", "hook",
                                content="Edit .claude/hooks/session_start.py")
        with sqlite3.connect(_schema.DB_PATH) as conn:
            prior = ss.fetch_prior_sessions(conn, "current999", 5)
        ids = [p["session_id"] for p in prior]
        self.assertEqual(ids, ["new222", "old111"])  # 최신 first
        self.assertEqual(prior[1]["categories"]["harness_skill_edit"], 2)
        self.assertEqual(prior[0]["categories"]["cm_hook_edit"], 1)

    def test_current_session_excluded(self):
        ss = self.hooks["session_start"]
        self.insert_session("me", started_at="2026-05-22T00:00:00Z")
        with sqlite3.connect(_schema.DB_PATH) as conn:
            prior = ss.fetch_prior_sessions(conn, "me", 5)
        self.assertEqual(prior, [])


class FetchPendingDrafts(HookTestBase):
    def test_drafts_listed_with_sid(self):
        ss = self.hooks["session_start"]
        (_schema.DRAFTS_DIR / "2026-05-22_aaa111.md").write_text("body", encoding="utf-8")
        (_schema.DRAFTS_DIR / "2026-05-23_bbb222.md").write_text("body", encoding="utf-8")
        out = ss.fetch_pending_drafts(5)
        self.assertEqual(sorted(out), ["2026-05-22 aaa111", "2026-05-23 bbb222"])

    def test_no_drafts_dir(self):
        ss = self.hooks["session_start"]
        import shutil
        shutil.rmtree(_schema.DRAFTS_DIR)
        out = ss.fetch_pending_drafts(5)
        self.assertEqual(out, [])

    def test_limit_respected(self):
        ss = self.hooks["session_start"]
        for i in range(10):
            (_schema.DRAFTS_DIR / f"2026-05-2{i % 5}_sid{i:03d}.md").write_text("x", encoding="utf-8")
        out = ss.fetch_pending_drafts(3)
        self.assertEqual(len(out), 3)


class FetchGitStatusShort(HookTestBase):
    def test_subprocess_failure_returns_empty(self):
        ss = self.hooks["session_start"]
        with patch("subprocess.run", side_effect=FileNotFoundError("git missing")):
            out = ss.fetch_git_status_short(10)
        self.assertEqual(out, [])

    def test_max_lines_truncated(self):
        ss = self.hooks["session_start"]
        class FakeResult:
            returncode = 0
            stdout = "\n".join(f" M file{i}.py" for i in range(20))
        with patch("subprocess.run", return_value=FakeResult()):
            out = ss.fetch_git_status_short(5)
        self.assertEqual(len(out), 5)
        self.assertTrue(out[0].endswith("file0.py"))


class FormatAdaptAlert(HookTestBase):
    def test_below_threshold_returns_none(self):
        ss = self.hooks["session_start"]
        out = ss.format_adapt_alert({"harness_invocation": 1, "agent_invocation": 1}, 0.0)
        self.assertIsNone(out)

    def test_invocations_threshold_emits_alert(self):
        ss = self.hooks["session_start"]
        out = ss.format_adapt_alert(
            {"harness_invocation": 8, "agent_invocation": 5}, 0.0
        )
        self.assertIsNotNone(out)
        self.assertIn("Phase 10 ADAPT", out)
        self.assertIn("invocations=13", out)

    def test_failures_threshold_emits_alert(self):
        ss = self.hooks["session_start"]
        out = ss.format_adapt_alert({"agent_failure": 5}, 0.0)
        self.assertIsNotNone(out)
        self.assertIn("failures=5", out)


class FormatInject(HookTestBase):
    def test_basic_composition(self):
        ss = self.hooks["session_start"]
        out = ss.format_inject(
            session_id="cur555",
            project_name="dharness",
            prior=[{"session_id": "old111", "date": "2026-05-20",
                    "started_at": "2026-05-20T00:00:00Z",
                    "categories": {"harness_skill_edit": 3}}],
            git_lines=[" M README.md"],
            pending_drafts=["2026-05-22 aaa111"],
            adapt_alert=None,
            budget=2000,
        )
        self.assertIn("cur555", out)
        self.assertIn("dharness", out)
        self.assertIn("harness_skill_edit:3", out)
        self.assertIn("README.md", out)
        self.assertIn("aaa111", out)

    def test_no_prior_category_label(self):
        ss = self.hooks["session_start"]
        out = ss.format_inject(
            session_id="x", project_name="p",
            prior=[{"session_id": "s", "date": "d", "started_at": "t", "categories": {}}],
            git_lines=[], pending_drafts=[], adapt_alert=None, budget=2000,
        )
        self.assertIn("(no dharness_event)", out)

    def test_budget_truncation(self):
        ss = self.hooks["session_start"]
        long_lines = [f"  ?? big_file_{i}.txt" for i in range(200)]
        out = ss.format_inject(
            session_id="x", project_name="p",
            prior=[], git_lines=long_lines, pending_drafts=[], adapt_alert=None,
            budget=200,
        )
        self.assertEqual(len(out), 200)
        self.assertTrue(out.endswith("…"))

    def test_adapt_alert_included(self):
        ss = self.hooks["session_start"]
        out = ss.format_inject(
            session_id="x", project_name="p", prior=[],
            git_lines=[], pending_drafts=[], adapt_alert="[CM] ⚠️ ADAPT 권장",
            budget=2000,
        )
        self.assertIn("ADAPT 권장", out)


class MainEndToEnd(HookTestBase):
    def test_session_inserted_and_inject_emitted(self):
        ss = self.hooks["session_start"]
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ss.main()
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertIn("hookSpecificOutput", payload)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")
        ctx = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("[CM] session_id=", ctx)
        # session_id 파일 박제 확인.
        sid = _schema.SESSION_ID_FILE.read_text(encoding="utf-8")
        self.assertEqual(len(sid), 6)
        # sessions 테이블 row 박제 확인.
        with sqlite3.connect(_schema.DB_PATH) as conn:
            n = conn.execute("SELECT COUNT(*) FROM sessions WHERE session_id=?", (sid,)).fetchone()[0]
        self.assertEqual(n, 1)
        # telemetry harness_invocation 박제 확인 (Phase 10 adapt 계수의 입력).
        today = time.strftime("%Y-%m-%d", time.gmtime())
        tel = (_schema.TELEMETRY_DIR / f"{today}.jsonl").read_text(encoding="utf-8")
        self.assertIn('"type": "harness_invocation"', tel)


if __name__ == "__main__":
    unittest.main(verbosity=2)
