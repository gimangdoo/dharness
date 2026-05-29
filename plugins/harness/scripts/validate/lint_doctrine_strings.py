#!/usr/bin/env python3
"""doctrine 문자열 lint — markdown 본문에 박제되어야 할 doctrine 키워드를 정형 검증.

PT1 (2026-05-27): test_schema.py:HarnessNewGates의 다수 assertIn(string, gates) 패턴을
독립 lint script로 추출. 단위 테스트 카운트 정직화 — 단순 markdown grep을
unit test로 박제하지 않는다.

검증 대상 doctrine:
- anti-premature-judgment doctrine (phase-entry-gates.md / SKILL.md pointer)
- Phase 1·2·5 entry 게이트 (phase-entry-gates.md)
- Phase 3.5 / 5.5 / 7.5 self-critique (SKILL.md)
- harness-new 커맨드 동기화 (harness-new.md)

실행:
    py plugins/harness/scripts/validate/lint_doctrine_strings.py

종료 코드:
    0 — 모든 doctrine 매칭
    1 — 1+ 미박제 문구 발견 (stderr에 누락 리포트)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL_MD = REPO_ROOT / "plugins" / "harness" / "skills" / "harness" / "SKILL.md"
GATES_MD = REPO_ROOT / "plugins" / "harness" / "skills" / "harness" / "references" / "phase-entry-gates.md"
CMD_MD = REPO_ROOT / "plugins" / "harness" / "commands" / "harness-new.md"
DOCTRINE_REGISTRY = REPO_ROOT / "plugins" / "harness" / "skills" / "harness" / "references" / "doctrine-registry.md"
VALIDATE_DIR = REPO_ROOT / "plugins" / "harness" / "scripts" / "validate"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


_CHECKS: list[tuple[str, Path, str]] = [
    # (label, file, must-contain substring)
    ("SKILL.md: phase-entry-gates.md pointer", SKILL_MD, "phase-entry-gates.md"),
    ("phase-entry-gates.md: Anti-premature-judgment doctrine", GATES_MD, "Anti-premature-judgment doctrine"),
    ("phase-entry-gates.md: 'cwd 디렉토리 이름' 단정 금지", GATES_MD, "cwd 디렉토리 이름"),
    ("phase-entry-gates.md: '단정 허용 조건' 게이트", GATES_MD, "단정 허용 조건"),
    ("phase-entry-gates.md: Phase 1 산출물 강제", GATES_MD, "산출물 강제"),
    ("phase-entry-gates.md: Phase 1 실 파일 read 강제", GATES_MD, "실 파일 read 강제"),
    ("phase-entry-gates.md: silent skip 차단", GATES_MD, "silent skip 차단"),
    ("phase-entry-gates.md: Phase 2 질문 폭격 강제", GATES_MD, "질문 폭격 강제"),
    ("phase-entry-gates.md: Phase 2 user_confirmed_fields", GATES_MD, "user_confirmed_fields"),
    ("phase-entry-gates.md: Phase 5 Cardinality justification", GATES_MD, "Cardinality justification"),
    ("phase-entry-gates.md: Phase 5 inline 대안 검토", GATES_MD, "inline 대안 검토"),
    ("phase-entry-gates.md: Phase 5 single-use → inline 룰", GATES_MD, "single-use → inline"),
    ("phase-entry-gates.md: Phase 5 이름 유일성 사전 점검", GATES_MD, "이름 유일성 사전 점검"),
    ("harness-new.md: Anti-premature-judgment pointer", CMD_MD, "Anti-premature-judgment"),
    ("harness-new.md: 2026-05-15 entry 게이트 pointer", CMD_MD, "entry 게이트 (2026-05-15)"),
    ("SKILL.md: Phase 3.5 self-critique 섹션", SKILL_MD, "Phase 3.5: Self-Critique on Domain Analysis"),
    ("SKILL.md: Phase 3.5 single-pass silent error doctrine", SKILL_MD, "single-pass silent error"),
    ("SKILL.md: Phase 3.5 _critique_phase3_ 산출물", SKILL_MD, "_critique_phase3_"),
    ("SKILL.md: Phase 5.5 self-critique 섹션", SKILL_MD, "Phase 5.5: Self-Critique on Agent Definitions"),
    ("SKILL.md: Phase 5.5 역할 중복 cross-review doctrine", SKILL_MD, "역할 중복"),
    ("SKILL.md: Phase 5.5 _critique_phase5_ 산출물", SKILL_MD, "_critique_phase5_"),
    ("SKILL.md: Phase 7.5 dry-run 섹션", SKILL_MD, "Phase 7.5: Orchestrator Dry-Run Simulation"),
    ("SKILL.md: Phase 7.5 dead link 검출 doctrine", SKILL_MD, "dead link"),
    ("SKILL.md: Phase 7.5 _critique_phase7_ 산출물", SKILL_MD, "_critique_phase7_"),
]


_REGISTRY_ID_ROW_RE = re.compile(r"^\|\s*([WRSPI]\d+)\s*\|")
_CODE_DOCTRINE_ID_RE = re.compile(r"\b([WRSPI]\d+)\b(?!-)")
_CODE_TARGETS: tuple[str, ...] = (
    "chain.py", "chain_advisor.py", "chain_doc_sync.py", "chain_intent.py",
    "chain_registry.py", "chain_version.py", "_chain_proxy.py",
    "schema.py", "structure.py",
)
# 코드 본문 내 NON-doctrine 의미 — `[WRSPI]\d+` 패턴은 매치되나 doctrine 색인 대상 아님.
# - S1~S10: trigger signal id (catalog namespace, docstring/주석에서도 사용 — registry §3의 동명 doctrine id와 우연 겹침)
# - SQLite·PySQLite 등 라이브러리명 일부는 패턴 미적합이라 제외 무필요.
_CODE_DOCTRINE_IGNORE: frozenset[str] = frozenset({
    "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10",
})


def _load_registry_doctrine_ids() -> set[str]:
    ids: set[str] = set()
    if not DOCTRINE_REGISTRY.exists():
        return ids
    for raw in DOCTRINE_REGISTRY.read_text(encoding="utf-8-sig").splitlines():
        m = _REGISTRY_ID_ROW_RE.match(raw)
        if m:
            ids.add(m.group(1))
    return ids


def _iter_comment_segments(text: str):
    """py source line-by-line iter — comment 또는 docstring 영역 substring만 yield.

    docstring tracking: 라인의 triple-quote 카운트가 홀수면 토글. 라인 내 시작·끝이 같은 라인이면
    내부는 docstring으로 간주 (간단 휴리스틱, 모듈/함수 docstring 대부분 cover).
    string literal 내 hash로 인한 false-positive는 일부 있으나 본 lint는 over-strict 허용 (Phase 4 PA16).
    """
    in_docstring = False
    for line in text.splitlines():
        triple_count = line.count('"""') + line.count("'''")
        starts_in = in_docstring
        if triple_count % 2 == 1:
            in_docstring = not in_docstring
        if starts_in or in_docstring:
            yield line
            continue
        idx = line.find("#")
        if idx == -1:
            continue
        # 일부 string literal 내 #를 더 강하게 회피하려면 quote balance를 봐야 하나, 단순화.
        yield line[idx + 1:]


