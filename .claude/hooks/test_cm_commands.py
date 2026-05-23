"""cm_commands.py 단위 테스트 (/cm-* 슬래시 커맨드 핸들러).

실행:
    py .claude/hooks/test_cm_commands.py

stdlib unittest, 외부 의존성 0. tmp 디렉토리 + fresh DB에서 cmd_status,
cmd_sessions, cmd_reset, cmd_claudemd_list/apply/discard, 표 파싱 헬퍼를 검증한다.

_sanitize_reason은 test_schema.py에 이미 박제.
"""

from __future__ import annotations

import io
import sqlite3
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from _test_fixtures import HookTestBase
import _schema


def _captured(fn, *args, **kw) -> tuple[int, str]:
    """stdout 캡처하면서 fn 호출 → (rc, stdout) 반환."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = fn(*args, **kw)
    return rc, buf.getvalue()


class CmdStatus(HookTestBase):
    def test_db_missing_returns_1(self):
        cc = self.hooks["cm_commands"]
        # setUp이 DB를 만들었으니 지운다.
        _schema.DB_PATH.unlink()
        rc, _ = _captured(cc.cmd_status)
        self.assertEqual(rc, 1)

    def test_counts_displayed(self):
        cc = self.hooks["cm_commands"]
        self.insert_session("s1")
        self.insert_observation("s1", "harness_skill_edit", "skill")
        (_schema.DRAFTS_DIR / "2026-05-23_draft01.md").write_text("x", encoding="utf-8")
        rc, out = _captured(cc.cmd_status)
        self.assertEqual(rc, 0)
        self.assertIn("observations:", out)
        self.assertIn("sessions:", out)
        self.assertIn("changelog draft:", out)


class CmdSessions(HookTestBase):
    def test_lists_sorted_recent_first(self):
        cc = self.hooks["cm_commands"]
        self.insert_session("old", started_at="2026-05-20T00:00:00Z", date="2026-05-20")
        self.insert_session("mid", started_at="2026-05-21T00:00:00Z", date="2026-05-21")
        self.insert_session("new", started_at="2026-05-22T00:00:00Z", date="2026-05-22")
        rc, out = _captured(cc.cmd_sessions, 10)
        self.assertEqual(rc, 0)
        new_idx = out.find("new")
        old_idx = out.find("old")
        self.assertLess(new_idx, old_idx)  # 최신 먼저.

    def test_limit_respected(self):
        cc = self.hooks["cm_commands"]
        for i in range(5):
            self.insert_session(f"sid{i}", date=f"2026-05-2{i}",
                                started_at=f"2026-05-2{i}T00:00:00Z")
        rc, out = _captured(cc.cmd_sessions, 2)
        self.assertEqual(rc, 0)
        # 2 개 row만 표시.
        lines = [ln for ln in out.splitlines() if "sid" in ln]
        self.assertEqual(len(lines), 2)


class CmdReset(HookTestBase):
    def test_no_confirm_returns_1(self):
        cc = self.hooks["cm_commands"]
        rc, out = _captured(cc.cmd_reset, False)
        self.assertEqual(rc, 1)
        self.assertIn("--confirm", out)

    def test_confirmed_wipes_and_reinits(self):
        cc = self.hooks["cm_commands"]
        # pre-existing 데이터.
        self.insert_session("victim")
        self.insert_observation("victim", "harness_skill_edit", "skill")
        rc, _ = _captured(cc.cmd_reset, True)
        self.assertEqual(rc, 0)
        # 부트스트랩 후 DB 빈 상태.
        with sqlite3.connect(_schema.DB_PATH) as conn:
            n = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        self.assertEqual(n, 0)


class CmdClaudemdList(HookTestBase):
    def test_empty(self):
        cc = self.hooks["cm_commands"]
        rc, out = _captured(cc.cmd_claudemd_list)
        self.assertEqual(rc, 0)
        self.assertIn("0건", out)

    def test_lists_drafts_with_sid(self):
        cc = self.hooks["cm_commands"]
        (_schema.DRAFTS_DIR / "2026-05-22_aaa111.md").write_text("body", encoding="utf-8")
        (_schema.DRAFTS_DIR / "2026-05-23_bbb222.md").write_text("body", encoding="utf-8")
        rc, out = _captured(cc.cmd_claudemd_list)
        self.assertEqual(rc, 0)
        self.assertIn("aaa111", out)
        self.assertIn("bbb222", out)
        self.assertIn("apply: /cm-claudemd-apply", out)


class DraftRowExtraction(HookTestBase):
    def test_extract_draft_row(self):
        cc = self.hooks["cm_commands"]
        text = """## 표 행

