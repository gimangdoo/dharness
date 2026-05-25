"""chain_advisor.py — W8 methodology-advisor handoff adapter 결정적 검증 (chain.py 분할, 2026-05-25 sub-cycle γ).

박제 doctrine:
  - W8 (methodology-advisor 위임 + adapter 변환) — advisor handoff merge 후
    intent_profile.md 5 cross-field 룰 + methodology/source enum 결정적 검증.

본 모듈은 단독 entry-point가 아니다 — chain.py가 import 후 main() chain에서 호출.
chain.INTENT_PROFILE / chain.FRONTMATTER_RE / chain._strip_quotes는 runtime lookup으로
circular import 안전.
"""

from __future__ import annotations

import re
import sys


class _ChainProxy:
    def __getattr__(self, name: str):
        mod = sys.modules.get("chain") or sys.modules["__main__"]
        return getattr(mod, name)


chain = _ChainProxy()


_METHODOLOGY_ENUM = {
    "tdd", "bdd", "ddd", "spec-driven", "trunk-based",
    "kanban", "scrum", "shape-up", "xp", "none", "unknown",
}
_METHODOLOGY_SOURCE_ENUM = {"advisor", "user", "inferred", "none"}


def _strip_inline_comment(val: str) -> str:
    """YAML inline 주석(` #` 또는 `\\t#`) 제거. quoted scalar 내부 `#`은 보존."""
    v = val.strip()
    if not v:
        return v
    if v[0] in ('"', "'"):
        quote = v[0]
        end = v.find(quote, 1)
        if end != -1:
            return v[: end + 1]
        return v
    m = re.search(r"\s+#", v)
    if m:
        return v[: m.start()].rstrip()
    return v


def _extract_section_scalar(yaml_body: str, section: str, key: str) -> str | None:
    """frontmatter 본문에서 `section.key` scalar 값 추출. inline·indented 양쪽 지원.

    반환:
      None  — section 또는 key 박제 미존재
      str   — scalar 값 (quotes·inline 주석 제거). 빈 string 가능.
    """
    in_section = False
    section_indent = -1
    for raw in yaml_body.splitlines():
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        if not in_section:
            if stripped.startswith(f"{section}:") and indent == 0:
                in_section = True
                section_indent = indent
            continue
        if indent <= section_indent:
            return None
        m = re.match(rf"^{re.escape(key)}\s*:\s*(.*)$", stripped)
        if m:
            val = _strip_inline_comment(m.group(1))
            if val and not val.startswith("["):
                return chain._strip_quotes(val)
            return None
    return None


def _extract_section_list(yaml_body: str, section: str, key: str) -> list[str] | None:
    """frontmatter 본문에서 `section.key` list 값 추출. inline·dash 양쪽 지원.

    반환:
      None  — section 또는 key 박제 미존재
      list  — 박제 list (빈 list 포함). 원소 string.
    """
    strip_quotes = chain._strip_quotes
    in_section = False
    section_indent = -1
    in_list = False
    list_indent = -1
    items: list[str] = []
    for raw in yaml_body.splitlines():
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        if not in_section:
            if stripped.startswith(f"{section}:") and indent == 0:
                in_section = True
                section_indent = indent
            continue
        if not in_list:
            if indent <= section_indent:
                return None
            m = re.match(rf"^{re.escape(key)}\s*:\s*(.*)$", stripped)
            if m:
                inline = _strip_inline_comment(m.group(1))
                if inline.startswith("["):
                    body_in = inline.strip().lstrip("[").rstrip("]")
                    return [strip_quotes(t.strip()) for t in body_in.split(",") if t.strip()]
                if inline:
                    return []
                in_list = True
                list_indent = indent
            continue
        if in_list:
            if stripped.startswith("- ") and indent > list_indent:
                items.append(strip_quotes(_strip_inline_comment(stripped[2:])))
                continue
            if indent <= list_indent and stripped:
                break
    return items if in_list else None


def check_advisor_handoff_adapter_consistency() -> list[str]:
    """W8 v0.12.1 adapter doctrine — advisor handoff merge 후 intent_profile.md 정합 검증.

    검증 룰 (intent-profile-schema.md §8, 5건):
      1. methodology_source=advisor + methodology_matrix_row=null/미박제 → 모순
      2. methodology_source≠advisor + methodology_matrix_row 박제 → 모순
      3. methodology_source=advisor + meta.advisor_handoff_version 미박제 → 모순 (재현성 손실)
      4. meta.advisor_secondary_methodologies non-empty + methodology_source≠advisor → 모순
      5. methodology_source=advisor + methodology non-enum-or-non-lowercase → 모순 (adapter 변환 누락)
    추가: methodology 값 ∈ dharness enum 11 (또는 "unknown"), methodology_source ∈ enum 4.

    intent_profile.md 미존재 또는 workflow.methodology·methodology_source 양쪽 모두 미박제 시
    silent skip (Phase 2 미진입 또는 advisor 영역 미합성 — 검증 대상 아님).
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

    methodology = _extract_section_scalar(body, "workflow", "methodology")
    source = _extract_section_scalar(body, "workflow", "methodology_source")
    matrix_row = _extract_section_scalar(body, "workflow", "methodology_matrix_row")
    handoff_version = _extract_section_scalar(body, "meta", "advisor_handoff_version")
    secondary = _extract_section_list(body, "meta", "advisor_secondary_methodologies") or []

    if source is None and methodology is None:
        return errors

    matrix_present = matrix_row is not None and matrix_row.lower() != "null"

    if methodology is not None and methodology not in _METHODOLOGY_ENUM:
        errors.append(
            f"intent_profile.md workflow.methodology=`{methodology}` — "
            f"dharness enum 11 외 (W8 adapter doctrine, intent-profile-schema.md §2)"
        )

    if source is not None and source not in _METHODOLOGY_SOURCE_ENUM:
        errors.append(
            f"intent_profile.md workflow.methodology_source=`{source}` — "
            f"enum 4(advisor/user/inferred/none) 외 (W8 adapter doctrine)"
        )

    if source == "advisor" and not matrix_present:
        errors.append(
            "intent_profile.md workflow.methodology_source=advisor + "
            "methodology_matrix_row 미박제 — §8 cross-field 룰 위반 (W8)"
        )

    if source not in (None, "advisor") and matrix_present:
        errors.append(
            f"intent_profile.md workflow.methodology_source=`{source}` + "
            f"methodology_matrix_row=`{matrix_row}` — 비-advisor source는 "
            "matrix_row 보유 금지 (W8 §8 cross-field 룰)"
        )

    if source == "advisor" and not handoff_version:
        errors.append(
            "intent_profile.md workflow.methodology_source=advisor + "
            "meta.advisor_handoff_version 미박제 — v0.12.1 adapter 룰 위반 "
            "(원본 source string 손실, 재현성 ↓, W8)"
        )

    if secondary and source != "advisor":
        errors.append(
            f"intent_profile.md meta.advisor_secondary_methodologies non-empty + "
            f"workflow.methodology_source=`{source or 'none'}` — secondary list는 "
            "advisor source 시만 박제 (v0.12.1 adapter 룰, W8)"
        )

    if source == "advisor" and methodology:
        if methodology != methodology.lower():
            errors.append(
                f"intent_profile.md workflow.methodology=`{methodology}` "
                f"(source=advisor) — lowercase 정규화 누락 "
                "(v0.12.1 adapter 변환 step 3 미실행, W8)"
            )

    return errors
