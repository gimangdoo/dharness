# Permission Profiles — MCP 후보 인벤토리

> **Read at phase:** Phase 5-2 (MCP 후보 검색 시), §10 dynamic adoption Step 1 (discover).
>
> P7 분리(2026-05-23) — `permission-profiles.md` §3·§3-0·§3-1을 본 파일로 흡수. main 본문의 §3 위치엔 pointer만 잔존.

`*` = 공식 reference (anthropic/modelcontextprotocol), `+` = API 키 필요, `~` = 유료/민감 데이터

## §3. MCP 후보 인벤토리 (Tier 분류)

### 3-0. verification_status 정책 (P6-9 — 2026-05-14)

§3 인벤토리의 각 MCP는 다음 3 status 중 하나로 분류 — Phase 5-2 *합성 default 풀* 포함 여부 결정.

| status | symbol | 합성 default 풀 | 점수 페널티 (`A` 정확도) | 사용 자격 |
|---|---|---|---|---|
| **probe-verified** | ✓ | 포함 | +4 (probe ✓ 보너스 — 기존 §3 점수표 정합) | 즉시 사용 가능. fixture source-grep 100% 일치 + 도구 enumeration 박제 |
| **docs-only** | 📜 | **제외** | -2 ("docs only" 페널티 — `mcp-recommendation.md §3` 매핑) | 사용자 명시 R-7 confirm + §10 Step 2 probe 통과 시 승격 |
| **pending** | ⚠️ | **제외** | -4 (대칭 페널티 — 박제 정보 부족) | §10 dynamic adoption 진입 + Step 2 probe 필수. inline `mcpServers:` 직접 합성 ❌ |

#### MCP × verification_status (2026-05-14 cycle 박제)

| MCP | status | 근거 |
|---|---|---|
| `fetch` / `sequential-thinking` / `git` / `sqlite` | ✓ | `fixtures/probe_*.js` 실행 OK + `tools/list` source-grep 100% 일치 (cycle ≤22) |
| `filesystem` / `time` / `memory` | ✓ (probe-only) | install 미수행이나 stdio JSON-RPC probe로 도구 enum 확정 (13~18차 cycle) |
| `playwright` | ✓ | 22차 외부 PowerShell probe 실행 — default 23종 + caps=vision +6종 empirical 확정 |
| `chrome-devtools` | 📜 → ✓ (verify-only) | 23차 npm/GitHub source verify 확정 (Google LLC org / Apache-2.0 / mcpName 정합). Node ≥20.19 host 환경 의존. probe 도구 enum은 host 측 별건 |
| `brave-search` / `tavily` / `exa` / `firecrawl` / `github` | 📜 | docs 박제 (17차) + 18차 fixture 준비. API 키 보유 후 §10 Step 2 probe 필수 |
| `slack` / `postgres` | ⚠️ | 이름·Tier·카테고리만 박제. 합성 default 풀 ❌ |

> **합성 default 풀 doctrine (P6-9):** Phase 5-2가 inline `mcpServers:` *자동 합성* 시 ✓ 외 status는 **금지**. 📜는 R-7 confirm gate에서 *제안*만, ⚠️는 §10 dynamic adoption 진입 안내 후 응답 종료.
>
> **점수 페널티 정합 (`mcp-recommendation.md §3` cross-reference):** docs-only `-2`, pending `-4`. 본 표 갱신 시 mcp-recommendation 양 doc 동시 적용 필수.
>
> **status 승격 워크플로우:** 📜 → ✓는 §10 Step 2 probe 1회로 자동 승격. ⚠️ → 📜는 trusted source 확인 + fixture 준비 (`fixtures/probe_<server>.js`) 후 확정. ⚠️ → ✓는 1단계 점프 ❌ (probe 완료가 docs 박제 확정을 함의 X — npm cross-check + source verify 별건).


| Tier | 정의 | 자동 적용 정책 |
|------|------|--------------|
| **T0** | 무키·로컬 only | 사용자 1회 동의 후 `allow` 가능 |
| **T1** | 무료 API 키 또는 PAT 필요 | 키 등록 + 사용자 명시 동의 → `allow` |
| **T2** | 유료 또는 민감 외부 시스템 | 항상 `ask`, 자동 `allow` 금지 |

