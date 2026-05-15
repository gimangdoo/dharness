"""P7-2 dogfood telemetry — KO/EN reference pair token measurement (deterministic).

LLM-free. tiktoken cl100k_base 기반. 4 POC pair의 정적 token cost를 측정해
`_workspace/_telemetry/poc_dogfood_static.jsonl`에 누적 적재.

용도:
    py plugins/harness/scripts/poc/measure_dogfood.py [--json] [--strip-poc-note]

`--strip-poc-note`: EN 파일에서 P7-1/P7-2 POC note 부록 section 제거 후 측정
(content-level reduction 격리 — 부록은 항상 KO에 없으므로 비교 왜곡 방지).

실 세션 dogfood (응답 품질·실행 시간·오류율 비교)는 본 스크립트 범위 외 —
`references/poc-dogfood-protocol.md` 사용자 측정 doctrine 참조.
"""

from __future__ import annotations

import io
import json
import re
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[4]
REF_DIR = REPO_ROOT / "plugins" / "harness" / "skills" / "harness" / "references"
TELEMETRY_DIR = REPO_ROOT / "_workspace" / "_telemetry"
TELEMETRY_LOG = TELEMETRY_DIR / "poc_dogfood_static.jsonl"

POC_PAIRS = [
    "team-tools-api",
    "agent-design-patterns",
    "skill-testing-guide",
    "skill-writing-guide",
]

POC_NOTE_RE = re.compile(
    r"(?ms)^##\s+P7-[12]\s+POC\s+note.*\Z"
)


def _strip_poc_note(text: str) -> str:
    return POC_NOTE_RE.sub("", text).rstrip() + "\n"


def measure_pair(stem: str, strip_poc_note: bool, encoder) -> dict:
    ko_path = REF_DIR / f"{stem}.md"
    en_path = REF_DIR / f"{stem}.en.md"
    ko_text = ko_path.read_text(encoding="utf-8-sig")
    en_text = en_path.read_text(encoding="utf-8-sig")
    if strip_poc_note:
        en_text = _strip_poc_note(en_text)
    ko_tokens = len(encoder.encode(ko_text))
    en_tokens = len(encoder.encode(en_text))
    ko_bytes = len(ko_text.encode("utf-8"))
    en_bytes = len(en_text.encode("utf-8"))
    ratio = round(en_tokens / ko_tokens, 4) if ko_tokens else None
    delta = en_tokens - ko_tokens
    return {
        "stem": stem,
        "ko_path": str(ko_path.relative_to(REPO_ROOT)),
        "en_path": str(en_path.relative_to(REPO_ROOT)),
        "ko_tokens": ko_tokens,
        "en_tokens": en_tokens,
        "ko_bytes": ko_bytes,
        "en_bytes": en_bytes,
        "token_ratio_en_over_ko": ratio,
        "token_delta": delta,
        "strip_poc_note": strip_poc_note,
    }


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    strip = "--strip-poc-note" in argv

    try:
        import tiktoken
    except ImportError:
        msg = "tiktoken 미설치 — `py -m pip install tiktoken` 필요"
        if as_json:
            print(json.dumps({"status": "precondition_fail", "error": msg}, ensure_ascii=False))
        else:
            print(f"❌ {msg}")
        return 2

    encoder = tiktoken.get_encoding("cl100k_base")
    results: list[dict] = []
    missing: list[str] = []
    for stem in POC_PAIRS:
        ko = REF_DIR / f"{stem}.md"
        en = REF_DIR / f"{stem}.en.md"
        if not ko.exists() or not en.exists():
            missing.append(stem)
            continue
        results.append(measure_pair(stem, strip, encoder))

    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    summary = {
        "section": "poc_dogfood_static",
        "ts": now_iso,
        "strip_poc_note": strip,
        "pairs_measured": len(results),
        "missing": missing,
        "pairs": results,
    }

    if results:
        avg_ratio = round(
            sum(r["token_ratio_en_over_ko"] or 0 for r in results) / len(results), 4
        )
        total_ko = sum(r["ko_tokens"] for r in results)
        total_en = sum(r["en_tokens"] for r in results)
        summary["aggregate"] = {
            "avg_token_ratio_en_over_ko": avg_ratio,
            "total_ko_tokens": total_ko,
            "total_en_tokens": total_en,
            "total_delta": total_en - total_ko,
            "total_ratio": round(total_en / total_ko, 4) if total_ko else None,
        }

    TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
    with open(TELEMETRY_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(summary, ensure_ascii=False) + "\n")

    if as_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    icon = "✅" if not missing else "⚠️"
    print(f"{icon} P7-2 dogfood static: {len(results)} pairs measured, {len(missing)} missing")
    for r in results:
        print(
            f"  - {r['stem']}: KO={r['ko_tokens']}tok / EN={r['en_tokens']}tok "
            f"(ratio={r['token_ratio_en_over_ko']}, Δ={r['token_delta']:+d})"
        )
    if "aggregate" in summary:
        agg = summary["aggregate"]
        print(
            f"  aggregate: total KO={agg['total_ko_tokens']}tok / EN={agg['total_en_tokens']}tok "
            f"(ratio={agg['total_ratio']}, avg pair ratio={agg['avg_token_ratio_en_over_ko']})"
        )
    print(f"  log: {TELEMETRY_LOG.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
