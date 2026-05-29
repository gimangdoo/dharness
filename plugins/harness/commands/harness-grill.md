---
description: 추궁(grilling) 모드 진입 — 모호 답안을 한 문항씩 추천 답 제시 후 사용자 확정 (4 step 진입점).
argument-hint: "<domain|inquiry|agents|feedback> [필드명 옵션]"
allowed-tools: Read
---

# Harness — Grilling Mode 진입

`references/grilling-loop.md` 1q + recommended answer + branch tree walk + codebase exploration fallback 패턴을 명시 호출. batch 표 출력 대신 순차 1q로 사용자 답변 거부율 ↓, doctrine 박제 강도 ↑.

## 인자

| 인자 | 값 | 설명 |
|---|---|---|
| `<step>` | `domain` / `inquiry` / `agents` / `feedback` | grilling 진입 step. 4 enum만 허용. |
| `[field]` (옵션) | dot-path 또는 cardinality slug | 특정 필드/후보 한정 grilling. 미지정 시 step 진입 조건 매칭 항목 전체. |

### step → phase 매핑

| step | phase | grilling 대상 |
|---|---|---|
| `domain` | 0.5 | `$ARGUMENTS` 4항목 (작업 유형/입력 source/출력 target/사용자 숙련도) empty 항목 |
| `inquiry` | 2 | `intent_profile.md` Low confidence 항목 + 필수 5필드 미답 |
| `agents` | 5 | cardinality 표 모호 후보 (inline vs agent 결정) |
| `feedback` | 9 | 사용자 피드백 어휘 모호 진화 대상 |

예시:
- `/harness:harness-grill inquiry constraints.team.size` — 필수 5필드 1개 grilling
- `/harness:harness-grill domain` — `$ARGUMENTS` 4항목 검사 empty 항목 grilling
- `/harness:harness-grill agents` — cardinality 모호 후보 grilling
- `/harness:harness-grill feedback` — 피드백 어휘 모호 grilling

> **legacy**: 기존 phase 번호 form (`0.5` / `2` / `5` / `9`)도 advanced 옵션으로 그대로 수신 — `references/grilling-loop.md` §7 dot-path 사용처와 정합 유지.

## 선조건

| step | 필요 산출물 |
|---|---|
| `domain` | *상위 `/harness:harness-new` 흐름의* `$ARGUMENTS` (도메인 한 문장) — 본 slash command 자체의 `$ARGUMENTS`가 아니라 부모 호출의 도메인 문장 참조 (SKILL.md Phase 0.5). 단독 호출 시 도메인 문장 누락이면 hard fail |
| `inquiry` | `_workspace/_baseline/project_profile.md` 존재 (Phase 1 완료) |
| `agents` | Phase 4 팀 패턴 결정 완료 + cardinality 표 임시 산출 |
| `feedback` | 사용자 피드백 raw 발화 1건 이상 |

미충족 시: "{step} grilling 진입 불가 — 선행 산출물 {경로} 부재" 메시지 + hard fail.

## 실행 절차

1. **진입 조건 검증** — step별 선조건 검사 (위 표). 미충족 시 hard fail.
2. **대상 항목 수집**:
   - `domain`: *상위 `/harness:harness-new` 흐름의* `$ARGUMENTS` 4항목 (작업 유형/입력 source/출력 target/사용자 숙련도) 중 empty 항목 — SKILL.md Phase 0.5 게이트 입력
   - `inquiry`: `intent_profile.md` 미존재 시 brownfield 단계 1·2 진행 — `meta.confidence_low` 항목 + 필수 5필드 미답 항목
   - `agents`: cardinality 표에서 `inline 대안 검토 = 모호` 후보
   - `feedback`: 사용자 피드백 어휘 모호 분류 — §9-2 표 5행 중 어느 진화 대상인지
3. **Cap 적용** — 대상 항목이 step별 cap 초과 시 우선순위 룰(`grilling-loop.md` §5) 후 상위 N개만 grilling, 나머지 batch fallback. cap N은 step별 override:

   | step | cap | 출처 |
   |---|---|---|
   | `domain`   | 5 | `grilling-loop.md` §5 default |
   | `inquiry`  | 5 | `grilling-loop.md` §5 default |
   | `agents`   | 2 | SKILL.md Phase 5 entry gate (모호 후보 cap 2 — 합성 시간 폭증 방지) |
   | `feedback` | 5 | `grilling-loop.md` §5 default |
4. **Grilling Loop** — 항목별 순차 1q:
   - 표시 형태: `{필드}: ? / recommended: {값} / 근거: {source} / → 맞음 / 수정 / 모르겠음 / 코드 봐`
   - recommendation 출처는 `project_profile.md` signals ≥2 또는 §3-1 직접 매핑만 허용 (anti-premature-judgment doctrine)
   - "코드 봐" 응답 시 §3 자동 추론 재실행 (1회 한정 loop)
5. **박제** — 항목별 `meta.grilling_log[]` entry 추가 (`grilling-loop.md` §8 형식). `agents` step의 경우 cardinality 표 결정 + 박제만, intent_profile 미수정.
6. **종료 조건** — 모든 대상 처리 완료 OR cap 도달 OR 사용자 "모르겠음" 연속 ≥3 OR hard fail.
7. **검증** — 종료 후 `py plugins/harness/scripts/validate/chain.py` 자동 실행. `check_intent_profile_grilling_log` 회로가 박제 entry 정합 검증.

## 박제 산출물

`inquiry` / `feedback` — `intent_profile.md` `meta.grilling_log[]` append.
`domain` — `$ARGUMENTS` 4항목 empty 채운 후 본문 Phase 1 직접 진입 (별도 박제 0).
`agents` — cardinality 표 결정만, 박제는 Phase 5 본문 합성 시 에이전트 정의에 흡수.

## 자동 적용 금지

grilling 결과는 *사용자 confirm된 답안* — 자동으로 다른 산출물(`.claude/agents/`, 오케스트레이터 등)을 수정하지 않는다. 후속 진화는 `/harness:harness-evolve` 명시 호출.

## 관련

- 패턴 본체: `plugins/harness/skills/harness/references/grilling-loop.md`
- Phase 2 진입 조건: `references/project-inquiry.md` §4-4-b
- 검증: `scripts/validate/chain.py check_intent_profile_grilling_log` (Phase B 신설)