| MCP | Tier | 카테고리 | install 명령 (검증 시점) | 도구 enumeration |
|-----|------|---------|-----------------|---|
| `fetch` (mcp-server-fetch-typescript) | T0 | research | `claude mcp add fetch -- npx -y mcp-server-fetch-typescript` ✓ | 4종: `get_raw_text`, `get_rendered_html`, `get_markdown`, `get_markdown_summary` ✓ |
| `sequential-thinking` * | T0 | reasoning-aux | `claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking` ✓ | 1종: `sequentialthinking` ✓ |
| `filesystem` * | T0 | code-test | `claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem <allowed-path-1> [<allowed-path-2>...]` ✓ probe-only (13차 사이클 후속, plugin host 본 저장소 미install — `fixtures/probe_filesystem.js`) | 14종 ✓: **read 10종** = `read_file`, `read_text_file`, `read_media_file`, `read_multiple_files`, `list_directory`, `list_directory_with_sizes`, `directory_tree`, `search_files`, `get_file_info`, `list_allowed_directories` + **write 4종** = `write_file`, `edit_file`, `create_directory`, `move_file` (default 권고: read 10종 `allow`, write 4종 `deny` 또는 `ask` — 빌트인 Read/Write/Edit과 중복이라 *capability profile = code-test의 path-roots 격리 가치*가 핵심 사용 사례) |
| `git` * (Python, uvx) | T0 | code-test | `claude mcp add git <uvx-abs-path> -- mcp-server-git --repository <repo-abs>` ✓ (uvx는 `pip install --user uv` 후 `%APPDATA%\Python\Python312\Scripts\uvx.exe`) | 12종 ✓: `git_status`, `git_diff_unstaged`, `git_diff_staged`, `git_diff`, `git_commit`, `git_add`, `git_reset`, `git_log`, `git_create_branch`, `git_checkout`, `git_show`, `git_branch` (모두 `repo_path` required, 변형 도구는 `target`/`message`/`files`/`branch_name`/`revision`/`branch_type` 추가 required) |
| `time` * | T0 | reasoning-aux | `claude mcp add time <uvx-abs-path> -- mcp-server-time` ✓ probe-only (Python, uvx 경유 — `fixtures/probe_time.js`) | 2종 ✓ (모두 read-only): `get_current_time` (`required=[timezone]`), `convert_time` (`required=[source_timezone,time,target_timezone]`) — 부수 효과 0, default 권고: 2종 모두 `allow` |
| `memory` * | T0 | reasoning-aux / web-research (cross-mapping) | `claude mcp add memory -- npx -y @modelcontextprotocol/server-memory` ✓ probe-only (Knowledge Graph storage, npm — `fixtures/probe_memory.js`) | 9종 ✓: **read 3종** = `read_graph`, `search_nodes` (`required=[query]`), `open_nodes` (`required=[names]`) + **create/add write 3종** = `create_entities`, `create_relations`, `add_observations` + **delete write 3종** = `delete_entities`, `delete_observations`, `delete_relations`. default 권고: read 3 `allow` / create+add 3 `ask` / delete 3 `deny` (destructive). plugin host self-host CM (운영 시)은 자체 sqlite 사용 — memory MCP는 *외부 derived 프로젝트의 persistent knowledge graph* 용도. **§3-1 매트릭스에선 `web-research` 행에 매핑** (Knowledge Graph는 외부 리서치 사실 누적용) — `reasoning-aux` profile에서도 도메인 사실 회상에 사용 가능 (capability profile은 mutually exclusive 아님) |
| `sqlite` * | T0 | external-integration | `claude mcp add sqlite <uvx-abs-path> -- mcp-server-sqlite --db-path <db-abs-path>` ✓ (8차 사이클, derived 프로젝트에서 검증; **`--db-path`는 절대경로 필수** — 상대경로면 health check `✗ Failed to connect`) | 6종 ✓: `read_query`, `write_query`, `create_table`, `list_tables`, `describe_table`, `append_insight` (read 3종을 allow, `write_query`/`create_table`/`append_insight` 3종을 deny/ask로 게이트 권장) |
| `playwright` (microsoft/playwright-mcp) | T1 | code-test | `claude mcp add playwright -- npx -y @playwright/mcp@latest [--caps=vision,pdf,devtools,network,storage,testing,config] [--browser=chromium\|firefox\|webkit\|msedge] [--isolated] [--headless]` ✅ probe-only empirical (22차 사이클, 외부 PowerShell `node fixtures/probe_playwright.js` 1회 — 본 세션 classifier 차단, 17차 §6 재확인 우회) | ✅ **probe ✓ 23종 default (22차 empirical, 17차 docs 박제 일부 정정)**: **navigation 2종** = `browser_navigate`, `browser_navigate_back` + **interaction 10종** = `browser_click`, `browser_drag`, `browser_hover`, `browser_select_option`, `browser_type`, `browser_press_key`, `browser_drop`, `browser_fill_form`, `browser_file_upload`, `browser_handle_dialog` + **inspect 4종** = `browser_snapshot`, `browser_take_screenshot`, `browser_wait_for`, `browser_console_messages` + **network 2종 (default)** = `browser_network_requests`, `browser_network_request` (🆕 22차 정정 — 17차 docs는 *caps=network opt-in*으로 추정했으나 *default에 2종 포함*) + **browser control 4종** = `browser_close`, `browser_resize`, `browser_evaluate`, `browser_run_code_unsafe` (⚠️ RCE-equivalent — 항상 `deny` 권고) + **tabs 1종** = `browser_tabs`. **caps=vision +6종 (22차 empirical 정정 — 17차 추정 5종 → 6종)** = `browser_mouse_move_xy`, `browser_mouse_click_xy`, `browser_mouse_drag_xy`, `browser_mouse_down`, `browser_mouse_up`, `browser_mouse_wheel` (🆕 *coordinate-based mouse 조작* — screenshot은 default에 이미 포함, vision의 진짜 의미는 좌표 기반 mouse 활성화 — vision-guided clicking). 다른 caps(pdf/devtools/network/storage/testing/config) 분해 측정 미완 — 외부 측정 권고: `$env:PLAYWRIGHT_FLAGS="--caps=<X>"; node fixtures/probe_playwright.js`로 각 caps의 추가 도구 enum. **부수 효과**: 첫 spawn 시 Chromium ~120MB lazy 다운로드 (browser_navigate 호출 시점) — **tools/list 단계엔 미발생** (22차 empirical 확정 — npx 패키지만 fetch, browser binary는 lazy) — 사용자 명시 confirm은 첫 navigate 시점에만 필요 |
| `chrome-devtools` (ChromeDevTools/chrome-devtools-mcp) | T1 | code-test | `claude mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest` (auto-launch — **default**) 또는 외부 Chrome 연결 시 `--browser-url=http://127.0.0.1:9222` 또는 `--ws-endpoint=<url>` (선조건: `chrome --remote-debugging-port=9222 --user-data-dir=<dir>`). 📜 docs 박제 (17차 사이클) + ✅ **패키지 출처 verify 확정** (23차 사이클): npm Author=**Google LLC** / Maintainers=mathias·orkon·google-wombot / GitHub `ChromeDevTools` org (39.2k★) / Apache-2.0 / latest v0.25.0 (2026-05-06) / mcpName `io.github.ChromeDevTools/chrome-devtools-mcp` — spoofing 위험 0, fixture `probe_chrome_devtools.js` "후보 1" 표기 ✅로 승급. 🚫 **Node engines 함정 (23차 empirical)**: 모든 49 versions이 `node ^20.19 \|\| ^22.12 \|\| >=23` 요구 (npm view 7 버전 cross-check); 측정 host 세션 v18.15.0에서 fixture 직접 spawn → `ERROR: chrome-devtools-mcp does not support Node v18.15.0` 즉시 종료. derived 프로젝트별 §10 진입 시 사용자 측 Node 20.19+ 가용성 확인 필수 (`--autoConnect` flag는 추가로 Chrome 144+ 요구). | 📜 docs 박제 44종 (17차 사이클): **input 10종** = `click`, `drag`, `fill`, `fill_form`, `handle_dialog`, `hover`, `press_key`, `type_text`, `upload_file`, `click_at` + **navigation 6종** = `close_page`, `list_pages`, `navigate_page`, `new_page`, `select_page`, `wait_for` + **emulation 2종** = `emulate`, `resize_page` + **performance 3종** = `performance_analyze_insight`, `performance_start_trace`, `performance_stop_trace` + **network 2종** = `get_network_request`, `list_network_requests` + **debugging 8종** = `evaluate_script`, `get_console_message`, `lighthouse_audit`, `list_console_messages`, `take_screenshot`, `take_snapshot`, `screencast_start`, `screencast_stop` + **memory 4종** = `take_memory_snapshot`, `get_memory_snapshot_details`, `get_nodes_by_class`, `load_memory_snapshot` + **extensions 5종** = `install_extension`, `list_extensions`, `reload_extension`, `trigger_extension_action`, `uninstall_extension` (⚠️ `install_extension`/`uninstall_extension` 권한 격상 — `deny` 권고) + **3p/webmcp 4종** = `execute_3p_developer_tool`, `list_3p_developer_tools`, `execute_webmcp_tool`, `list_webmcp_tools` (⚠️ `execute_*` 임의 코드 surface — `deny` 권고). **부수 효과**: auto-launch 모드는 Chromium 다운로드 또는 시스템 Chrome 기동 |
| `brave-search` * (brave/brave-search-mcp-server) | T1+ | research | `claude mcp add brave-search -e BRAVE_API_KEY=<key> -- npx -y @brave/brave-search-mcp-server --transport stdio` 📜 docs 박제 (17차 사이클 — API 키 보유 시점에 PoC) + 🔧 fixture: `fixtures/probe_brave_search.js` (18차 사이클) | 📜 docs 박제 8종 (17차 사이클): `brave_web_search`, `brave_local_search`, `brave_video_search`, `brave_image_search`, `brave_news_search`, `brave_summarizer`, `brave_place_search`, `brave_llm_context`. **모두 read-only** — default 권고 8종 `allow` (단 API quota 소진 부수 효과 — T1+에선 `ask`로 게이트 권장) |
| `tavily` (tavily-ai/tavily-mcp) | T1+ | research | `claude mcp add tavily -e TAVILY_API_KEY=<key> -- npx -y tavily-mcp@latest` 📜 docs 박제 (17차 사이클) + 🔧 fixture: `fixtures/probe_tavily.js` (18차 사이클 — 도구명 하이픈 첫 케이스 검증 의제 포함) | 📜 docs 박제 4종 (17차 사이클): `tavily-search`, `tavily-extract`, `tavily-map`, `tavily-crawl`. ⚠️ **하이픈 도구명** — `mcp__<server>__<tool>` 노출 시 변환 룰 확인 필요 (sequential-thinking 패턴은 `mcp__sequential-thinking__sequentialthinking`로 도구명 자체엔 하이픈 없음, tavily는 도구명에 하이픈 — 첫 케이스). 모두 read-only 검색·추출 — default 권고 4종 `allow` |
| `exa` (exa-labs/exa-mcp-server) | T1+ | research | `claude mcp add exa -e EXA_API_KEY=<key> -- npx -y exa-mcp-server` (또는 remote: `https://mcp.exa.ai/mcp?exaApiKey=<key>&tools=web_search_exa,web_fetch_exa,web_search_advanced_exa`) 📜 docs 박제 (17차 사이클) + 🔧 fixture: `fixtures/probe_exa.js` (18차 사이클 — deprecated 7종 자동 태깅 inline) | 📜 docs 박제 (17차 사이클): **default 2종** = `web_search_exa`, `web_fetch_exa` + **opt-in 1종** = `web_search_advanced_exa` + **deprecated 7종** = `get_code_context_exa`, `company_research_exa`, `crawling_exa`, `people_search_exa`, `linkedin_search_exa`, `deep_researcher_start`, `deep_researcher_check`, `deep_search_exa` (deprecated는 사용 권고 X). 모두 read-only — default 권고 3종 `allow` |
| `github` (github/github-mcp-server) | T1+ | external-integration | ⚠️ **No npm package** (17차 사이클 docs 정정 — 기존 §3 행이 npm 가정이었음). Docker: `claude mcp add github -- docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN=<pat> -e GITHUB_TOOLSETS=context,repos,issues,pull_requests,users ghcr.io/github/github-mcp-server` 또는 Go 바이너리: `go build -o github-mcp-server ./cmd/github-mcp-server && ./github-mcp-server stdio` 📜 docs 박제 (17차 사이클 정정) + 🔧 fixture: `fixtures/probe_github.js` (18차 사이클 — Docker spawn + `GITHUB_TOOLSETS` 3 조합 비교 측정 의도) | ✅ `GITHUB_TOOLSETS` env: 19종(`context`/`repos`/`issues`/`pull_requests`/`users` 5종 default + `actions`/`code_security`/`copilot`/`dependabot`/`discussions`/`gists`/`git`/`labels`/`notifications`/`orgs`/`projects`/`secret_protection`/`security_advisories`/`stargazers`) + 특수 `all`. 도구별 enum은 PAT 필요 — toolset당 ~5-15 도구 추정, 실 enum은 사용자 측 키 보유 시점에 별건 |
| `firecrawl` (mendableai/firecrawl-mcp-server) | T2~ | research | `claude mcp add firecrawl -e FIRECRAWL_API_KEY=fc-<key> -- npx -y firecrawl-mcp` (자체호스팅 시 `-e FIRECRAWL_API_URL=<endpoint>`) 📜 docs 박제 (17차 사이클 — 유료 quota 소진 부수 효과로 T2~) + 🔧 fixture: `fixtures/probe_firecrawl.js` (18차 사이클 — deprecated 4종 자동 태깅 + `firecrawl_browser_execute` 🚫 deny 권고 inline) | 📜 docs 박제 14종 (17차 사이클): **read 5종** = `firecrawl_scrape`, `firecrawl_search`, `firecrawl_map`, `firecrawl_extract`, `firecrawl_check_batch_status` + **batch/crawl 4종** = `firecrawl_batch_scrape`, `firecrawl_crawl`, `firecrawl_check_crawl_status`, `firecrawl_agent`, `firecrawl_agent_status` (⚠️ 대규모 API quota 소진 — `ask` 권고) + **deprecated browser 4종** = `firecrawl_browser_create`, `firecrawl_browser_execute`, `firecrawl_browser_list`, `firecrawl_browser_delete` (사용 권고 X). default 권고: read 5종 `ask` (T2~) / batch+crawl `ask` / `firecrawl_browser_execute` `deny` (임의 코드 실행) |
| `slack` | T2~ | external-integration | (PoC 미완) | (PoC 미완) |
| `postgres` * | T2~ | external-integration | (PoC 미완) | DB 접속 문자열로 제한 |

