# Architecture Profile — dharness self-host

> **baseline 스냅샷** (2026-06-07, 묶음 C). 선언된 모듈 경계 기준선 — arch review L11-1 해소.
> 향후 L11(coupling) 리뷰가 best-effort 절대관측이 아닌 본 contract 대비 diff로 동작.
> validator 미연동 (free-form snapshot).

## 1. 최상위 경계 — 2 구성요소

| 구성요소 | 경로 | 배포 | 경계 규칙 |
|---|---|---|---|
| **harness plugin** | `plugins/harness/` | 외부 install 대상 | self-host(`.claude/`·`_workspace/`) 참조 금지. derived 런타임에 CM 주입 0. |
| **Context Manager** | root `.claude/` + `_workspace/` | dharness 본 폴더 한정 | harness plugin 내부 모듈 import 금지. 외부 install 미지원. |

## 2. harness plugin 내부 layering

| 레이어 | 경로 | 시점 | 의존 방향 |
|---|---|---|---|
| 검증 (validate) | `scripts/validate/` | dev-time | `schema.py`(shared) → 단방향. wiki 참조 금지. |
| wiki bridge | `scripts/wiki/` | self-host runtime | `schema.py:validate_candidate_contract` 공유. validate chain 역참조 금지. |
| shared contract | `scripts/validate/schema.py` | 양시점 | 최하위 — 누구도 역의존 안 받음. REPO_ROOT 마커 walk-up 단일화. |

### chain.py dispatcher 패턴
`chain.py` = dispatcher 전용 (main entry + import re-export). 도메인별 검증 fn은 6 sub-module 분리:
`chain_intent` / `chain_advisor` / `chain_doc_sync` / `chain_version` / `chain_registry` (+ `_chain_proxy` lazy lookup).
신규 검증 fn은 도메인 적합 sub-module 또는 신규 sub-module — chain.py 직접 추가 금지(god-module drift 차단, L11-6 관찰).

## 3. Context Manager 내부 경계

| 모듈 | 경로 | 역할 | 경계 |
|---|---|---|---|
| event hooks | `.claude/hooks/{session_start,post_tool_use,session_end}.py` | 결정적 capture/분류/적재 | LLM 호출 0. host 세션 깨뜨림 금지(예외 swallow). |
| helpers | `.claude/hooks/{_schema,_transcript_utils,cm_commands}.py` | DB·transcript·command 백엔드 | event hook이 import. 단방향. |
| 영속 | `_workspace/_memory/` (sqlite) + `_workspace/_telemetry/*.jsonl` | observations·tool 출력·telemetry | hooks만 write. |

## 4. 계약 단일 출처 (fork 금지)
- candidate contract 검증 = `schema.py:validate_candidate_contract` (chain.py·bridge.py 공유)
- REPO_ROOT = `schema.py` 마커(`.claude-plugin/marketplace.json`) walk-up
- doctrine ID = `doctrine-registry.md` (chain_registry.py 역인덱스 검증)
- INTENT_REQUIRED = `schema.py:INTENT_REQUIRED` (doc sync = chain_intent)
