---
description: 진행 중 하네스에 신규 기능 요구를 흡수 — 해당 기능을 grilling으로 추궁해 의도를 확정하고, intent_profile.md(scope·vision 등)에 수정/추가한다 (profile 확장, 전체 재구축 아님).
argument-hint: <추가하려는 기능 한 문장>
allowed-tools: Read, Glob, Grep, Write, Edit
---

# Harness — Feature (신규 기능 의도 흡수)

이미 구축된 하네스에 사용자가 *진행 중 새 기능*을 요구할 때, 그 기능에 대해 grilling으로 의도를 추궁하고 `_workspace/_baseline/intent_profile.md`에 반영한다. **`harness-new`와 유사하나 전체 재구축이 아니라 baseline profile 확장 범위** — 에이전트/스킬 구조 변경은 하지 않고, 의도(scope·vision·constraints)만 갱신한다.

> **profile 확장 doctrine (2026-05-30):** 신규 기능 요구는 두 레이어로 갈린다 — (1) *의도 레이어* (이 기능이 무엇이고 왜 필요한가 → intent_profile) 와 (2) *구조 레이어* (이 기능을 위해 에이전트/스킬을 추가·수정해야 하는가 → agents/skills). 본 명령은 **(1) 의도 레이어만** 담당한다. 구조 변경이 필요하다고 판단되면 본 명령은 그 변경안을 *식별·보고*만 하고, 적용은 `/harness:harness-evolve`로 인계한다. `harness-new`(전체 구축) ↔ `harness-feature`(의도 확장) ↔ `harness-evolve`(구조 변경)의 3단 분리.

## 컨텍스트

- **인자**: `$ARGUMENTS` (추가 기능 한 문장; 예: "결제 환불 흐름 추가", "관리자 대시보드에 매출 차트")
- **입력**: `$ARGUMENTS` + 기존 `_workspace/_baseline/intent_profile.md` + `_workspace/_baseline/project_profile.md` + (코드 grounded 추론용) 프로젝트 코드
- **출력**: 갱신된 `intent_profile.md` (scope/vision/constraints 등 + `meta.user_confirmed_fields`·`meta.grilling_log[]`) + `_workspace/_baseline/changelog.md` 변경 이력 한 행

## 선조건 검증

1. `.claude/agents/`에 에이전트가 1개 이상 있는가? (= 하네스 존재)
2. `_workspace/_baseline/intent_profile.md`가 존재하는가? (= baseline 존재)

**미충족 시:**

| 항목 | 안내 |
|---|---|
| (1) 또는 (2) 부재 | "구축된 하네스/baseline이 없습니다. 신규 기능이 아니라 신규 구축입니다 — `/harness:harness-new <도메인>`을 먼저 호출하세요." 후 중단 |
| `$ARGUMENTS` 비어있음 | "추가할 기능을 인자로 제공하세요: `/harness:harness-feature <기능 한 문장>`" |

## 실행 절차

### 1. 기능 위치 추론 (anti-premature-judgment 정합)

`$ARGUMENTS`의 기능이 기존 intent_profile의 어느 섹션에 들어가는지 *후보*를 제시한다 (단정 금지 — SKILL.md Phase 0.5 doctrine). 주 후보:

| 기능 성격 | intent_profile 반영 위치 |
|---|---|
| MVP 핵심 추가 기능 | `scope.must_have[]` append |
| 명시적 범위 제외였다가 편입 | `scope.out_of_scope[]`에서 제거 + `scope.must_have[]`로 이동 |
| 새 사용자 그룹/가치 | `vision.target_users[]` / `vision.success_definition` 보강 |
| 새 기술·제약 동반 | `constraints.tech_stack.preferred[]` / `constraints.compliance` 보강 |
| 새 배포 표면 | `architecture.deployment_target[]` 추가 |

코드 grounded 추론 가능 시(brownfield) `project_profile.md` signals로 추천값 1순위 후보를 제시한다.

### 2. Grilling — 기능 의도 추궁 (`references/grilling-loop.md` 패턴)

`references/grilling-loop.md`의 1q + recommended answer + skip merge 패턴을 명시 호출한다 (`/harness:harness-grill feedback`과 동일 엔진, 본 명령 내 명시 분기 — 자율 진입 없음). 기능 1건당 추궁 축:

