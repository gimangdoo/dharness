---
description: 하네스 정합성 감사 — .claude/agents/ ↔ 오케스트레이터, .claude/skills/ ↔ 스킬 구성, CLAUDE.md 변경 이력 일치 여부 점검. 자동 수정 없음.
---

# Harness — Audit

하네스 산출물 간 **구조적 정합성**을 점검한다. `skills/harness/SKILL.md` Phase 9-5 운영/유지보수 워크플로우의 §1 현황 감사 단계를 수동으로 트리거하는 명령이다.

> `/harness-adapt`과 다름: adapt은 **telemetry 기반 행동 drift**, audit은 **파일 간 구조 일관성**.

## 컨텍스트
- **입력**: `.claude/agents/`, `.claude/skills/`, `CLAUDE.md` 하네스 포인터, `_workspace/_baseline/*.md`
- **출력**: `_workspace/_audit_{ts}.md` 정합성 리포트. **자동 수정 없음** — 발견된 불일치를 사용자에게 보고 후 후속 명령(`/harness-add-agent`, `/harness-evolve` 등)으로 안내.

## 선조건 검증

1. `.claude/agents/` 또는 `.claude/skills/`에 1개 이상 파일이 있는가?

**미충족 시:** "감사할 하네스가 없습니다. `/harness-new`를 먼저 실행하세요."

## 검사 항목

### 1. 에이전트 ↔ 오케스트레이터 정합성
- `.claude/agents/{name}.md` 파일 목록 ↔ 오케스트레이터 스킬에서 호출되는 에이전트 이름 비교
- **Orphan agent**: 정의 파일은 있으나 오케스트레이터가 참조하지 않음
- **Phantom agent**: 오케스트레이터가 호출하지만 정의 파일 없음
- 각 에이전트 정의의 `model: "opus"` 명시 여부

### 2. 스킬 ↔ 에이전트·오케스트레이터 정합성
- `.claude/skills/{name}/SKILL.md` 목록 ↔ 에이전트·오케스트레이터에서 사용/언급되는 스킬 비교
- **Orphan skill**: 어느 에이전트도 사용하지 않는 스킬
- **Phantom skill**: 참조되지만 파일 없음
- 각 스킬 SKILL.md의 frontmatter(`name`, `description`) 유효성
- 본문 ≤500줄 가이드라인 준수
- description의 트리거 키워드 빈약도 (구체 키워드 < 3개면 flag)

### 3. CLAUDE.md 하네스 포인터 정합성
- 하네스 포인터 섹션 존재 여부
- 트리거 규칙 + 변경 이력 두 섹션 모두 존재
- **변경 이력 누락 감지**: 최근 `.claude/agents/`·`.claude/skills/` 파일 mtime이 변경 이력 마지막 날짜보다 새로움 → 미기록 변경 의심

### 4. baseline 정합성
- `_workspace/_baseline/project_profile.md`, `intent_profile.md` 존재 여부
- 마지막 갱신 후 경과 시간 (3개월 초과 시 flag)
- intent profile 필수 5개 필드 채워짐 (`tech_stack`, `team.size`, `timeline.horizon`, `deployment_target`, `test_rigor`)

### 5. Phase 10 인프라 정합성
- `_workspace/_telemetry/` 디렉토리 존재 여부
- 오케스트레이터에 capture 훅 흔적 (`.jsonl` append 패턴)
- 오케스트레이터 description에 Phase 10 트리거 키워드 ("점검", "drift", "적응", "baseline 갱신") 포함

## 실행 절차

1. 위 5개 항목을 순차 검사
2. 각 발견 사항을 심각도(🔴 차단 / 🟡 경고 / 🟢 OK)로 분류
3. `_workspace/_audit_{timestamp}.md` 작성 — 항목별 발견 사항 + 권장 조치
4. 사용자에게 요약 보고

## 발견된 불일치 처리

| 패턴 | 권장 후속 명령 |
|---|---|
| Orphan agent | `/harness-evolve "에이전트 X 사용 안 됨 — 제거 또는 재배치"` |
| Phantom agent/skill | 수동 — 오케스트레이터 또는 정의 파일 직접 수정 |
| 변경 이력 누락 | 사용자에게 최근 변경 회상 요청 → 수동 기록 |
| baseline stale | `/harness-baseline` |
| Phase 10 인프라 누락 | 수동 — 오케스트레이터에 capture 훅 추가 + description 갱신 |

**자동 수정 절대 금지** — audit은 read-only.