> **검증된 도구 참조 패턴 (frontmatter `tools:`)**: `mcp__<server>__<tool>` — 예: `mcp__fetch__get_markdown`, `mcp__sequential-thinking__sequentialthinking`. **서버명·도구명의 하이픈/언더스코어는 문자열 그대로 보존됨 (§11-1 6차 사이클 ✓ 확정)** — sequential-thinking이 `mcp__sequential-thinking__sequentialthinking`으로 노출됨이 다음 세션 SessionStart deferred tool list로 측정 완료. 17종 모두 §3 인벤토리 enumeration과 100% 일치.

> "검증 미완"은 본 문서 작성 시점에 실제 install·도구 enumeration·옵션 확인이 안 된 항목 — PoC에서 채워야 함.

> ⚠️ **PoC 미완 항목 사용 시 안전 룰 (§10 진입 전 필수)**
>
> 본 표에서 "(PoC 미완)" 표기된 항목(`filesystem`/`time`/`memory`/`playwright`/`chrome-devtools`/`brave-search`/`tavily`/`exa`/`firecrawl`/`slack`/`postgres`)은 **이름·Tier·카테고리만 박제된 *추정 후보***이다. 다음 셋 모두 미검증:
> - 실제 install 명령 (특히 패키지 spoofing 변형 가능성)
> - 도구 enumeration (이름·required params·schema)
> - toolset 필터 옵션 (env 또는 CLI flag)
>
> **§10 dynamic adoption 진입 시 필수 단계 (Step 2 pre-install probe 1회)**:
> 1. trusted source 확인(§8-3 안전 룰) — github.com/modelcontextprotocol/servers 또는 사용자 명시 trust
> 2. probe_sqlite.js 패턴으로 stdio JSON-RPC 핑 → 도구 enumeration 확정
> 3. 결과를 §3 표 행에 채움 (cycle별 누적 — §8-2 진척표와 동일 방식)
>
> **요약:** PoC 미완 항목은 *이름이 박제되었어도 사용 자격은 없음*. §10 진입을 거치지 않고 inline `mcpServers:` 합성에 직접 사용하면 schema mismatch / 패키지 spoof / 잘못된 toolset env 등으로 silent fail 가능.

