---
description: 기존 하네스에 에이전트 1명 추가. Phase 1·2·3 SKIP, baseline 재분석 비용 회피하고 비용 최소로 확장.
argument-hint: <새 에이전트 역할 한 줄 설명>
---

# Harness — Add Agent

기존 하네스가 있다는 전제 하에 새 에이전트 1명을 추가한다. **Phase 1·2·3는 스킵**하여 baseline 재분석 비용을 치르지 않는다. Phase 0 매트릭스의 "에이전트 추가" 행에 해당하는 명시적 진입점이다.

## 컨텍스트
- **인자**: `$ARGUMENTS` (에이전트 역할 한 줄; 예: "보안 리뷰어", "DB 마이그레이션 검증자")
- **입력**: 기존 `.claude/agents/`, `.claude/skills/`, `_workspace/_baseline/*.md`, 기존 오케스트레이터 스킬
- **출력**: 새 `.claude/agents/{name}.md` + 기존 오케스트레이터 수정 + CLAUDE.md 변경 이력 한 행

## 선조건 검증 (먼저 실행)

1. `.claude/agents/`에 기존 에이전트 정의 파일이 1개 이상 있는가?
2. `_workspace/_baseline/project_profile.md`가 존재하는가?
3. `_workspace/_baseline/intent_profile.md`가 존재하는가?
4. 기존 오케스트레이터 스킬을 `.claude/skills/`에서 식별 가능한가? (Phase 7-4 CLAUDE.md 포인터의 `{orchestrator-skill-name}` 단서)

**미충족 시 즉시 중단**하고 사용자에게 안내:

| 미충족 항목 | 안내 메시지 |
|-----------|----------|
| (1) | "기존 하네스가 없습니다. `/harness:harness-new <도메인>`을 먼저 실행하세요." |
| (2)·(3) | "baseline이 없거나 불완전합니다. `/harness:harness-baseline`을 먼저 실행하세요." |
| (4) | "오케스트레이터 식별 실패 — CLAUDE.md 포인터 또는 `.claude/skills/`를 수동 확인하세요." |

## 실행 절차

`plugins/harness/skills/harness/SKILL.md`의 워크플로우를 따르되 **Phase 1·2·3는 SKIP** — 기존 `_workspace/_baseline/*.md`를 그대로 입력으로 사용한다.

1. **Phase 4-1·4-3 (팀 배치 검토만)**: 새 에이전트가 기존 패턴/팀 구조에 어떻게 들어맞는지만 결정. **기존 다른 에이전트 정의는 건드리지 않음.** 분리 기준 4축(전문성·병렬성·컨텍스트·재사용성)으로 새 에이전트의 독립성 확인.
2. **Phase 5 (에이전트 정의 생성)**: `.claude/agents/{새이름}.md` 작성.
   - **빌트인 타입(`general-purpose`/`Explore`/`Plan`)이라도 파일 생성 필수**
   - `model: "opus"` 명시
   - 필수 섹션: 핵심 역할, 작업 원칙, 입력/출력 프로토콜, 에러 핸들링, 협업, 팀 통신 프로토콜
3. **Phase 7-1·7-3 (오케스트레이터 수정)**: 기존 오케스트레이터 스킬에 새 에이전트 반영.
   - 팀 구성·작업 할당·데이터 흐름 갱신
   - description에 새 트리거 키워드(있으면) 추가
   - **새 오케스트레이터 생성 금지** — 기존 수정만
4. **Phase 8 (검증, 부분)**:
   - **필수**: §1 구조 검증, §2 실행 모드 검증, §4 트리거 검증
   - **변경 영향 시**: §3 실행 테스트, §5 드라이런
5. **CLAUDE.md 변경 이력 갱신**: Phase 7-4 템플릿 형식으로 한 행 추가.
   ```
   | {YYYY-MM-DD} | 에이전트 추가: {이름} | 오케스트레이터 + .claude/agents/ | {사유} |
   ```

## 범위 외

- **스킬은 새로 만들지 않는다** — 새 에이전트가 전용 스킬을 필요로 하면 별도로 `/harness:harness-add-skill`(차후 추가) 호출, 또는 사용자에게 안내
- **baseline 갱신하지 않는다** — 코드/의도가 크게 바뀌었다고 판단되면 `/harness:harness-baseline`로 안내
- **Phase 10 trigger 안 함** — drift 점검은 `/harness:harness-adapt`
