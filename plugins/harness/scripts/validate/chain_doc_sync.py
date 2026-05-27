"""chain_doc_sync.py — S13/S14 cross-doc count sync 결정적 검증 (chain.py 분할, 2026-05-25 sub-cycle ε).

박제 doctrine:
  - S13 (output-checklist.md must/should 카운트 ↔ 인용 박제 정합)
  - S14 (commands/harness-*.md glob count ↔ README/doctrine-registry R4 인용)

본 모듈은 단독 entry-point가 아니다 — chain.py가 import 후 main() chain에서 호출.
chain.PLUGIN_REFERENCES_DIR / chain.PLUGIN_SKILL_MD / chain.PLUGIN_COMMANDS_DIR /
chain.PLUGIN_README / chain._DOCTRINE_REGISTRY는 runtime에 lookup하므로 circular 안전.
"""

from __future__ import annotations

import re

from _chain_proxy import chain


# S13 박제 — output-checklist.md 본문 카운트 ↔ 인용 박제 정합 검증 대상 파일.
_OUTPUT_CHECKLIST_QUOTE_TARGETS = (
    ("SKILL.md", lambda: chain.PLUGIN_SKILL_MD),
    ("harness-new.md", lambda: chain.PLUGIN_COMMANDS_DIR / "harness-new.md"),
)
_OUTPUT_CHECKLIST_QUOTE_PATTERN = re.compile(r"must\s+(\d+)\s*/\s*should\s+(\d+)")
_OUTPUT_CHECKLIST_HEADER_PATTERN = re.compile(
    r"must\s*\(\s*(\d+)\s*\)\s*/\s*should\s*\(\s*(\d+)\s*\)"
)


def check_output_checklist_count_sync() -> list[str]:
    """S13 doctrine doc sync — output-checklist.md must/should 카운트 ↔ 인용 박제 정합 (2026-05-25).

    `output-checklist.md` 본문 ## 차단 (must) / ## 권장 (should) 섹션 `- [ ]` 항목 카운트가
    정본. 헤더 `must (N) / should (M)` 박제 + SKILL.md·harness-new.md 인용 박제 `must N / should M`
    토큰이 정본과 mismatch 시 FAIL. 체크리스트 항목 추가/삭제 시 cross-doc 동기 강제.
    """
    checklist = chain.PLUGIN_REFERENCES_DIR / "output-checklist.md"
    if not checklist.exists():
        return []
    try:
        body = checklist.read_text(encoding="utf-8-sig")
    except OSError:
        return []

    must_count = 0
    should_count = 0
    current: str | None = None
    for raw in body.splitlines():
        stripped = raw.strip()
        if stripped.startswith("## "):
            header = stripped.lower()
            if "must" in header or "차단" in header:
                current = "must"
            elif "should" in header or "권장" in header:
                current = "should"
            else:
                current = None
            continue
        if current == "must" and stripped.startswith("- [ ]"):
            must_count += 1
        elif current == "should" and stripped.startswith("- [ ]"):
            should_count += 1

    errors: list[str] = []

    for m in _OUTPUT_CHECKLIST_HEADER_PATTERN.finditer(body):
        mu, sh = int(m.group(1)), int(m.group(2))
        if mu != must_count or sh != should_count:
            errors.append(
                f"output-checklist.md: 헤더 `must ({mu}) / should ({sh})` ↔ "
                f"본문 정본 `must {must_count} / should {should_count}` drift (S13)"
            )

    for label, resolver in _OUTPUT_CHECKLIST_QUOTE_TARGETS:
        path = resolver()
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        for m in _OUTPUT_CHECKLIST_QUOTE_PATTERN.finditer(text):
            mu, sh = int(m.group(1)), int(m.group(2))
            if mu != must_count or sh != should_count:
                errors.append(
                    f"{label}: 인용 박제 `must {mu} / should {sh}` ↔ "
                    f"output-checklist.md 정본 `must {must_count} / should {should_count}` "
                    f"drift (S13)"
                )
    return errors


# S14 박제 — commands/harness-*.md glob count 정본 ↔ 인용 박제.
_README_CATALOG_HEADER_PATTERN = re.compile(r"Slash command 카탈로그\s*\((\d+)\s*개\)")
_DOCTRINE_R4_LINE_PATTERN = re.compile(
    r"^\|\s*R4\s*\|.*?(\d+)\s*슬래시\s*커맨드.*?\|", re.MULTILINE
)


def check_command_count_sync() -> list[str]:
    """S14 doctrine doc sync — commands/harness-*.md glob count ↔ README/doctrine-registry 인용 (2026-05-25).

    `plugins/harness/commands/harness-*.md` glob count가 정본. 인용 박제 위치:
      - `README.md`: `### Slash command 카탈로그 (N개)` 헤더
      - `doctrine-registry.md` R4 행 본문 `N 슬래시 커맨드`
    drift 시 FAIL. 명령 추가/제거 시 cross-doc 동기 강제.
    """
    if not chain.PLUGIN_COMMANDS_DIR.exists():
        return []
    canonical = len(sorted(chain.PLUGIN_COMMANDS_DIR.glob("harness-*.md")))
    errors: list[str] = []

    if chain.PLUGIN_README.exists():
        try:
            text = chain.PLUGIN_README.read_text(encoding="utf-8-sig")
        except OSError:
            text = ""
        for m in _README_CATALOG_HEADER_PATTERN.finditer(text):
            quoted = int(m.group(1))
            if quoted != canonical:
                errors.append(
                    f"README.md: `Slash command 카탈로그 ({quoted}개)` ↔ "
                    f"commands/harness-*.md glob 정본 {canonical} drift (S14)"
                )

    registry = chain._DOCTRINE_REGISTRY
    if registry.exists():
        try:
            reg = registry.read_text(encoding="utf-8-sig")
        except OSError:
            reg = ""
        for m in _DOCTRINE_R4_LINE_PATTERN.finditer(reg):
            quoted = int(m.group(1))
            if quoted != canonical:
                errors.append(
                    f"doctrine-registry.md: R4 본문 `{quoted} 슬래시 커맨드` ↔ "
                    f"commands/harness-*.md glob 정본 {canonical} drift (S14)"
                )
    return errors
