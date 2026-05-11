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
   - **부수 효과 분석 (필수, 1줄):** 새 에이전트 도입으로 기존 오케스트레이터의 데이터 흐름이 바뀌면 *기존 다른 에이전트의 입출력 프로토콜에 영향이 있는지* 점검. 영향 발견 시 사용자에게 보고 후 *기존 에이전트 수정은 본 명령 범위 외*임을 명시 — 별도 `/harness:harness-evolve` 또는 `/harness:harness-audit`로 안내.
2. **Phase 5 (에이전트 정의 생성)**: `.claude/agents/{새이름}.md` 작성.
   - **빌트인 타입(`general-purpose`/`Explore`/`Plan`)이라도 파일 생성 필수**
   - `model: "opus"` 명시
   - 필수 섹션: 핵심 역할, 작업 원칙, 입력/출력 프로토콜, 에러 핸들링, 협업, 팀 통신 프로토콜
   - **Phase 5-2 (도구·MCP 자동 할당)**: capability profile 매칭 → `claude mcp list`로 인벤토리 확인 → 사용자 confirm → frontmatter `tools:` allowlist 합성. 카탈로그·결정 트리·안전 정책은 `plugins/harness/skills/harness/references/permission-profiles.md` 단일 출처(§3-§7). 외부 MCP는 자동 install·자동 `allow` 금지(T0 한정).
     - **§3-1 매트릭스 1차 후보 발췌 (14차 사이클 — `런타임 가용 default 카탈로그`):** profile 확정 후 §3-1에서 행 매핑 — code-test(`git`+`filesystem`) / web-research(`fetch`+`memory`) / external-integration(`sqlite`) / reasoning-aux(`sequential-thinking`+`time`). 각 행에 `default permissions bucket`이 박제되어 있어 `permissions.allow/ask/deny` 합성에 1:1 활용. 멀티 inline `mcpServers:` 패턴(N개 MCP 동시 등재) 예시는 `fixtures/synthesis_example/web-research/`(fetch+memory) + §3-1 "채택 패턴 권고" YAML 참조.
     - 신규 MCP를 *합성 시점*에 install했다면 사용자에게 **"다음 세션부터 사용 가능"** 명시 (mid-session 미전파 — empirical 확정).
     - 프로젝트 진행 중 신규 MCP 채택은 **§10 dynamic adoption** — 별도 진입점 `/harness:harness-mcp-adopt <사유>` (본 명령 범위 외).
     - **🆕 inline `mcpServers:` 합성 시 deny 박제 default (10차 P0 새 발견 함의):** inline 서버의 도구는 frontmatter `tools:` allowlist로 *줄지 않으므로*, 부수 효과 도구(`write_*`/`insert_*`/`update_*`/`delete_*`/`exec_*` 등)는 *반드시* `settings.json permissions.deny`에 박제. `ask`로 강등하면 사용자 confirm 1회로 통과 — strict read-only 의도라면 `deny`가 default (§5-3 참조). 합성 후 정합 점검은 `/harness:harness-mcp-status` §4 (deny vs inline advertise 도구 매트릭스).
     - **§4 결정 트리 분기 c (MCP 미install) 발화 시 처리:**
       1. 본 명령(`harness-add-agent`)에서 *합성을 즉시 중단* — agent.md / settings.json / CLAUDE.md 4 산출물 어느 하나도 작성하지 않음.
       2. 사용자에게 다음 안내를 출력 후 응답 종료:
          ```
          ⚠️ 합성 중단 — 새 에이전트의 capability profile에 매핑되는 MCP `<server-name>`이 현재 derived 프로젝트에 미install.
          → 먼저 `/harness:harness-mcp-adopt <사유>`로 채택 (§10 5-step: discover → probe → confirm → install → reflect)
          → install 완료 + *세션 재시작* 후 본 명령(`/harness:harness-add-agent <역할>`) 재호출
          ```
       3. 재호출 시 §4 결정 트리 분기 a/b가 발화하도록 *세션 재시작 후*에만 진행 — mid-session에서는 install된 MCP가 도구 풀에 미적재라 합성해도 inline `mcpServers:` 검증 불가.
       4. **자동 install·자동 fallback 금지 (§6)** — 본 분기에서 LLM이 임의로 `claude mcp add`를 실행하면 §6 정책 위반.
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
