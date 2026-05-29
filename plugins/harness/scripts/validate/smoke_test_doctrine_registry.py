"""실 repo doctrine-registry.md ↔ 실 chain.py/structure.py/schema.py 회귀 smoke test.

PT2 (2026-05-27): default suite에서 분리. fixture 기반 unit test는
`test_chain.py:CheckDoctrineRegistryFnRefs` + `CheckDoctrineRegistryInverseIndex`가
이미 커버. 본 파일은 실 repo state drift만 검출 (CI 별도 stage 후보).

실행:
    py plugins/harness/scripts/validate/smoke_test_doctrine_registry.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import chain  # noqa: E402


class DoctrineRegistryRealRepo(unittest.TestCase):
    """실 모듈 경로 사용 — drift 발생 시 즉시 FAIL."""

    def test_repo_doctrine_registry_no_stale_fn_refs(self):
        errors = chain.check_doctrine_registry_fn_refs()
        self.assertEqual(errors, [], f"stale fn refs detected: {errors}")

    def test_repo_doctrine_registry_inverse_index_consistent(self):
        errors = chain.check_doctrine_registry_inverse_index()
        self.assertEqual(errors, [], f"inverse index drift detected: {errors}")


# ────────────────────────────────────────────────────────────────────────
# PA15 (audit2 2026-05-28): test_chain.py의 RealRepo case 본 파일로 이전.
# default suite는 fixture 기반 unit만 유지, real-repo state drift는 본 smoke로.
# ────────────────────────────────────────────────────────────────────────


class IntentRequiredDocSyncRealRepo(unittest.TestCase):
    """실 repo SKILL.md/phase-entry-gates.md/intent-profile-schema.md ↔ 6 INTENT_REQUIRED 박제 회귀."""

    def test_real_repo_doc_sync_no_drift(self):
        errors = chain.check_intent_required_doc_sync()
        self.assertEqual(errors, [], f"doc sync drift detected: {errors}")


class CheckAdvisorHandoffAdapterRealRepo(unittest.TestCase):
    """실 repo intent_profile.md(존재 시) ↔ adapter doctrine 회귀.

    dharness self-host에는 _workspace/_baseline/ 부재 — silent skip PASS.
    """

    def test_repo_intent_profile_advisor_consistency(self):
        errors = chain.check_advisor_handoff_adapter_consistency()
        self.assertEqual(errors, [], f"adapter doctrine 위반: {errors}")


class CheckOutputChecklistCountSyncRealRepo(unittest.TestCase):
    """실 repo output-checklist.md ↔ SKILL.md/harness-new.md 인용 동기 회귀 (S13)."""

    def test_real_repo_no_count_drift(self):
        errors = chain.check_output_checklist_count_sync()
        self.assertEqual(errors, [], f"output-checklist count drift: {errors}")


class CheckCommandCountSyncRealRepo(unittest.TestCase):
    """실 repo commands/harness-*.md ↔ README 카탈로그 + doctrine-registry R4 동기 회귀 (S14)."""

    def test_real_repo_no_command_count_drift(self):
        errors = chain.check_command_count_sync()
        self.assertEqual(errors, [], f"command count drift: {errors}")


class CheckTriggerCatalogPythonSyncRealRepo(unittest.TestCase):
    """실 repo trigger-keyword-catalog.md §1 ↔ chain._TRIGGER_SIGNAL_KEYWORDS 회귀 (S15)."""

    def test_real_repo_no_drift(self):
        errors = chain.check_trigger_catalog_python_sync()
        self.assertEqual(errors, [], f"trigger catalog ↔ code dict drift: {errors}")


class CheckPhaseCountSyncRealRepo(unittest.TestCase):
    """실 repo SKILL.md 헤더 ↔ 4 ad 위치 회귀 (S16)."""

    def test_real_repo_no_drift(self):
        errors = chain.check_phase_count_sync()
        self.assertEqual(errors, [], f"phase count drift: {errors}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
