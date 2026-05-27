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


if __name__ == "__main__":
    unittest.main(verbosity=2)
