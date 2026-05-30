# Permission Profiles — Empirical 검증 상태 + 실증 reproducer (§8 + §11)

> **Read at phase:** §8-2 미완 항목 진단 시 / Phase 5-2 합성 후 정합 점검 시 / `/harness:harness-status --mcp` 보고 정합 시 / 외부 환경 reproducer 실행 시.
>
> P7 추가 분리(2026-05-28, PA5) — `permission-profiles.md` §8 (검증 상태) + §11 (실증 reproducer) ~15KB를 본 파일로 흡수. main §8/§11은 1줄 redirect.

## §8. 검증 상태

### 8-1. 공식 docs로 확정된 사실 ✓ + empirical 검증 ✓✓

- ✓ **Subagent는 자체 컨텍스트 윈도우를 가짐** (docs §sub-agents intro)
- ✓ **기본은 모든 도구 inherit (MCP 포함)** — `tools:` allowlist를 명시해야 제한됨 (docs §"Configure tools")
- ✓ **`tools:` allowlist에 MCP 도구를 안 적으면 subagent는 MCP 호출 불가**, 단 `.mcp.json` 등록 MCP는 *parent 컨텍스트에는 여전히 적재*됨
- ✓✓ **Inline `mcpServers:` frontmatter — parent 컨텍스트 미적재 (10차 P0 empirical 확정)** — subagent 시작 시 connect, 종료 시 disconnect (docs §"Configure MCP servers": *"Use the mcpServers field to give a subagent access to MCP servers that aren't available in the main conversation"*). **2026-05-10 P0 재현 검증으로 *parent ToolSearch 0 hit + subagent 도구 노출 4종* 양면 통과** — 결과 박제: `fixtures/README.md` "결과 로그" 2026-05-10 §11-2 P0 행.
- ✓ **`disallowedTools`는 inherit pool에서 제거**, `tools` 명시 시엔 그것만 허용 (`disallowedTools` 우선 적용 후 `tools` resolve)
- ✓ **🆕 `tools:` allowlist는 inline 서버 도구를 줄이지 못함 (10차 새 발견)** — inline `mcpServers:`로 connect된 서버는 advertise 도구 *전부* subagent에 노출. allowlist 1종 명시도 4종 전부 노출. inline 서버의 도구 카운트 통제는 Layer A(서버 측 advertise 필터) 또는 Layer C `permissions.deny`로만. → `permission-profiles.md §1` Layer B 셀 (3-layer 표 본 doctrine) + `permission-profiles-synthesis.md §5-1` 새 발견 caveat 참조.

### 8-2. 검증 상태 요약

**✓ Empirical 확정:**
- T0 MCP 7종 install + 도구 enumeration (총 48 도구) — fetch 4 / sequential-thinking 1 / git 12 / sqlite 6 / filesystem 14 / time 2 / memory 9. 모두 JSON-RPC `tools/list` stdio 핑으로 검증, `permission-profiles-inventory.md §3` = §3-1 매트릭스 cross-reference.
- T1 playwright probe-only — default 23종 + `--caps=vision` +6종 (좌표 기반 mouse). docs 박제 vs 실 probe 100% 일치.
- T1 chrome-devtools 패키지 출처 — npm Author=Google LLC + Apache-2.0 + GitHub `ChromeDevTools` org 39.2k★ + mcpName `io.github.ChromeDevTools/chrome-devtools-mcp` 3-source 교차 일치 (spoofing 위험 0). docs 박제 44 도구 카운트와 README 100% 일치. 단 engines `node ^20.19 || ^22.12 || >=23` 요구 — Node 18에서 spawn hard fail.
- **§11-2 inline `mcpServers:` parent isolation 양면 검증** — derived 프로젝트의 정정 schema(list-of-dicts + `type: stdio`) fixture spawn 시 [1] subagent 도구 풀에 inline 정의 도구 노출 [2] parent `ToolSearch` 0 hit. inline 정의는 *subagent에만* connect되고 parent 컨텍스트 deferred pool에는 미적재.
- **§11-4 §10 5-step e2e 시연** — derived 프로젝트에서 sqlite MCP 채택 워크플로우 전체 reproducer (Discover→Probe→Confirm→Install→Reflect 4 산출물).
- **mid-session 미전파** — 3개 MCP가 `claude mcp list`에서 `✓ Connected`인 동일 세션의 부모 측 `ToolSearch` "mcp__" → 0 hit + `Explore` 서브에이전트 spawn 후 inherit pool 점검 → 0 hit. MCP 도구 풀은 SessionStart 시 1회 materialize, mid-session add는 다음 세션부터 반영.
- **§6 자동 install 금지 정책 enforcement** — Anthropic auto-mode classifier가 `npx -y <pkg>` 패턴을 *untrusted external code execution outside trusted repo*로 자동 차단 (T0/T1 모두 동일). 사용자 명시 동의 후 통과.
- **mcp gate 키 mode-independent falsification** — `~/.claude.json` 4-key gate(project-scope/user-scope `enabledMcpjsonServers` + `hasTrustDialogAccepted` + `disabledMcpjsonServers` 명시 차단) 모두 deferred pool 적재를 제어하지 못함 (인터랙티브·`-p` 양쪽 empirical). `.mcp.json` 존재만으로 적재.