```
| 2026-05-23 | foo | bar | reason |
```

다른 내용.
"""
        row = cc._extract_draft_row(text)
        self.assertEqual(row, "| 2026-05-23 | foo | bar | reason |")

    def test_no_row_returns_none(self):
        cc = self.hooks["cm_commands"]
        self.assertIsNone(cc._extract_draft_row("no code fence here"))


class ChangelogTableLocate(HookTestBase):
    def test_locates_table_after_heading(self):
        cc = self.hooks["cm_commands"]
        lines = [
            "# CHANGELOG",
            "",
            "## 변경 이력",
            "",
            "| 날짜 | 변경 | 대상 | 사유 |",
            "|---|---|---|---|",
            "| 2026-05-20 | a | b | c |",
            "| 2026-05-21 | d | e | f |",
            "",
            "## 다른 섹션",
        ]
        span = cc._find_change_history_table(lines)
        self.assertEqual(span, (4, 7))  # header_idx=4, last_row_idx=7

    def test_no_anchor_returns_none(self):
        cc = self.hooks["cm_commands"]
        self.assertIsNone(cc._find_change_history_table(["# Other"]))


class CmdClaudemdApply(HookTestBase):
    def _seed(self, sid: str, with_placeholder: bool = True) -> Path:
        """draft + CHANGELOG.md skeleton 부트스트랩."""
        if with_placeholder:
            reason = _schema.DRAFT_REASON_PLACEHOLDER
        else:
            reason = "기존 사유"
        draft_body = f"""---
session_id: {sid}
---

# draft

## 표 행

