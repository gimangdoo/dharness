# Phase 5-2 + §10 합성 산출물 구체 예시 — `data-analyst` 시나리오

§5 합성 템플릿이 §10 Step 5의 4 산출물로 결합되는 정합 결과 1세트. 외부 도입자가 자신의 도메인으로 매핑할 때 *형태 참고*.

## 시나리오

**가상 derived 프로젝트:** "이커머스 sales 데이터 정량 분석 — 로컬 SQLite DB(`./data/sales.db`)에서 일별 매출·코호트 retention 산출."

**자동 합성 결과:**
- 에이전트 `data-analyst` 1명 (capability profile = `external-integration` + `code-test` 부분 hybrid)
- 매핑 MCP: `sqlite` (T0, 로컬 DB만) — read 도구 3종 자동 `allow`, write 2종 `ask` 게이트
- 패턴: inline `mcpServers:` (§5-1 권장 — Layer B subagent 격리, parent 컨텍스트 미적재)

## 산출물 4종 (§10 Step 5 = "Reflect")

| 산출물 | 파일 | 위치(derived 프로젝트 기준) | 비고 |
|--------|------|---------------------------|------|
| (a) 카탈로그 footnote | (메타) | `plugins/harness/skills/harness/references/permission-profiles.md` §3 sqlite 행 | 본 fixture에는 텍스트만 — 실제 갱신은 §10 적용 시점 |
| (b) 에이전트 정의 | [`data-analyst.agent.md`](./data-analyst.agent.md) | `.claude/agents/data-analyst.md` | inline `mcpServers:` 패턴 |
| (c) 권한 게이트 | [`settings.json`](./settings.json) | `.claude/settings.json` | sqlite read 3종 allow / write 2종 ask |
| (d) 변경 이력 1행 | [`CLAUDE_md_row.md`](./CLAUDE_md_row.md) | derived 프로젝트의 `CLAUDE.md` "변경 이력" 표 | 1행 그대로 복사 가능 |

## 관찰 포인트

1. **inline vs `.mcp.json` 선택** — 본 예시는 *inline* (subagent 격리 + parent 미적재). 만약 parent도 sqlite 도구를 호출해야 하면 §5-2 `.mcp.json` 패턴으로 전환 (이 경우 settings.json `enabledMcpjsonServers` 추가 필수, §11-3 토글 결과에 따라 토큰 영향 결정).

2. **read vs write 분리** — `read_query` / `list_tables` / `describe_table`는 `allow` (자동), `write_query` / `append_insight`는 `ask` (사용자 confirm 매번). Tier T0이라도 *부수 효과*가 있는 도구는 ask로 분리하는 것이 §6 정책의 실제 적용 형태.

3. **mid-session 운영 함의** — 합성 시점에 sqlite MCP를 install했다면 사용자에게 "다음 세션부터 사용 가능" 명시 필수 (§8-2 mid-session 미전파 사실). 본 예시는 그 안내 문구를 `data-analyst.agent.md` 본문 끝에 박제.

## 적용 경계

- 본 예시는 *derived 프로젝트* 대상. dharness root에는 적용하지 않음 (§10/§11 분계).
- "data-analyst"는 가상 이름 — 실제 도메인에 맞게 이름·도메인 specific 책임을 교체.
- sqlite MCP는 §11-4에서 PoC 미완 상태 (probe 전용 fixture만 있음). 본 예시는 *enumeration 결과를 가정한* 형태이며, 실제 도구명·params는 `probe_sqlite.js` 실행으로 1차 확정 후 본 fixture를 갱신해야 한다.

## 사용 흐름

1. `synthesis_example/` 디렉토리 전체를 *derived 프로젝트*로 복사 후 다음 매핑:
   - `data-analyst.agent.md` → `<derived>/.claude/agents/data-analyst.md`
   - `settings.json` → `<derived>/.claude/settings.json` (기존 키와 deep merge — 덮어쓰지 말 것)
   - `CLAUDE_md_row.md`의 한 행 → `<derived>/CLAUDE.md` "변경 이력" 표 끝에 추가
2. derived 프로젝트에서 `claude mcp add sqlite ...` 실행 (§10 Step 4)
3. 세션 재시작 후 `Agent` tool로 `subagent_type: "data-analyst"` spawn 검증
