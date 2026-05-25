"""chain_intent.py — intent_profile.md 도메인 결정적 검증 (chain.py 분할, 2026-05-25).

박제 doctrine:
  - W3 (sub-cycle α 흡수, 2026-05-25) — meta.user_confirmed_fields ↔ INTENT_REQUIRED 5필드 정합
      · _INTENT_USER_CONFIRMED_REQUIRED (chain.INTENT_REQUIRED alias)
      · _extract_user_confirmed_fields helper
      · check_required_user_confirmed_fields
      · check_intent_required_doc_sync (W3 doc sync — schema ↔ doc 3곳)
  - W7 (sub-cycle β 흡수, 2026-05-25) — meta.grilling_log[] enum 강제
      · _GRILLING_VALID_PHASES / _GRILLING_VALID_SOURCES / _GRILLING_REQUIRED_KEYS
      · _extract_grilling_log_block / _parse_grilling_entries helpers
      · check_intent_profile_grilling_log
  - W9 (cycle 4, 2026-05-25) — intent_profile.md §8 필수/cross-field 결정적 4 fn
      · check_intent_profile_version (C14-1)
      · check_intent_profile_project_type (C14-2, enum {greenfield, brownfield})
      · check_intent_profile_brownfield_inferred (C14-3)
      · check_intent_profile_greenfield_locked_in (C15-4 모순 invariant)

본 모듈은 단독 entry-point가 아니다 — chain.py가 import 후 main() chain에서 호출.
chain.INTENT_PROFILE / chain.FRONTMATTER_RE 등은 runtime에 lookup하므로 모듈 import 시점
circular 안전 (test_chain의 module-level monkey-patch 호환 유지).
"""

from __future__ import annotations

import re
import sys


# chain.py와 양방향 import 회피 — fn 본문에서만 sys.modules lookup으로 runtime resolve.
# chain.py module-level `from chain_intent import ...`가 본 모듈 body 실행 시
# `import chain` 했다면 partial init 충돌 — 그래서 import 자체를 lazy proxy로 우회.
class _ChainProxy:
    def __getattr__(self, name: str):
        # chain.py가 `__main__`으로 실행되면 sys.modules에 'chain' 키가 없으므로 fallback.
        mod = sys.modules.get("chain") or sys.modules["__main__"]
        return getattr(mod, name)


chain = _ChainProxy()

_PROJECT_TYPE_ENUM = {"greenfield", "brownfield"}
_INTENT_VERSION_PATTERN = re.compile(r"^version\s*:\s*(\S+)\s*$", re.MULTILINE)
_INTENT_PROJECT_TYPE_PATTERN = re.compile(r"^project_type\s*:\s*([\w-]+)\s*$", re.MULTILINE)
_INTENT_LOCKED_IN_PATTERN = re.compile(r"^\s*locked_in\s*:\s*\[(.*?)\]\s*$", re.MULTILINE)


def _extract_user_confirmed_fields(yaml_body: str) -> list[str] | None:
    """meta.user_confirmed_fields list 추출 — inline / indented / compact YAML 양쪽 지원.

    반환값 의미:
      None  — meta.user_confirmed_fields 필드 자체 박제 미존재
      list  — 박제 list (빈 list 포함). 원소는 dot-path string.

    inline 형태 `user_confirmed_fields: []` / `user_confirmed_fields: [a, b]`도 지원.
    """
    strip_quotes = chain._strip_quotes
    lines = yaml_body.splitlines()
    in_meta = False
    meta_indent = -1
    in_list = False
    list_indent = -1
    items: list[str] = []
    for raw in lines:
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        if not in_meta:
            if stripped.startswith("meta:") and indent == 0:
                in_meta = True
                meta_indent = indent
            continue
        if in_meta and not in_list:
            if indent <= meta_indent:
                return None
            m = re.match(r"^user_confirmed_fields\s*:\s*(.*)$", stripped)
            if m:
                inline = m.group(1).strip()
                if inline.startswith("["):
                    body = inline.strip().lstrip("[").rstrip("]")
                    return [strip_quotes(t.strip()) for t in body.split(",") if t.strip()]
                if inline:
                    return []
                in_list = True
                list_indent = indent
            continue
        if in_list:
            if stripped.startswith("- ") and indent > list_indent:
                items.append(strip_quotes(stripped[2:].strip()))
                continue
            if indent <= list_indent and stripped:
                break
    if in_list:
        return items
    return None