> ⚠️ **"install 명령" 컬럼의 용도 — 합성 산출물용 default 아님**
>
> 본 컬럼의 `claude mcp add ...` 명령은 *PoC enumeration·검증 환경 install* 형태이며, `~/.claude.json` projects.{cwd}.mcpServers (= scope `local`) 또는 `.mcp.json` (= scope `project`) 적재 = **parent 컨텍스트에 도구 정의 적재**. 이 경로는 `permission-profiles.md §5-2`의 anti-pattern과 동일한 토큰 비용을 부담한다.
>
> **합성 산출물에서는 §5-1 inline `mcpServers:`가 default** — 본 컬럼의 install 명령에서 *동일 패키지명·인자*를 추출해 inline `command:`/`args:`/`env:` 필드로 옮기되, 등록 자체(`claude mcp add`)는 **생략**한다. 예: `claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=... -e GITHUB_TOOLSETS=pull_requests -- npx -y @modelcontextprotocol/server-github` → §5-1-b의 inline `mcpServers.github` 블록으로 변환.
>
> 본 컬럼을 그대로 실행해도 되는 경우는 (1) 본 PoC처럼 도구 enumeration 검증 (2) `permission-profiles.md §5-2`의 3 예외 조건 — *그 외에는 §5-1 변환*.

