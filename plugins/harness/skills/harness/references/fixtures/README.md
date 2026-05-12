# Permission-profiles fixtures — §10 pre-install probe + 합성 예시

`plugins/harness/skills/harness/references/permission-profiles.md` §10 dynamic adoption Step 2 (pre-install probe)와 §5 합성 산출물의 *복사 실행만으로 끝낼 수 있는* fixture 모음.

## Pre-install probe (`probe_*.js`)

각 fixture는 install 없이 stdio JSON-RPC `tools/list` 핑으로 MCP 서버의 도구 카탈로그를 enumerate한다. 출력: `COUNT=N` + per-tool `name·required·all-params`.

| 파일 | MCP | Tier | Runtime | 메모 |
|------|-----|------|---------|------|
| `probe_fetch.js` (예) | fetch | T0 | npm | (해당 파일 없으면 패턴은 sqlite 동일) |
| `probe_filesystem.js` | filesystem | T0 | npm | 14 도구 (read 10 + write 4) |
| `probe_memory.js` | memory | T0 | npm | 9 도구 (Knowledge Graph) |
| `probe_sqlite.js` | sqlite | T0 | uvx | 6 도구. `--db-path` 절대경로 필수 |
| `probe_time.js` | time | T0 | uvx | 2 도구 (모두 read-only) |
| `probe_playwright.js` | playwright | T1 | npm | default 23 + caps 분해 측정 (`$env:PLAYWRIGHT_FLAGS="--caps=vision"`) |
| `probe_chrome_devtools.js` | chrome-devtools | T1 | npm | 44 도구 docs 박제. **engines `node ^20.19 \|\| ^22.12 \|\| >=23` 요구** — Node 18 spawn hard fail |
| `probe_brave_search.js` | brave-search | T1+ | npm | 8 도구. `BRAVE_API_KEY` 필요 |
| `probe_tavily.js` | tavily | T1+ | npm | 4 도구. `TAVILY_API_KEY` + 도구명 하이픈 (첫 케이스) |
| `probe_exa.js` | exa | T1+ | npm | 3 active + 7 deprecated. `EXA_API_KEY` 필요 |
| `probe_github.js` | github | T1+ | Docker | toolsets 19 (PAT 필요). `GITHUB_TOOLSETS` env 토글 |
| `probe_firecrawl.js` | firecrawl | T2~ | npm | 10 active + 4 deprecated browser. `FIRECRAWL_API_KEY` (유료 quota) |

> ⚠️ **probe도 코드 실행** — `npx -y <pkg>` / `uvx <pkg>` 둘 다 임의 패키지를 spawn. install과 동일 위협 모델. 실행 전 패키지 출처 trust 확인 필수 ([§8-3](../permission-profiles.md#8-3-재사용-가능한-검증-기법)).

### 사용법

```powershell
# 기본
node plugins\harness\skills\harness\references\fixtures\probe_sqlite.js

# env 토글 (예: playwright caps 분해 측정)
$env:PLAYWRIGHT_FLAGS="--caps=vision"; node plugins\harness\skills\harness\references\fixtures\probe_playwright.js

# T1+ (API 키 필요)
$env:BRAVE_API_KEY="<key>"; node plugins\harness\skills\harness\references\fixtures\probe_brave_search.js
```

## 합성 산출물 예시 (`synthesis_example/`)

§5 합성 + §10 Step 5 산출물 1세트를 시나리오별 디렉토리로 제공. 외부 도입자가 자신의 도메인으로 매핑할 때 *형태 참고*.

| 디렉토리 | 시나리오 | 패턴 |
|----------|----------|------|
| `synthesis_example/data-analyst/` | sqlite 분석 에이전트 | **단일 inline `mcpServers:`** (sqlite 1종) |
| `synthesis_example/web-research/` | fetch + memory 리서치 에이전트 | **멀티 inline `mcpServers:`** (fetch + memory 2종 동시 등재) |

각 디렉토리에 `.agent.md` / `settings.json` / `CLAUDE_md_row.md` / `README.md` 4 파일 — 4 산출물 1세트 ([§10 Step 5](../permission-profiles.md#10-2-5-step-채택-절차-모든-트리거-공통)).

## 관련 문서

| 주제 | 위치 |
|------|------|
| §10 dynamic adoption 5-step | [`../permission-profiles.md` §10](../permission-profiles.md#10-dynamic-mcp-adoption--프로젝트-진행에-따른-mcp-신규-채택) |
| §8-3 재사용 검증 기법 (stdio JSON-RPC probe 패턴) | [`../permission-profiles.md` §8-3](../permission-profiles.md#8-3-재사용-가능한-검증-기법) |
| §3 MCP 인벤토리 (Tier 분류 + install 명령) | [`../permission-profiles.md` §3](../permission-profiles.md#3-mcp-후보-인벤토리-tier-분류) |
| §3-1 T0 MCP × capability profile 매트릭스 | [`../permission-profiles.md` §3-1](../permission-profiles.md#3-1-검증-완료-t0-mcp--capability-profile-매트릭스) |
