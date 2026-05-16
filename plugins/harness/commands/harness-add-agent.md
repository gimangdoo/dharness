---
description: 기존 하네스에 에이전트 1명 추가. Phase 1·2·3 SKIP, baseline 재분석 비용 회피하고 비용 최소로 확장.
argument-hint: <새 에이전트 역할 한 줄 설명>
---

# Harness — Add Agent

기존 하네스가 있다는 전제 하에 새 에이전트 1명을 추가한다. **Phase 1·2·3는 스킵**하여 baseline 재분석 비용을 치르지 않는다. Phase 0 매트릭스의 "에이전트 추가" 행에 해당하는 명시적 진입점이다.

> **Cross-doc 인용 규약 (M3 단일 출처 — 2026-05-14):** 본 문서의 bare `§N`은 `references/permission-profiles.md §N`을 가리킨다. SKILL.md Phase 8 sub-step은 `Phase 8-N` 형식. 예외(다른 doc 참조)는 인라인 명시.

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
   - **부수 효과 분석 (필수, 1줄):** 새 에이전트 도입으로 기존 오케스트레이터의 데이터 흐름이 바뀌면 *기존 다른 에이전트의 입출력 프로토콜에 영향이 있는지* 점검. 영향 발견 시 사용자에게 보고 후 *기존 에이전트 수정은 본 명령 범위 외*임을 명시 — 별도 `/harness:harness-evolve` 또는 `/harness:harness-audit`로 안내.
2. **Phase 5 (에이전트 정의 생성)**: `.claude/agents/{새이름}.md` 작성.
   - **빌트인 타입(`general-purpose`/`Explore`/`Plan`)이라도 파일 생성 필수**
   - `model: "opus"` 명시
   - 필수 섹션: 핵심 역할, 작업 원칙, 입력/출력 프로토콜, 에러 핸들링, 협업, 팀 통신 프로토콜
   - **Phase 5-2 (도구·MCP 자동 할당)** — 절차·doctrine 단일 출처: `permission-profiles.md` §0-2 진입 매트릭스 + `mcp-recommendation.md` §1·§5 (Mg1 통합 — 2026-05-14).
     - **본 명령 진입 시 read 순서** (`permission-profiles.md` §0-2 표 발췌):
       1. `mcp-recommendation.md` §1 (signal 10종 S1~S10 추출)
       2. `permission-profiles.md` §2 (8 capability profile 매칭)
       3. `permission-profiles.md` §3·§3-1 (T0 7종 매트릭스 1차 후보)
       4. `permission-profiles.md` §4 결정 트리 (profile → MCP 매핑 + 분기 a/b/c/d)
       5. `permission-profiles.md` §5-1 (inline `mcpServers:` 합성) + §5-3 (permissions deny 강제)
     - **사용자 confirm gate**: profile 확정 + MCP 후보 표 (§3-1 + mcp-recommendation §3 점수) 동봉. `claude mcp list`로 install 여부 확인.
     - **본 명령 *범위 외* (별도 진입점 위임)**:
       - 런타임 MCP 채택 (§4 분기 c 발화 — MCP 미install) → `/harness:harness-mcp-adopt <사유>` (§10 5-step). 본 명령 *합성 즉시 중단* + 사용자 안내 출력 후 응답 종료. **자동 install 금지** (§6).
       - 합성 *후* 정합 진단 → `/harness:harness-mcp-status`
     - **본 명령 *고유* 안내 (단일 출처)**:
       - 신규 MCP를 *합성 시점*에 install했다면 사용자에게 **"다음 세션부터 사용 가능"** 명시 (mid-session 미전파 — empirical 확정, §5-1 cycle 4)
       - inline `mcpServers:` 합성 시 부수 효과 도구는 **반드시 `settings.json permissions.deny` 박제** (Layer C 강제, §5-3 doctrine)
3. **Phase 7-1·7-3 (오케스트레이터 수정)**: 기존 오케스트레이터 스킬에 새 에이전트 반영.
   - 팀 구성·작업 할당·데이터 흐름 갱신
   - description에 새 트리거 키워드(있으면) 추가
   - **새 오케스트레이터 생성 금지** — 기존 수정만
4. **Phase 8 (검증, 부분)** — `SKILL.md` Phase 8 sub-step 매핑:
   - **필수**: Phase 8-1 구조 검증, Phase 8-2 실행 모드 검증, Phase 8-4 트리거 검증
   - **변경 영향 시**: Phase 8-3 실행 테스트, Phase 8-5 드라이런
5. **CLAUDE.md 변경 이력 갱신**: Phase 7-4 템플릿 형식으로 한 행 추가.
   ```
   | {YYYY-MM-DD} | 에이전트 추가: {이름} | 오케스트레이터 + .claude/agents/ | {사유} |
   ```

6. **출력 마지막 단계 — 사용자 안내 템플릿 (필수, 합성 시 신규 MCP install이 발생한 경우)**:
   합성 결과 보고 마지막에 *반드시* 다음 형식으로 출력 (LLM이 빠뜨리지 않도록 강제):
   ```
   ✅ 합성 완료
     - .claude/agents/<name>.md 생성
     - .claude/settings.json permissions 갱신 (allow N종 / ask M종 / deny K종)
     - CLAUDE.md 변경 이력 1행 추가
     - 신규 MCP install: <server-name> ✓ Connected

   ⚠️ 다음 세션부터 사용 가능 — mid-session에 install된 MCP는 본 세션 도구 풀과 기 spawn된 subagent inherit pool에 미적재 (§5-1 cycle 4 empirical 확정).
   다음 세션 시작 후 `/harness:harness-mcp-status`로 정합 점검 권고.
   ```
   *MCP install 없이 빌트인만 합성한 경우*는 ⚠️ 단락 생략, ✅ 단락만 출력.

## 범위 외

- **스킬은 새로 만들지 않는다** — 새 에이전트가 전용 스킬을 필요로 하면 별도로 `/harness:harness-add-skill`(차후 추가) 호출, 또는 사용자에게 안내
- **baseline 갱신하지 않는다** — 코드/의도가 크게 바뀌었다고 판단되면 `/harness:harness-baseline`로 안내
- **Phase 10 trigger 안 함** — drift 점검은 `/harness:harness-adapt`
- **MCP 상태 진단 안 함** — 합성 *전후* 인벤토리/정합 진단이 필요하면 `/harness:harness-mcp-status` (read-only). 런타임 채택은 `/harness:harness-mcp-adopt <사유>`.