---

## §3-1. 검증 완료 T0 MCP × capability profile 매트릭스

§3 인벤토리에서 PoC 완료된 **T0 MCP 7종 (총 48 도구)** 을 capability profile별로 매트릭스화한 *런타임 가용 default 카탈로그*. Phase 5-2 합성 시 `permission-profiles.md §4` 결정 트리가 capability profile을 확정하면 본 표에서 해당 행을 1차 후보로 발췌한다.

**검증 완료 카운트:**
- `fetch` 4 + `sequential-thinking` 1 + `git` 12 + `sqlite` 6 + `filesystem` 14 + `time` 2 + `memory` 9 = **48 도구** (+ github toolset 카탈로그 19 enum)
- 모두 `permission-profiles.md §8-3 stdio JSON-RPC tools/list 핑`으로 source-grep 100% 일치 검증 (`fixtures/probe_*.js`)

### 매트릭스

| capability profile | 권고 MCP (T0) | 도구 카운트 | Layer 결합 | default 권한 bucket | mid-session add 후 미전파? |
|---|---|---|---|---|---|
| **code-test** | `git` + `filesystem` | 12 + 14 | `permission-profiles-synthesis.md §5-1-a` Layer B 단독 (둘 다 toolset 필터 미지원) | `git` 12종 ask (commit/checkout/reset이 부수 효과) / `filesystem` read 10종 `allow` + write 4종 `deny` (빌트인 Read/Write/Edit과 중복 — `filesystem`의 가치는 *path-roots 격리*) | ✅ 다음 세션부터 |
| **web-research** | `fetch` + `memory` | 4 + 9 | `permission-profiles-synthesis.md §5-1-a` Layer B 단독 (fetch/memory 모두 toolset 필터 미지원) | `fetch` 4종 `allow` (모두 read-only) / `memory` read 3종 `allow` + create/add 3종 `ask` + delete 3종 `deny` | ✅ 다음 세션부터 |
| **external-integration** | `sqlite` (+ T1+ `github` 별도) | 6 | `permission-profiles-synthesis.md §5-1-a` Layer B 단독 (sqlite는 toolset 미지원) / `github`는 §5-1-b Layer A+B 결합 (env `GITHUB_TOOLSETS`) | `sqlite` read 3종 `allow` + write 3종 `deny` (read-only 강제) | ✅ 다음 세션부터 |
| **reasoning-aux** | `sequential-thinking` + `time` | 1 + 2 | `permission-profiles-synthesis.md §5-1-a` Layer B 단독 (toolset 미지원, 둘 다 부수 효과 0) | 3종 모두 `allow` (read-only) | ✅ 다음 세션부터 |
| **ml-pipeline** (2026-05-14 신설) | `filesystem` + `sqlite` + `memory` + `sequential-thinking` + `git` (T0만, cross-mapping 5종) | 14 + 6 + 9 + 1 + 12 = 42 | `permission-profiles-synthesis.md §5-1-a` Layer B 단독 (전부 toolset 미지원 — 5 MCP 동시 등록 부담 ↑ → *합성 시 도메인별로 2~3종 선별* 권장) | dataset read `allow` / 모델 write·실험 DB write `ask` / git commit `ask` | ✅ 다음 세션부터 (전용 MCP huggingface/wandb 등은 §10 진입 후 추가) |
| **devops-infra** (2026-05-14 신설) | `git` + `filesystem` + `time` + `sequential-thinking` (T0 4종) | 12 + 14 + 2 + 1 = 29 | `permission-profiles-synthesis.md §5-1-a` Layer B 단독 | git 12종 `ask` (commit/checkout/reset 부수 효과) / filesystem write `deny` (IaC 변경은 명시 confirm) / time 2종 `allow` / `kubectl`/`terraform` 등은 `Bash` 빌트인으로 — 변경 도구 패턴 매칭 `ask` | ✅ 다음 세션부터 (kubernetes/terraform/aws MCP는 §10 진입 후 추가) |
| **mobile-native** (2026-05-14 신설) | `filesystem` + `git` + `sequential-thinking` (T0 3종) + `playwright`/`chrome-devtools` (T1, derived 프로젝트별) | 14 + 12 + 1 + 23 + 44 | `permission-profiles-synthesis.md §5-1-a` Layer B 단독 (T0) / §5-1-b Layer A+B (playwright caps 필터) | filesystem write iOS/Android root 격리 / git `ask` / playwright `browser_run_code_unsafe` `deny` (RCE-equivalent) / chrome-devtools `install_extension`/`execute_*` `deny` | ✅ 다음 세션부터 (Appium/Xcode MCP는 §10 진입 후 추가) |
| **data-eng** (2026-05-14 신설) | `sqlite` + `filesystem` + `git` + `memory` + `sequential-thinking` (T0 5종) | 6 + 14 + 12 + 9 + 1 = 42 | `permission-profiles-synthesis.md §5-1-a` Layer B 단독 | sqlite `read_query` `allow` / `write_query` `ask` / `create_table`/`drop_table` `deny` (마이그레이션은 dedicated agent) / filesystem data lake path-root 격리 | ✅ 다음 세션부터 (postgres T2~ + snowflake/bigquery/databricks/dbt MCP는 §10 진입 후 추가) |

