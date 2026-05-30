---
description: 통합 변경 front door — 사용자 피드백을 분류해 변경안을 설계하고, 승인 시 해당 내부 op(텍스트 수정·에이전트 추가/제거·스킬 추가/수정·분할·통합·baseline 갱신·MCP 채택)를 직접 적용한다 (Phase 9 수동 진화 진입점).
argument-hint: <피드백 한 문장 또는 단락>
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# Harness — Evolve (통합 변경 front door)

사용자 피드백을 받아 `plugins/harness/skills/harness/SKILL.md` Phase 9 수동 진화 워크플로우를 실행한다. **본 명령이 모든 구조적 변경의 단일 진입점** — 피드백을 분류하고(Phase 9-2 표), 변경안을 *설계*해 보여준 뒤, 사용자 *승인*을 받아 해당 **내부 op**를 직접 적용한다.

> **통합 front door doctrine (2026-05-30, command 병합):** 이전의 개별 명령 `harness-add-agent` / `-add-skill` / `-remove` / `-split` / `-merge` / `-baseline` / `-mcp-adopt`는 별도 슬래시 커맨드를 폐기하고 **본 명령의 내부 op로 흡수**됐다. 사용자는 자유 텍스트 피드백 하나만 주면 되고, 본 명령이 분류→설계→승인→적용을 담당한다. 각 op의 결정적 불변식(예: remove의 dangling cleanup, split의 4축 검증)은 `references/agent-design-patterns.md`에 그대로 박제돼 있으며 op 실행 시 read 한다.

## 진화 명령 분기 doctrine (2026-05-30 개정)

| 명령 | 진입 시점 | 입력 | 영역 |
|---|---|---|---|
| **`/harness:harness-evolve`** | 사용자가 *변경 의도* 발화 (자유 텍스트) | 자유 텍스트 | 모든 구조적 변경 (본 명령 + 내부 op) |
| **`/harness:harness-adapt`** | 사용자가 *명시 호출* (자율 감지 없음) | `_workspace/_telemetry/*.jsonl` | Phase 10 telemetry drift |
| **`/harness:harness-status --deep`** | 사용자가 *LLM 정합 감사* 요청 | 하네스 산출물 | read-only 추론 진단 (수정 없음) |
| **`/harness:harness-validate`** | 사용자가 *결정적 검증* 요청 | 하네스 산출물 | read-only 결정 검증 (LLM 0) |

**언제 evolve?**: "분석이 피상적" / "보안 검토도 필요(에이전트 추가)" / "X 제거" / "Y를 둘로 쪼개" / "이 둘 합쳐" / "baseline 다시" / "MCP 붙여" — *모두 evolve*. 본 명령이 자유 텍스트를 분류해 적절한 내부 op로 라우팅한다.

## 컨텍스트
- **인자**: `$ARGUMENTS` (피드백 한 문장 또는 단락; 예: "분석이 너무 피상적이야", "보안 검토 에이전트 추가해줘", "검증을 먼저 해야 할 것 같아", "X 에이전트 제거")
- **입력**: `$ARGUMENTS` + 기존 하네스 산출물 + (가능 시) 직전 실행의 `_workspace/` 산출물
- **출력**: 수정된 에이전트/스킬/오케스트레이터/baseline + `_workspace/_baseline/changelog.md` 변경 이력 한 행 (출처: Phase 9)

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

`$ARGUMENTS`를 분류해 **수정 대상 + 내부 op**를 정한다:

| 피드백 유형 | 수정 대상 | 내부 op | 분류 단서 |
|---|---|---|---|
| 결과물 품질 | 해당 에이전트의 스킬 | `edit-skill` | "분석이 피상적", "출력 너무 짧음", "근거 부족" |
| 에이전트 역할 (보강) | 에이전트 정의 `.md` | `edit-agent` | "X 톤 바꿔", "이 역할 범위 조정" |
| 에이전트 추가 | 새 에이전트 정의 | `add-agent` | "X도 필요해", "보안 검토 누가 하나" |
| 스킬 추가/수정 | 스킬 SKILL.md | `add-skill` / `edit-skill` | "Y 스킬 추가", "이 스킬 갱신" |
| 워크플로우 순서 | 오케스트레이터 스킬 | `edit-orchestrator` | "X 먼저", "순서 바꿔", "병렬로" |
| 책임 분할 | 1개 → 2+ | `split` | "X는 너무 많은 걸 함 — 쪼개" |
| 책임 통합 | 2+ → 1개 | `merge` | "이 둘 합쳐", "중복됨" |
| 제거 | 에이전트/스킬 1개 | `remove` | "X 사용 안 됨 — 제거" |
| 트리거 누락 | 스킬 description | `edit-skill-desc` | "이 표현으로 작동 안 함" |
| baseline 노후 | project/intent profile | `baseline` | "프로젝트 다시 분석", "baseline 갱신" |
| 런타임 MCP 필요 | settings/.mcp.json + 에이전트 tools | `mcp-adopt` | "X MCP 붙여", "이 도구 필요" |

