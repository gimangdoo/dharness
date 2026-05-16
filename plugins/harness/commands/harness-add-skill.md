---
description: 기존 하네스에 스킬 1개 추가/수정. Phase 1·2·3·4·5 SKIP, baseline·에이전트 정의 그대로 두고 스킬만 추가.
argument-hint: <스킬 이름 또는 스킬 의도 한 줄>
---

# Harness — Add Skill

기존 에이전트가 사용할 새 스킬을 추가하거나 기존 스킬을 수정한다. **에이전트 정의는 건드리지 않는다.**

## 컨텍스트
- **인자**: `$ARGUMENTS` (스킬 이름 또는 스킬 의도; 예: "보안 취약점 스캔 스킬", "API contract validator")
- **입력**: 기존 `.claude/agents/`, `.claude/skills/`, 어느 에이전트가 이 스킬을 쓸지(필요 시 사용자에게 확인)
- **출력**: 새 `.claude/skills/{name}/SKILL.md` (+ `references/`, `scripts/`, `assets/` 선택), 기존 오케스트레이터의 데이터 흐름·트리거 키워드 갱신(필요 시), CLAUDE.md 변경 이력 한 행

## 선조건 검증

1. `.claude/agents/`에 기존 에이전트가 1개 이상 있는가?
2. 새 스킬을 사용할 에이전트(들)가 식별 가능한가? — 인자가 모호하면 사용자에게 묻는다.

**미충족 시:**

| 항목 | 안내 |
|---|---|
| (1) | "에이전트가 없습니다. `/harness:harness-new` 또는 `/harness:harness-add-agent`를 먼저 실행하세요." |
| (2) | 사용자에게 "어느 에이전트가 이 스킬을 사용할 예정인가요? (1개 또는 N개)" 질문 |

## 실행 절차

`plugins/harness/skills/harness/SKILL.md`의 워크플로우를 따르되 **Phase 1·2·3·4·5는 SKIP**한다.

1. **Phase 6 (스킬 생성)**:
   - `프로젝트/.claude/skills/{name}/SKILL.md` 생성
   - YAML frontmatter (`name`, `description`) + Markdown 본문, 본문 ≤500줄
   - **description은 적극적("pushy")** — 트리거 키워드 5개 이상, 유사하지만 트리거하면 안 되는 경우와 구분
   - **명령형 어조** ("~한다", "~하라"), **Why 설명** ("ALWAYS/NEVER" 강압 대신 이유 전달)
   - 본문이 길어지면 `references/`로 분리 + 본문에 "언제 읽으라" 포인터
   - 작성 룰 전체는 `plugins/harness/skills/harness/references/skill-writing-guide.md`
2. **Phase 7-1·7-3 (오케스트레이터 갱신, 영향 시)**:
   - 새 스킬을 사용하는 에이전트의 작업 흐름·데이터 전달 갱신
   - 트리거 키워드 영향 시 오케스트레이터 description 갱신
3. **Phase 8 (검증)** — `SKILL.md` Phase 8 sub-step 매핑:
   - **필수**: Phase 8-1 구조 검증, Phase 8-4 트리거 검증 (스킬 description의 should-trigger / should-NOT-trigger 8~10개씩)
   - **권장**: Phase 8-3 실행 테스트 (스킬에 2~3개 현실적 테스트 프롬프트, with-skill vs without-skill 비교)
4. **CLAUDE.md 변경 이력 갱신**:
   ```
   | {YYYY-MM-DD} | 스킬 추가: {이름} | .claude/skills/ + (영향 시) 오케스트레이터 | {사유} |
   ```

## 범위 외

- 새 에이전트 생성 → `/harness:harness-add-agent`
- baseline 갱신 → `/harness:harness-baseline`
- 기존 스킬 description만 수정하고 싶으면 → 직접 편집 + `/harness:harness-audit`로 정합성 확인