> **매트릭스의 권고는 *제안*이지 default 강제가 아님** — `permission-profiles.md §4` 결정 트리의 사용자 confirm 게이트가 항상 우선. 사용자 도메인이 매트릭스 외 조합을 요구하면 (예: web-research에 `git` 필요) `permission-profiles-dynamic-adoption.md §10` dynamic adoption 절차로 후보 확장.

> **도메인 4종 cross-mapping doctrine (2026-05-14):** 도메인 profile 4종(ml-pipeline/devops-infra/mobile-native/data-eng)은 *전용 T0 MCP가 거의 없음* — T0 5종(`filesystem`/`sqlite`/`memory`/`git`/`sequential-thinking`/`time`)을 도메인 시그널 매칭에 따라 *재조합*하는 형태. 전용 MCP(huggingface/kubernetes/appium/snowflake 등)는 PoC 미완 — `permission-profiles-dynamic-adoption.md §10` dynamic adoption 진입 후 §3 행 추가 → 본 매트릭스 행 갱신. PoC 미완 항목은 "후보 풀에서 *옵션*"이지 default 합성 사용 X.

### 채택 패턴 권고 — 7 MCPs 통합 inline `mcpServers:` (참고 예시)

capability profile이 2종 이상이 겹치는 *멀티 도메인 에이전트*는 inline `mcpServers:`에 여러 MCP를 동시 정의 가능. 단 **inline 서버는 advertise 도구 *전부* 노출**(10차 cycle P0 새 발견)되므로 부수 효과 도구는 `permissions.deny`에 박제 필수.

