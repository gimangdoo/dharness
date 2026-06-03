"""bridge.py 단위 — emit/pull/dedup/skip-telemetry (P5 C1).

실행: repo root에서 `py -3 -m plugins.harness.scripts.wiki.test_bridge`
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

# repo root를 path에 — repo root `-m` 호출과 in-dir 호출 양쪽서 동작 (L15-5 fix).
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from plugins.harness.scripts.wiki import bridge  # noqa: E402


def _skill_md(slug="demo-skill", version=1):
    return (
        "---\n"
        f"name: {slug}\n"
        "description: 데모 skill. \"데모 실행\"·\"demo run\"·\"샘플 트리거\" 시 작동. NOT: 신규 파일 생성.\n"
        "meta:\n"
        "  skill_kind: user-facing\n"
        f"  candidate_version: {version}\n"
        "  gap_source: pattern-synthesis\n"
        "  static_tier: PASS\n"
        "  llm_judge_tier: not-run\n"
        "  mc_tier: not-run\n"
        "  promoted_to: null\n"
        "---\n\n"
        f"# {slug}\n\n본문.\n"
    )


def _eval(slug="demo-skill", version=1, *, verdict=None, all_pass=False):
    status = "PASS" if all_pass else "not-run"
    return {
        "candidate_slug": slug,
        "candidate_version": version,
        "gap_source": "pattern-synthesis",
        "emit_at": "2026-06-03T00:00:00Z",
        "evals": {
            "static": {"status": "PASS", "last_run": "2026-06-03", "findings": []},
            "llm_judge": {"status": status, "last_run": None, "verdict": None},
            "monte_carlo": {"status": status, "last_run": None, "verdict": None},
        },
        "promotion": {"verdict": verdict, "promoted_to": None, "promoted_at": None},
    }


_ROWS = [("2026-06-03", "emit", "테스트 Emit.")]


class EmitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cand = self.root / "candidates"
        self.tel = self.root / "_telemetry"

    def tearDown(self):
        self.tmp.cleanup()

    def _emit(self, **kw):
        return bridge.emit_candidate(
            self.cand, "demo-skill", 1, _skill_md(), _eval(), _ROWS,
            telemetry_dir=self.tel, **kw)

    def _telemetry_events(self):
        out = []
        for f in self.tel.glob("*.jsonl"):
            for line in f.read_text(encoding="utf-8").splitlines():
                out.append(json.loads(line))
        return out

    def test_presence_gate_absent(self):
        # candidates/ 미존재 → skip + no-op
        res = self._emit()
        self.assertEqual(res["status"], "skipped")
        self.assertEqual(res["reason"], "target-absent")
        evs = self._telemetry_events()
        self.assertTrue(any(e["type"] == "wiki_bridge_skipped"
                            and e["milestone"] == "emit"
                            and e["reason"] == "target-absent" for e in evs))

    def test_emit_success(self):
        self.cand.mkdir()
        res = self._emit()
        self.assertEqual(res["status"], "emitted")
        d = self.cand / "demo-skill-v1"
        self.assertTrue((d / "SKILL.md").is_file())
        self.assertTrue((d / "eval-results.json").is_file())
        self.assertTrue((d / "changelog.md").is_file())
        # 자가검증 통과 → 형식 정합
        self.assertEqual(bridge._validate_candidate_dir(d), [])
        evs = self._telemetry_events()
        self.assertTrue(any(e["type"] == "wiki_bridge_emit"
                            and e["outcome"] == "success" for e in evs))

    def test_idempotent_append(self):
        self.cand.mkdir()
        self._emit()
        before = (self.cand / "demo-skill-v1" / "SKILL.md").read_text(encoding="utf-8")
        res = bridge.emit_candidate(
            self.cand, "demo-skill", 1, "OVERWRITE-ATTEMPT", _eval(),
            [("2026-06-04", "static", "재실행 행.")], telemetry_dir=self.tel)
        self.assertEqual(res["status"], "exists")
        # SKILL.md 미덮어씀
        self.assertEqual((self.cand / "demo-skill-v1" / "SKILL.md").read_text(encoding="utf-8"), before)
        # changelog 행 추가됨
        cl = (self.cand / "demo-skill-v1" / "changelog.md").read_text(encoding="utf-8")
        self.assertIn("재실행 행.", cl)

    def test_dedup_soft_block(self):
        self.cand.mkdir()
        triggers = ["데모 실행", "demo run"]
        res = bridge.emit_candidate(
            self.cand, "demo-skill", 1, _skill_md(), _eval(), _ROWS,
            triggers=triggers,
            existing_triggers={"existing-x": ["데모 실행", "demo run"]},
            telemetry_dir=self.tel)
        self.assertEqual(res["status"], "soft_block")
        self.assertEqual(res["dedup"]["conflict"], "existing-x")
        self.assertGreaterEqual(res["dedup"]["overlap"], 0.75)
        # write 안 됨 (soft-block은 advisory, I/O 0)
        self.assertFalse((self.cand / "demo-skill-v1").exists())
        evs = self._telemetry_events()
        self.assertTrue(any(e["reason"] == "dedup-hit" for e in evs))

    def test_dedup_below_threshold_passes(self):
        self.cand.mkdir()
        res = bridge.emit_candidate(
            self.cand, "demo-skill", 1, _skill_md(), _eval(), _ROWS,
            triggers=["데모 실행", "demo run", "고유 트리거 A", "고유 트리거 B"],
            existing_triggers={"existing-x": ["데모 실행", "전혀 다른 것"]},
            telemetry_dir=self.tel)
        self.assertEqual(res["status"], "emitted")

    def test_note_skip_not_reusable(self):
        # LLM 비-Emit 결정(재사용 가치 없음) 추적 신호 (L08-002)
        bridge.note_skip("emit", "not-reusable", session_id="x", telemetry_dir=self.tel)
        evs = self._telemetry_events()
        self.assertTrue(any(e["type"] == "wiki_bridge_skipped"
                            and e["reason"] == "not-reusable"
                            and e["milestone"] == "emit" for e in evs))

    def test_invalid_rollback(self):
        self.cand.mkdir()
        # candidate_version cross-field 불일치 → 자가검증 FAIL → 롤백
        res = bridge.emit_candidate(
            self.cand, "demo-skill", 1, _skill_md(version=1), _eval(version=99), _ROWS,
            telemetry_dir=self.tel)
        self.assertEqual(res["status"], "invalid")
        self.assertFalse((self.cand / "demo-skill-v1").exists())  # 롤백됨
        evs = self._telemetry_events()
        self.assertTrue(any(e["type"] == "wiki_bridge_emit"
                            and e["outcome"] == "failure" for e in evs))


class PullTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cand = self.root / "candidates"
        self.tel = self.root / "_telemetry"

    def tearDown(self):
        self.tmp.cleanup()

    def _write_candidate(self, slug, version, eval_results):
        d = self.cand / f"{slug}-v{version}"
        d.mkdir(parents=True)
        (d / "eval-results.json").write_text(
            json.dumps(eval_results, ensure_ascii=False), encoding="utf-8")

    def test_pull_presence_gate(self):
        res = bridge.pull_promoted(self.cand, telemetry_dir=self.tel)
        self.assertEqual(res, [])
        evs = [json.loads(l) for f in self.tel.glob("*.jsonl")
               for l in f.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(any(e["type"] == "wiki_bridge_skipped"
                            and e["milestone"] == "pull" for e in evs))

    def test_pull_filters_promoted(self):
        self.cand.mkdir()
        # 미승격 (verdict None) → 제외
        self._write_candidate("not-promoted", 1, _eval("not-promoted", 1))
        # 3 tier PASS + verdict 박제 → 포함
        self._write_candidate("promoted-a", 2,
                              _eval("promoted-a", 2, verdict="promote", all_pass=True))
        # verdict 있으나 tier 미통과 → 제외
        partial = _eval("partial-b", 1, verdict="promote", all_pass=False)
        self._write_candidate("partial-b", 1, partial)

        res = bridge.pull_promoted(self.cand, telemetry_dir=self.tel)
        slugs = {r["slug"] for r in res}
        self.assertEqual(slugs, {"promoted-a"})
        self.assertEqual(res[0]["version"], 2)
        evs = [json.loads(l) for f in self.tel.glob("*.jsonl")
               for l in f.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(any(e["type"] == "wiki_bridge_pull"
                            and e["n_promoted"] == 1 for e in evs))


    def test_pull_unreadable_traced(self):
        # 깨진 eval-results.json → 무음 skip 아니라 추적 신호 (L08-006)
        self.cand.mkdir()
        d = self.cand / "broken-v1"
        d.mkdir(parents=True)
        (d / "eval-results.json").write_text("{not json", encoding="utf-8")
        res = bridge.pull_promoted(self.cand, telemetry_dir=self.tel)
        self.assertEqual(res, [])
        evs = [json.loads(l) for f in self.tel.glob("*.jsonl")
               for l in f.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(any(e["type"] == "wiki_bridge_skipped"
                            and e["reason"] == "unreadable-candidate" for e in evs))
        pull = next(e for e in evs if e["type"] == "wiki_bridge_pull")
        self.assertEqual(pull["n_scanned"], 1)
        self.assertEqual(pull["n_skipped_unreadable"], 1)


class DedupUnitTest(unittest.TestCase):
    def test_jaccard(self):
        # 완전 일치 → 1.0
        r = bridge._dedup_check(["a", "b"], {"x": ["a", "b"]})
        self.assertEqual(r["overlap"], 1.0)
        self.assertEqual(r["conflict"], "x")
        # 무교집합 → 0.0, conflict None
        r = bridge._dedup_check(["a"], {"x": ["z"]})
        self.assertEqual(r["overlap"], 0.0)
        self.assertIsNone(r["conflict"])
        # 빈 입력 → 0.0
        self.assertEqual(bridge._dedup_check([], {"x": ["a"]})["overlap"], 0.0)
        self.assertEqual(bridge._dedup_check(["a"], None)["overlap"], 0.0)


if __name__ == "__main__":
    unittest.main()
