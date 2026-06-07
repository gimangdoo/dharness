# Dogfood E2E Verification — wiki bridge 실 송수신 round-trip (P5)

**날짜:** 2026-06-03
**대상:** `scripts/wiki/bridge.py` (emit_candidate / pull_promoted / dedup / telemetry)
**모드:** runnable e2e — mock wiki(tmpdir) 대상 실 I/O 실행. 실 wiki repo 미변경.
**스크립트:** [`run_e2e.py`](./run_e2e.py) — `py -3 _workspace/_dogfood/2026-06-03_wiki_bridge_e2e/run_e2e.py`

---

## 1. 배경

P4까지 wiki 다리는 계약(`wiki-bridge.md`)+게이트(`chain.py:check_wiki_candidate_schema`)+fixture만 박제 — 실 송수신 I/O는 SKILL 7-7/5-0 산문 지시뿐(코드 0). P5가 이를 `bridge.py` 헬퍼로 박제. 본 e2e는 round-trip(Emit → schema → promotion → Feedback pull → presence-gate skip)이 실제 도는지 실증.

## 2. 체크 결과 (6/6 PASS)

| # | 체크 | milestone | 결과 |
|---|---|---|---|
| ① | candidates/ 부재 시 emit no-op + `wiki_bridge_skipped{reason:target-absent}` | presence-gate | ✅ |
| ② | candidates/ 존재 시 `<slug>-v1/` 3파일(SKILL.md/eval-results.json/changelog.md) 박제 | M1 Emit | ✅ |
| ③ | emit 산출물이 M5 contract(`_validate_candidate_dir`) 통과 | M5 gate | ✅ |
| ④ | 3 tier PASS + `promotion.verdict` 주입 → `pull_promoted` 반환 | M4 Feedback | ✅ |
| ⑤ | verdict None → pull 제외 (미승격 재사용 강제 아님) | M4 필터 | ✅ |
| ⑥ | `wiki_bridge_emit`·`wiki_bridge_skipped`·`wiki_bridge_pull` telemetry 전부 박제 | observability | ✅ |

## 3. 안전 확인

- **실 wiki repo write 0** — 전 I/O가 `tempfile.TemporaryDirectory()` 안. raw/ 미변경.
- **자가검증 롤백** — cross-field 불일치 candidate는 write 후 자가검증 FAIL 시 생성분 제거 (별도 단위 `test_bridge.py:test_invalid_rollback` 커버).
- **dedup advisory** — overlap≥임계는 `soft_block` 반환(hard-block 아님), I/O 0 (`test_dedup_soft_block`).
- **사용자 gate 유지** — 헬퍼는 gate *후* 호출되는 기계적 I/O. 승인 판단은 LLM 레이어.

## 4. 회귀

`scripts/wiki/test_bridge.py` 9/9 PASS · `chain.py` PASS · `test_chain` 170 · smoke 8/8. `chain.py:check_wiki_candidate_schema`(S18 validator) 불변.

## 5. 결론

P4 "계약만, 실행 산문" → P5 "실행 헬퍼 + observability + e2e 실증" 종결. 자동 round-trip 동작 확인. 남은 outward-facing 안전장치(사용자 gate)는 설계상 유지 — 자동화 ≠ gate 제거.
