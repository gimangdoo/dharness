---
description: grilling 모드 명시 진입점 — 1q-at-a-time + LLM recommended answer로 Phase 0.5/2/5/9-1의 모호 답안 확정. mattpocock grill-me 흡수 (2026-05-19, Phase C).
argument-hint: "<phase> [field]"
---

# Harness — Grilling Mode 진입

`references/grilling-loop.md` 1q + recommended answer + branch tree walk + codebase exploration fallback 패턴을 명시 호출. batch 표 출력 대신 순차 1q로 사용자 답변 거부율 ↓, doctrine 박제 강도 ↑.

## 인자

| 인자 | 값 | 설명 |
|---|---|---|
| `<phase>` | `0.5` / `2` / `5` / `9` | grilling 진입 phase. 4 phase만 허용 (`grilling-loop.md` §7). |
| `[field]` (옵션) | dot-path 또는 cardinality slug | 특정 필드/후보 한정 grilling. 미지정 시 phase 진입 조건 매칭 항목 전체. |

예시:
- `/harness:harness-grill 2 constraints.team.size` — 필수 5필드 1개 grilling
- `/harness:harness-grill 0.5` — Phase 0.5 4항목 검사 empty 항목 grilling
- `/harness:harness-grill 5` — Phase 5 cardinality 모호 후보 grilling
- `/harness:harness-grill 9` — Phase 9-1 피드백 어휘 모호 grilling

## 선조건

| Phase | 필요 산출물 |
|---|---|
| `0.5` | `$ARGUMENTS` (도메인 한 문장) — 명시 거부 시 hard fail |
| `2` | `_workspace/_baseline/project_profile.md` 존재 (Phase 1 완료) |
| `5` | Phase 4 팀 패턴 결정 완료 + cardinality 표 임시 산출 |
| `9` | 사용자 피드백 raw 발화 1건 이상 |

미충족 시: "Phase {N} grilling 진입 불가 — 선행 산출물 {경로} 부재" 메시지 + hard fail.

## 실행 절차

1. **진입 조건 검증** — phase별 선조건 검사 (위 표). 미충족 시 hard fail.
2. **대상 항목 수집**:
   - phase=0.5: `$ARGUMENTS` 4항목 (작업 유형/입력 source/출력 target/사용자 숙련도) 중 empty 항목
   - phase=2: `intent_profile.md` 미존재 시 brownfield 단계 1·2 진행 — `meta.confidence_low` 항목 + 필수 5필드 미답 항목
   - phase=5: cardinality 표에서 `inline 대안 검토 = 모호` 후보
   - phase=9: 사용자 피드백 어휘 모호 분류 — §9-2 표 5행 중 어느 진화 대상인지
3. **Cap 적용** — 대상 항목 >5 시 우선순위 룰(`grilling-loop.md` §5) 후 상위 5개만 grilling, 나머지 batch fallback.
4. **Grilling Loop** — 항목별 순차 1q:
   - 표시 형태: `{필드}: ? / recommended: {값} / 근거: {source} / → 맞음 / 수정 / 모르겠음 / 코드 봐`
   - recommendation 출처는 `project_profile.md` signals ≥2 또는 §3-1 직접 매핑만 허용 (anti-premature-judgment doctrine)
   - "코드 봐" 응답 시 §3 자동 추론 재실행 (1회 한정 loop)
5. **박제** — 항목별 `meta.grilling_log[]` entry 추가 (`grilling-loop.md` §8 형식). phase=5의 경우 cardinality 표 결정 + 박제만, intent_profile 미수정.
6. **종료 조건** — 모든 대상 처리 완료 OR cap 도달 OR 사용자 "모르겠음" 연속 ≥3 OR hard fail.
7. **검증** — 종료 후 `py plugins/harness/scripts/validate/chain.py` 자동 실행. `check_intent_profile_grilling_log` 회로가 박제 entry 정합 검증.

## 박제 산출물

phase=2 / phase=9 — `intent_profile.md` `meta.grilling_log[]` append.
phase=0.5 — `$ARGUMENTS` 4항목 empty 채운 후 본문 Phase 1 직접 진입 (별도 박제 0).
phase=5 — cardinality 표 결정만, 박제는 Phase 5 본문 합성 시 에이전트 정의에 흡수.

## 자동 적용 금지

grilling 결과는 *사용자 confirm된 답안* — 자동으로 다른 산출물(`.claude/agents/`, 오케스트레이터 등)을 수정하지 않는다. 후속 진화는 `/harness:harness-evolve` 명시 호출.

## 관련

- 패턴 본체: `plugins/harness/skills/harness/references/grilling-loop.md`
- Phase 2 진입 조건: `references/project-inquiry.md` §4-4-b
- 검증: `scripts/validate/chain.py check_intent_profile_grilling_log` (Phase B 신설)
