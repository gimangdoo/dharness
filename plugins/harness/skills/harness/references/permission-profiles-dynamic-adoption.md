# Permission Profiles — Dynamic Adoption §10

> **Read at phase:** Phase 9 baseline drift 후 신규 capability 등장 시 / Phase 5-2 합성 시 인벤토리 미충족 시 / 사용자 명시 MCP 채택 요청 시. `/harness:harness-evolve`의 mcp-adopt 내부 op 본문 (2026-05-30 mcp-adopt command 흡수).
>
> P7 분리(2026-05-23) — `permission-profiles.md` §10 (10-A~10-G)을 본 파일로 흡수. main 본문엔 pointer만 잔존.
>
> 2026-05-28 anchor rename — 의미 anchor (A. 트리거 / B. 5-step / C. 프로젝트 유형 / D. Rollback / E. inline update / F. 자동화 한계 / G. 병렬 세션). 이전 숫자 anchor (10-1~10-7)은 audit2 PA4 정정 대상이었음.

## §10. Dynamic MCP Adoption — 프로젝트 진행에 따른 MCP 신규 채택

`permission-profiles-inventory.md §3` 인벤토리는 정적 스냅샷. 실제 프로젝트는 (a) 도메인이 바뀌거나 (b) phase가 진행되면서 (c) 사용자가 직접 요구하면서 새 MCP가 필요해진다. 이 절차는 **합성 시점이 아닌 *런타임 시점*의 MCP 도입**을 다룬다.

> **적용 경계:** 본 §10 절차는 *derived 프로젝트의 `.claude/`* (= 사용자가 본 메타 스킬로 새로 합성한 프로젝트)를 대상으로 한다. **plugin host 본 저장소 자체는 self-host CM 격리 영역**(운영 중인 경우) — `plugins/harness/`는 read-only invariant이고, host 본 저장소의 `.claude/`는 (운영 시) host self-host CM의 자체 진화 기록자라 §10 채택 대상이 아니다. 단, 본 PoC를 위해 plugin host 프로젝트에서 MCP를 install·검증하는 행위는 *예외적 검증 환경* — `~/.claude.json` `projects.{host}.mcpServers`에 격리되며 derived 프로젝트로 누수되지 않음.

### 10-A. 트리거 신호 (3종)

| # | 신호 | 발생 위치 | 자동 감지 가능? |
|---|------|---------|---------------|
| T1 | **도메인/phase 전환** — baseline 갱신 후 신규 capability 등장 (예: prototype→deploy로 이동하면서 cloud provider integration 필요) | Phase 1·9 / `_workspace/_baseline/*.md` diff | ✅ Phase 9에서 baseline 비교로 감지 |
| T2 | **에이전트 합성 시 인벤토리 미충족** — `permission-profiles.md §4` 결정 트리 분기 `c)` 발동 | Phase 5-2 | ✅ `claude mcp list` 결과 vs profile 후보 차집합 |
| T3 | **사용자 명시 요청** — "Slack 알림 보내는 에이전트", "DB 마이그레이션 검증" 등 | 임의 시점 | ❌ 항상 사용자 발화 기반 |

### 10-B. 5-step 채택 절차 (모든 트리거 공통)

