"""_chain_proxy.py — chain.py runtime lookup proxy 단일 정본 (PV8, 2026-05-27).

분할된 chain_*.py 5 모듈에서 chain.* 속성 lookup 시 circular import 방지를 위한
runtime lookup proxy. 5 모듈 각자 copy로 박제됐던 중복을 본 파일 1정본으로 통합.

본 모듈은 단독 entry-point가 아니다 — chain.py 또는 chain_*.py가 import.
"""

from __future__ import annotations

import sys


class _ChainProxy:
    def __getattr__(self, name: str):
        mod = sys.modules.get("chain") or sys.modules["__main__"]
        return getattr(mod, name)


chain = _ChainProxy()