**📜 Docs 박제 (외부 환경에서 empirical 확정 대기):**
- T1+ MCP 5종 — brave-search 8 / tavily 4 (도구명 하이픈) / exa 3 active + 7 deprecated / firecrawl 10 active + 4 deprecated browser / github toolsets 19 (Docker/Go 바이너리, npm 미지원). 모두 API 키 보유 시점에 [`fixtures/probe_*.js`](./fixtures/) 복사 실행으로 enum 확정 가능.
- T1 chrome-devtools 44 도구 — 실 probe spawn은 Node 20.19+ 환경 + 외부 PowerShell 1회 필요.

**✅ 합성 룰 empirical 확정:**
- inline `mcpServers:` frontmatter schema는 **list-of-dicts + 각 항목에 `type: stdio` 필수** — plain dict는 silent skip (공식 docs `https://code.claude.com/docs/en/sub-agents` 발췌).
- `tools:` allowlist는 inline 서버 도구를 줄이지 못함 — advertise 도구 전체 노출. 부수 효과 도구 차단은 `permissions.deny`로 강제 (`ask` 강등은 부족).
- uvx-기반 MCP는 `command:` 필드에 *uvx 절대경로* 필수, path 인자(`--db-path`/`--repository`)도 *절대경로* 필수 — 상대경로면 health check `✗ Failed to connect`.
- `claude mcp add` 기본 스코프 = `local` (`~/.claude.json` projects.{path}.mcpServers — 다른 프로젝트 누수 없음).

**⚠️ 영구 외부 의제 (plugin host 본 저장소 측정 부적합):**
- Layer A server-side `--toolsets`/env 채널의 *deferred pool* 적재 효과 — advertise 단계 축소는 empirical 확정(playwright caps probe)이나 plugin host 세션 deferred pool 카운트 변화는 derived 프로젝트의 인터랙티브 세션 재시작 측정이 필요.
- T1 chrome-devtools 실 probe enum diff (Node 20.19+ 환경)
- T1+ 5종 실 spawn enum (API 키)
- 모두 외부 도입자의 §10 dynamic adoption 시점에 자연 진행.

### 8-3. 재사용 가능한 검증 기법

**stdio JSON-RPC `tools/list` 직접 핑** — Claude 세션 재시작 없이 MCP 서버의 도구 카탈로그를 empirical하게 enumerate하는 패턴. 임시 Node 스크립트로 (1) `initialize` (2) `notifications/initialized` (3) `tools/list` 3 메시지를 stdio에 write하고 응답을 파싱. 도구 enumeration을 install 없이 일회성 npx로 수행 가능 (probe fixture 11종이 `./fixtures/probe_*.js`).

