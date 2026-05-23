"""SessionEnd hook 단위 테스트.

실행:
    py .claude/hooks/test_session_end.py

stdlib unittest, 외부 의존성 0. tmp 디렉토리 + fresh DB에서 dharness_event 집계,
draft 파일 생성, sessions.ended_at UPDATE, telemetry finalize emit을 검증한다.
"""

from __future__ import annotations

import json
import sqlite3
import time
import unittest

from _test_fixtures import HookTestBase
import _schema


class CollectSessionEvents(HookTestBase):
    def test_zero_events(self):
        se = self.hooks["session_end"]
        with sqlite3.connect(_schema.DB_PATH) as conn:
            summary = se._collect_session_events(conn, "empty01")
        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["categories"], {})
        self.assertEqual(summary["targets"], [])

    def test_aggregation_and_dedup(self):
        se = self.hooks["session_end"]
        self.insert_observation("s1", "harness_skill_edit", "skill",
                                content="Edit plugins/harness/skills/harness/SKILL.md")
        self.insert_observation("s1", "harness_skill_edit", "skill",
                                content="Edit plugins/harness/skills/harness/SKILL.md")  # 중복 target
        self.insert_observation("s1", "harness_reference_edit", "reference",
                                content="Edit plugins/harness/skills/harness/references/x.md")
        self.insert_observation("s1", "git_commit", "git",
                                content="Bash git commit -m foo")  # git은 target 추출 skip
        with sqlite3.connect(_schema.DB_PATH) as conn:
            summary = se._collect_session_events(conn, "s1")
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["categories"]["harness_skill_edit"], 2)
        self.assertEqual(summary["categories"]["git_commit"], 1)
        self.assertEqual(summary["kinds"]["skill"], 2)
        self.assertEqual(summary["kinds"]["git"], 1)
        self.assertEqual(len(summary["targets"]), 2)  # SKILL.md + references/x.md
        self.assertNotIn("git", summary["targets"])


class GenerateDraft(HookTestBase):
    def test_zero_events_returns_none(self):
        se = self.hooks["session_end"]
        with sqlite3.connect(_schema.DB_PATH) as conn:
            path = se.generate_draft(conn, "empty02", "2026-05-23", 10)
        self.assertIsNone(path)

    def test_draft_file_emitted_with_table_row(self):
        se = self.hooks["session_end"]
        self.insert_observation("draft01", "harness_skill_edit", "skill",
                                content="Edit plugins/harness/skills/harness/SKILL.md")
        self.insert_observation("draft01", "cm_hook_edit", "hook",
                                content="Edit .claude/hooks/post_tool_use.py")
        with sqlite3.connect(_schema.DB_PATH) as conn:
            path = se.generate_draft(conn, "draft01", "2026-05-23", 37)
        self.assertIsNotNone(path)
        self.assertEqual(path.name, "2026-05-23_draft01.md")
        text = path.read_text(encoding="utf-8")
        self.assertIn("session_id: draft01", text)
        self.assertIn("duration_min: 37", text)
        self.assertIn("total_events: 2", text)
        # 표 행 형식 검증.
        self.assertIn("| 2026-05-23 | dharness_event 자동 draft", text)
        self.assertIn("harness_skill_edit:1", text)
        self.assertIn("cm_hook_edit:1", text)
        self.assertIn(_schema.DRAFT_REASON_PLACEHOLDER, text)

    def test_draft_targets_truncated(self):
        """8개 초과 시 (+N more)로 truncate (DRAFT_TARGETS_MAX=8)."""
        se = self.hooks["session_end"]
        for i in range(12):
            self.insert_observation(
                "manytargets", "harness_skill_edit", "skill",
                content=f"Edit plugins/harness/skills/harness/file{i:02d}.md",
            )
        with sqlite3.connect(_schema.DB_PATH) as conn:
            path = se.generate_draft(conn, "manytargets", "2026-05-23", 5)
        text = path.read_text(encoding="utf-8")
        # 표 행에는 8개만 + (+4 more).
        self.assertIn("(+4 more)", text)
        # 전체 12개는 본문 "변경 대상" 섹션에 박제.
        self.assertIn("전체 12개", text)


class MainEndToEnd(HookTestBase):
    def test_no_session_id_skips(self):
        se = self.hooks["session_end"]
        # session_id 파일 없음.
        rc = se.main()
        self.assertEqual(rc, 0)

    def test_finalize_emits_telemetry_and_updates_session(self):
        se = self.hooks["session_end"]
        sid = "endtoend01"
        self.write_session_id(sid)
        self.insert_session(sid, started_at="2026-05-23T00:00:00Z", ended_at=None)
        sess_dir = _schema.MEMORY_ROOT / "sessions" / sid
        sess_dir.mkdir(parents=True)
        # raw.jsonl에 tool_result 라인 1줄.
        (sess_dir / "raw.jsonl").write_text(
            json.dumps({"ts": "2026-05-23T00:01:00Z", "kind": "tool_result",
                        "tool": "Edit", "output_size": 100}) + "\n",
            encoding="utf-8",
        )
        # dharness_event 1건 — draft 생성 트리거.
        self.insert_observation(sid, "harness_skill_edit", "skill")
        rc = se.main()
        self.assertEqual(rc, 0)
        # sessions UPDATE 검증.
        with sqlite3.connect(_schema.DB_PATH) as conn:
            row = conn.execute(
                "SELECT ended_at, tools_used FROM sessions WHERE session_id=?", (sid,)
            ).fetchone()
        self.assertIsNotNone(row[0])
        self.assertIn("Edit", row[1])
        # transcript.md 박제 확인.
        self.assertTrue((sess_dir / "transcript.md").exists())
        # draft 파일 박제 확인.
        drafts = list(_schema.DRAFTS_DIR.glob(f"*_{sid}.md"))
        self.assertEqual(len(drafts), 1)
        # telemetry session_capture_finalize + claudemd_draft_created emit.
        today = time.strftime("%Y-%m-%d", time.gmtime())
        tel = (_schema.TELEMETRY_DIR / f"{today}.jsonl").read_text(encoding="utf-8")
        self.assertIn("session_capture_finalize", tel)
        self.assertIn("claudemd_draft_created", tel)

    def test_zero_events_no_draft_but_finalize_still_emits(self):
        se = self.hooks["session_end"]
        sid = "noevents01"
        self.write_session_id(sid)
        self.insert_session(sid, started_at="2026-05-23T00:00:00Z", ended_at=None)
        sess_dir = _schema.MEMORY_ROOT / "sessions" / sid
        sess_dir.mkdir(parents=True)
        (sess_dir / "raw.jsonl").touch()
        rc = se.main()
        self.assertEqual(rc, 0)
        drafts = list(_schema.DRAFTS_DIR.glob(f"*_{sid}.md"))
        self.assertEqual(drafts, [])  # event 0건 → draft 미생성.
        today = time.strftime("%Y-%m-%d", time.gmtime())
        tel = (_schema.TELEMETRY_DIR / f"{today}.jsonl").read_text(encoding="utf-8")
        self.assertIn("session_capture_finalize", tel)
        self.assertNotIn("claudemd_draft_created", tel)


if __name__ == "__main__":
    unittest.main(verbosity=2)
