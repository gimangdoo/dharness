---
description: 신규 도메인/프로젝트에 하네스를 처음 구축. Phase 0-8 전체 + Phase 10 인프라(telemetry 디렉토리, 자동 알림 포인터, 트리거 키워드)까지 실행. 단일 프로젝트 모드 + derived install 모드 양쪽 1급 시민.
argument-hint: <도메인 한 문장 설명> [--mode=single|derived]
---

# Harness — New

새 도메인/프로젝트에 하네스(에이전트 팀 + 스킬 세트 + 오케스트레이터 + CLAUDE.md 포인터)를 처음부터 구축한다. description 매칭 확률에 의존하지 않고 명시적으로 호출하는 명령어다.

## 모드 분기 (사용자 확정 doctrine 2026-05-14)

본 명령은 **2개 모드** 양쪽 1급 시민:

| 모드 | 시나리오 | 자동 감지 단서 |
|---|---|---|
| **`single`** | 현 프로젝트 자체의 harness를 dogfood로 구축. cwd가 dharness root와 동일하거나 self-host CM 운영 중. | `.harness-host` marker 파일 존재 OR `.claude/hooks/` Python hook 박제 OR cwd가 dharness 폴더 |
| **`derived`** | dharness plugin을 install한 외부 프로젝트에 harness 합성. host-agnostic 워크플로우. | `.harness-host` 미존재 + `.claude/hooks/` 미존재 + plugin marketplace install 흔적 |

**모드 결정 우선순위:**
1. `$ARGUMENTS`에 `--mode=single` 또는 `--mode=derived` 명시 → 그대로
2. 자동 감지 룰로 1개 모드 단서 hit → 해당 모드 채택 + 사용자에게 보고
3. 양쪽 모두 또는 양쪽 모두 아님 → 사용자 confirm 게이트

**모드별 행동 차이:**

| 항목 | single | derived |
|---|---|---|
| baseline 위치 | `_workspace/_baseline/` (host root) | `{프로젝트}/_workspace/_baseline/` |
| telemetry capture | host의 `.claude/hooks/post_tool_use.py` 자동 (CM 운영 중) | orchestrator LLM 직접 append (orchestrator-template.md §Phase 10 강제 블록) |
| CLAUDE.md 변경 이력 적재 | `.claude/hooks/session_end.py`가 draft 자동 생성 + `/cm-claudemd-apply` | orchestrator가 manual 1행 추가 + 사용자 직접 commit |
| Phase 5-2 MCP install | `claude mcp add` 즉시 + 다음 세션부터 사용 가능 (mid-session 미전파 — empirical) | 동일 — host-agnostic |
| Phase 8 트리거 회귀 검증 | should/should-NOT 8+8 권장 | should/should-NOT 8+8 *강제* (derived 환경은 self-host CM 가드 없음) |

## 컨텍스트
- **인자**: `$ARGUMENTS` (도메인/프로젝트 한 문장 설명 + 선택 `--mode=`; 예: "fintech risk-assessment team --mode=derived", "이커머스 추천 엔진 검증")
- **입력**: 사용자 프로젝트 코드(있으면 자동 감지) + `$ARGUMENTS`
- **출력**: `.claude/agents/`, `.claude/skills/`, `CLAUDE.md` 하네스 포인터, `_workspace/_baseline/{project,intent}_profile.md`, `_workspace/_telemetry/` 디렉토리

## 선조건 검증 (먼저 실행)

1. `.claude/agents/`와 `.claude/skills/`가 비어있거나 존재하지 않는가?

**미충족(이미 하네스 있음) 시:** 사용자에게 보고하고 다음 중 선택받는다:
- 기존 위에 새로 덮어쓰기 → 진행 (단, 기존 산출물을 `_workspace_prev/`로 백업)
- 에이전트 추가만 원함 → `/harness:harness-add-agent` 안내 후 중단
- baseline 갱신만 원함 → `/harness:harness-baseline` 안내 후 중단

## 실행 절차

`plugins/harness/skills/harness/SKILL.md`의 워크플로우 **Phase 0-8 전체 + Phase 10 인프라**를 따른다 (Phase 9는 사후 진화 트리거이므로 초기 구축에서는 실행하지 않고, Phase 10은 capture 디렉토리·CLAUDE.md 자동 알림 블록·트리거 키워드 포함만 사전 배치).