> ⚠️ **패키지 출처 검증 — probe도 코드 실행이다**
>
> `npx -y <pkg>` / `uvx <pkg>` 둘 다 임의 패키지를 *실행*한다 (probe도 spawn → 코드 실행 surface). install이 아니어서 "가벼움"이 아니며, **install과 동일 위협 모델**이 적용된다 (`permission-profiles.md §6` 정책의 install 금지 정신과 일관).
>
> **probe 실행 전 필수 확인:**
> 1. 패키지 이름이 다음 trusted source 중 하나에 있는가? (이름 spoofing 주의 — `mcp-server-fetch` vs `mcp-server-fetch-typescript` 같은 변형 패키지 존재)
>    - 공식 reference: `github.com/modelcontextprotocol/servers` (anthropic/MCP 메인테이너)
>    - `permission-profiles-inventory.md §3` 인벤토리에 ✓로 박제된 검증 완료 패키지
>    - 사용자가 *명시적으로 trust*한 source (예: 회사 내부 npm 레지스트리)
> 2. trust 안 되는 패키지면 **probe도 실행 금지** — 사용자에게 출처 확인 요청 후 명시 동의 받음
> 3. probe 실행 시에도 *최소 권한* 환경에서 (예: `--no-network` flag 가능 시 적용)
>
> **추가 안전 룰:** `permission-profiles-inventory.md §3` 인벤토리에 📜 docs 박제만 있고 ✅ empirical 미확정 항목(`tavily`/`exa`/`firecrawl`/`slack`/`postgres`/`brave-search` + chrome-devtools 실 probe enum)은 *§3에 박제는 되었지만 도구 enumeration empirical 검증이 미완*. 이들도 §10 dynamic adoption 진입 시점에 위 1·2 단계 동일 적용.

---

## §11. 실증 가능한 테스트 레시피 — §8-2 미완 항목 reproducer

§8-2의 미완 항목 각각을 외부 환경(다음 세션·derived 프로젝트·API 키)에서 *복사 실행*만으로 재현할 수 있도록 박제. 각 레시피는 자기 완결적 — 본 문서 외 다른 컨텍스트 불필요.

> **적용 경계:** 본 §11 fixture들은 *외부 검증 환경*(다음 세션·derived 프로젝트·재시작·신규 install) 의존이라 plugin host 세션에서는 mid-session 직접 실행 불가. §11-2의 `mcp-isolation-probe.agent.md`는 특히 *plugin host 본 저장소 밖의 derived 프로젝트* `.claude/agents/`에 복사해야 하며, host 본 저장소 `.claude/agents/`(self-host CM 운영 시)에는 두지 않는다 (격리 위반). `permission-profiles-dynamic-adoption.md §10`과 동일한 분계 — 본 fixture 결과는 derived 프로젝트 동작 검증이지 host 자체 동작 검증이 아니다.

### 11-1. `mcp__<server>__<tool>` 노출 패턴 검증 (다음 세션)

▶ **Fixture:** [`./fixtures/verify_11_1.md`](./fixtures/verify_11_1.md) — 다음 세션에서 첫 user 메시지로 입력할 프롬프트 + 결과 캡처 템플릿 + §3 표 갱신 액션 박제 완료.

**목적:** mid-session add된 MCP가 다음 세션 시작 시 실제 어떤 도구명으로 노출되는지 (특히 하이픈을 포함한 서버명 `sequential-thinking`이 `mcp__sequential-thinking__*` 또는 `mcp__sequential_thinking__*` 중 어느 것인지).

**선조건:** 본 세션에서 fetch/sequential-thinking/git 3개 MCP 등록 완료 (`claude mcp list`로 ✓ Connected 확인).

**절차:**
```
1. Claude Code 세션 종료 후 재시작 (같은 plugin host 프로젝트)
2. 첫 user 메시지에 다음 한 줄 입력:
   "ToolSearch query 'mcp__'로 max_results 20 검색하고 발견된 모든 도구의 정확한 이름만 bullet로 나열해줘"
3. 응답에서 `mcp__fetch__*`, `mcp__git__*`, `mcp__sequential-thinking__*` (또는 `_thinking_`) 패턴을 확인
4. 결과를 §3 표 footnote 또는 §11-1 끝에 검증 일자 + 실제 노출 형태로 기록
```

**예상 결과 (확인 필요):**
- fetch 4종: `mcp__fetch__get_raw_text` / `get_rendered_html` / `get_markdown` / `get_markdown_summary`
- git 12종: `mcp__git__git_status` / `git_diff_unstaged` / ... / `git_branch`
- sequential-thinking 1종: `mcp__sequential-thinking__sequentialthinking` (하이픈 보존 가능성 높음)

### 11-2. 서브에이전트 inline `mcpServers:` parent isolation 측정 (derived 프로젝트)

▶ **Fixture:** [`./fixtures/mcp-isolation-probe.agent.md`](./fixtures/mcp-isolation-probe.agent.md) — derived 프로젝트 `.claude/agents/` 위치에 그대로 복사 가능한 ready-to-spawn 에이전트 파일 (frontmatter `tools:` allowlist + inline `mcpServers:` + 출력 파싱 형식까지 박제).

