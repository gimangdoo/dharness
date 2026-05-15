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


class ClassifyMisc(unittest.TestCase):
    def test_non_recognized_tool(self):
        # WebFetch/Read는 dharness_event 분류 대상 아님
        self.assertIsNone(classify_dharness_event("WebFetch", {"url": "https://example.com"}))
        self.assertIsNone(classify_dharness_event("Read", {"file_path": "README.md"}))


class POCParity(unittest.TestCase):
    """P7-2 옵션 B 영문 POC parity 회귀 — KO/EN pair 4건 invariant.

    검증:
      1. 4 KO/EN file pair 존재
      2. KO file 상단 *English POC 박스* (`[file.en.md]` cross-link 포함) 박제
      3. EN file 하단 `P7-2 POC note` 또는 `P7-1 POC note` 박제
    """

    REPO_ROOT = Path(__file__).resolve().parents[2]
    REF_DIR = REPO_ROOT / "plugins" / "harness" / "skills" / "harness" / "references"

    POC_PAIRS = [
        "team-tools-api",
        "agent-design-patterns",
        "skill-testing-guide",
        "skill-writing-guide",
    ]

    def test_poc_pair_existence(self):
        for stem in self.POC_PAIRS:
            ko = self.REF_DIR / f"{stem}.md"
            en = self.REF_DIR / f"{stem}.en.md"
            self.assertTrue(ko.exists(), f"KO source missing: {ko.relative_to(self.REPO_ROOT)}")
            self.assertTrue(en.exists(), f"EN POC missing: {en.relative_to(self.REPO_ROOT)}")

    def test_ko_has_poc_box_with_en_link(self):
        for stem in self.POC_PAIRS:
            ko = self.REF_DIR / f"{stem}.md"
            text = ko.read_text(encoding="utf-8-sig")
            self.assertIn("English POC", text,
                          f"{ko.name}: `English POC` 박스 헤더 미박제")
            self.assertIn(f"{stem}.en.md", text,
                          f"{ko.name}: `.en.md` cross-link 미박제")

    def test_en_has_poc_note(self):
        for stem in self.POC_PAIRS:
            en = self.REF_DIR / f"{stem}.en.md"
            text = en.read_text(encoding="utf-8-sig")
            has_note = ("P7-2 POC note" in text) or ("P7-1 POC note" in text)
            self.assertTrue(has_note,
                            f"{en.name}: `P7-1/P7-2 POC note` 미박제")

    def test_structural_parity_section_count(self):
        """KO/EN ## section count 정합 — EN은 POC note 부록 1 section 추가만 허용."""
        section_re = re.compile(r"(?m)^##\s")
        for stem in self.POC_PAIRS:
            ko_text = (self.REF_DIR / f"{stem}.md").read_text(encoding="utf-8-sig")
            en_text = (self.REF_DIR / f"{stem}.en.md").read_text(encoding="utf-8-sig")
            ko_count = len(section_re.findall(ko_text))
            en_count = len(section_re.findall(en_text))
            self.assertEqual(en_count, ko_count + 1,
                             f"{stem}: EN sections ({en_count}) must equal KO ({ko_count}) + 1 POC note. "
                             "structural drift detected — KO/EN section count divergence.")

    def test_structural_parity_code_fence_count(self):
        """KO/EN ``` code fence count 정합 — POC note에 fence 없으므로 동수."""
        for stem in self.POC_PAIRS:
            ko_text = (self.REF_DIR / f"{stem}.md").read_text(encoding="utf-8-sig")
            en_text = (self.REF_DIR / f"{stem}.en.md").read_text(encoding="utf-8-sig")
            ko_count = ko_text.count("```")
            en_count = en_text.count("```")
            self.assertEqual(ko_count, en_count,
                             f"{stem}: code fence count drift — KO={ko_count}, EN={en_count}. "
                             "structural divergence in fenced code blocks.")

    def test_structural_parity_table_row_count(self):
        """KO/EN markdown table row count 정합 — POC note에 표 없으므로 동수."""
        row_re = re.compile(r"(?m)^\|.*\|\s*$")
        for stem in self.POC_PAIRS:
            ko_text = (self.REF_DIR / f"{stem}.md").read_text(encoding="utf-8-sig")
            en_text = (self.REF_DIR / f"{stem}.en.md").read_text(encoding="utf-8-sig")
            ko_count = len(row_re.findall(ko_text))
            en_count = len(row_re.findall(en_text))
            self.assertEqual(ko_count, en_count,
                             f"{stem}: table row count drift — KO={ko_count}, EN={en_count}. "
                             "structural divergence in markdown tables.")

    def test_structural_parity_bullet_count(self):
        """KO/EN bullet list item count 정합 — POC note에 bullet 없으므로 동수."""
        bullet_re = re.compile(r"(?m)^\s*[-*]\s")
        for stem in self.POC_PAIRS:
            ko_text = (self.REF_DIR / f"{stem}.md").read_text(encoding="utf-8-sig")
            en_text = (self.REF_DIR / f"{stem}.en.md").read_text(encoding="utf-8-sig")
            ko_count = len(bullet_re.findall(ko_text))
            en_count = len(bullet_re.findall(en_text))
            self.assertEqual(ko_count, en_count,
                             f"{stem}: bullet count drift — KO={ko_count}, EN={en_count}. "
                             "structural divergence in bullet lists.")

    def test_skill_md_dogfood_box(self):
        skill_md = self.REPO_ROOT / "plugins" / "harness" / "skills" / "harness" / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8-sig")
        self.assertIn("P7-2 옵션 B", text,
                      "SKILL.md: P7-2 옵션 B dogfood 매핑 박스 미박제")
        for stem in self.POC_PAIRS:
            self.assertIn(f"{stem}.en.md", text,
                          f"SKILL.md dogfood 박스: `{stem}.en.md` 미박제")