1. **무엇** — 기능의 구체 동작 범위 (recommended: `$ARGUMENTS` + 코드 signal 기반 후보)
2. **왜** — 기존 `vision.success_definition`과의 연결 (이 기능이 어떤 성공 지표를 움직이나)
3. **범위 경계** — 이번 범위(must_have) vs 차후(out_of_scope) 분리
4. **제약** — 새 기술/규제/배포 표면 동반 여부

Cap·skip·"코드 봐" fallback은 `grilling-loop.md` §5·§6·§4 그대로. 단일 세션 ≤5 question.

### 3. intent_profile 갱신 (승인 게이트)

추궁으로 확정된 값을 intent_profile.md에 *반영안*으로 제시하고 사용자 승인 후 박제. **자동 적용 0.**

- **frontmatter merge**: §1에서 정한 섹션에 값 append/이동. `intent-profile-schema.md` 형식 준수 (enum·list).
- **inferred vs user_confirmed 박제**:
  - 사용자가 grilling에서 직접 confirm한 필드 → `meta.user_confirmed_fields[]`에 dot-path 추가
  - 코드 추론만 되고 미확인 → `meta.inferred_fields[]` + `meta.source{}`에 출처 인용 (S7 doctrine, 인용 0이면 schema 위반)
  - 스킵/미결 → `meta.open_questions[]`에 "(harness-feature 기능 추가 — 미결)" 등록
- **grilling_log 박제**: question별 `meta.grilling_log[]` entry (`grilling-loop.md` §8 형식, `phase: "9"`).
- **schema 불변식 유지**: INTENT_REQUIRED 6필드는 *건드리지 않는다* (이미 충족 상태). 신규 기능이 필수 필드(예: `architecture.deployment_target`) 값을 *추가*하면 해당 dot-path를 `user_confirmed_fields`에 유지.

### 4. 구조 변경 필요성 식별 → evolve 인계 (보고만)

확정된 기능이 기존 에이전트/스킬로 처리 불가하다고 판단되면 (예: "보안 검토가 필요한데 담당 에이전트 없음"), **구조 변경안을 식별해 보고만** 한다. 적용은 본 명령 범위 밖:

```
ℹ️ 이 기능은 구조 변경을 동반할 수 있습니다:
   - {예: 보안 검토 에이전트 부재 → 추가 권고}
   적용: /harness:harness-evolve "{식별된 변경 한 문장}"
```

구조 변경 여부 판단은 기존 `.claude/agents/` 역할 본문 ↔ 신규 기능 요구 매칭으로 추론한다 (LLM, read-only). 본 명령은 agents/skills 파일을 *수정하지 않는다*.

### 5. 변경 이력 갱신 (`_workspace/_baseline/changelog.md`)

출처를 명시해 Phase 9 진화와 구분 가능하게:

```
| {YYYY-MM-DD} | Phase 9: 신규 기능 의도 흡수 — {기능 요약} (cmd: harness-feature) | intent_profile.md | {사유: 반영 섹션 + confirmed/inferred} |
```

## 범위 외

- **구조 변경 0** — 에이전트/스킬/오케스트레이터 정의 미수정. 모두 `/harness:harness-evolve`.
- **전체 재구축 0** — Phase 1~8 재실행 아님. baseline 전면 갱신은 `/harness:harness-evolve "baseline 갱신"`(baseline op).
- **자동 적용 0** — intent_profile 갱신은 사용자 승인 게이트 후만.

## 완료 후 검증

intent_profile 갱신 후 `py plugins/harness/scripts/validate/chain.py --only check_intent_profile_grilling_log,check_required_user_confirmed_fields,check_intent_profile_version` 자동 실행 — grilling_log enum·필수 필드·version 정합 회귀 확인.

## 관련

- grilling 패턴 본체: `plugins/harness/skills/harness/references/grilling-loop.md`
- intent_profile 형식: `references/intent-profile-schema.md`
- 구조 변경 인계처: `/harness:harness-evolve` (통합 변경 front door)
- 신규 전체 구축: `/harness:harness-new`