```
Step 1. Discover — 후보 식별
  - 1차 출처: permission-profiles-inventory.md §3 (이미 검증된 항목)
  - 2차 출처: 공식 reference (github.com/modelcontextprotocol/servers)
  - 3차 출처: npm 레지스트리 검색 (`mcp-server-*`, `@*/mcp-*`), awesome-mcp-servers 류 큐레이션
  - LLM 환각 방지: 후보 이름은 반드시 위 3개 출처 중 하나에서 *원문 발췌* (URL 동봉)

Step 2. Pre-install probe — install 없이 도구 enumerate (`permission-profiles-empirical.md §8-3` 기법 재사용)
  - **패키지 출처 검증 (필수, §8-3 안전 룰)**:
      1. trusted source 확인 — github.com/modelcontextprotocol/servers / permission-profiles-inventory.md §3 ✓ 항목 / 사용자 명시 trust 중 하나
      2. 미trust 패키지면 probe 실행 금지 — 사용자에게 출처 확인 요청
      3. probe도 코드 실행이라 install과 동일 위협 모델
  - 일회성 spawn으로 stdio JSON-RPC `initialize` → `notifications/initialized` → `tools/list`
  - 명령 패턴:
      npx -y <pkg>            # npm 기반
      uvx <pkg> [-- <args>]   # Python 기반
      docker run --rm -i <img> # docker 기반
  - 결과: 도구 목록·required params·schema → 사용자 confirm 자료
  - install 영구화 전이라 *config 부작용*은 0 (PATH 등록·~/.claude.json 수정 없음). 단 *코드 실행 부작용*은 0이 아님 — 패키지 코드가 spawn된다.

Step 3. User confirm gate (필수)
  - AskUserQuestion 으로 Tier 분류·필요 키·대안 빌트인 함께 제시
  - 자동 install 금지 (`permission-profiles.md §6`) — 사용자 클릭으로만 진행
  - T2 / 키 필요 항목은 키 등록 절차도 함께 제시

Step 4. Install + 적재
  - 스코프 결정: 기본 `local` (이 프로젝트만, `~/.claude.json` projects.{path}.mcpServers)
                  팀 공유 필요 시 `project` (`./.mcp.json` commit 대상)
                  본인 모든 프로젝트엔 `user` (`~/.claude.json` 전역)
  - 명령:
      claude mcp add <name> <command> [args...] [-e KEY=VAL ...] [-s local|project|user]
  - toolset 필터 동시 적용 (Layer A): GitHub `GITHUB_TOOLSETS=...`, Playwright `--caps=...` 등
  - 검증: `claude mcp list` → `✓ Connected` 확인 (실패 시 stderr 확인)
  - **경로 인자는 절대경로 필수** — `--db-path ./...`, `--repository ./...` 등 상대경로는 health check 실행 시 cwd가 `claude` 호출 디렉토리와 다를 수 있어 `✗ Failed to connect` 발생 (8차 사이클 sqlite 시연 empirical). uvx 실행자 자체도 PATH 미통과 시 spawn 실패하므로 절대경로 (`%APPDATA%\Python\Python312\Scripts\uvx.exe`) 권장.

Step 5. Reflect — 4 산출물 동시 패치 (atomicity 분계 주의)
  a. **permission-profiles-inventory.md §3 인벤토리 표** — 새 행 추가 (Tier·카테고리·install 명령·도구 enumeration)
       ⚠️ *atomicity 범위 외* — 본 행은 plugin host 본 저장소(`plugins/harness/skills/harness/references/permission-profiles-inventory.md`) 편집이라 외부 install 도입자에게는 *읽기 전용*. PR 또는 plugin host 본 저장소 직접 편집 권한이 있는 도입자만 적용 가능. 권한이 없는 도입자는 본 (a)를 *권고로 보고*만 출력 (변경 이력에 "§3 인벤토리 갱신은 plugin host 본 저장소 PR 필요" 표기).
  b. **에이전트 frontmatter `tools:`** — 영향 받는 .claude/agents/*.md에 `mcp__<name>__<tool>` 추가 (subagent-only면 `permission-profiles-synthesis.md §5-1` inline `mcpServers:` 권장)
  c. **`.claude/settings.json` `permissions.{allow,ask,deny}`** — Tier 정책 반영 (T0=allow / T1·T2=ask / 민감 도구=deny)
  d. **변경 이력** (`_workspace/_baseline/changelog.md`) — Phase 7-4 형식 1행: `| {date} | MCP 채택: {name} | {tier}/{category} | {trigger 사유} |`

  **atomic 적용 범위:** (b)·(c)·(d) 3개만 atomic 묶음. 셋 중 하나라도 실패하면 전부 rollback (§10-D 절차로). (a)는 plugin host 본 저장소 편집이라 별도 트랙 — atomic 그룹에 포함되지 않음. 도입자 권한 부재 시 (a) 권고 메시지만 남기고 (b)(c)(d) atomic 진행.
```