def check_required_user_confirmed_fields() -> list[str]:
    """W3 doctrine — intent_profile.md meta.user_confirmed_fields가 INTENT_REQUIRED 5필드 전부 커버.

    prefix 매칭 — `constraints.tech_stack.locked_in` 등록은 `constraints.tech_stack` 커버.
    intent_profile.md 미존재 시 silent skip (schema.py가 별도 FAIL).
    meta.user_confirmed_fields 박제 자체 미존재 또는 빈 list → 5필드 모두 누락 FAIL.

    근거: phase-entry-gates.md §Phase 2 step 1 + Phase 0.5 anti-premature-judgment evidence #2.
    """
    errors: list[str] = []
    if not chain.INTENT_PROFILE.exists():
        return errors
    try:
        text = chain.INTENT_PROFILE.read_text(encoding="utf-8-sig")
    except OSError:
        return errors

    fm = chain.FRONTMATTER_RE.search(text)
    body = fm.group(1) if fm else text

    confirmed = _extract_user_confirmed_fields(body)
    if confirmed is None:
        errors.append(
            "intent_profile.md meta.user_confirmed_fields 필드 박제 누락 — "
            "Phase 2 doctrine 위반 (W3, phase-entry-gates.md §Phase 2 step 1)"
        )
        confirmed = []

    for required in chain._INTENT_USER_CONFIRMED_REQUIRED:
        prefix = required + "."
        if not any(c == required or c.startswith(prefix) for c in confirmed):
            errors.append(
                f"intent_profile.md meta.user_confirmed_fields: 필수 필드 `{required}` 누락 — "
                f"사용자 raw 답변 미박제 (W3 anti-premature-judgment 강제)"
            )
    return errors


_INTENT_REQUIRED_DOC_TARGETS = (
    ("SKILL.md", lambda: chain.PLUGIN_SKILL_MD),
    ("phase-entry-gates.md", lambda: chain.PLUGIN_REFERENCES_DIR / "phase-entry-gates.md"),
    ("intent-profile-schema.md", lambda: chain.PLUGIN_REFERENCES_DIR / "intent-profile-schema.md"),
)


def check_intent_required_doc_sync() -> list[str]:
    """W3 doctrine doc sync — schema.py:INTENT_REQUIRED 5필드가 본문 doc에 모두 박제 (2026-05-24).

    필드 list가 schema.py와 doc 5곳에 분산 hard-code된 drift 위험을 결정적으로 차단.
    각 doc 위치(SKILL.md / phase-entry-gates.md / intent-profile-schema.md)에 5필드 모두
    문자열 hit 보장. 1 필드라도 doc 누락 시 FAIL — schema 진화 시 doc 동기화 강제.
    """
    errors: list[str] = []
    for label, resolver in _INTENT_REQUIRED_DOC_TARGETS:
        path = resolver()
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        for field in chain.INTENT_REQUIRED:
            if field not in text:
                errors.append(
                    f"{label}: schema.py:INTENT_REQUIRED 필드 `{field}` 박제 누락 "
                    f"— doc ↔ schema sync drift (W3 doc sync)"
                )
    return errors


def _count_yaml_list_items(raw: str) -> int:
    """inline YAML list `[a, b, c]` 항목 카운트."""
    s = raw.strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return 0
        return len([p for p in inner.split(",") if p.strip()])
    return 0


def _count_inferred_fields(body: str) -> int | None:
    """meta.inferred_fields 항목 카운트. 미박제 시 None.

    inline list (`inferred_fields: [a, b]`) + block list (다음 줄 `- item`) 양 지원.
    """
    lines = body.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^\s*inferred_fields\s*:\s*(.*)$", line)
        if not m:
            continue
        rest = m.group(1).strip()
        if rest.startswith("["):
            return _count_yaml_list_items(rest)
        if rest in ("", "|", ">"):
            count = 0
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if nxt.strip() == "":
                    j += 1
                    continue
                if re.match(r"^\s+-\s+\S", nxt):
                    count += 1
                    j += 1
                    continue
                break
            return count
        return 0
    return None


