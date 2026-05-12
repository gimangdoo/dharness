---
description: 신규 도메인/프로젝트에 하네스를 처음 구축. Phase 0-8 전체 실행.
argument-hint: <도메인 한 문장 설명>
---

# Harness — New

새 도메인/프로젝트에 하네스(에이전트 팀 + 스킬 세트 + 오케스트레이터 + CLAUDE.md 포인터)를 처음부터 구축한다. description 매칭 확률에 의존하지 않고 명시적으로 호출하는 명령어다.

## 컨텍스트
- **인자**: `$ARGUMENTS` (도메인/프로젝트 한 문장 설명; 예: "fintech risk-assessment team", "이커머스 추천 엔진 검증")
- **입력**: 사용자 프로젝트 코드(있으면 자동 감지) + `$ARGUMENTS`
- **출력**: `.claude/agents/`, `.claude/skills/`, `CLAUDE.md` 하네스 포인터, `_workspace/_baseline/{project,intent}_profile.md`

## 선조건 검증 (먼저 실행)

1. `.claude/agents/`와 `.claude/skills/`가 비어있거나 존재하지 않는가?

**미충족(이미 하네스 있음) 시:** 사용자에게 보고하고 다음 중 선택받는다:
- 기존 위에 새로 덮어쓰기 → 진행 (단, 기존 산출물을 `_workspace_prev/`로 백업)
- 에이전트 추가만 원함 → `/harness:harness-add-agent` 안내 후 중단
- baseline 갱신만 원함 → `/harness:harness-baseline` 안내 후 중단

## 실행 절차

`plugins/harness/skills/harness/SKILL.md`의 워크플로우 **Phase 0-8 전체**를 따른다 (Phase 9는 사후 진화 트리거이므로 초기 구축에서는 실행하지 않는다).

1. **Phase 0 (Pre-flight)**: 위 선조건이 통과했다면 신규 구축으로 분기.
2. **Phase 1 (Code Research)**: greenfield/brownfield 자동 감지 + Quick/Deep 모드 선택. 결과 `_workspace/_baseline/project_profile.md`는 후속 baseline 재실행 시 비교 기준점.
3. **Phase 2 (Project Inquiry)**: 7섹션(vision/scope/constraints/architecture/quality/workflow/meta) 수집. 필수 5개 필드(`tech_stack`, `team.size`, `timeline.horizon`, `deployment_target`, `test_rigor`) 강제. brownfield는 4단계(자동 추론 → 확인 → 갭 → 코드 grounded).
4. **Phase 3~6**: 도메인 분석 → 팀 아키텍처 설계 → 에이전트 정의 → 스킬 생성. **`.claude/agents/{name}.md` 파일 생성 필수** (빌트인 타입이라도). 모든 Agent 호출에 `model: "opus"` 명시. **Phase 5-2 (도구·MCP 자동 할당)** — capability profile 매칭 → `claude mcp list` 확인 → 사용자 confirm → frontmatter `tools:` allowlist 합성. T0(무키·로컬) 한정 자동, 카탈로그·결정 트리·안전 정책은 `plugins/harness/skills/harness/references/permission-profiles.md` 단일 출처(§3-§7). **§3-1 매트릭스**는 검증 완료 T0 MCP 7종(48 도구) × 4 capability profile의 런타임 가용 default 카탈로그 — profile 확정 시 1차 후보로 발췌 (멀티 inline 패턴 예시는 `fixtures/synthesis_example/web-research/`). 합성 시점에 install된 신규 MCP는 *다음 세션부터* 사용 가능 (mid-session 미전파). 런타임 신규 채택은 `/harness:harness-mcp-adopt` (§10 dynamic adoption — 별건).
5. **Phase 7 (오케스트레이션)**: 통합 스킬 + Phase 7-4 CLAUDE.md 포인터(트리거 규칙 + 변경 이력) + Phase 7-5 후속 작업 키워드 description 포함.
6. **Phase 8 (검증)**: 7단계 — 구조·실행 모드·실행 테스트·트리거·드라이런·테스트 시나리오·반복 개선.

## 완료 후 체크

`plugins/harness/skills/harness/SKILL.md` §산출물 체크리스트의 항목을 확인한다.

## 후속 명령어

- 에이전트 추가: `/harness:harness-add-agent <역할>`
- 사용자 피드백 진화: `/harness:harness-evolve <피드백>`
- 런타임 신규 MCP 채택: `/harness:harness-mcp-adopt <사유>` (§10 dynamic adoption)
- MCP 상태 진단 (read-only): `/harness:harness-mcp-status`