### 10-C. 프로젝트 유형별 채택 패턴 (참고)

| 프로젝트 유형 | phase별 자주 등장하는 MCP |
|--------------|----------------------|
| **Web 서비스** | prototype: `fetch`/`sequential-thinking` → develop: `git`/`playwright`/`chrome-devtools` → integrate: `github`(toolset=`pull_requests,actions`)/`postgres` → ops: `slack`/`linear` |
| **Data 파이프라인** | prototype: `sequential-thinking` → develop: `sqlite`/`filesystem` → integrate: `postgres`/`github` → ops: `slack` |
| **Mobile/Embedded** | develop: `git`/`filesystem` → integrate: `github`(toolset=`actions,issues`) → release: `notion`/`linear` |
| **Research/Analysis** | 전 phase: `fetch`/`brave-search`/`tavily`/`exa` + `sequential-thinking` + 후반 `firecrawl`/`memory` |
| **DevOps/Infra** | develop: `git`/`filesystem` → integrate: `github`(toolset=`actions,security_advisories,dependabot`) → ops: `slack` + custom webhooks |

> 위 매트릭스는 *제안 후보군*일 뿐 강제 아님. 사용자 confirm 게이트는 모든 케이스 동일.

### 10-D. Rollback 절차

기존 채택을 되돌릴 때 (성능 문제·정책 위반·미사용):

```
1. claude mcp remove <name> [-s local|project|user]
2. 영향 받는 에이전트 frontmatter `tools:`에서 해당 mcp__<name>__* 제거
3. .claude/settings.json `permissions.{allow,ask,deny}` 정리
4. permission-profiles-inventory.md §3 인벤토리는 KEEP (PoC 결과는 미래 재채택 자료) — 행 끝에 "(2026-MM-DD rolled back: 사유)" 부기
5. _workspace/_baseline/changelog.md 변경 이력 1행: `| {date} | MCP 회수: {name} | {원래 채택일} | {회수 사유} |`
```

### 10-E. inline 정의 갱신 절차 (rollback 아님)

채택은 유지하되 *inline `mcpServers:` 정의*를 수정해야 할 때 (DB 경로 변경 / uvx 경로 환경 차이 / toolset 확장·축소 / 환경 변수 키 이름 변경 등). rollback이 아니므로 §10-D와 별도 절차.

**갱신 트리거 (5종):**

| # | 신호 | 예시 |
|---|------|------|
| U1 | **DB/repo 경로 변경** | `--db-path` / `--repository`이 가리키는 파일 이동 또는 이름 변경 |
| U2 | **uvx/실행자 경로 변경** | OS 마이그레이션 / Python 버전 업그레이드 / Homebrew → user-install |
| U3 | **toolset 필터 조정** | github의 `GITHUB_TOOLSETS=pull_requests` → `pull_requests,issues` (Layer A 확장) |
| U4 | **환경 변수 키 변경** | `GH_TOKEN` → `GITHUB_PERSONAL_ACCESS_TOKEN` (서버 버전 업그레이드 시) |
| U5 | **MCP 서버 버전 pin 변경** | `npx -y @org/mcp-server@1.0` → `@1.2` |

**갱신 5-step:**

