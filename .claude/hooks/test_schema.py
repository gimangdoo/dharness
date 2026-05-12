"""classify_dharness_event 분류기 + _sanitize_reason 단위 테스트.

실행:
    py .claude/hooks/test_schema.py

stdlib unittest만 사용 (외부 의존성 0). 4가지 핵심 분류 룰을 커버:
  1. FILE_TOOLS × harness/CM/CLAUDE.md/README/skip 경로
  2. Bash × git subcommand 매핑 + 비-git 명령 skip
  3. _workspace/__pycache__/.git skip 룰
  4. tool_input 누락 시 None
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# .claude/hooks/를 import path에 추가 (test_schema.py가 같은 디렉토리에 있음)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _schema import classify_dharness_event  # noqa: E402
from cm_commands import _sanitize_reason  # noqa: E402


class ClassifyFileEdit(unittest.TestCase):
    def _check(self, file_path: str, expected_category: str | None, expected_kind: str | None = None):
        result = classify_dharness_event("Edit", {"file_path": file_path})
        if expected_category is None:
            self.assertIsNone(result, f"expected None for {file_path}, got {result}")
            return
        self.assertIsNotNone(result, f"expected match for {file_path}")
        self.assertEqual(result["category"], expected_category)
        if expected_kind is not None:
            self.assertEqual(result["artifact_kind"], expected_kind)

    def test_harness_skill(self):
        self._check("plugins/harness/skills/harness/SKILL.md", "harness_skill_edit", "skill")

    def test_harness_reference(self):
        self._check("plugins/harness/skills/harness/references/permission-profiles.md",
                    "harness_reference_edit", "reference")

    def test_harness_command(self):
        self._check("plugins/harness/commands/harness-new.md", "harness_command_edit", "command")

    def test_harness_manifest(self):
        self._check("plugins/harness/.claude-plugin/plugin.json",
                    "harness_manifest_edit", "plugin_manifest")

    def test_cm_schema(self):
        self._check(".claude/hooks/_schema.py", "cm_schema_edit", "schema")

    def test_cm_hook(self):
        self._check(".claude/hooks/session_start.py", "cm_hook_edit", "hook")

    def test_cm_skill(self):
        self._check(".claude/skills/memory-search/SKILL.md", "cm_skill_edit", "skill")

    def test_cm_command(self):
        self._check(".claude/commands/cm-status.md", "cm_command_edit", "command")

    def test_cm_settings(self):
        self._check(".claude/settings.local.json", "cm_settings_edit", "settings")

    def test_claude_md(self):
        self._check("CLAUDE.md", "claudemd_edit", "claude_md")

    def test_marketplace(self):
        self._check(".claude-plugin/marketplace.json", "marketplace_edit", "plugin_manifest")

    def test_readme(self):
        self._check("README.md", "readme_edit", "doc")

    def test_gitignore(self):
        self._check(".gitignore", "gitignore_edit", "config")

    def test_workspace_skipped(self):
        self._check("_workspace/_memory/observations/observations.db", None)
        self._check("_workspace/_telemetry/2026-05-11.jsonl", None)
        self._check("_workspace/_drafts/2026-05-10_abc.md", None)

    def test_pycache_skipped(self):
        self._check(".claude/hooks/__pycache__/_schema.cpython-312.pyc", None)

    def test_git_dir_skipped(self):
        self._check(".git/config", None)

    def test_unknown_path_none(self):
        self._check("random/path/foo.txt", None)


class ClassifyFileEditEdgeCases(unittest.TestCase):
    def test_missing_file_path(self):
        self.assertIsNone(classify_dharness_event("Edit", {}))

    def test_empty_file_path(self):
        self.assertIsNone(classify_dharness_event("Edit", {"file_path": ""}))

    def test_write_tool(self):
        # Write도 _FILE_TOOLS에 포함
        result = classify_dharness_event("Write", {"file_path": "README.md"})
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "readme_edit")

    def test_multiedit_tool(self):
        result = classify_dharness_event("MultiEdit", {"file_path": "CLAUDE.md"})
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "claudemd_edit")

    def test_tool_tag_lowercased(self):
        result = classify_dharness_event("Edit", {"file_path": "README.md"})
        self.assertIn("edit", result["tags"])


class ClassifyBash(unittest.TestCase):
    def _check(self, command: str, expected_category: str | None):
        result = classify_dharness_event("Bash", {"command": command})
        if expected_category is None:
            self.assertIsNone(result, f"expected None for {command!r}, got {result}")
            return
        self.assertIsNotNone(result, f"expected match for {command!r}")
        self.assertEqual(result["category"], expected_category)
        self.assertEqual(result["artifact_kind"], "git")

    def test_git_commit(self):
        self._check("git commit -m 'fix'", "git_commit")

    def test_git_add(self):
        self._check("git add .claude/hooks/_schema.py", "git_add")

    def test_git_push(self):
        self._check("git push origin main", "git_push")

    def test_git_checkout(self):
        self._check("git checkout -b feature", "git_checkout")

    def test_git_reset(self):
        self._check("git reset --hard HEAD~1", "git_reset")

    def test_git_status_skipped(self):
        # status는 _GIT_RELEVANT에 없음 (read-only)
        self._check("git status --short", None)

    def test_git_log_skipped(self):
        # log도 read-only라 _GIT_RELEVANT에 없음
        self._check("git log --oneline", None)

    def test_non_git_skipped(self):
        self._check("ls -la", None)
        self._check("py .claude/hooks/cm_commands.py status", None)

    def test_long_command_truncated(self):
        cmd = "git commit -m '" + "x" * 300 + "'"
        result = classify_dharness_event("Bash", {"command": cmd})
        self.assertIsNotNone(result)
        # 200자 + … 토큰
        self.assertLessEqual(len(result["content"]), 200)


class ClassifyMisc(unittest.TestCase):
    def test_non_recognized_tool(self):
        # WebFetch/Read는 dharness_event 분류 대상 아님
        self.assertIsNone(classify_dharness_event("WebFetch", {"url": "https://example.com"}))
        self.assertIsNone(classify_dharness_event("Read", {"file_path": "README.md"}))


class SanitizeReason(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(_sanitize_reason([]), "")
        self.assertEqual(_sanitize_reason([""]), "")
        self.assertEqual(_sanitize_reason([" ", " "]), "")

    def test_single_word(self):
        self.assertEqual(_sanitize_reason(["fix"]), "fix")

    def test_multi_word_joined(self):
        self.assertEqual(_sanitize_reason(["Phase", "9", "e2e", "검증"]), "Phase 9 e2e 검증")

    def test_pipe_escaped(self):
        self.assertEqual(_sanitize_reason(["a|b|c"]), "a\\|b\\|c")

    def test_newline_to_space(self):
        self.assertEqual(_sanitize_reason(["line1\nline2"]), "line1 line2")
        self.assertEqual(_sanitize_reason(["line1\r\nline2"]), "line1  line2")


if __name__ == "__main__":
    unittest.main()