```yaml
mcpServers:
  - filesystem:
      type: stdio
      command: npx
      args: ["-y", "@modelcontextprotocol/server-filesystem", "<allowed-path>"]
  - git:
      type: stdio
      command: <uvx-abs-path>
      args: ["mcp-server-git", "--repository", "<repo-abs>"]
  - sqlite:
      type: stdio
      command: <uvx-abs-path>
      args: ["mcp-server-sqlite", "--db-path", "<db-abs>"]
```

> 위 YAML은 **list-of-dicts + `type: stdio`** 필수 (9차 cycle docs RESOLUTION). 합성 직후 *현재 세션* 미전파, 다음 세션부터 사용 가능 (4차 cycle empirical).

### 카탈로그 사용 흐름

1. Phase 5-2 합성 시 `permission-profiles.md §4` 결정 트리가 에이전트 description → capability profile N개 *제안*
2. 본 §3-1 매트릭스에서 profile별 권고 MCP 행 매핑
3. 매핑 후보를 사용자에게 AskUserQuestion으로 confirm (Tier·도구 카운트·default permissions 동봉)
4. 사용자 confirm 후 `permission-profiles-synthesis.md §5-1` inline `mcpServers:` 패턴으로 합성 — 동시에 §3-1의 default 권한 bucket을 `permissions` 산출물로 박제

