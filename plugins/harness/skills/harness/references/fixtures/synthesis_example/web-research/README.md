# Phase 5-2 + §10 합성 산출물 구체 예시 — `web-research` 시나리오

§5 합성 템플릿이 §10 Step 5의 4 산출물로 결합되는 정합 결과 1세트. **두 번째 시나리오 (14차 사이클 P2 1차 종합 보고)** — `data-analyst` 단일 MCP 패턴에 이어 *멀티 inline `mcpServers:` 패턴*을 박제. 외부 도입자가 자신의 도메인으로 매핑할 때 *형태 참고*.

> ✅ **14차 사이클 박제 근거 (2026-05-11)** — fetch(4종) + memory(9종) 두 MCP 모두 PoC enumeration ✓ (`fixtures/probe_fetch`는 별도 PoC 미박제이나 [§3 인벤토리](../../../permission-profiles.md#3-mcp-후보-인벤토리-tier-분류)에 검증 완료 박제, memory는 `fixtures/probe_memory.js`로 P2 T0 batch에서 확정). 14차 사이클은 두 MCP를 `web-research` capability profile의 *권고 조합*으로 [§3-1 매트릭스](../../../permission-profiles.md#3-1-검증-완료-t0-mcp--capability-profile-매트릭스-14차-사이클-p2-1차-종합-보고)에 박제했다.

## 시나리오

**가상 derived 프로젝트:** "기술 트렌드 리서치 — 외부 블로그/논문/문서를 markdown으로 정제하여 본문 반환 + 도메인 사실은 persistent Knowledge Graph에 누적해 다음 세션의 동일 도메인 질의를 빠르게 재이용."

**자동 합성 결과:**
- 에이전트 `web-research` 1명 (capability profile = `web-research`)
- 매핑 MCP: `fetch` (T0, 4 도구 — 모두 read-only) + `memory` (T0, 9 도구 — CRUD)
- 패턴: **inline `mcpServers:` 멀티 등재** (§5-1 권장 — Layer B subagent 격리, parent 컨텍스트 미적재 + 멀티 MCP 동시 inline)

## 산출물 4종 (§10 Step 5 = "Reflect")

| 산출물 | 파일 | 위치(derived 프로젝트 기준) | 비고 |
|--------|------|---------------------------|------|
| (a) 카탈로그 footnote | (메타) | `plugins/harness/skills/harness/references/permission-profiles.md` §3 fetch/memory 행 | §3-1 매트릭스 `web-research` 행과 동시 갱신 |
| (b) 에이전트 정의 | [`web-research.agent.md`](./web-research.agent.md) | `.claude/agents/web-research.md` | inline `mcpServers:` 멀티 패턴 (fetch + memory) |
| (c) 권한 게이트 | [`settings.json`](./settings.json) | `.claude/settings.json` | fetch 4종 allow + memory 7종(read 3 allow / create+add 3 ask / delete 3 deny) |
| (d) 변경 이력 1행 | [`CLAUDE_md_row.md`](./CLAUDE_md_row.md) | derived 프로젝트의 `CLAUDE.md` "변경 이력" 표 | 멀티 inline 패턴 표기 ("MCP 채택: fetch + memory") |

## 관찰 포인트

1. **멀티 inline 패턴 — 한 에이전트가 N개 MCP 동시 등재** — 본 예시는 `fetch` + `memory` 2개를 같은 `mcpServers:` list에 박음. 10차 cycle P0 empirical 확정으로 inline 패턴은 parent 미적재이므로 N개를 등재해도 *parent 컨텍스트 부담은 0*. 단 **subagent에는 advertise 도구 *전부* 노출** (10차 P0 새 발견)이므로 각 MCP의 부수 효과 도구는 `permissions.deny`에 박제 필수.

2. **CRUD 분리 — read 3 / create+add 3 / delete 3** (memory MCP 특성) — `data-analyst`의 read/write 2분기와 달리 `memory`는 3분기 권한 모델 필요. read(`read_graph`/`search_nodes`/`open_nodes`)는 `allow`로 자동화. create/add(`create_entities`/`create_relations`/`add_observations`)는 KG 누적이라 사용자 확인 가치 있어 `ask`. delete(`delete_*` 3종)는 KG 일관성·이력 보존 위해 `deny` (단순 ask는 사용자가 prompt에서 실수 confirm 시 통과 — 영구 삭제는 `deny`만 안전).

3. **placeholder 0개 — uvx vs npx 차이** — `data-analyst`는 uvx-기반(sqlite)이라 절대경로 placeholder 2개 필수. 본 `web-research`는 npx-기반(fetch + memory)이라 `npx`가 PATH에 통과한다면 placeholder 0개로 OS 무관 작동. **uvx와 npx의 PATH 가용성 차이**: npx는 Node.js install 시 자동 PATH 등록되어 일반적으로 통과, uvx는 user-level pip install이라 PATH 수동 추가 필요한 케이스 다수.

4. **KG 누적의 *세션 간 영속성*** — `memory` MCP는 default로 `~/.memory.json`에 KG 저장. *모든 derived 프로젝트가 공유*. 프로젝트별 격리가 필요하면 inline `args:`에 `--storage <abs-path>` 추가 (단 `--storage` 옵션 지원 여부는 패키지 버전별 별도 확인 — PoC 미완 항목).

5. **mid-session 운영 함의** — 두 MCP 모두 합성 시점에 `claude mcp add` 실행했다면 (또는 inline 패턴이라 등록 자체를 생략했다면 더더욱) 사용자에게 "다음 세션부터 사용 가능" 명시 필수 (§8-2 mid-session 미전파 사실, 4차 cycle empirical). 본 예시는 그 안내 문구를 `web-research.agent.md` 본문 끝에 박제.

## 적용 경계

- 본 예시는 *derived 프로젝트* 대상. dharness root에는 적용하지 않음 (§10/§11 분계).
- "web-research"는 가상 이름 — 실제 도메인에 맞게 이름·도메인 specific 책임을 교체. KG 누적 entity의 명명 규칙(`<도메인>:<항목>` 같은 prefix)은 사용자가 직접 정의.
- 본 예시는 *멀티 inline 패턴*의 형태 참고 — `code-test` profile의 `filesystem` + `git` 결합도 동일 패턴(npx + uvx 혼합)으로 응용 가능.

## 사용 흐름

1. `web-research/` 디렉토리 전체를 *derived 프로젝트*로 복사 후 다음 매핑:
   - `web-research.agent.md` → `<derived>/.claude/agents/web-research.md`
   - `settings.json` → `<derived>/.claude/settings.json` (기존 키와 deep merge — 덮어쓰지 말 것)
   - `CLAUDE_md_row.md`의 한 행 → `<derived>/CLAUDE.md` "변경 이력" 표 끝에 추가
2. **`claude mcp add`는 생략 가능** — inline `mcpServers:` 패턴은 spawn 시 connect되므로 parent 등록 불요 (§5-1 권장). 단 npx PATH 미통과 환경이면 `web-research.agent.md` 본문 끝의 "placeholder 치환 표"에 따라 `command:`를 절대경로로 치환.
3. 세션 재시작 후 `Agent` tool로 `subagent_type: "web-research"` spawn 검증. 첫 spawn 시 subagent의 도구 풀에 `mcp__fetch__*` 4종 + `mcp__memory__*` 9종 노출 확인 (parent ToolSearch에는 미노출 = 10차 cycle P0 양면 검증과 동일).

## 권한 모델 정합 매트릭스 (참고)

| 도구 | bucket | 사유 |
|---|---|---|
| `mcp__fetch__get_raw_text` | allow | read-only, 부수 효과 0 |
| `mcp__fetch__get_rendered_html` | allow | read-only, JavaScript rendered 페이지용 |
| `mcp__fetch__get_markdown` | allow | read-only, 기본 정제 출력 |
| `mcp__fetch__get_markdown_summary` | allow | read-only, 긴 페이지 요약 |
| `mcp__memory__read_graph` | allow | KG read |
| `mcp__memory__search_nodes` | allow | KG read (query) |
| `mcp__memory__open_nodes` | allow | KG read (by name) |
| `mcp__memory__create_entities` | ask | KG 누적 — 사용자 확인 |
| `mcp__memory__create_relations` | ask | KG 누적 — 사용자 확인 |
| `mcp__memory__add_observations` | ask | KG 누적 — 사용자 확인 |
| `mcp__memory__delete_entities` | deny | KG destructive — 영구 삭제 |
| `mcp__memory__delete_observations` | deny | KG destructive — 영구 삭제 |
| `mcp__memory__delete_relations` | deny | KG destructive — 영구 삭제 |

> **bucket 변경 시 양면 갱신:** 위 표를 갱신하면 동 디렉토리의 `settings.json` `permissions.{allow,ask,deny}` + `CLAUDE_md_row.md` 비고 컬럼 카운트도 동시 정합 — drift 시 외부 도입자가 한 세트 복사 후 어긋남.
