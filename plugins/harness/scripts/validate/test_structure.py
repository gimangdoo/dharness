"""structure.py 신규 검사 단위 테스트 (PATCH-03, 2026-05-22).

커버:
  check_skills_dir — 빈 스킬 디렉토리(SKILL.md 미존재) 검출 + 본문 부재 검출
  check_skill_file — frontmatter-only(본문 부재) / 워크플로우 섹션 누락

실행:
    py plugins/harness/scripts/validate/test_structure.py

각 테스트는 임시 디렉토리에 `.claude/skills/` 구조 만들고 module-level
REPO_ROOT/AGENTS_DIR/SKILLS_DIR/CLAUDE_MD를 *모킹 후 복원*. 외부 의존성 0.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import structure  # noqa: E402


class _StructureTestBase(unittest.TestCase):
    _VALID = '---\nname: s1\ndescription: "desc"\n---\n\n## 워크플로우\n\n1. 단계\n'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".claude" / "skills").mkdir(parents=True)
        self._saved = {
            "REPO_ROOT": structure.REPO_ROOT,
            "AGENTS_DIR": structure.AGENTS_DIR,
            "SKILLS_DIR": structure.SKILLS_DIR,
            "CLAUDE_MD": structure.CLAUDE_MD,
        }
        structure.REPO_ROOT = self.root
        structure.AGENTS_DIR = self.root / ".claude" / "agents"
        structure.SKILLS_DIR = self.root / ".claude" / "skills"
        structure.CLAUDE_MD = self.root / "CLAUDE.md"

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(structure, k, v)
        self.tmp.cleanup()

    def _make_skill_dir(self, name: str, content: str | None) -> Path:
        d = structure.SKILLS_DIR / name
        d.mkdir()
        if content is not None:
            (d / "SKILL.md").write_text(content, encoding="utf-8")
        return d


class CheckSkillsDir(_StructureTestBase):
    def test_valid_skill_passes(self):
        self._make_skill_dir("s1", self._VALID)
        count, errors = structure.check_skills_dir()
        self.assertEqual(count, 1)
        self.assertEqual(errors, [])

    def test_empty_dir_no_skill_md_fails(self):
        self._make_skill_dir("s1", None)  # 디렉토리만, SKILL.md 없음
        count, errors = structure.check_skills_dir()
        self.assertEqual(count, 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("SKILL.md 미존재", errors[0])
        self.assertIn("s1", errors[0])

    def test_frontmatter_only_body_absent_fails(self):
        self._make_skill_dir("s1", '---\nname: s1\ndescription: "desc"\n---\n')
        count, errors = structure.check_skills_dir()
        self.assertEqual(count, 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("본문 부재", errors[0])

    def test_missing_workflow_section_fails(self):
        self._make_skill_dir("s1", '---\nname: s1\ndescription: "desc"\n---\n\n## 개요\n내용만 있음.\n')
        count, errors = structure.check_skills_dir()
        self.assertEqual(count, 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("필수 섹션 누락", errors[0])

    def test_mixed_valid_and_empty(self):
        self._make_skill_dir("good", self._VALID)
        self._make_skill_dir("bad", None)
        count, errors = structure.check_skills_dir()
        self.assertEqual(count, 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("bad", errors[0])

    def test_no_skills_dir_passes(self):
        shutil.rmtree(structure.SKILLS_DIR)
        count, errors = structure.check_skills_dir()
        self.assertEqual(count, 0)
        self.assertEqual(errors, [])

    def test_lowercase_skill_md_flagged(self):
        d = structure.SKILLS_DIR / "s1"
        d.mkdir()
        (d / "skill.md").write_text(self._VALID, encoding="utf-8")
        count, errors = structure.check_skills_dir()
        self.assertEqual(count, 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("대소문자", errors[0])


if __name__ == "__main__":
    unittest.main()