### 미완 잔존 (P3/P4 수준 — 본 §3-1 매트릭스 *외부* 영역)

| Tier | MCP | 막힘 사유 | 진척 | 해소 후 매트릭스 행 |
|---|---|---|---|---|
| T1 | `playwright` ✅ probe ✓ / `chrome-devtools` 출처 ✅ + 실 probe 미완 | toolset 필터 형태가 CLI flag — env 키 없음 | ✅ **playwright probe-only empirical 확정** (default 23종 + caps=vision +6종 = 29). **chrome-devtools 부분 진척**: 패키지 출처 verify 확정(Google LLC + ChromeDevTools 공식 org + Apache-2.0 + mcpName, docs 44 카운트 100% 일치) + 🚫 **Node engines 함정**(모든 49 versions이 `node ^20.19 \|\| ^22.12 \|\| >=23` 요구). 실 probe enum은 derived 프로젝트별 `permission-profiles-dynamic-adoption.md §10` dynamic adoption + Node 20.19+ 환경 가용 시점. | playwright → code-test 행에 추가 가능 / chrome-devtools는 출처 ✅ + 실 enum은 *외부 의제* (Node 환경 + 사용자 결정) |
| T1+ | `github` | toolsets enum은 ✓ 확정(19종) — 실 install·도구 풀 측정만 PoC 미완 (PAT 필요) | 📜 docs 박제 — **No npm package** (Docker/Go 바이너리만). install 명령·env·toolset 옵션 박제. | external-integration 행에 *결합형* 별도 박제 (PAT 보유 시점) |
| T1+ | `brave-search` / `tavily` / `exa` | API 키 발급 필요 | 📜 docs 박제 (brave 8 / tavily 4 (도구명 하이픈 첫 케이스) / exa 3 active + 7 deprecated) | web-research 행 확장 (각 키 보유 시점) |
| T2~ | `firecrawl` / `slack` / `postgres` | 유료 또는 민감 외부 시스템 | 📜 docs 박제 (firecrawl 10 active + 4 deprecated browser) — slack/postgres 미완 | research / external-integration 행에 ask-only 부기 |

> **본 매트릭스의 closure 기준:** "PoC enumeration ✓"가 되는 시점에 본 §3-1에 행 추가 — `tier·profile·도구 카운트·default permissions·Layer 결합` 5컬럼 동시 박제. 추가 절차는 `permission-profiles-dynamic-adoption.md §10` 5-step + §10 Step 5 (a) 인벤토리 갱신 = §3 행 갱신 + 본 §3-1 매트릭스 동시 갱신.
