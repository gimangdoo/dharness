"""chain_doc_sync.py — S13/S14/S15/S16 cross-doc count sync 결정적 검증 (chain.py 분할, 2026-05-25 sub-cycle ε).

박제 doctrine:
  - S13 (output-checklist.md must/should 카운트 ↔ 인용 박제 정합)
  - S14 (commands/harness-*.md glob count ↔ README/doctrine-registry R4 인용)
  - S15 (trigger-keyword-catalog.md §1 표 ↔ chain._TRIGGER_SIGNAL_KEYWORDS dict, 2026-05-28 audit2 PA6)
  - S16 (SKILL.md `### Phase` 헤더 카운트 ↔ 4 ad 위치 박제, 2026-05-28 audit2 PA9)

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


# S15 박제 — trigger-keyword-catalog.md §1 표 ↔ chain._TRIGGER_SIGNAL_KEYWORDS dict sync.
# §1 표 row 패턴: `| **S{n} {label}** [(suffix)] | profile | korean kw, ... | english kw, ... | strength |`
# `**` 닫힘 후 ` (2026-05-14)` 등 첫 컬럼 부속 텍스트 흡수 — `[^|]*` 추가.
_CATALOG_ROW_PATTERN = re.compile(
    r"^\|\s*\*\*S(\d+)\b[^|]*?\*\*[^|]*\|[^|]*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|[^|]*\|\s*$",
    re.MULTILINE,
)


def _parse_catalog_keywords(text: str) -> dict[str, set[str]]:
    """trigger-keyword-catalog.md §1 표 parse → signal_id → keyword set.

    각 row의 column 3(Korean) + column 4(English)를 comma-split하여 합집합. parentheses
    suffix(`(2026-05-14)` 등 신호명 부속)는 cell parse 영향 X — regex가 `**S{n}\\b[^|]*\\*\\*`
    범위로 흡수.
    """
    catalog: dict[str, set[str]] = {}
    for m in _CATALOG_ROW_PATTERN.finditer(text):
        sid = f"S{m.group(1)}"
        ko = {k.strip() for k in m.group(2).split(",") if k.strip()}
        en = {k.strip() for k in m.group(3).split(",") if k.strip()}
        catalog[sid] = ko | en
    return catalog


def check_trigger_catalog_python_sync() -> list[str]:
    """S15 doctrine doc sync — trigger-keyword-catalog.md §1 ↔ chain._TRIGGER_SIGNAL_KEYWORDS dict (2026-05-28).

    catalog가 단일 출처 (doctrine S11) — dict는 catalog의 모든 키워드 cover. 누락 시:
      - catalog → dict 누락: derived `.claude/skills/*` description에서 본 키워드 hit해도
        signal_coverage 검증 silent miss. FAIL.
      - dict → catalog 누락: dict 등록됐으나 정본 미박제 — 정본 부재 doctrine 위반. FAIL.

    catalog table parse 실패 (row 0건) 시 1 error — 표 format 깨졌거나 §1 헤더 변경 신호.
    """
    catalog_path = chain.PLUGIN_REFERENCES_DIR / "trigger-keyword-catalog.md"
    if not catalog_path.exists():
        return []
    try:
        text = catalog_path.read_text(encoding="utf-8-sig")
    except OSError:
        return []

    catalog = _parse_catalog_keywords(text)
    if not catalog:
        return [
            "trigger-keyword-catalog.md §1: row parse 실패 — 표 format 깨졌거나 헤더 변경 (S15)"
        ]

    errors: list[str] = []
    code_dict = chain._TRIGGER_SIGNAL_KEYWORDS

    catalog_sids = set(catalog.keys())
    code_sids = set(code_dict.keys())

    for sid in sorted(catalog_sids - code_sids):
        errors.append(
            f"trigger-keyword-catalog.md §1: signal `{sid}` 박제됐으나 "
            f"chain._TRIGGER_SIGNAL_KEYWORDS dict 미등록 (S15 sync drift)"
        )
    for sid in sorted(code_sids - catalog_sids):
        errors.append(
            f"chain._TRIGGER_SIGNAL_KEYWORDS: signal `{sid}` 등록됐으나 "
            f"trigger-keyword-catalog.md §1 미박제 (S15 sync drift)"
        )

    for sid in sorted(catalog_sids & code_sids):
        cat_kw = catalog[sid]
        code_kw = set(code_dict[sid])
        only_cat = cat_kw - code_kw
        only_code = code_kw - cat_kw
        for kw in sorted(only_cat):
            errors.append(
                f"trigger-keyword-catalog.md §1 {sid}: 키워드 `{kw}` 박제됐으나 "
                f"chain._TRIGGER_SIGNAL_KEYWORDS[{sid}] 미등록 (S15 sync drift)"
            )
        for kw in sorted(only_code):
            errors.append(
                f"chain._TRIGGER_SIGNAL_KEYWORDS[{sid}]: 키워드 `{kw}` 등록됐으나 "
                f"trigger-keyword-catalog.md §1 미박제 (S15 sync drift)"
            )
    return errors


# S16 박제 — SKILL.md `### Phase` 헤더 카운트 정본 ↔ 4 ad 위치 박제 sync.
_SKILL_PHASE_HEADER_PATTERN = re.compile(r"^### Phase ([\d.]+)\b", re.MULTILINE)
# `(N)[-/space](phase|Phase|단계) ... [(—] (M)[ ]?(본 phase|base|phase) [ ]?+[ ]?(K)[ ]?critique`
# em-dash(`—` U+2014) / en-dash(`–` U+2013) / 괄호 시작 모두 매치. `[^(—–]*?` non-greedy로
# 헤더 토큰 ↔ breakdown 토큰 인접성 보장 (다른 phase 박제 행 인접 시 cross 회피).
_PHASE_AD_PATTERN = re.compile(
    r"(\d+)\s*[-]?\s*(?:phase|Phase|단계)[^(—–]*?[\(—–]\s*(\d+)\s*(?:본\s*)?(?:base|phase)\s*\+\s*(\d+)\s*critique",
    re.IGNORECASE,
)


def _phase_ad_targets() -> tuple[tuple[str, "object"], ...]:
    """4 ad 위치 박제 — chain.REPO_ROOT 기반 절대경로 resolve.

    target file 박제 (S16 doctrine):
      - .claude-plugin/marketplace.json (plugin 마켓 광고)
      - plugins/harness/.claude-plugin/plugin.json (plugin 자체 광고)
      - plugins/harness/README.md (plugin README)
      - README.md (루트 README 본문 + L520 표)
    """
    repo = chain.REPO_ROOT
    return (
        ("marketplace.json", repo / ".claude-plugin" / "marketplace.json"),
        ("plugin.json", repo / "plugins" / "harness" / ".claude-plugin" / "plugin.json"),
        ("plugin README", chain.PLUGIN_README),
        ("root README", repo / "README.md"),
    )


def check_phase_count_sync() -> list[str]:
    """S16 doctrine doc sync — SKILL.md `### Phase` 헤더 카운트 ↔ 4 ad 위치 박제 (2026-05-28).

    SKILL.md가 정본 — `### Phase X` 또는 `### Phase X.Y` 헤더 매칭. critique/sim phase는
    X.Y 패턴 중 `0.5` 제외 (0.5는 Pre-flight Clarification = base 카테고리, 2026-05-28 audit2
    PA3 정정 doctrine). base = 정수 phase + `0.5`, critique = `3.5/5.5/7.5`.

    각 ad 위치의 `N-phase ... (M base + K critique)` 토큰이 정본과 mismatch 시 FAIL. PA3
    회귀 (광고 문장 drift) 자동 차단.
    """
    skill_md = chain.PLUGIN_SKILL_MD
    if not skill_md.exists():
        return []
    try:
        text = skill_md.read_text(encoding="utf-8-sig")
    except OSError:
        return []

    headers = _SKILL_PHASE_HEADER_PATTERN.findall(text)
    if not headers:
        return []

    total = len(headers)
    critique = sum(1 for p in headers if "." in p and p != "0.5")
    base = total - critique

    errors: list[str] = []
    for label, path in _phase_ad_targets():
        if not path.exists():
            continue
        try:
            ad = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        for m in _PHASE_AD_PATTERN.finditer(ad):
            ad_total, ad_base, ad_critique = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if (ad_total, ad_base, ad_critique) != (total, base, critique):
                errors.append(
                    f"{label}: `{ad_total}-phase ({ad_base} base + {ad_critique} critique)` ↔ "
                    f"SKILL.md 정본 `{total}-phase ({base} base + {critique} critique)` "
                    f"drift (S16)"
                )
    return errors