def _check_code_doctrine_refs() -> list[str]:
    """PA16 — chain*.py/schema.py/structure.py 주석·docstring 내 `[WRSPI]\\d+` doctrine id가
    doctrine-registry.md 표 본문에 등재됐는지 cross-check. 미등재 → registry 박제 누락 알림.
    """
    failures: list[str] = []
    valid = _load_registry_doctrine_ids()
    if not valid:
        failures.append(f"doctrine-registry.md 파싱 실패 ({DOCTRINE_REGISTRY.relative_to(REPO_ROOT)})")
        return failures
    for name in _CODE_TARGETS:
        path = VALIDATE_DIR / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8-sig")
        missing: dict[str, set[int]] = {}
        for line_no, segment in enumerate(_iter_comment_segments(text), start=1):
            for m in _CODE_DOCTRINE_ID_RE.finditer(segment):
                did = m.group(1)
                if did in _CODE_DOCTRINE_IGNORE:
                    continue
                if did not in valid:
                    missing.setdefault(did, set()).add(line_no)
        for did in sorted(missing):
            lines = ",".join(str(n) for n in sorted(missing[did])[:3])
            failures.append(
                f"{name}: 주석/docstring doctrine id `{did}` 미등재 (registry §1~§5 행 없음, hits L{lines})"
            )
    return failures


def run() -> int:
    cache: dict[Path, str] = {}
    failures: list[str] = []
    for label, path, needle in _CHECKS:
        if not path.exists():
            failures.append(f"{label}: 파일 부재 ({path.relative_to(REPO_ROOT)})")
            continue
        if path not in cache:
            cache[path] = _read(path)
        if needle not in cache[path]:
            failures.append(f"{label}: '{needle}' 미박제")
    code_failures = _check_code_doctrine_refs()
    failures.extend(code_failures)
    if failures:
        print(f"[lint_doctrine_strings] {len(failures)}건 미박제:", file=sys.stderr)
        for f in failures:
            print(f"  · {f}", file=sys.stderr)
        return 1
    print(f"[lint_doctrine_strings] {len(_CHECKS)}건 doctrine 박제 + {len(_CODE_TARGETS)}개 코드 파일 doctrine ref 확인.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
