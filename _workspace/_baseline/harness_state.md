# Harness State — dharness self-host

> **baseline 스냅샷** (2026-06-07, 묶음 C, v0.18.4). 산출물 인벤토리 기준선 — arch review L15-4 해소.
> baseline-drift 검사·adapt/evolve baseline op가 본 스냅샷을 on-disk 참조 상태로 diff.
> validator 미연동 (free-form). 인벤토리 변경 시 본 파일 갱신 → review diff 신호.

## 1. harness plugin 산출물

| 종류 | 수 | 목록 |
|---|---|---|
| skills | 1 | `harness` (skills/harness/SKILL.md) |
| commands | 7 | harness-{new, evolve, adapt, feature, grill, status, validate} |
| agents | 0 | (메타 스킬 팩토리 — orchestrator agent 미정의) |

### validate 모듈 (11, scripts/validate/)
`chain.py`(dispatcher) · `chain_intent` · `chain_advisor` · `chain_doc_sync` · `chain_version` ·
`chain_registry` · `_chain_proxy` · `schema.py`(shared contract) · `structure.py` ·
`lint_doctrine_strings.py` · `smoke_test_doctrine_registry.py`

### wiki 모듈 (1, scripts/wiki/)
`bridge.py` — emit_candidate / pull_promoted / note_skip / _dedup_check (P5, self-host 전용)

## 2. Context Manager 산출물 (self-host 전용)

| 종류 | 수 | 목록 |
|---|---|---|
| event hooks | 3 | session_start (SessionStart) · post_tool_use (PostToolUse) · session_end (SessionEnd) |
| hook helpers | 3 | _schema.py · _transcript_utils.py · cm_commands.py |
| slash commands | 7 | cm-{status, sessions, reset, claudemd-apply, claudemd-discard, prune, reset-adapt-counter} |
| skills | 1 | memory-search (자연어 evolution 이력 검색) |

## 3. 버전 / 정합

| 항목 | 값 |
|---|---|
| plugin version | 0.18.4 (marketplace.json == plugin.json) |
| dharness_version anchor | 0.18.4 (intent_profile.md meta — drift 0) |
| 검증 상태 | chain.py PASS · test_chain PASS · smoke PASS |

## 4. 최근 종결 마일스톤
- P5 wiki bridge 실행 자동화 (PR #1 merged, 2026-06-07)
- 묶음 B: CM agent_failure telemetry 필드 정합 (PR #2 merged, 2026-06-07)
- 묶음 C: baseline 트리오+project_profile materialize (本 스냅샷, 2026-06-07)
