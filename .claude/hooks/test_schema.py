"""classify_dharness_event 분류기 + _sanitize_reason 단위 테스트.

실행:
    py .claude/hooks/test_schema.py

stdlib unittest만 사용 (외부 의존성 0). 6가지 핵심 룰을 커버:
  1. FILE_TOOLS × harness/CM/CLAUDE.md/README/skip 경로
  2. Bash × git subcommand 매핑 + 비-git 명령 skip
  3. _workspace/__pycache__/.git skip 룰
  4. tool_input 누락 시 None
  5. P7-2 옵션 B 영문 POC parity (KO/EN pair + 박스 + note + SKILL.md dogfood 매핑 + 구조 parity: section/fence/table/bullet)
  6. Anti-premature-judgment doctrine 박스 + Phase 1/2 entry 게이트 박제 (SKILL.md)
"""

from __future__ import annotations

import re
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

    def test_git_chain_add_commit(self):
        # P0-2 chain 분류 — `add && commit`이 add가 아니라 commit으로 분류되어야 함 (우선순위)
        result = classify_dharness_event(
            "Bash", {"command": "git add file.py && git commit -m 'fix'"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "git_commit")
        self.assertIn("git_chain", result["tags"])

    def test_git_chain_add_push(self):
        result = classify_dharness_event(
            "Bash", {"command": "git add . && git commit -m 'x' && git push"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "git_push")
        self.assertIn("git_chain", result["tags"])

    def test_git_chain_semicolon(self):
        result = classify_dharness_event(
            "Bash", {"command": "git add x ; git rm y ; git commit -m 'm'"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "git_commit")

    def test_git_single_no_chain_tag(self):
        # 단일 명령은 git_chain tag 없음
        result = classify_dharness_event("Bash", {"command": "git add file.py"})
        self.assertIsNotNone(result)
        self.assertNotIn("git_chain", result["tags"])

    def test_git_chain_with_status_filtered(self):
        # status는 _GIT_RELEVANT 미존재 — chain에서 filter
        result = classify_dharness_event(
            "Bash", {"command": "git status ; git add ."}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "git_add")

    def test_echo_quoted_git_not_matched(self):
        # PX3: echo "git commit"은 quoting으로 보호 — false positive 차단.
        self._check('echo "git commit -m fix"', None)
        self._check("echo 'git push origin main'", None)

    def test_heredoc_git_not_matched(self):
        # PX3: heredoc 내부 git 키워드는 single-quoted string처럼 다뤄야 안전.
        # shlex가 heredoc 자체는 모르지만, 일반적인 cat << EOF ... EOF 패턴에선
        # quoted body 외부의 git 키워드가 없어야 false positive 없음.
        self._check("cat 'git commit -m fix' > /tmp/x", None)

    def test_comment_only_git_not_matched(self):
        # PX3: shlex(comments=True)가 #로 시작하는 토큰을 주석으로 처리.
        self._check("# git commit -m fix", None)

    def test_pipe_left_of_git_not_matched(self):
        # PX3: `echo foo | git ...` 같은 pipe는 right-of-pipe가 진짜 명령.
        # 단, echo는 git이 아니므로 전체 결과는 매치 안 됨.
        self._check("echo abc | grep xyz", None)

    def test_pipe_right_of_git_matched(self):
        # pipe 오른쪽이 git이면 chain 검출.
        result = classify_dharness_event(
            "Bash", {"command": "echo abc | git apply -"}
        )
        # git apply는 _GIT_RELEVANT에 없으므로 None.
        self.assertIsNone(result)

    def test_pipe_right_of_git_with_relevant_subcommand(self):
        # right-of-pipe가 git push면 매치.
        result = classify_dharness_event(
            "Bash", {"command": "echo done | git push"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["category"], "git_push")


class ClassifyMisc(unittest.TestCase):
    def test_non_recognized_tool(self):
        # WebFetch/Read는 dharness_event 분류 대상 아님
        self.assertIsNone(classify_dharness_event("WebFetch", {"url": "https://example.com"}))
        self.assertIsNone(classify_dharness_event("Read", {"file_path": "README.md"}))


# HarnessNewGates 박스 (anti-premature-judgment + Phase 1·2·5 entry + Phase 3.5/5.5/7.5
# self-critique doctrine 박제 회귀) → PT1 (2026-05-27) 분리:
# `plugins/harness/scripts/validate/lint_doctrine_strings.py`. markdown grep 24건은
# 단위 테스트로 박제하지 않는다 (test 카운트 정직화).


class ChainWritesAndCoverage(unittest.TestCase):
    """A7 glob intersection + Q1 orchestrator agent coverage 회귀 (2026-05-15)."""

    REPO_ROOT = Path(__file__).resolve().parents[2]
    SCRIPTS_DIR = REPO_ROOT / "plugins" / "harness" / "scripts" / "validate"

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(cls.SCRIPTS_DIR))
        import importlib
        import chain  # noqa: E402
        cls.chain = importlib.reload(chain)

    def test_glob_overlap_literal_vs_glob(self):
        self.assertTrue(self.chain._paths_overlap("_workspace/output.md", "_workspace/*.md"))
        self.assertTrue(self.chain._paths_overlap("_workspace/*.md", "_workspace/output.md"))

    def test_glob_overlap_no_intersection(self):
        self.assertFalse(self.chain._paths_overlap("_workspace/output.md", "_workspace/other.md"))
        self.assertFalse(self.chain._paths_overlap("a/foo.md", "b/*.md"))

    def test_glob_overlap_exact(self):
        self.assertTrue(self.chain._paths_overlap("a.md", "a.md"))

    def test_glob_overlap_single_star_analytical(self):
        # `a/*x.md` ∩ `a/x*.md` — 둘 다 `a/xx.md` 매칭. 양방향 fnmatch 미검출 → analytical 회로
        self.assertTrue(self.chain._paths_overlap("a/*x.md", "a/x*.md"))
        self.assertTrue(self.chain._paths_overlap("a/x*.md", "a/*x.md"))

    def test_glob_overlap_single_star_no_intersection(self):
        # 다른 prefix — overlap 불가
        self.assertFalse(self.chain._paths_overlap("a/*x.md", "b/x*.md"))
        # 다른 suffix
        self.assertFalse(self.chain._paths_overlap("a/*x.md", "a/x*.txt"))

    def _swap_module_roots(self, td_path: Path, agents_dir: Path, skills_dir: Path):
        old = (self.chain.REPO_ROOT, self.chain.AGENTS_DIR, self.chain.SKILLS_DIR)
        self.chain.REPO_ROOT = td_path
        self.chain.AGENTS_DIR = agents_dir
        self.chain.SKILLS_DIR = skills_dir
        return old

    def _restore_module_roots(self, old):
        self.chain.REPO_ROOT, self.chain.AGENTS_DIR, self.chain.SKILLS_DIR = old

    def test_e2e_glob_overlap_detected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            agents = td_path / ".claude" / "agents"
            agents.mkdir(parents=True)
            (agents / "agent_a.md").write_text(
                "---\nname: agent-a\nwrites: [_workspace/*.md]\n---\nbody\n",
                encoding="utf-8",
            )
            (agents / "agent_b.md").write_text(
                "---\nname: agent-b\nwrites: [_workspace/output.md]\n---\nbody\n",
                encoding="utf-8",
            )
            old = self._swap_module_roots(td_path, agents, td_path / ".claude" / "skills")
            try:
                errs = self.chain.check_agent_write_path_overlap()
            finally:
                self._restore_module_roots(old)
            self.assertTrue(
                any("glob 교집합" in e for e in errs),
                f"glob intersection FAIL 미발생: errs={errs}",
            )

    def test_e2e_coverage_dead_agent_flagged(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            agents = td_path / ".claude" / "agents"
            skills = td_path / ".claude" / "skills"
            orch_dir = skills / "orchestrator-main"
            agents.mkdir(parents=True)
            orch_dir.mkdir(parents=True)
            (agents / "ghost.md").write_text(
                "---\nname: ghost\n---\nbody\n", encoding="utf-8"
            )
            (orch_dir / "SKILL.md").write_text(
                "---\nname: orchestrator-main\ndescription: x\n---\nNo agent refs here.\n",
                encoding="utf-8",
            )
            old = self._swap_module_roots(td_path, agents, skills)
            try:
                errs = self.chain.check_orchestrator_agent_coverage()
            finally:
                self._restore_module_roots(old)
            self.assertTrue(
                any("미참조" in e and "ghost" in e for e in errs),
                f"dead agent FAIL 미발생: errs={errs}",
            )

    def test_e2e_coverage_referenced_agent_passes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            agents = td_path / ".claude" / "agents"
            skills = td_path / ".claude" / "skills"
            orch_dir = skills / "orchestrator-main"
            agents.mkdir(parents=True)
            orch_dir.mkdir(parents=True)
            (agents / "alive.md").write_text(
                "---\nname: alive\n---\nbody\n", encoding="utf-8"
            )
            (orch_dir / "SKILL.md").write_text(
                "---\nname: orchestrator-main\ndescription: x\n---\n"
                "Spawn `.claude/agents/alive.md` for task.\n",
                encoding="utf-8",
            )
            old = self._swap_module_roots(td_path, agents, skills)
            try:
                errs = self.chain.check_orchestrator_agent_coverage()
            finally:
                self._restore_module_roots(old)
            self.assertEqual(errs, [], f"referenced agent에 false FAIL: errs={errs}")


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
