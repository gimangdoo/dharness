"""chain_intent.py — intent_profile.md §8 W9 결정적 검증 (chain.py 분할, 2026-05-25 cycle 6+ MVP).

W9 doctrine — C14/C15 7 finding 중 deterministic 4종 (cycle 4 hybrid 합성 결정):
  - check_intent_profile_version (C14-1)
  - check_intent_profile_project_type (C14-2, enum {greenfield, brownfield})
  - check_intent_profile_brownfield_inferred (C14-3)
  - check_intent_profile_greenfield_locked_in (C15-4 모순 invariant)

본 모듈은 단독 entry-point가 아니다 — chain.py가 import 후 main() chain에서 호출.
chain.INTENT_PROFILE / chain.FRONTMATTER_RE는 runtime에 lookup하므로 모듈 import 시점
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