def check_intent_profile_version() -> list[str]:
    """C14-1 — intent_profile.md frontmatter `version:` 필드 존재 (2026-05-25)."""
    if not chain.INTENT_PROFILE.exists():
        return []
    try:
        text = chain.INTENT_PROFILE.read_text(encoding="utf-8-sig")
    except OSError:
        return []
    fm = chain.FRONTMATTER_RE.search(text)
    body = fm.group(1) if fm else text
    if not _INTENT_VERSION_PATTERN.search(body):
        return [
            "intent_profile.md frontmatter `version:` 필드 누락 — schema §8 필수 룰 위반 (C14-1)"
        ]
    return []


def check_intent_profile_project_type() -> list[str]:
    """C14-2 — intent_profile.md frontmatter `project_type:` 필드 + enum (2026-05-25)."""
    if not chain.INTENT_PROFILE.exists():
        return []
    try:
        text = chain.INTENT_PROFILE.read_text(encoding="utf-8-sig")
    except OSError:
        return []
    fm = chain.FRONTMATTER_RE.search(text)
    body = fm.group(1) if fm else text
    m = _INTENT_PROJECT_TYPE_PATTERN.search(body)
    if not m:
        return [
            "intent_profile.md frontmatter `project_type:` 필드 누락 — schema §8 필수 룰 위반 (C14-2)"
        ]
    value = m.group(1).strip().strip('"\'')
    if value not in _PROJECT_TYPE_ENUM:
        return [
            f"intent_profile.md `project_type: {value}` — enum {sorted(_PROJECT_TYPE_ENUM)} 외 (C14-2)"
        ]
    return []


def check_intent_profile_brownfield_inferred() -> list[str]:
    """C14-3 — project_type=brownfield 시 inferred_fields 비어있지 않음 (2026-05-25)."""
    if not chain.INTENT_PROFILE.exists():
        return []
    try:
        text = chain.INTENT_PROFILE.read_text(encoding="utf-8-sig")
    except OSError:
        return []
    fm = chain.FRONTMATTER_RE.search(text)
    body = fm.group(1) if fm else text
    m = _INTENT_PROJECT_TYPE_PATTERN.search(body)
    if not m:
        return []
    if m.group(1).strip().strip('"\'') != "brownfield":
        return []
    count = _count_inferred_fields(body)
    if count is None:
        return [
            "intent_profile.md brownfield인데 meta.inferred_fields 박제 누락 "
            "— Code Research 1+ 추론 필수 (C14-3)"
        ]
    if count == 0:
        return [
            "intent_profile.md brownfield인데 meta.inferred_fields 비어있음 "
            "— Code Research 1+ 추론 필수 (C14-3)"
        ]
    return []


def check_intent_profile_greenfield_locked_in() -> list[str]:
    """C15-4 — project_type=greenfield + constraints.tech_stack.locked_in != [] 모순 (2026-05-25).

    greenfield는 새 프로젝트라 기 도입 lock 기술이 없음. locked_in 비공 list 시 모순 FAIL.
    """
    if not chain.INTENT_PROFILE.exists():
        return []
    try:
        text = chain.INTENT_PROFILE.read_text(encoding="utf-8-sig")
    except OSError:
        return []
    fm = chain.FRONTMATTER_RE.search(text)
    body = fm.group(1) if fm else text
    m = _INTENT_PROJECT_TYPE_PATTERN.search(body)
    if not m or m.group(1).strip().strip('"\'') != "greenfield":
        return []
    errors: list[str] = []
    for lm in _INTENT_LOCKED_IN_PATTERN.finditer(body):
        inner = lm.group(1).strip()
        if not inner:
            continue
        items = [p.strip() for p in inner.split(",") if p.strip()]
        if items:
            errors.append(
                f"intent_profile.md project_type=greenfield + constraints.tech_stack.locked_in={items} "
                f"— 모순 (C15-4, schema §8 cross-field)"
            )
            break
    return errors