**목적:** `permission-profiles-synthesis.md §5-1` 합성 템플릿이 실제로 (a) subagent에는 도구 노출 (b) parent에는 미적재 — 양쪽 동시 검증.

**선조건:** plugin host 본 저장소 *밖*의 derived 프로젝트 1개 (예: `~/myproject/`). plugin host 본 저장소는 host self-host CM 격리 영역(운영 시)이라 부적합.

**절차:**

1. derived 프로젝트에 다음 파일 생성 — `~/myproject/.claude/agents/mcp-isolation-probe.md`:

   ```yaml
   ---
   name: mcp-isolation-probe
   description: MCP isolation empirical probe — inline mcpServers를 갖고 도구 노출 보고
   model: opus
   tools:
     - Bash
     - mcp__fetch__get_markdown
   mcpServers:
     - fetch:
         type: stdio
         command: npx
         args: ["-y", "mcp-server-fetch-typescript"]
   ---

   당신의 단일 책임: 자신의 도구 풀을 점검하여 다음을 보고한다.
   1. `mcp__fetch__*` 도구가 보이는가? 보인다면 정확한 이름 모두 나열.
   2. 위 목록 외에 inline `mcpServers:`가 합성한 다른 `mcp__*` 도구가 있는가?
   3. ToolSearch가 가용하면 query "mcp__"로 max_results 10 검색 결과 보고.
   ```

2. parent에서 `claude mcp list`로 fetch가 등록되어 있지 않음을 확인 (등록되어 있다면 `claude mcp remove fetch` 선행).

3. parent에서 `Agent` tool로 위 subagent를 spawn:
   ```
   subagent_type: "mcp-isolation-probe"
   prompt: "위 책임 수행"
   ```

4. **검증 1 (도구 노출):** subagent 응답에 `mcp__fetch__get_markdown`이 노출되어야 함.

5. **검증 2 (parent isolation):** subagent 종료 후 parent에서 `ToolSearch` query `"mcp__fetch__"` → 결과 0 (적재 안 됨)이어야 함. 적재되어 있다면 inline 합성이 isolation을 깨고 있음 → §8-1 확정 사실 재검증 필요.

**관찰 포인트:** Agent tool 호출 시 `subagent_type`에 임의 이름(=agent.md의 `name:`)이 전달 가능한지가 핵심 — 안 되면 Task tool 또는 다른 spawn 경로 시도.

### 11-3. `enabledMcpjsonServers` 토글의 효과 측정 (재시작 필요)

▶ **Fixture:** [`./fixtures/verify_11_3.md`](./fixtures/verify_11_3.md) — 7차 사이클 갱신본. 베이스라인(B1) → 토글 OFF → 측정(B2) → 3축 메트릭 분기 판정 → 복원 4단계. **3축 메트릭 = M1(system prompt 토큰) / M2(deferred pool 카운트) / M3(schema fetch 빈도)** — deferred pool 발견 이후 도구 카운트 단독으로는 분기 표지가 되지 않으므로 3축 조합 필수.

**목적:** `.claude/settings.json`의 `enabledMcpjsonServers` 배열에서 서버를 *빼면* — (A) 컨텍스트 적재 자체가 차단되는지 vs (B) 적재는 되고 호출만 차단되는지.

**선조건:** 프로젝트에 `.mcp.json` 또는 `~/.claude.json` projects.{path}.mcpServers로 등록된 MCP 1개 이상.

**절차 (요약 — 자세한 입력 프롬프트는 fixture 참조):**
```
1. 베이스라인 측정: 모든 MCP enabled 상태에서 세션 시작 → 첫 turn에 (M1, M2, M3) 측정 → B1
     M1: system prompt 토큰 — mcp__* 도구 이름·description 적재량 (근사)
     M2: deferred pool 카운트 — ToolSearch "mcp__" 검색 hit 수
     M3: schema fetch 빈도 — typical turn에서 ToolSearch select:<name> 발생 여부
2. 세션 종료 후 .claude/settings.json 편집:
     { "enabledMcpjsonServers": [] }
3. 세션 재시작 → 동일 절차로 B2 측정
4. 분기 (3축 조합):
     B2.M2 == 0  AND  B2.M1 << B1.M1   → 적재 자체 차단 ✓ (Layer A 진짜 효과)
     B2.M2 == 0  AND  B2.M1 ≈ B1.M1     → 표면 카운트만 0 (재측정 권장)
     B2.M2 == B1.M2 AND B2.M1 ≈ B1.M1   → 호출만 차단 (Layer A는 Layer C와 동급)
     0 < B2.M2 < B1.M2                  → 서버별 차등 (분리 측정)
```