1. **Phase 0 (Pre-flight)**: 위 선조건이 통과했다면 신규 구축으로 분기.
2. **Phase 0.5 + Anti-premature-judgment doctrine (2026-05-15 강제)**: SKILL.md Phase 0.5의 🛑 anti-premature-judgment 박스 필독. cwd 디렉토리 이름·파일 이름·`$ARGUMENTS` 키워드 *단독*으로 도메인/유형/기능 단정 금지. 단정 허용은 Phase 1 + Phase 2 산출물 양쪽 박제 후만.
3. **Phase 1 (Code Research)**: greenfield/brownfield 자동 감지 + Quick/Deep 모드 선택. 결과 `_workspace/_baseline/project_profile.md`는 Phase 10의 t=0 anchor. **🚧 entry 게이트 (2026-05-15)**: greenfield라도 빈 stub 파일 *반드시* 박제 (`project_type`, `signals`, `directory_tree`, `inferred_domain: null` 필드). silent skip 차단.
4. **Phase 2 (Project Inquiry)**: 7섹션(vision/scope/constraints/architecture/quality/workflow/meta) 수집. 필수 5개 필드(`tech_stack`, `team.size`, `timeline.horizon`, `deployment_target`, `test_rigor`) 강제. brownfield는 4단계(자동 추론 → 확인 → 갭 → 코드 grounded). **🚧 entry 게이트 (2026-05-15)**: 필수 5필드 *모두*에 대해 사용자 raw 답변 인용 → `meta.user_confirmed_fields` 박제. 답변 거부 시 `meta.inferred_fields` + 별도 confirm 게이트. 본 게이트 미충족 시 Phase 3 진입 차단.
5. **Phase 3~6**: 도메인 분석 → 팀 아키텍처 설계 → 에이전트 정의 → 스킬 생성. **`.claude/agents/{name}.md` 파일 생성 필수** (빌트인 타입이라도). 모든 Agent 호출에 `model: "opus"` 명시. **Phase 5-2 (도구·MCP 자동 할당)** — capability profile 매칭 → `claude mcp list` 확인 → 사용자 confirm → frontmatter `tools:` allowlist 합성. T0(무키·로컬) 한정 자동, 카탈로그·결정 트리·안전 정책은 `plugins/harness/skills/harness/references/permission-profiles.md` 단일 출처(§3-§7). **§3-1 매트릭스(14차 사이클)는 검증 완료 T0 MCP 7종(48 도구) × 4 capability profile의 *런타임 가용 default 카탈로그*** — profile 확정 시 1차 후보로 발췌 (멀티 inline 패턴 예시는 `fixtures/synthesis_example/web-research/`). 합성 시점에 install된 신규 MCP는 *다음 세션부터* 사용 가능 (mid-session 미전파 — empirical 4차 사이클). 런타임 신규 채택은 `/harness:harness-mcp-adopt` (§10 dynamic adoption — 별건).
6. **Phase 7 (오케스트레이션)**: 통합 스킬 + Phase 7-4 CLAUDE.md 포인터(트리거 규칙 + 변경 이력) + Phase 7-5 후속 작업 키워드 description 포함.
7. **Phase 8 (검증)**: 7단계 — 구조·실행 모드·실행 테스트·트리거·드라이런·테스트 시나리오·반복 개선.

## 완료 후 체크

`plugins/harness/skills/harness/SKILL.md` §산출물 체크리스트의 24개 항목을 확인한다. 특히 다음 3개는 Phase 10 작동의 전제조건이므로 반드시 확인:

- [ ] `_workspace/_telemetry/` 디렉토리 사전 생성됨
- [ ] 오케스트레이터에 telemetry capture 훅 삽입됨 (매 실행 시 `_telemetry/{date}.jsonl` append)
- [ ] Phase 10 트리거 키워드("점검", "drift", "적응", "baseline 갱신")가 오케스트레이터 description에 포함됨

## 후속 명령어

- 에이전트 추가: `/harness:harness-add-agent <역할>`
- 에이전트/스킬 제거: `/harness:harness-remove <agent|skill> <이름>`
- 책임 분할: `/harness:harness-split <agent|skill> <원본> <결과 2개 이상>`
- 책임 통합: `/harness:harness-merge <agent|skill> <결과> <원본 2개 이상>`
- 진행 가시성 단일 진입점: `/harness:harness-status [--verbose]`
- 결정적 일관성 검증 (LLM 0): `/harness:harness-validate [--json] [--strict]`
- drift 점검 (Phase 10 수동 트리거): `/harness:harness-adapt`
- 런타임 신규 MCP 채택: `/harness:harness-mcp-adopt <사유>` (`permission-profiles.md §10` dynamic adoption)
- MCP 상태 진단 (read-only): `/harness:harness-mcp-status`
