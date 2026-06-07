"""wiki bridge round-trip e2e 실증 (P5 C4 dogfood).

실행: repo root에서 `py -3 _workspace/_dogfood/2026-06-03_wiki_bridge_e2e/run_e2e.py`
mock wiki(tmp) 대상 — emit→schema→promotion 주입→pull→presence-gate skip 6 체크.
실 wiki repo 미변경 (tmpdir only). 결과는 verification.md 박제.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from plugins.harness.scripts.wiki import bridge  # noqa: E402

CHECKS: list[tuple[str, bool]] = []


def check(label: str, cond: bool):
    CHECKS.append((label, cond))
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")


def _skill_md():
    return (
        "---\nname: demo-skill\n"
        "description: 데모 skill. \"데모 실행\"·\"demo run\"·\"샘플\" 시 작동. NOT: 신규 파일 생성.\n"
        "meta:\n  skill_kind: user-facing\n  candidate_version: 1\n"
        "  gap_source: pattern-synthesis\n  static_tier: PASS\n"
        "  llm_judge_tier: not-run\n  mc_tier: not-run\n  promoted_to: null\n---\n\n"
        "# demo-skill\n\n본문.\n"
    )


def _eval(verdict=None, all_pass=False):
    s = "PASS" if all_pass else "not-run"
    return {
        "candidate_slug": "demo-skill", "candidate_version": 1,
        "gap_source": "pattern-synthesis", "emit_at": "2026-06-03T00:00:00Z",
        "evals": {
            "static": {"status": "PASS", "last_run": "2026-06-03", "findings": []},
            "llm_judge": {"status": s, "last_run": None, "verdict": None},
            "monte_carlo": {"status": s, "last_run": None, "verdict": None},
        },
        "promotion": {"verdict": verdict, "promoted_to": None, "promoted_at": None},
    }


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cand = root / "harness" / "candidates"
        tel = root / "_telemetry"

        print("① presence-gate (candidates/ 미존재):")
        r = bridge.emit_candidate(cand, "demo-skill", 1, _skill_md(), _eval(),
                                  [("2026-06-03", "emit", "e2e.")], telemetry_dir=tel)
        check("부재 시 emit skip (no-op)", r["status"] == "skipped" and r["reason"] == "target-absent")

        print("② M1 Emit (candidates/ 생성 후):")
        cand.mkdir(parents=True)
        r = bridge.emit_candidate(cand, "demo-skill", 1, _skill_md(), _eval(),
                                  [("2026-06-03", "emit", "e2e.")], telemetry_dir=tel)
        d = cand / "demo-skill-v1"
        check("emit 성공 + 3파일 박제",
              r["status"] == "emitted" and all((d / f).is_file()
              for f in ("SKILL.md", "eval-results.json", "changelog.md")))

        print("③ M5 schema gate (emit 산출물 자가검증):")
        check("written candidate가 contract 통과", bridge._validate_candidate_dir(d) == [])

        print("④ promotion 주입 + M4 pull:")
        (d / "eval-results.json").write_text(
            json.dumps(_eval(verdict="promote", all_pass=True), ensure_ascii=False),
            encoding="utf-8")
        promoted = bridge.pull_promoted(cand, telemetry_dir=tel)
        check("3 tier PASS + verdict → pull 반환",
              len(promoted) == 1 and promoted[0]["slug"] == "demo-skill")

        print("⑤ 미승격 제외:")
        (d / "eval-results.json").write_text(
            json.dumps(_eval(verdict=None, all_pass=False), ensure_ascii=False),
            encoding="utf-8")
        check("verdict None → pull 제외", bridge.pull_promoted(cand, telemetry_dir=tel) == [])

        print("⑥ telemetry observability:")
        events = [json.loads(l) for f in tel.glob("*.jsonl")
                  for l in f.read_text(encoding="utf-8").splitlines()]
        types = {e["type"] for e in events}
        check("emit/skip/pull telemetry 전부 박제",
              {"wiki_bridge_emit", "wiki_bridge_skipped", "wiki_bridge_pull"} <= types)

    passed = sum(1 for _, c in CHECKS if c)
    print(f"\n=== {passed}/{len(CHECKS)} PASS ===")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