```
| 2026-05-23 | foo | bar | {reason} |
```
"""
        path = _schema.DRAFTS_DIR / f"2026-05-23_{sid}.md"
        path.write_text(draft_body, encoding="utf-8")
        _schema.CHANGELOG_MD.write_text(
            "# CHANGELOG\n\n## 변경 이력\n\n"
            "| 날짜 | 변경 | 대상 | 사유 |\n"
            "|---|---|---|---|\n"
            "| 2026-05-20 | old | x | reason |\n",
            encoding="utf-8",
        )
        return path

    def test_draft_missing_returns_1(self):
        cc = self.hooks["cm_commands"]
        rc, out = _captured(cc.cmd_claudemd_apply, "nope999", [])
        self.assertEqual(rc, 1)
        self.assertIn("draft 미발견", out)

    def test_placeholder_substituted_with_reason(self):
        cc = self.hooks["cm_commands"]
        draft = self._seed("apply01")
        rc, out = _captured(cc.cmd_claudemd_apply, "apply01", ["테스트", "사유"])
        self.assertEqual(rc, 0)
        cl = _schema.CHANGELOG_MD.read_text(encoding="utf-8")
        self.assertIn("| 2026-05-23 | foo | bar | 테스트 사유 |", cl)
        self.assertNotIn(_schema.DRAFT_REASON_PLACEHOLDER, cl.splitlines()[-1])
        # draft 파일이 applied/로 이동.
        self.assertFalse(draft.exists())
        self.assertTrue((_schema.DRAFTS_APPLIED / draft.name).exists())

    def test_no_reason_keeps_placeholder(self):
        cc = self.hooks["cm_commands"]
        self._seed("apply02")
        rc, out = _captured(cc.cmd_claudemd_apply, "apply02", [])
        self.assertEqual(rc, 0)
        cl = _schema.CHANGELOG_MD.read_text(encoding="utf-8")
        self.assertIn(_schema.DRAFT_REASON_PLACEHOLDER, cl)
        self.assertIn("placeholder인 채로 추가", out)

    def test_reason_sanitized_pipe_and_newline(self):
        """사유 안 `|`·줄바꿈은 table 깨짐 방지로 escape/공백 처리."""
        cc = self.hooks["cm_commands"]
        self._seed("apply03")
        rc, _ = _captured(cc.cmd_claudemd_apply, "apply03", ["a|b\nc"])
        self.assertEqual(rc, 0)
        cl = _schema.CHANGELOG_MD.read_text(encoding="utf-8")
        # `|` → `\|`, `\n` → space.
        self.assertIn(r"a\|b c", cl)

    def test_changelog_missing_returns_1(self):
        cc = self.hooks["cm_commands"]
        self._seed("apply04")
        _schema.CHANGELOG_MD.unlink()
        rc, out = _captured(cc.cmd_claudemd_apply, "apply04", [])
        self.assertEqual(rc, 1)
        self.assertIn("CHANGELOG.md 없음", out)


class CmdPrune(HookTestBase):
    def _seed_old_session(self, sid: str, old_date: str = "2025-01-01") -> None:
        """오래된 세션 + observation + tool_output + telemetry + applied draft 박제."""
        self.insert_session(sid, started_at=f"{old_date}T00:00:00Z", date=old_date)
        self.insert_observation(sid, "harness_skill_edit", "skill", date=old_date)
        # session dir + raw.jsonl + tool_output dir.
        sess_dir = _schema.MEMORY_ROOT / "sessions" / sid
        sess_dir.mkdir(parents=True, exist_ok=True)
        (sess_dir / "raw.jsonl").write_text("x", encoding="utf-8")
        tool_dir = _schema.TOOL_OUTPUTS / sid
        tool_dir.mkdir(parents=True, exist_ok=True)
        (tool_dir / "1.log").write_text("y", encoding="utf-8")
        # telemetry 파일 (오래된 date).
        (_schema.TELEMETRY_DIR / f"{old_date}.jsonl").write_text("z\n", encoding="utf-8")
        # applied draft.
        _schema.DRAFTS_APPLIED.mkdir(parents=True, exist_ok=True)
        (_schema.DRAFTS_APPLIED / f"{old_date}_{sid}.md").write_text("a", encoding="utf-8")

    def _seed_recent_session(self, sid: str) -> None:
        """최근 세션 (prune 대상 아님)."""
        today = time.strftime("%Y-%m-%d", time.gmtime())
        self.insert_session(sid, started_at=f"{today}T00:00:00Z", date=today)
        sess_dir = _schema.MEMORY_ROOT / "sessions" / sid
        sess_dir.mkdir(parents=True, exist_ok=True)
        (sess_dir / "raw.jsonl").write_text("recent", encoding="utf-8")

    def test_invalid_days_returns_1(self):
        cc = self.hooks["cm_commands"]
        rc, out = _captured(cc.cmd_prune, 0, False)
        self.assertEqual(rc, 1)
        self.assertIn("1 이상", out)

    def test_db_missing_returns_1(self):
        cc = self.hooks["cm_commands"]
        _schema.DB_PATH.unlink()
        rc, _ = _captured(cc.cmd_prune, 30, False)
        self.assertEqual(rc, 1)

    def test_dry_run_no_deletion(self):
        cc = self.hooks["cm_commands"]
        self._seed_old_session("old01")
        rc, out = _captured(cc.cmd_prune, 30, False)
        self.assertEqual(rc, 0)
        self.assertIn("[dry-run]", out)
        self.assertIn("--confirm", out)
        # 데이터 미삭제.
        sess_dir = _schema.MEMORY_ROOT / "sessions" / "old01"
        self.assertTrue(sess_dir.exists())
        with sqlite3.connect(_schema.DB_PATH) as conn:
            n = conn.execute("SELECT COUNT(*) FROM sessions WHERE session_id='old01'").fetchone()[0]
        self.assertEqual(n, 1)

    def test_confirm_deletes_old_keeps_recent(self):
        cc = self.hooks["cm_commands"]
        self._seed_old_session("old02", old_date="2025-01-01")
        self._seed_recent_session("new02")
        rc, _ = _captured(cc.cmd_prune, 30, True)
        self.assertEqual(rc, 0)
        # 오래된 세션 디렉토리·tool_output·telemetry·draft 삭제.
        self.assertFalse((_schema.MEMORY_ROOT / "sessions" / "old02").exists())
        self.assertFalse((_schema.TOOL_OUTPUTS / "old02").exists())
        self.assertFalse((_schema.TELEMETRY_DIR / "2025-01-01.jsonl").exists())
        self.assertFalse((_schema.DRAFTS_APPLIED / "2025-01-01_old02.md").exists())
        # DB row 삭제.
        with sqlite3.connect(_schema.DB_PATH) as conn:
            n = conn.execute("SELECT COUNT(*) FROM sessions WHERE session_id='old02'").fetchone()[0]
            obs = conn.execute("SELECT COUNT(*) FROM observations WHERE session_id='old02'").fetchone()[0]
        self.assertEqual(n, 0)
        self.assertEqual(obs, 0)
        # 최근 세션 보존.
        self.assertTrue((_schema.MEMORY_ROOT / "sessions" / "new02").exists())
        with sqlite3.connect(_schema.DB_PATH) as conn:
            n = conn.execute("SELECT COUNT(*) FROM sessions WHERE session_id='new02'").fetchone()[0]
        self.assertEqual(n, 1)

    def test_pending_drafts_preserved(self):
        """pending drafts (DRAFTS_DIR 루트)은 prune 대상 아님."""
        cc = self.hooks["cm_commands"]
        self._seed_old_session("old03", old_date="2025-01-01")
        pending = _schema.DRAFTS_DIR / "2025-01-01_old03.md"
        pending.write_text("pending", encoding="utf-8")
        rc, _ = _captured(cc.cmd_prune, 30, True)
        self.assertEqual(rc, 0)
        self.assertTrue(pending.exists())  # pending draft 보존.

    def test_no_old_data_reports_zero(self):
        cc = self.hooks["cm_commands"]
        self._seed_recent_session("recent01")
        rc, out = _captured(cc.cmd_prune, 30, True)
        self.assertEqual(rc, 0)
        self.assertIn("삭제할 데이터가 없습니다", out)


class CmdClaudemdDiscard(HookTestBase):
    def test_specific_sid_moved(self):
        cc = self.hooks["cm_commands"]
        draft = _schema.DRAFTS_DIR / "2026-05-23_disc01.md"
        draft.write_text("body", encoding="utf-8")
        rc, _ = _captured(cc.cmd_claudemd_discard, "disc01")
        self.assertEqual(rc, 0)
        self.assertFalse(draft.exists())
        self.assertTrue((_schema.DRAFTS_DISCARDED / draft.name).exists())

    def test_no_sid_discards_all(self):
        cc = self.hooks["cm_commands"]
        a = _schema.DRAFTS_DIR / "2026-05-22_aaa.md"
        b = _schema.DRAFTS_DIR / "2026-05-23_bbb.md"
        a.write_text("x", encoding="utf-8")
        b.write_text("y", encoding="utf-8")
        rc, _ = _captured(cc.cmd_claudemd_discard, None)
        self.assertEqual(rc, 0)
        self.assertFalse(a.exists())
        self.assertFalse(b.exists())
        self.assertTrue((_schema.DRAFTS_DISCARDED / a.name).exists())

    def test_missing_sid_returns_1(self):
        cc = self.hooks["cm_commands"]
        rc, out = _captured(cc.cmd_claudemd_discard, "nope")
        self.assertEqual(rc, 1)
        self.assertIn("draft 미발견", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