# W7 doctrine — meta.grilling_log[] enum 강제 (sub-cycle β 흡수, 2026-05-25).
_GRILLING_VALID_PHASES = ("0.5", "2", "5", "9")
_GRILLING_VALID_SOURCES = ("signals>=2", "section_3_1_direct", "section_3_2_estimate")
_GRILLING_REQUIRED_KEYS = ("phase", "field", "mode", "recommended", "recommended_source", "user_response")


def _extract_grilling_log_block(yaml_body: str) -> str | None:
    lines = yaml_body.splitlines()
    in_meta = False
    meta_indent = -1
    log_indent = -1
    in_log = False
    collected: list[str] = []
    for raw in lines:
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            if in_log:
                collected.append(raw)
            continue
        indent = len(line) - len(stripped)
        if not in_meta:
            if stripped.startswith("meta:") and indent == 0:
                in_meta = True
                meta_indent = indent
            continue
        if in_meta and not in_log:
            if indent <= meta_indent:
                return None
            if stripped.startswith("grilling_log:"):
                in_log = True
                log_indent = indent
            continue
        if in_log:
            if stripped.startswith("- ") and indent == log_indent:
                collected.append(raw)
                continue
            if indent <= log_indent and stripped:
                break
            collected.append(raw)
    return "\n".join(collected) if collected else None


def _parse_grilling_entries(block: str) -> list[dict[str, str]]:
    strip_quotes = chain._strip_quotes
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    key_value_re = re.compile(r"^([A-Za-z_]+)\s*:\s*(.*?)\s*$")
    for raw in block.splitlines():
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if current is not None:
                entries.append(current)
            current = {}
            body = stripped[2:].strip()
            m = key_value_re.match(body)
            if m:
                current[m.group(1)] = strip_quotes(m.group(2))
            continue
        if current is None:
            continue
        m = key_value_re.match(stripped)
        if m:
            current[m.group(1)] = strip_quotes(m.group(2))
    if current is not None:
        entries.append(current)
    return entries


def check_intent_profile_grilling_log() -> list[str]:
    """meta.grilling_log[] doctrine 검증 (Phase B, 2026-05-19, grill-me 흡수).

    intent_profile.md frontmatter의 meta.grilling_log 박제 항목별로:
      - 필수 키 6개 (phase/field/mode/recommended/recommended_source/user_response) 존재
      - phase ∈ {"0.5","2","5","9"}, mode == "grilling"
      - recommended_source ∈ {"signals>=2","section_3_1_direct","section_3_2_estimate"}
        (디렉토리·파일 이름 단독 추천 — anti-premature-judgment doctrine 위반 차단)

    intent_profile.md 또는 meta.grilling_log 미박제 시 silent skip (옵션 필드).
    """
    errors: list[str] = []
    if not chain.INTENT_PROFILE.exists():
        return errors
    try:
        text = chain.INTENT_PROFILE.read_text(encoding="utf-8-sig")
    except OSError:
        return errors

    fm = chain.FRONTMATTER_RE.search(text)
    body = fm.group(1) if fm else text

    log_block = _extract_grilling_log_block(body)
    if log_block is None:
        return errors

    entries = _parse_grilling_entries(log_block)
    for idx, entry in enumerate(entries):
        missing = [k for k in _GRILLING_REQUIRED_KEYS if k not in entry]
        if missing:
            errors.append(
                f"intent_profile.md meta.grilling_log[{idx}]: 필수 키 누락 {missing} — grilling-loop.md §8 위반"
            )
            continue
        if entry["phase"] not in _GRILLING_VALID_PHASES:
            errors.append(
                f"intent_profile.md meta.grilling_log[{idx}].phase = `{entry['phase']}` 허용값 {_GRILLING_VALID_PHASES} 외"
            )
        if entry["mode"] != "grilling":
            errors.append(
                f"intent_profile.md meta.grilling_log[{idx}].mode = `{entry['mode']}` — 'grilling' 고정값"
            )
        if entry["recommended_source"] not in _GRILLING_VALID_SOURCES:
            errors.append(
                f"intent_profile.md meta.grilling_log[{idx}].recommended_source = `{entry['recommended_source']}` "
                f"— anti-premature-judgment doctrine 위반. 허용값 {_GRILLING_VALID_SOURCES}"
            )
    return errors