class HarnessNewGates(unittest.TestCase):
    """SKILL.md anti-premature-judgment doctrine + Phase 1/2 entry 게이트 박제 회귀.

    사용자 요구 2026-05-15: `/harness:harness-new` 진입 시 cwd 디렉토리 이름·파일 이름 단독
    도메인 단정 차단. Phase 1 산출물 강제 + Phase 2 필수 5필드 사용자 답변 raw 인용 강제.
    """

    REPO_ROOT = Path(__file__).resolve().parents[2]
    SKILL_MD = REPO_ROOT / "plugins" / "harness" / "skills" / "harness" / "SKILL.md"
    CMD_MD = REPO_ROOT / "plugins" / "harness" / "commands" / "harness-new.md"

    def test_anti_premature_judgment_doctrine_present(self):
        text = self.SKILL_MD.read_text(encoding="utf-8-sig")
        self.assertIn("Anti-premature-judgment doctrine", text,
                      "SKILL.md: Anti-premature-judgment doctrine 박스 미박제")
        self.assertIn("cwd 디렉토리 이름", text,
                      "SKILL.md: 'cwd 디렉토리 이름' 단정 금지 doctrine 미박제")
        self.assertIn("단정 허용 조건", text,
                      "SKILL.md: '단정 허용 조건' 게이트 미박제")

    def test_phase1_entry_gate_present(self):
        text = self.SKILL_MD.read_text(encoding="utf-8-sig")
        self.assertIn("Phase 1 entry 게이트", text,
                      "SKILL.md: Phase 1 entry 게이트 박스 미박제")
        self.assertIn("산출물 강제", text,
                      "SKILL.md: Phase 1 '산출물 강제' 문구 미박제")
        self.assertIn("실 파일 read 강제", text,
                      "SKILL.md: Phase 1 '실 파일 read 강제' 문구 미박제")
        self.assertIn("silent skip 차단", text,
                      "SKILL.md: 'silent skip 차단' 문구 미박제")

    def test_phase2_entry_gate_present(self):
        text = self.SKILL_MD.read_text(encoding="utf-8-sig")
        self.assertIn("Phase 2 entry 게이트", text,
                      "SKILL.md: Phase 2 entry 게이트 박스 미박제")
        self.assertIn("질문 폭격 강제", text,
                      "SKILL.md: Phase 2 '질문 폭격 강제' 문구 미박제")
        self.assertIn("user_confirmed_fields", text,
                      "SKILL.md: Phase 2 meta.user_confirmed_fields 박제 doctrine 미박제")

    def test_harness_new_command_synced(self):
        text = self.CMD_MD.read_text(encoding="utf-8-sig")
        self.assertIn("Anti-premature-judgment", text,
                      "harness-new.md: 게이트 포인터 미동기화")
        self.assertIn("entry 게이트 (2026-05-15)", text,
                      "harness-new.md: 2026-05-15 entry 게이트 포인터 미박제")

    def test_phase5_cardinality_gate_present(self):
        text = self.SKILL_MD.read_text(encoding="utf-8-sig")
        self.assertIn("Phase 5 entry 게이트", text,
                      "SKILL.md: Phase 5 entry 게이트 박스 미박제")
        self.assertIn("Cardinality justification", text,
                      "SKILL.md: Phase 5 'Cardinality justification' 문구 미박제")
        self.assertIn("inline 대안 검토", text,
                      "SKILL.md: Phase 5 'inline 대안 검토' 컬럼 doctrine 미박제")
        self.assertIn("single-use → inline", text,
                      "SKILL.md: Phase 5 'single-use → inline' 룰 미박제")
        self.assertIn("이름 유일성 사전 점검", text,
                      "SKILL.md: Phase 5 '이름 유일성 사전 점검' doctrine 미박제")


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


