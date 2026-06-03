# Runtime Telemetry Schema

> **베이스:** [runtime-adaptation.md](./runtime-adaptation.md) — Phase 10 telemetry 저장 형식·이벤트 타입·공통 규약 분리분 (2026-05-31 doc 분할 #3). Capture/Diagnostic/Adapt 레이어·승인 UX·검증 룰은 베이스 단일 출처.

---

## 목차

1. [저장 형식](#1-저장-형식)
2. [이벤트 타입 표](#2-이벤트-타입-표)
3. [공통 규약](#3-공통-규약)

---

## 1. 저장 형식

`_workspace/_telemetry/{YYYY-MM-DD}.jsonl` — 날짜별 append-only JSONL. 한 줄에 한 이벤트.

```jsonl
{"ts":"2026-05-09T11:30:00Z","type":"harness_invocation","session_id":"a3f","trigger_keyword":"하네스 실행"}
{"ts":"2026-05-09T11:30:12Z","type":"agent_invocation","session_id":"a3f","agent":"qa","duration_s":45,"outcome":"success"}
{"ts":"2026-05-09T11:31:02Z","type":"skill_invocation","session_id":"a3f","skill":"code-review","outcome":"success"}
{"ts":"2026-05-09T11:32:18Z","type":"agent_failure","session_id":"a3f","agent":"qa","error":"timeout","retry_succeeded":true}
{"ts":"2026-05-09T11:35:00Z","type":"project_signal","signal":"new_dependency","value":"trpc@10.45.0","source":"package.json#dependencies"}
{"ts":"2026-05-09T11:35:02Z","type":"user_bypass","expected_skill":"code-review","actual_action":"manual_edit","note":"사용자가 오케스트레이터 호출 없이 직접 수정"}
```

## 2. 이벤트 타입 표

| `type` | 필드 | 캡처 시점 |
|------|------|----------|
| `harness_invocation` | `session_id`, `trigger_keyword` | 하네스 스킬 트리거 직후 |
| `agent_invocation` | `session_id`, `agent`, `duration_s`, `outcome` | 에이전트 실행 종료 직후 |
| `skill_invocation` | `session_id`, `skill`, `outcome` | 스킬 실행 종료 직후 |
| `agent_failure` | `session_id`, `agent`, `error`, `retry_succeeded` | 에이전트 실행 실패 (재시도 결과 포함) |
| `project_signal` | `signal`, `value`, `source` | Capture 시 프로젝트 스캔에서 baseline과 다른 값 발견 시 |
| `user_bypass` | `expected_skill`, `actual_action`, `note` | 오케스트레이터 우회 감지 시 |
| `user_feedback` | `session_id`, `category`, `text` | Phase 9 피드백 수집 시 (Phase 10에서도 활용) |
| `wiki_bridge_emit` | `session_id`, `slug`, `outcome` | M1 Emit 직후 (`scripts/wiki/bridge.py:emit_candidate`) |
| `wiki_bridge_skipped` | `session_id`, `milestone`, `reason` | wiki 다리 skip 시 — `milestone`=`emit`/`pull`, `reason`=`target-absent`/`not-reusable`/`dedup-hit` |
| `wiki_bridge_pull` | `session_id`, `n_promoted` | M4 Feedback 조회 직후 (`scripts/wiki/bridge.py:pull_promoted`) |

`outcome` 값: `success` / `partial` / `failure`. `wiki_bridge_*`는 self-host 전용(P5) — `bridge.py`가 자동 박제하며 wiki 미설정 vs skip 구분 신호를 보장한다(wiki-bridge.md §0).

## 3. 공통 규약

- 모든 이벤트에 `ts` (ISO8601 UTC) 필수
- `session_id`는 한 세션 내 모든 이벤트에 동일 (orchestrator가 발급)
- `value`/`error`는 100자 이내로 truncate (긴 stack trace는 별도 로그)
- 이벤트는 **절대 삭제·수정 금지**. 잘못 캡처된 것도 그대로 두고, 후속 이벤트로 정정
