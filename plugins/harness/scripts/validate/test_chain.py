"""chain.py 신규 검사 함수 단위 테스트 (Tier A 박제, 2026-05-16).

커버:
  Q2  — check_agent_model_field (frontmatter `model:` 필드 강제)
  Q5  — check_skill_description_overlap (pairwise Jaccard ≥ threshold 트리거 충돌)
  Q11 — check_skill_signal_coverage (10 signal 중 최소 1 hit)
  Q12 — check_agent_tools_mcp_consistency (`tools:` mcp__ ↔ `mcpServers:` 정의 정합)

실행:
    py plugins/harness/scripts/validate/test_chain.py

각 테스트는 임시 디렉토리에 `.claude/agents|skills/` 구조 만들고 module-level
REPO_ROOT/AGENTS_DIR/SKILLS_DIR을 *모킹 후 복원*. 외부 의존성 0.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import chain  # noqa: E402


class _ChainTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".claude" / "agents").mkdir(parents=True)
        (self.root / ".claude" / "skills").mkdir(parents=True)
        self._saved = {
            "REPO_ROOT": chain.REPO_ROOT,
            "AGENTS_DIR": chain.AGENTS_DIR,
            "SKILLS_DIR": chain.SKILLS_DIR,
        }
        chain.REPO_ROOT = self.root
        chain.AGENTS_DIR = self.root / ".claude" / "agents"
        chain.SKILLS_DIR = self.root / ".claude" / "skills"

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(chain, k, v)
        self.tmp.cleanup()

    def _write_agent(self, name: str, frontmatter: str, body: str = "본문") -> Path:
        path = chain.AGENTS_DIR / f"{name}.md"
        path.write_text(f"---\n{frontmatter}\n---\n\n{body}\n", encoding="utf-8")
        return path

    def _write_skill(self, name: str, description: str, body: str = "## 워크플로우\n\n본문") -> Path:
        skill_dir = chain.SKILLS_DIR / name
        skill_dir.mkdir()
        path = skill_dir / "SKILL.md"
        path.write_text(
            f"---\nname: {name}\ndescription: \"{description}\"\n---\n\n{body}\n",
            encoding="utf-8",
        )
        return path


class CheckAgentModelField(_ChainTestBase):
    def test_model_present_passes(self):
        self._write_agent("a1", "name: a1\ndescription: desc\nmodel: opus")
        self.assertEqual(chain.check_agent_model_field(), [])

    def test_model_sonnet_passes(self):
        self._write_agent("a1", "name: a1\ndescription: desc\nmodel: sonnet")
        self.assertEqual(chain.check_agent_model_field(), [])

    def test_model_missing_fails(self):
        self._write_agent("a1", "name: a1\ndescription: desc")
        errors = chain.check_agent_model_field()
        self.assertEqual(len(errors), 1)
        self.assertIn("model:", errors[0])
        self.assertIn("a1", errors[0])

    def test_multiple_agents_only_missing_reported(self):
        self._write_agent("ok", "name: ok\ndescription: desc\nmodel: opus")
        self._write_agent("bad", "name: bad\ndescription: desc")
        errors = chain.check_agent_model_field()
        self.assertEqual(len(errors), 1)
        self.assertIn("bad", errors[0])


class CheckAgentToolsMcpConsistency(_ChainTestBase):
    def test_tools_mcp_consistent_passes(self):
        fm = (
            "name: a1\ndescription: desc\nmodel: opus\n"
            "tools:\n  - Read\n  - mcp__github__list_pull_requests\n"
            "mcpServers:\n  - github:\n      type: stdio\n      command: npx\n"
        )
        self._write_agent("a1", fm)
        self.assertEqual(chain.check_agent_tools_mcp_consistency(), [])

    def test_tools_mcp_missing_server_fails(self):
        fm = (
            "name: a1\ndescription: desc\nmodel: opus\n"
            "tools:\n  - mcp__github__list_pull_requests\n"
        )
        self._write_agent("a1", fm)
        errors = chain.check_agent_tools_mcp_consistency()
        self.assertEqual(len(errors), 1)
        self.assertIn("github", errors[0])
        self.assertIn("silent skip", errors[0])

    def test_multiple_mcp_servers_one_missing(self):
        fm = (
            "name: a1\ndescription: desc\nmodel: opus\n"
            "tools:\n  - mcp__github__x\n  - mcp__fetch__y\n"
            "mcpServers:\n  - github:\n      type: stdio\n      command: npx\n"
        )
        self._write_agent("a1", fm)
        errors = chain.check_agent_tools_mcp_consistency()
        self.assertEqual(len(errors), 1)
        self.assertIn("fetch", errors[0])

    def test_no_mcp_tools_passes(self):
        fm = "name: a1\ndescription: desc\nmodel: opus\ntools:\n  - Read\n  - Edit\n"
        self._write_agent("a1", fm)
        self.assertEqual(chain.check_agent_tools_mcp_consistency(), [])


class CheckSkillDescriptionOverlap(_ChainTestBase):
    def test_distinct_descriptions_pass(self):
        self._write_skill("s1", "데이터베이스 스키마 마이그레이션 자동화")
        self._write_skill("s2", "iOS Android 모바일 빌드 디버깅")
        self.assertEqual(chain.check_skill_description_overlap(), [])

    def test_duplicate_descriptions_fail(self):
        self._write_skill("s1", "코드 리뷰 자동화 PR 분석 워크플로우 도구")
        self._write_skill("s2", "코드 리뷰 자동화 PR 분석 워크플로우 도구")
        errors = chain.check_skill_description_overlap()
        self.assertEqual(len(errors), 1)
        self.assertIn("Jaccard", errors[0])

    def test_below_threshold_passes(self):
        self._write_skill("s1", "데이터베이스 마이그레이션 적용 워크플로우")
        self._write_skill("s2", "프론트엔드 UI 컴포넌트 React 빌드 시각화")
        self.assertEqual(chain.check_skill_description_overlap(), [])


class CheckSkillSignalCoverage(_ChainTestBase):
    def test_signal_hit_passes(self):
        self._write_skill("s1", "코드 리뷰 PR 분석 워크플로우")
        self.assertEqual(chain.check_skill_signal_coverage(), [])

    def test_signal_miss_fails(self):
        self._write_skill("s1", "그냥 어떤 작업을 하는 도구입니다")
        errors = chain.check_skill_signal_coverage()
        self.assertEqual(len(errors), 1)
        self.assertIn("signal coverage 0", errors[0])

    def test_english_signal_hit_passes(self):
        self._write_skill("s1", "Kubernetes infrastructure rollback monitoring")
        self.assertEqual(chain.check_skill_signal_coverage(), [])

    def test_ml_signal_hit_passes(self):
        self._write_skill("s1", "모델 학습 hyperparameter 평가")
        self.assertEqual(chain.check_skill_signal_coverage(), [])


if __name__ == "__main__":
    unittest.main()
