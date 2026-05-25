"""chain_registry.py — R6 doctrine-registry 정합 결정적 검증 (chain.py 분할, 2026-05-25 sub-cycle ζ).

박제 doctrine:
  - R6 (a) doctrine-registry 인용 `<module>.py:<fn>` ↔ 실제 fn 존재 정합
  - R6 (b) §1-5 module 인용 ↔ §6 inverse index 매핑 정합

자기참조 박제 — 본 모듈 자신이 R6를 박제하므로 _DOCTRINE_FN_REF_PATTERN /
_INVERSE_MODULE_ROW_PATTERN alternation에 `chain_registry`도 포함.

본 모듈은 단독 entry-point가 아니다 — chain.py가 import 후 main() chain에서 호출.
chain._strip_code_fences는 runtime lookup으로 circular 회피.
"""

from __future__ import annotations

import re
import sys


class _ChainProxy:
    def __getattr__(self, name: str):
        mod = sys.modules.get("chain") or sys.modules["__main__"]
        return getattr(mod, name)


chain = _ChainProxy()


_DOCTRINE_FN_REF_PATTERN = re.compile(
    r"`(chain|chain_intent|chain_version|chain_doc_sync|chain_advisor|chain_registry|structure|schema)\.py:([A-Za-z_][A-Za-z0-9_]*)`"
)
_DEF_PATTERN = re.compile(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
# 모듈-레벨 UPPERCASE 상수 (e.g. INTENT_REQUIRED) — registry가 fn 외 canonical symbol 인용 시 허용.
_CONST_PATTERN = re.compile(r"^([A-Z_][A-Z0-9_]*)\s*=", re.MULTILINE)


def _collect_module_fns(module_name: str) -> set[str]:
    path = chain._VALIDATE_DIR / f"{module_name}.py"
    if not path.exists():
        return set()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return set()
    return set(_DEF_PATTERN.findall(text)) | set(_CONST_PATTERN.findall(text))


def check_doctrine_registry_fn_refs() -> list[str]:
    """doctrine-registry.md의 `chain.py:<fn>`·`structure.py:<fn>`·`schema.py:<fn>` 인용 ↔
    실제 모듈 def 존재 정합 (R6 doctrine, 2026-05-24).

    drift 영구 차단: registry 인용이 실 fn명과 어긋나면 contributor가 잘못된 경로로
    정합 점검을 시도. registry는 단일 출처 색인이므로 결정적 검증 필수.
    """
    errors: list[str] = []
    registry = chain._DOCTRINE_REGISTRY
    if not registry.exists():
        return errors
    try:
        text = registry.read_text(encoding="utf-8-sig")
    except OSError:
        return errors
    scanned = chain._strip_code_fences(text)
    fn_cache: dict[str, set[str]] = {}
    seen: set[tuple[str, str]] = set()
    for module, fn in _DOCTRINE_FN_REF_PATTERN.findall(scanned):
        key = (module, fn)
        if key in seen:
            continue
        seen.add(key)
        if module not in fn_cache:
            fn_cache[module] = _collect_module_fns(module)
        if fn not in fn_cache[module]:
            errors.append(
                f"doctrine-registry.md: `{module}.py:{fn}` 인용 — 실제 fn 미존재 "
                f"(R6 doctrine drift)"
            )
    return errors


# §6 inverse index row: ``| `<module>.py` | <ids cell> |``
_INVERSE_MODULE_ROW_PATTERN = re.compile(
    r"^\|\s*`(chain|chain_intent|chain_version|chain_doc_sync|chain_advisor|chain_registry|structure|schema)\.py`[^|]*\|\s*([^|]+)\|",
    re.MULTILINE,
)
# §1-5 doctrine row: ``| W1 | ... |`` — capture id + rest of line for module ref scan.
_DOCTRINE_ROW_LINE_PATTERN = re.compile(
    r"^\|\s*((?:W|R|S|P|I)\d+)\s*\|([^\n]*)$",
    re.MULTILINE,
)
_DOCTRINE_ID_TOKEN_PATTERN = re.compile(r"\b((?:W|R|S|P|I)\d+)\b")


def check_doctrine_registry_inverse_index() -> list[str]:
    """doctrine-registry.md §6 역색인 ↔ §1-5 doctrine id 매핑 정합 (R6 확장, 2026-05-24).

    §1-5 row가 `chain.py:<fn>` / `structure.py:<fn>` / `schema.py:<fn>`를 인용하면
    §6 inverse index의 해당 module 행에도 그 doctrine id가 등재돼 있어야 한다.
    contributor가 §6 색인 read만으로 doctrine ↔ module 매핑을 추적하므로 drift 차단.
    """
    errors: list[str] = []
    registry = chain._DOCTRINE_REGISTRY
    if not registry.exists():
        return errors
    try:
        text = registry.read_text(encoding="utf-8-sig")
    except OSError:
        return errors
    scanned = chain._strip_code_fences(text)

    inverse: dict[str, set[str]] = {}
    for module, ids_cell in _INVERSE_MODULE_ROW_PATTERN.findall(scanned):
        ids = set(_DOCTRINE_ID_TOKEN_PATTERN.findall(ids_cell))
        inverse.setdefault(module, set()).update(ids)

    reported: set[tuple[str, str]] = set()
    for match in _DOCTRINE_ROW_LINE_PATTERN.finditer(scanned):
        doctrine_id = match.group(1)
        row_body = match.group(2)
        for module, _fn in _DOCTRINE_FN_REF_PATTERN.findall(row_body):
            key = (doctrine_id, module)
            if key in reported:
                continue
            if module not in inverse:
                reported.add(key)
                errors.append(
                    f"doctrine-registry.md: §1-5 {doctrine_id} → `{module}.py:` "
                    f"인용 — §6 inverse index에 `{module}.py` 행 부재 (R6 확장)"
                )
                continue
            if doctrine_id not in inverse[module]:
                reported.add(key)
                errors.append(
                    f"doctrine-registry.md: §1-5 {doctrine_id} → `{module}.py:` "
                    f"인용 — §6 `{module}.py` 행에 {doctrine_id} 미등재 (R6 확장)"
                )
    return errors
