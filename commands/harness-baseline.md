---
description: baseline 갱신 — Phase 1·2 재실행하여 project_profile·intent_profile을 새 t=0 anchor로 갱신. 영향 받는 에이전트/스킬 점검 포함.
---

# Harness — Baseline Refresh

`_workspace/_baseline/project_profile.md`(코드 baseline)와 `intent_profile.md`(의도 baseline)을 다시 생성하여 Phase 10의 t=0 anchor를 갱신한다. 프로젝트가 크게 진화하여 기존 baseline이 stale해졌을 때 사용한다.

## 언제 사용하는가

Phase 0 매트릭스의 "baseline 갱신" 행 트리거:
- 사용자가 "프로젝트 다시 분석", "baseline 갱신" 등 명시 요청
- `/harness-adapt`이 stack/architecture의 큰 변화를 감지
- 마지막 baseline 분석 후 일정 기간 경과 (권장 3개월)

## 컨텍스트
- **입력**: 사용자 프로젝트 코드(현재 상태), 기존 `_workspace/_baseline/*.md` (diff 비교용), 기존 `.claude/agents/`·`.claude/skills/` (영향 분석용)
- **출력**: 갱신된 `_workspace/_baseline/project_profile.md`, `intent_profile.md`. 기존 baseline은 `_workspace/_baseline_prev/`로 이동하여 보존. 영향 분석 리포트 `_workspace/_baseline/_drift_{ts}.md`.

## 선조건 검증

1. `_workspace/_baseline/project_profile.md`가 존재하는가? (없으면 신규 분석으로 분기)
2. `.claude/agents/`에 에이전트가 1개 이상 있는가?

**미충족 시:**

| 항목 | 안내 |
|---|---|
| (1) | "기존 baseline이 없습니다. `/harness-new <도메인>`으로 처음부터 구축하세요." |
| (2) | "에이전트가 없습니다 — baseline만 있고 하네스가 미완성. `/harness-new`로 전체 진행 권장." |

## 실행 절차

`skills/harness/SKILL.md`의 Phase 1·2를 재실행 + 영향 분석 + 후속 Phase 권고.

### 1. 기존 baseline 백업
- `_workspace/_baseline/` → `_workspace/_baseline_prev/` 이동
- 비교 시 `_baseline_prev/`를 참조

### 2. Phase 1 재실행 (Code Research)
- greenfield/brownfield 자동 감지 (이번엔 brownfield일 가능성 높음)
- 모드 선택: 기본 Quick scan, 사용자 키워드 오버라이드 ("깊이 분석" → Deep)
- 새 `_workspace/_baseline/project_profile.md` 생성

### 3. Phase 2 재실행 (Project Inquiry)
- **diff 우선 전략**: 기존 `intent_profile.md`를 먼저 보여주고 "변경된 부분만 갱신" 모드 제공
- 사용자가 "전부 다시" 선택 시 7섹션 풀 inquiry
- 자동 추론 가능한 필드는 새 코드 기준으로 갱신 (brownfield 4단계 적용)
- 새 `_workspace/_baseline/intent_profile.md` 생성

### 4. Drift 리포트 생성

`_workspace/_baseline/_drift_{timestamp}.md`에:
- §변경된 stack/architecture/convention/maturity/pain_points
- §변경된 intent 필드
- §영향 받을 가능성 있는 에이전트·스킬 매핑

### 5. 영향 받는 후속 Phase 권고

drift 리포트를 기반으로 사용자에게 권고:

| 변화 유형 | 권고 명령 |
|---|---|
| 새 도메인/요구 추가 | `/harness-add-agent` |
| 기존 에이전트 책임 변경 | `/harness-evolve` (사용자 피드백 형식으로 수동 진화) |
| 사용 패턴까지 보려면 | `/harness-adapt` (telemetry 결합) |
| 정합성만 확인 | `/harness-audit` |

### 6. CLAUDE.md 변경 이력 갱신
```
| {YYYY-MM-DD} | baseline 갱신 — Phase 1·2 재실행 | _workspace/_baseline/ | {사유} |
```

## 자동 적용 금지

baseline 갱신만 수행하고, **에이전트/스킬/오케스트레이터는 자동 수정하지 않는다.** drift 리포트로 보고만 하고 후속 명령은 사용자가 명시 호출.