class POCDogfoodMeasure(unittest.TestCase):
    """P7-2 dogfood 정적 측정 회로 회귀 (2026-05-15)."""

    REPO_ROOT = Path(__file__).resolve().parents[2]
    POC_DIR = REPO_ROOT / "plugins" / "harness" / "scripts" / "poc"
    PROTOCOL = REPO_ROOT / "plugins" / "harness" / "skills" / "harness" / "references" / "poc-dogfood-protocol.md"

    def test_measure_script_present(self):
        script = self.POC_DIR / "measure_dogfood.py"
        self.assertTrue(script.exists(), f"measure_dogfood.py 미존재: {script}")

    def test_protocol_doctrine_present(self):
        self.assertTrue(self.PROTOCOL.exists(), "poc-dogfood-protocol.md 미존재")
        text = self.PROTOCOL.read_text(encoding="utf-8-sig")
        for marker in ("옵션 B-a", "옵션 B-b", "옵션 B-c", "결정 임계", "measure_dogfood.py"):
            self.assertIn(marker, text, f"protocol doctrine `{marker}` 미박제")

    def test_strip_poc_note_removes_appendix(self):
        sys.path.insert(0, str(self.POC_DIR))
        import importlib
        import measure_dogfood  # noqa: E402
        measure_dogfood = importlib.reload(measure_dogfood)
        sample = "# Title\n\nbody body\n\n## P7-2 POC note\n\nappendix line\n"
        stripped = measure_dogfood._strip_poc_note(sample)
        self.assertNotIn("appendix line", stripped)
        self.assertNotIn("P7-2 POC note", stripped)
        self.assertIn("body body", stripped)

    def test_skill_md_measure_pointer(self):
        skill_md = self.REPO_ROOT / "plugins" / "harness" / "skills" / "harness" / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8-sig")
        self.assertIn("measure_dogfood.py", text, "SKILL.md: measure_dogfood.py pointer 미박제")
        self.assertIn("poc-dogfood-protocol.md", text, "SKILL.md: protocol reference pointer 미박제")


class UpliftBaseline(unittest.TestCase):
    """Q2 uplift baseline 회로 회귀 (2026-05-15)."""

    REPO_ROOT = Path(__file__).resolve().parents[2]
    UPLIFT_DIR = REPO_ROOT / "plugins" / "harness" / "scripts" / "uplift"
    PROTOCOL = REPO_ROOT / "plugins" / "harness" / "skills" / "harness" / "references" / "uplift-protocol.md"

    def test_measure_script_present(self):
        script = self.UPLIFT_DIR / "measure_session.py"
        self.assertTrue(script.exists(), f"measure_session.py 미존재: {script}")

    def test_protocol_doctrine_present(self):
        self.assertTrue(self.PROTOCOL.exists(), "uplift-protocol.md 미존재")
        text = self.PROTOCOL.read_text(encoding="utf-8-sig")
        for marker in (
            "측정 지표", "Fixture task", "결정 게이트", "measure_session.py",
            "baseline", "harness",
        ):
            self.assertIn(marker, text, f"uplift doctrine `{marker}` 미박제")

    def test_summarize_pure_aggregation(self):
        sys.path.insert(0, str(self.UPLIFT_DIR))
        import importlib
        import measure_session  # noqa: E402
        measure_session = importlib.reload(measure_session)
        events = [
            {"type": "session_capture_init", "ts": "2026-05-15T10:00:00Z", "session_id": "x"},
            {"type": "tool_output_captured", "raw_size": 12345, "session_id": "x"},
            {"type": "tool_output_captured", "raw_size": 678, "session_id": "x"},
            {"type": "agent_invocation", "session_id": "x"},
            {"type": "agent_failure", "session_id": "x"},
            {"type": "agent_invocation", "session_id": "x"},
            {"type": "session_capture_finalize", "ts": "2026-05-15T10:05:30Z", "session_id": "x"},
        ]
        s = measure_session.summarize("x", events)
        self.assertEqual(s["tool_invocations"], 2)
        self.assertEqual(s["total_raw_size_bytes"], 12345 + 678)
        self.assertEqual(s["agent_invocations"], 2)
        self.assertEqual(s["agent_failures"], 1)
        self.assertEqual(s["failure_ratio"], 0.5)
        self.assertEqual(s["duration_seconds"], 330)

    def test_skill_md_uplift_pointer(self):
        skill_md = self.REPO_ROOT / "plugins" / "harness" / "skills" / "harness" / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8-sig")
        self.assertIn("uplift-protocol.md", text, "SKILL.md: uplift-protocol pointer 미박제")
        self.assertIn("measure_session.py", text, "SKILL.md: measure_session pointer 미박제")


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