분류 모호하면 사용자에게 확인 (필요 시 `/harness:harness-grill feedback` 패턴 — 자율 진입 없음, 본 명령 내 명시 분기).

### 2. 변경 대상 식별

분류된 op의 수정 대상에서 구체 파일/섹션을 찾는다. op별 read 필수 reference:

| op | 적용 전 read | 결정적 불변식 |
|---|---|---|
| `add-agent` / `edit-agent` | `references/agent-design-patterns.md`, `references/permission-profiles*.md` (tools allowlist), `references/qa-agent-guide.md` (QA 시) | 정의 파일 필수 섹션 + `model:` 필드 + 입력 신뢰 경계(부작용 도구 보유 시) |
| `add-skill` / `edit-skill` | `references/skill-writing-guide.md` | 빈 스킬 금지(본문까지 박제) + `SKILL.md` 대문자 + description pushy |
| `split` | `references/agent-design-patterns.md` "분리 기준 4축" | 4축(전문성·병렬성·컨텍스트·재사용성) 검증 + 참조 갱신 |
| `merge` | `references/agent-design-patterns.md` | 책임 중복·통신 비용 진단 + 참조 갱신 |
| `remove` | — | dangling reference 자동 정리 (오케스트레이터·CLAUDE.md·다른 스킬 참조) |
| `baseline` | `references/code-research.md`, `references/orchestrator-template.md` (HOW draft) | project/intent profile 재수집 + `meta.dharness_version` 재박제 + CLAUDE.md HOW 재초안 + 영향 에이전트/스킬 점검 |
| `mcp-adopt` | `references/permission-profiles-dynamic-adoption.md` §10 (발견→탐침→확인→설치→반영 5단계) | 사용자 confirm gate + T0 한정 자동 allow |

### 3. 변경안 설계 + 제시 (승인 게이트)

수정 전후 diff 형식으로 변경안을 *설계*해 제시. **자동 적용 0 — 사용자 승인 필수.**

- 작은 변경(텍스트 수정, 단일 스킬 본문) → diff 미리보기 후 승인 즉시 적용
- 큰 변경(`add-agent`/`remove`/`split`/`merge`/`baseline`) → 영향 범위(영향 받는 파일·참조·오케스트레이터)를 함께 제시 후 승인

### 4. 변경 적용 (내부 op 실행)

승인된 op를 직접 실행한다. op별 §2 reference의 불변식을 지킨다. 적용 후 **결정적 회귀 검증** — `/harness:harness-validate`(구조·schema·chain) 호출, 트리거 영향 시 8-4 트리거 검증, 대규모 변경 시 8-5 드라이런.

### 5. 변경 이력 갱신 (`_workspace/_baseline/changelog.md`)

**출처를 명시하여 Phase 9와 Phase 10을 구분 가능하게**:

```
| {YYYY-MM-DD} | Phase 9: 사용자 피드백 — {요약} (op: {op}) | {대상 파일} | {사유: 분류된 유형} |
```

`baseline` op는 구 `harness-baseline` 명령의 doctrine을 본 명령이 흡수(2026-05-30) — `_workspace/_baseline/*` 수동 편집 금지 규칙은 본 op 내부에서 동일하게 적용된다.

## 진화 트리거 (command-only)

본 명령은 사용자가 `/harness:harness-evolve <피드백>`을 명시 호출할 때만 실행된다. harness는 "피드백 2회 반복", "반복 실패", "우회 감지" 같은 신호를 *자동 판단해 다음 액션을 제안하지 않는다* (autonomous trigger 제거 doctrine, 2026-05-30).

구조적 점검·telemetry 분석이 필요하다고 판단하는 주체는 **사용자**다. 사용자가 원하면 `/harness:harness-status --deep`(LLM 감사) 또는 `/harness:harness-adapt`(telemetry drift)를 직접 호출한다.
