---
description: 기준선(baseline) 갱신 — 코드·의도 프로파일을 다시 수집해 새 anchor로 박제 + CLAUDE.md HOW 섹션 재초안 + 영향 받는 에이전트·스킬 점검.
argument-hint: [--allow-self-host]
allowed-tools: Read, Glob, Grep, Write, Edit
---

# Harness — Baseline Refresh

`_workspace/_baseline/project_profile.md`(코드 baseline)와 `intent_profile.md`(의도 baseline)을 다시 생성하여 Phase 10의 t=0 anchor를 갱신한다. 갱신된 `project_profile.md` 기반으로 CLAUDE.md HOW 섹션(Phase 7-4.5 신양식) 재draft도 함께 수행한다. 프로젝트가 크게 진화하여 기존 baseline이 stale해졌을 때, 또는 기존 derived CLAUDE.md를 Phase 7-4.5 신양식으로 마이그레이션할 때 사용한다.

## 언제 사용하는가

Phase 0 매트릭스의 "baseline 갱신" 행 트리거:
- 사용자가 "프로젝트 다시 분석", "baseline 갱신" 등 명시 요청
- `/harness:harness-adapt`이 stack/architecture의 큰 변화를 감지
- 마지막 baseline 분석 후 일정 기간 경과 (권장 3개월)
- 기존 derived CLAUDE.md를 Phase 7-4.5 신양식(HOW 섹션)으로 마이그레이션 ("CLAUDE.md 신양식 적용", "HOW 섹션 추가" 등)

## 컨텍스트
- **입력**: 사용자 프로젝트 코드(현재 상태), 기존 `_workspace/_baseline/*.md` (diff 비교용), 기존 `.claude/agents/`·`.claude/skills/` (영향 분석용), 기존 `CLAUDE.md` (HOW 섹션 마이그레이션 대상)
- **출력**: 갱신된 `_workspace/_baseline/project_profile.md`, `intent_profile.md`. 기존 baseline은 `_workspace/_baseline_prev/`로 이동하여 보존. 영향 분석 리포트 `_workspace/_baseline/_drift_{ts}.md`. 사용자 승인 시 CLAUDE.md `## HOW` 섹션 삽입/갱신.

## 선조건 검증

0. **self-host 영역 검출** (A2 audit2 fix, 2026-05-28): cwd에 `.harness-host` marker 존재하는가?

   **존재 시:** 본 명령은 **dharness 자체** `_workspace/_baseline/`를 덮어쓸 위험. 의도된 self-host dogfood가 아니면 즉시 중단. 두 경로 중 선택:
   - dharness 자체 baseline 갱신 의도 → `$ARGUMENTS`에 `--allow-self-host` 명시 후 재호출.
   - 사용자 derived 프로젝트 baseline 갱신 의도 → 해당 프로젝트 디렉토리로 `cd` 후 재호출 (해당 위치엔 `.harness-host` 부재).

   `--allow-self-host` 미명시 + marker 존재 → 즉시 중단, 위 안내 출력.

1. `_workspace/_baseline/project_profile.md`가 존재하는가? (없으면 신규 분석으로 분기)
2. `.claude/agents/`에 에이전트가 1개 이상 있는가?

**미충족 시:**

| 항목 | 안내 |
|---|---|
| (1) | "기존 baseline이 없습니다. `/harness:harness-new <도메인>`으로 처음부터 구축하세요." |
| (2) | "에이전트가 없습니다 — baseline만 있고 하네스가 미완성. `/harness:harness-new`로 전체 진행 권장." |

## 실행 절차

`plugins/harness/skills/harness/SKILL.md`의 Phase 1·2를 재실행 + 영향 분석 + 후속 Phase 권고.

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
- **`meta.dharness_version` 박제** — `plugins/harness/.claude-plugin/plugin.json` `version` 필드를 read 후 frontmatter `meta.dharness_version: "<현 plugin version>"`로 저장. doctrine drift 진단의 새 기준점 (`intent-profile-schema.md` §5).

### 4. Drift 리포트 생성

`_workspace/_baseline/_drift_{timestamp}.md`에:
- §변경된 stack/architecture/convention/maturity/pain_points
- §변경된 intent 필드
- §영향 받을 가능성 있는 에이전트·스킬 매핑
- §CLAUDE.md HOW 섹션 재draft 필요 여부 (stack/build/entry_points/commands 변경 시 yes)

### 5. CLAUDE.md HOW 섹션 재draft (Phase 7-4.5 적용)

> **목적**: 갱신된 `project_profile.md`의 객관 데이터를 CLAUDE.md `## HOW` 섹션에 반영. 기존 derived CLAUDE.md가 7-4.5 신양식 미적용이면 본 단계가 마이그레이션 진입점.

5-1. **건너뜀 조건 판정**:
- 비코드 도메인 (`project_profile.md`에 `stack.languages` 비어있음) → skip
- 사용자가 명시적으로 "HOW 섹션 불필요" 의사 표명 → skip
- 그 외 → 진행

5-2. **현 CLAUDE.md 상태 진단**:
- `## HOW` 섹션 존재 여부 확인
- 존재하면 → **갱신 모드** (기존 섹션 통째로 교체)
- 부재면 → **신규 삽입 모드** (`## 규칙` 다음, 변경 이력 포인터 `---` 직전)

5-3. **draft 생성** (`plugins/harness/skills/harness/SKILL.md` Phase 7-4.5 절차 그대로):
- `_workspace/_baseline/project_profile.md`에서 `stack.languages`/`stack.frameworks`/`stack.runtime`, `build_tools`, `entry_points`, `key_directories`, `commands.dev`/`build`/`test` 추출
- `_workspace/_drafts/claudemd_how_{ts}.md`에 7-4.5 template 박제

5-4. **사용자 게이트** — diff 형식 제시 후 inline confirm:
- `Y` → CLAUDE.md에 삽입/교체 적용
- `N` → `_workspace/_drafts/discarded/`로 이동
- 모호한 응답 → 재확인

5-5. **변경 이력 한 행 추가** (5-4 Y인 경우):
```
| {YYYY-MM-DD} | baseline 갱신 — CLAUDE.md HOW 섹션 {삽입|갱신} | CLAUDE.md | {신양식 마이그레이션|stack drift 반영} |
```

### 6. 영향 받는 후속 Phase 권고

drift 리포트를 기반으로 사용자에게 권고:

| 변화 유형 | 권고 명령 |
|---|---|
| 새 도메인/요구 추가 | `/harness:harness-add-agent` |
| 기존 에이전트 책임 변경 | `/harness:harness-evolve` (사용자 피드백 형식으로 수동 진화) |
| 사용 패턴까지 보려면 | `/harness:harness-adapt` (telemetry 결합) |
| 정합성만 확인 | `/harness:harness-audit` |

### 7. 변경 이력 갱신 (`_workspace/_baseline/changelog.md`)
```
| {YYYY-MM-DD} | baseline 갱신 — Phase 1·2 재실행 | _workspace/_baseline/ | {사유} |
```

## 자동 적용 금지

baseline 갱신만 수행하고, **에이전트/스킬/오케스트레이터는 자동 수정하지 않는다.** drift 리포트로 보고만 하고 후속 명령은 사용자가 명시 호출.

**예외**: Step 5 CLAUDE.md HOW 섹션은 사용자 게이트 후 *직접 적용*. Phase 7-4.5가 baseline 산출물(`project_profile.md`) ↔ CLAUDE.md를 직결하는 doctrine이며, 사용자 confirm을 거치므로 anti-premature-judgment 위반 아님.
