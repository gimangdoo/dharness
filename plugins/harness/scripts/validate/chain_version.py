"""chain_version.py — I1/I2 doctrine drift refit (chain.py 분할, 2026-05-25 sub-cycle δ).

박제 doctrine:
  - I1 (doctrine drift refit) — plugin doctrine 업그레이드 후 기존 derived harness 끌어올리기
  - I2 (meta.dharness_version anchor) — intent_profile.md frontmatter에 합성 시점 plugin version 박제

본 모듈은 단독 entry-point가 아니다 — chain.py가 import 후 main() chain에서 호출.
chain.INTENT_PROFILE / chain.PLUGIN_JSON_FROM_SCRIPT / chain._extract_frontmatter_block은
runtime에 lookup하므로 모듈 import 시점 circular 안전.
"""

from __future__ import annotations

import json
import re

from _chain_proxy import chain


def _extract_dharness_version_from_baseline() -> str | None:
    if not chain.INTENT_PROFILE.exists():
        return None
    try:
        text = chain.INTENT_PROFILE.read_text(encoding="utf-8-sig")
    except OSError:
        return None
    fm = chain._extract_frontmatter_block(text)
    if not fm:
        return None
    m = re.search(
        r"^\s*dharness_version\s*:\s*['\"]?([^'\"\n]+?)['\"]?\s*$",
        fm,
        re.MULTILINE,
    )
    return m.group(1).strip() if m else None


def _read_current_plugin_version() -> str | None:
    try:
        data = json.loads(chain.PLUGIN_JSON_FROM_SCRIPT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    v = data.get("version") if isinstance(data, dict) else None
    return v if isinstance(v, str) else None


def check_dharness_version_drift() -> dict[str, str | None]:
    """baseline `intent_profile.md` `meta.dharness_version` vs 현 plugin.json `version` 비교.

    schema 위반 아님 (옵션 필드) — *warning/info* 영역. doctrine drift refit 권고 1줄.
    `harness-validate`/`harness-status`가 본 결과를 사용자에게 노출.
    (2026-05-23 doctrine drift refit 인프라.)
    """
    baseline_v = _extract_dharness_version_from_baseline()
    current_v = _read_current_plugin_version()
    if baseline_v is None or current_v is None or baseline_v == current_v:
        return {"baseline": baseline_v, "current": current_v, "message": None}
    msg = (
        f"dharness plugin upgrade 감지 — baseline `{baseline_v}` → 현 `{current_v}`. "
        f"doctrine refit 권고: `/harness:harness-status --deep` + `/harness:harness-validate` "
        f"진단 후 발견 항목별 `/harness:harness-evolve`(내부 add-skill/remove op)로 수정."
    )
    return {"baseline": baseline_v, "current": current_v, "message": msg}
