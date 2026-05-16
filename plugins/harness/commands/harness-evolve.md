---
description: 사용자 피드백을 입력으로 Phase 9 수동 진화 실행 — 피드백 유형 → 수정 대상 매핑(9-2 표) → 변경 적용 → 변경 이력 기록. 사용자 발화 진화 진입점.
argument-hint: <피드백 한 문장 또는 단락>
---

# Harness — Evolve (사용자 피드백 진입점)

사용자 피드백을 받아 `plugins/harness/skills/harness/SKILL.md` Phase 9의 수동 진화 워크플로우를 실행한다. Phase 9-2 표에 따라 피드백 유형을 분류하고 적절한 수정 대상을 찾아 변경한다.

## 진화 명령 3분기 doctrine (2026-05-14)

| 명령 | 진입 시점 | 입력 | 특화 워크플로우 |
|---|---|---|---|
| **`/harness:harness-evolve`** | 사용자가 *명시적 피드백* 발화 | 자유 텍스트 | 본 명령 |
| **`/harness:harness-adapt`** | 시스템이 *telemetry drift* 자동 감지 (또는 사용자 명시 점검) | `_workspace/_telemetry/*.jsonl` | Phase 10 |
| **`/harness:harness-remove` / `-split` / `-merge`** | 사용자가 *구조적 변경* 명시 (삭제/분할/통합) | `agent|skill <이름>` | 격리 워크플로우 (자유 텍스트 진단 불필요 — 결정성 ↑) |

**언제 어느 것?**:
- "분석이 너무 피상적" / "팀이 너무 큼" / "보안 검토도 필요" → **evolve** (자유 발화 + LLM 분류)
- "최근 10회 호출에서 X 에이전트 실패율 30%" → **adapt** (telemetry 시그널)
- "X 에이전트 제거" / "Y를 둘로 쪼개" → **remove / split** (격리 워크플로우 + dangling cleanup 결정성)

본 명령이 자유 텍스트 진단 후 *구조적 변경*으로 판단되면 Step 3 변경안 제시 단계에서 격리 명령으로 *위임 안내*.

## 컨텍스트
- **인자**: `$ARGUMENTS` (피드백 한 문장 또는 단락; 예: "분석이 너무 피상적이야", "보안 검토도 필요해", "검증을 먼저 해야 할 것 같아")
- **입력**: `$ARGUMENTS` + 기존 하네스 산출물 + (가능 시) 직전 실행의 `_workspace/` 산출물
- **출력**: 수정된 에이전트/스킬/오케스트레이터 + CLAUDE.md 변경 이력 한 행 (출처: Phase 9)

## 선조건 검증

1. `.claude/agents/`에 에이전트가 1개 이상 있는가?
2. `$ARGUMENTS`가 비어있지 않은가?

**미충족 시:**

| 항목 | 안내 |
|---|---|
| (1) | "하네스가 없습니다. `/harness:harness-new`로 먼저 구축하세요." |
| (2) | "피드백을 인자로 제공하세요: `/harness:harness-evolve <피드백>`" |

## 실행 절차

### 1. 피드백 분류 (Phase 9-2 표 적용)

`$ARGUMENTS`를 5개 유형 중 하나로 분류:

| 피드백 유형 | 수정 대상 | 분류 단서 |
|---|---|---|
| 결과물 품질 | 해당 에이전트의 스킬 | "분석이 피상적", "출력 너무 짧음", "근거 부족" |
| 에이전트 역할 | 에이전트 정의 `.md` | "X도 필요해", "Y가 빠짐", "이 역할 누가 하나" |
| 워크플로우 순서 | 오케스트레이터 스킬 | "X 먼저", "순서 바꿔", "병렬로 해야" |
| 팀 구성 | 오케스트레이터 + 에이전트 | "이 둘 합쳐", "X는 분리", "팀 너무 큼" |
| 트리거 누락 | 스킬 description | "이 표현으로 작동 안 함", "캐주얼하게 말해도 동작해야" |

분류 모호하면 사용자에게 확인.

### 2. 변경 대상 식별

분류된 유형의 수정 대상에서 구체 파일/섹션 찾기:
- 결과물 품질 → 어느 에이전트 → 그 에이전트의 스킬 SKILL.md
- 에이전트 역할 → 어느 에이전트 정의 또는 새 에이전트 추가 필요
- 워크플로우 순서 → 오케스트레이터 본문 (Phase 정의 부분)
- 팀 구성 → 오케스트레이터 팀 구성 + 영향 받는 에이전트들
- 트리거 누락 → 스킬 description (frontmatter)

### 3. 변경안 제시

수정 전후 diff 형식으로 변경안 제시. 사용자 승인 받음.

**큰 변경 (에이전트 추가/삭제, 팀 재구성)인 경우** 즉시 진행하지 않고 다른 명령으로 안내:

| 변경 규모 | 권장 명령 |
|---|---|
| 새 에이전트 추가 필요 | `/harness:harness-add-agent` |
| 새 스킬 추가 필요 | `/harness:harness-add-skill` |
| 에이전트/스킬 제거 필요 | `/harness:harness-remove <agent|skill> <이름>` |
| 책임 분할 필요 | `/harness:harness-split <agent|skill> <원본> <결과 2개 이상>` |
| 책임 통합 필요 | `/harness:harness-merge <agent|skill> <결과> <원본 2개 이상>` |
| baseline 자체 갱신 필요 | `/harness:harness-baseline` |
| 정합성 점검 먼저 (LLM 추론) | `/harness:harness-audit` |
| 결정적 일관성 검증 (LLM 0) | `/harness:harness-validate` |

### 4. 변경 적용

승인된 변경을 해당 파일에 반영.

### 5. CLAUDE.md 변경 이력 갱신

**출처를 명시하여 Phase 9와 Phase 10을 구분 가능하게**:

```
| {YYYY-MM-DD} | Phase 9: 사용자 피드백 — {요약} | {대상 파일} | {사유: 분류된 유형} |
```

## 진화 트리거 누적 감지

`$ARGUMENTS`가 다음 패턴이면 사용자에게 **단발 변경 대신 구조적 점검** 권고:

- 같은 유형 피드백이 2회 이상 반복됨 (직전 변경 이력 확인) → "X 패턴 반복 → 구조적 문제 가능성. `/harness:harness-audit` 권장"
- 에이전트가 반복 실패하는 패턴 → "사용 drift 가능성. `/harness:harness-adapt`로 telemetry 분석 권장"
- 사용자가 오케스트레이터 우회 작업 중 → "트리거 매칭 실패 가능. `/harness:harness-audit` Step 3 (CLAUDE.md 변경 이력 의미 정합) 검사 권장"