```
Step 1. Locate — 영향 받는 inline 정의 위치 식별
  - <derived>/.claude/agents/*.md 모든 파일에서 frontmatter `mcpServers:` 안의 해당 서버 항목 검색
  - 같은 서버를 inline로 가진 agent가 N개면 N개 모두 동기화 대상

Step 2. Pre-update probe (선택, U2/U5에 권고)
  - 새 command/args/env 조합으로 `permission-profiles-empirical.md §8-3` stdio 핑 1회 — 도구 enumeration이 *기존 카탈로그와 동일*인지 확인
  - U3(toolset 확장)이면 도구 카운트 변화 사전 확인 가능
  - 출처 검증은 §10 Step 2와 동일 (trusted source 확인)

Step 3. User confirm gate (필수)
  - 변경 전후 diff를 사용자에게 표기 — 특히 U3·U4는 권한 surface 변화라 동의 필수
  - U1/U2 같은 단순 경로 정정도 확인 받음 — 자동 적용 금지

Step 4. Apply — 영향 받는 N개 agent.md 모두 동시 갱신 (atomic)
  - inline `mcpServers:`의 command/args/env 필드 직접 편집
  - **YAML schema 보존**: list-of-dicts + `type: stdio` 형태 유지 (9차 사이클 확정)
  - parent의 `~/.claude.json` projects.{cwd}.mcpServers는 *별도 출처* — `claude mcp remove <name>` + `claude mcp add ...`로 정합 갱신 (inline-only 패턴이면 parent 등록 자체가 없으므로 skip)

Step 5. Reflect — 갱신 사실 박제
  a. _workspace/_baseline/changelog.md 변경 이력 1행: `| {date} | MCP 정의 갱신: {server} | inline 정의 (N개 agent) | {U1~U5 사유 + before/after 요약} |`
  b. permission-profiles-inventory.md §3 인벤토리 행은 변경 사항이 *인벤토리 차원*인 경우(예: install 명령 footnote)에만 갱신 — agent별 inline 변경은 인벤토리 무관
  c. **mid-session 미전파 — 다음 세션부터 갱신 정의 적용** (permission-profiles-synthesis.md §5-1 cycle 4 사실, install·update 동일)
```

**rollback과의 차이:**

| | rollback (§10-D) | update (§10-E) |
|---|---|---|
| 채택 자체 | 회수 (`claude mcp remove`) | 유지 |
| agent `tools:` allowlist | 해당 `mcp__<name>__*` 제거 | 변경 없음 (U3이면 추가 가능) |
| settings.json permissions | 정리 | 변경 없음 (U3 toolset 확장 시 부분 갱신 가능) |
| 변경 이력 (`changelog.md`) | "MCP 회수" | "MCP 정의 갱신" |
| 참조 anchor | §10-D | §10-E |
| 인벤토리 §3 | "(rolled back)" 부기 | 변경 없음 (footnote만) |

**자동화 한계:** Step 1·2는 자동(grep·probe), Step 3·4는 사용자 게이트. Step 5는 자동 작성 후 사용자 확인.

### 10-F. 자동화 한계와 권장 진입점

| 자동화 가능 | 자동화 금지 (사용자 게이트) |
|------------|------------------------|
| Trigger 감지 (T1·T2) | install 실행 |
| 후보 discovery + URL 발췌 | API 키 발급·등록 |
| Pre-install probe + 도구 enumeration 표시 | `permissions.allow` 등록 (T0 외) |
| 산출물 4종 *제안* | 산출물 4종 *적용* |

**권장 진입점:** Phase 5-2 합성 시 자연 발화 (T2 트리거) → 사용자 confirm → 채택. `/harness:harness-evolve "X MCP 붙여"`의 mcp-adopt 내부 op가 본 §10을 호출한다.

### 10-G. 병렬 세션 운용 패턴 (Pattern A — 단일 writer + 외부 측정)

§10·`permission-profiles-empirical.md §11`의 측정·채택 작업을 *복수 세션 병렬*로 진행하려는 경우의 운영 doctrine. 13차 사이클 closure 직후 plugin host 운영 결정으로 채택 (host self-host CM 운영 시 doctrine — 외부 install user는 단일 writer 권장만 따르면 됨).

**공유 자원 충돌 분석:**