**기록처:** `permission-profiles.md §1` 표의 Layer 비교 컬럼 "컨텍스트 절감" 셀에 검증 결과 footnote 추가.

### 11-4. §10 Dynamic Adoption e2e 시연 — SQLite 분석 시나리오

▶ **Fixture:** [`./fixtures/probe_sqlite.js`](./fixtures/probe_sqlite.js) — Step 2 pre-install JSON-RPC stdio probe ready-to-run (UVX_PATH/DB_PATH만 환경 맞게 조정). Step 3 user confirm 통과 후 install 직전 도구 enumeration 자동 수행. (mcp_probe_git.js 동일 패턴, target만 sqlite로 교체)

**목적:** `permission-profiles-dynamic-adoption.md §10`의 5-step 절차가 실제 흐름으로 동작함을 1회 reproducer로 박제.

**시나리오:** "데이터 분석 에이전트가 로컬 SQLite DB(`./data/app.db`)를 조회해야 하는데 `sqlite` MCP가 인벤토리에 있지만 PoC 미완 상태."

**5-step 실행:**

```
[Step 1 — Discover]
  - 1차: §3 인벤토리에 sqlite 행 존재 (T0, external-integration)
  - 2차: github.com/modelcontextprotocol/servers → mcp-server-sqlite 패키지 확인
  - 후보 확정: mcp-server-sqlite (uvx 실행)

[Step 2 — Pre-install probe (§8-3 기법)]
  Node 임시 스크립트 작성:
    const { spawn } = require('child_process');
    const child = spawn('uvx', ['mcp-server-sqlite', '--db-path', './data/app.db'],
                        { stdio: ['pipe','pipe','pipe'] });
    // initialize → notifications/initialized → tools/list (§8-3 패턴)
  결과: read_query / write_query / list_tables / describe_table / append_insight 등 enumerate
  → install 없이 도구 카탈로그 확보

[Step 3 — User confirm gate]
  AskUserQuestion:
    "sqlite MCP install 진행? Tier=T0 (로컬 DB 파일만), 도구 5종 확인됨,
     키 불필요. install 시 .claude/settings.json에 allow=mcp__sqlite__read_query만 등록 추천 (write/append는 ask)"

[Step 4 — Install + 적재]
  claude mcp add sqlite <uvx-abs-path> -- mcp-server-sqlite --db-path ./data/app.db
  claude mcp list  # ✓ Connected 확인
  스코프: 기본 local (이 프로젝트만) — 팀 공유 필요 시 -s project로 .mcp.json commit

[Step 5 — Reflect (4 산출물)]
  a. permission-profiles-inventory.md §3 sqlite 행 갱신 — 도구 enumeration 채움
  b. .claude/agents/data-analyst.md frontmatter `tools:`에:
       mcp__sqlite__read_query, mcp__sqlite__list_tables, mcp__sqlite__describe_table
     (write_query / append_insight는 의도적 제외 — Tier 정책상 ask)
  c. .claude/settings.json:
       "permissions": {
         "allow": ["mcp__sqlite__read_query", "mcp__sqlite__list_tables", "mcp__sqlite__describe_table"],
         "ask":   ["mcp__sqlite__write_query", "mcp__sqlite__append_insight"]
       }
  d. _workspace/_baseline/changelog.md 변경 이력 1행:
       | {date} | MCP 채택: sqlite | T0/external-integration | data-analyst가 ./data/app.db 분석 필요 (T2 트리거) |
```

**검증 게이트:** 위 5-step을 *실제 derived 프로젝트*에서 1회 수행하여 (a) ✓ Connected (b) 다음 세션에서 `mcp__sqlite__read_query` 노출 (§11-1과 동일 검증) (c) settings.json `allow`로 read_query 무프롬프트 호출 (d) write_query 호출 시 ask 프롬프트 발생 — 4가지 동시 통과 시 §10 워크플로우 stable로 확정. 미통과 항목은 §10에 footnote로 박제.