| 자원 | 동시 쓰기 위험 |
|------|---------------|
| `~/.claude.json` (사용자 단일 파일) | 🔴 `claude mcp add` 동시 호출 시 last-writer-wins (데이터 손실) |
| `<derived>/.claude/settings.json` | 🔴 토글 측정 두 세션이 동시 편집 |
| plugin host `observations.db` (host self-host CM hook, 운영 시) | 🟡 default 모드 lock contention (WAL 미설정) |
| plugin host git index | 🔴 동시 commit 충돌 |
| Claude Code session context | 🟢 각 세션 격리 |

**Pattern A 운영 룰:**

1. **Single-writer 보장**: 단 한 세션만 `claude mcp add`·settings.json 편집·plugin host commit 책임. 다른 세션은 *읽기 전용*.
2. **외부 측정 분리**: P3-(c) 인터랙티브 측정 등 plugin host 외부 환경 의존 작업은 사용자가 별도 vscode.dev 터미널 탭에서 read-only 실행 → 결과 텍스트만 본 세션에 붙여넣기.
3. **`claude -p` one-shot 활용**: plugin host 세션의 Bash 도구로 `claude -p` 다중 호출 가능 (cycle 13 B1·B2 패턴) — 단, 같은 시점 동시 호출은 `~/.claude.json` 캐시 race 위험이라 순차 호출 권장.
4. **사용자 매뉴얼 게이트**: `~/.claude.json` 또는 `<derived>/.claude/settings.json` 쓰기는 auto-mode classifier가 자주 차단 — 사용자 PowerShell 1줄로 명시 게이트 (cycle 13 B2 토글 패턴). **🆕 15차 사이클 강 empirical (2026-05-11 측정 host 환경):** auto-mode classifier는 `~/.claude.json` user-scope 쓰기의 *첫* 호출은 통과시키지만 *후속* 쓰기는 일관 차단함이 양면 확인됨 (B6 측정의 `claude -p` 호출 차단 + 후속 복원 쓰기도 동일 차단). 복원조차 차단되는 상태에서 환경이 "perturbed restored-blocked"로 남을 위험 — *반드시* 매뉴얼 게이트 fixture(`fixtures/verify_11_3_p3b.ps1`) 또는 사용자 외부 PowerShell 1탭으로 측정 진행 + FINAL Set-Gate로 자동 복원 보장. plugin host 세션 Bash로 `~/.claude.json`을 *연속* 편집 시도하면 perturbed 상태 risk.

**기각된 대안:**

- **Pattern B (branch 분리)**: host self-host CM `observations.db`는 branch 격리 안 됨 — CM 데이터 의도적 단일성 보존. 측정용 일시 branch는 가능하나 merge 시점에 `verify_*.md`·`README.md` 충돌 해결 필요.
- **Pattern C (git worktree)**: worktree별로 `_workspace/_memory/observations.db`가 분리되어 CM 누적 가시성 깨짐 (host self-host CM 설계 의도 위반). 측정 외 작업에서는 권장 안 함.

**병렬화 ROI 권장 영역:**

| 영역 | 병렬화 가치 | 권장 패턴 |
|------|-----------|-----------|
| P2 T1+/T2+ probe (API 키별) | 🟢 높음 — 키별 독립 spawn | 키 도착 즉시 단발 probe 1 세션/키, 결과만 본 세션 박제 |
| P3-(c) interactive vs `-p` 비교 | 🟡 중간 — 측정 자체는 1회성 | 사용자 측 별도 터미널 1탭 (~5분), 결과 텍스트 회수 |
| P3-(a) server-side `--toolsets` | 🔴 낮음 — `~/.claude.json` 쓰기 직렬 | 본 세션 직렬 (mcp remove → 다른 env로 mcp add → 측정 → revert) |
| P3-(b) user-scope toggle | 🔴 낮음 — 동일 | 본 세션 직렬 |
| plugin host commit | 🔴 항상 직렬 | 단일 세션 |
