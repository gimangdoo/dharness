# Permission Profiles — MCP·도구 자동 할당 카탈로그

Phase 5(에이전트 정의)에서 생성되는 에이전트에 빌트인 도구 + MCP 도구 + 권한을 자동 합성할 때 사용하는 카탈로그·결정 트리·합성 룰. Phase 5는 이 문서를 *참조*만 하고, 본 문서가 단일 진실 원천.

---

## 1. 3-layer 권한 모델

에이전트에 도구/MCP를 부여하는 경로는 3개. 토큰 비용·통제 입자도가 다르다.

| Layer | 메커니즘 | 컨텍스트 절감 | 실행 통제 | 적용 시점 |
|-------|---------|-------------|---------|---------|
| **A. 서버 측 toolset 필터** | MCP 서버의 `--toolsets` / env (예: `GITHUB_TOOLSETS=issues,prs`) | ✅ 진짜 줄어듦 (서버가 advertise를 안 함) | ✅ 미advertise = 호출 불가 | `.mcp.json` 등록 시 |
| **B. 서브에이전트 `tools:` allowlist** | 에이전트 frontmatter에 명시 도구만 열거 | ✅ 서브에이전트 컨텍스트만 (parent 영향 X) | ✅ 미열거 = 미노출 | Phase 5 합성 시 |
| **C. `permissions.allow/ask/deny`** | `.claude/settings.json` 패턴 매칭 | ❌ 정의 로드는 그대로 | ✅ 호출 시 승인/차단 | 보안 게이트 |

**우선순위:** A > B > C. 토큰 절감이 목적이면 A·B 조합, C는 보안 wrapper로만.

> **빌트인 baseline — Claude Code deferred tool pool (§11-1 6차 사이클 발견)**
>
> Claude Code 현 빌드는 등록 MCP 도구를 *deferred pool*로 관리한다 — SessionStart 시 system prompt에 *이름 + 짧은 description*만 적재되고, 전체 JSON schema는 `ToolSearch select:<name>`로 lazy-fetch될 때 적재. 즉 *baseline 적재 비용*은 도구 수 × ~20-50 tokens (이름+설명) 수준이며, schema 풀 적재(~200-500 tokens/도구)는 호출 시점에만 발생. 17 MCP 도구 등록 상태에서 SessionStart 비용 추정 ≈ 17 × 30 ≈ **500 tokens** (이전 추정 17 × 350 = 6000 tokens 대비 ~12x 절감).
>
> **함의:**
> - 의도 ②(적재 최소화)의 baseline 자체가 docs 추정보다 우호적. inline `mcpServers:` 패턴 없이도 약식 절감이 작동.
> - 단 도구 *이름·description*은 여전히 등록 도구 수에 비례 → Layer A(서버 advertise 축소)의 가치 유효
> - Layer B(subagent 격리)는 *deferred pool 자체를 subagent 안으로 이동* → parent에는 이름조차 안 나타남, schema lazy-fetch도 subagent 내부에서만 → 절감 폭은 더 큼
> - **§11-3 측정 메트릭 재정의** (6차 사이클 갱신 완료): "도구 카운트 변화"에서 "M1=system prompt 토큰 / M2=deferred pool 카운트 / M3=schema fetch 빈도" 3축 조합으로 — `references/fixtures/verify_11_3.md` 본문 반영됨, 외부 실행자는 갱신본 사용

---

## 2. Capability Profiles (4종)

각 프로파일은 ① 빌트인 도구 ② MCP 후보 ③ 추천 toolset 필터 ④ 격리 권장 여부를 묶는다.

### 2-1. `code-test` — 테스트·코드 워크플로우
- **빌트인:** `Bash`, `Read`, `Edit`, `Glob`, `Grep`, `Write`
- **MCP 후보:** `playwright` (toolset=`browser,navigation`), `chrome-devtools`, `git`, `github` (toolset=`issues,prs,actions`)
- **격리:** Bash 호출이 빈번 → parent에 두는 게 효율적, MCP 부분만 서브에이전트 격리

### 2-2. `web-research` — 리서치·웹 검색
- **빌트인:** `WebFetch`, `WebSearch`
- **MCP 후보:** `fetch`, `brave-search`, `tavily`, `exa`, `firecrawl`
- **격리:** 강력 권장 — 검색 결과는 토큰 소비량이 크므로 서브에이전트가 요약만 반환

### 2-3. `external-integration` — 외부 시스템 연결
- **빌트인:** `Bash`, `WebFetch`
- **MCP 후보:** `github`, `slack`, `notion`, `linear`, `sqlite`, `postgres`
- **격리:** 필수 — 데이터 유출 경계를 명확히, 서브에이전트가 의도된 ops만 수행

### 2-4. `reasoning-aux` — 추론 보조
- **빌트인:** (없음)
- **MCP 후보:** `sequential-thinking`, `memory`, `time`
- **격리:** 불필요 — parent에 직접 부착해도 토큰 비용 낮음

---

## 3. MCP 후보 인벤토리 (Tier 분류)

`*` = 공식 reference (anthropic/modelcontextprotocol), `+` = API 키 필요, `~` = 유료/민감 데이터

| Tier | 정의 | 자동 적용 정책 |
|------|------|--------------|
| **T0** | 무키·로컬 only | 사용자 1회 동의 후 `allow` 가능 |
| **T1** | 무료 API 키 또는 PAT 필요 | 키 등록 + 사용자 명시 동의 → `allow` |
| **T2** | 유료 또는 민감 외부 시스템 | 항상 `ask`, 자동 `allow` 금지 |

| MCP | Tier | 카테고리 | install 명령 (검증 시점) | 도구 enumeration |
|-----|------|---------|-----------------|---|
| `fetch` (mcp-server-fetch-typescript) | T0 | research | `claude mcp add fetch -- npx -y mcp-server-fetch-typescript` ✓ | 4종: `get_raw_text`, `get_rendered_html`, `get_markdown`, `get_markdown_summary` ✓ |
| `sequential-thinking` * | T0 | reasoning-aux | `claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking` ✓ | 1종: `sequentialthinking` ✓ |
| `filesystem` * | T0 | code-test | (PoC 미완) | path roots로 제한 |
| `git` * (Python, uvx) | T0 | code-test | `claude mcp add git <uvx-abs-path> -- mcp-server-git --repository <repo-abs>` ✓ (uvx는 `pip install --user uv` 후 `%APPDATA%\Python\Python312\Scripts\uvx.exe`) | 12종 ✓: `git_status`, `git_diff_unstaged`, `git_diff_staged`, `git_diff`, `git_commit`, `git_add`, `git_reset`, `git_log`, `git_create_branch`, `git_checkout`, `git_show`, `git_branch` (모두 `repo_path` required, 변형 도구는 `target`/`message`/`files`/`branch_name`/`revision`/`branch_type` 추가 required) |
| `time` * | T0 | reasoning-aux | (PoC 미완) | (단일 도구 추정) |
| `memory` * | T0 | reasoning-aux | (PoC 미완) | (PoC 미완) |
| `sqlite` * | T0 | external-integration | `claude mcp add sqlite <uvx-abs-path> -- mcp-server-sqlite --db-path <db-abs-path>` ✓ (8차 사이클, derived 프로젝트에서 검증; **`--db-path`는 절대경로 필수** — 상대경로면 health check `✗ Failed to connect`) | 6종 ✓: `read_query`, `write_query`, `create_table`, `list_tables`, `describe_table`, `append_insight` (read 3종을 allow, `write_query`/`create_table`/`append_insight` 3종을 deny/ask로 게이트 권장) |
| `playwright` | T1 | code-test | (PoC 미완) | ✅ browser/api 분리 가능 |
| `chrome-devtools` | T1 | code-test | (PoC 미완) | (PoC 미완) |
| `brave-search` * | T1+ | research | (PoC 미완) | (PoC 미완) |
| `tavily` | T1+ | research | (PoC 미완) | (PoC 미완) |
| `exa` | T1+ | research | (PoC 미완) | (PoC 미완) |
| `github` | T1+ | external-integration | `claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=... -e GITHUB_TOOLSETS=...  -- ...` (toolsets 검증됨) | ✅ `GITHUB_TOOLSETS` env: 19종(`context`/`repos`/`issues`/`pull_requests`/`users` 5종 default + `actions`/`code_security`/`copilot`/`dependabot`/`discussions`/`gists`/`git`/`labels`/`notifications`/`orgs`/`projects`/`secret_protection`/`security_advisories`/`stargazers`) + 특수 `all` |
| `firecrawl` | T2~ | research | (PoC 미완) | (PoC 미완) |
| `slack` | T2~ | external-integration | (PoC 미완) | (PoC 미완) |
| `postgres` * | T2~ | external-integration | (PoC 미완) | DB 접속 문자열로 제한 |

> **검증된 도구 참조 패턴 (frontmatter `tools:`)**: `mcp__<server>__<tool>` — 예: `mcp__fetch__get_markdown`, `mcp__sequential-thinking__sequentialthinking`. **서버명·도구명의 하이픈/언더스코어는 문자열 그대로 보존됨 (§11-1 6차 사이클 ✓ 확정)** — sequential-thinking이 `mcp__sequential-thinking__sequentialthinking`으로 노출됨이 다음 세션 SessionStart deferred tool list로 측정 완료. 17종 모두 §3 인벤토리 enumeration과 100% 일치.

> "검증 미완"은 본 문서 작성 시점에 실제 install·도구 enumeration·옵션 확인이 안 된 항목 — PoC에서 채워야 함.

> ⚠️ **"install 명령" 컬럼의 용도 — 합성 산출물용 default 아님**
>
> 본 컬럼의 `claude mcp add ...` 명령은 *PoC enumeration·검증 환경 install* 형태이며, `~/.claude.json` projects.{cwd}.mcpServers (= scope `local`) 또는 `.mcp.json` (= scope `project`) 적재 = **parent 컨텍스트에 도구 정의 적재**. 이 경로는 §5-2의 anti-pattern과 동일한 토큰 비용을 부담한다.
>
> **합성 산출물에서는 §5-1 inline `mcpServers:`가 default** — 본 컬럼의 install 명령에서 *동일 패키지명·인자*를 추출해 inline `command:`/`args:`/`env:` 필드로 옮기되, 등록 자체(`claude mcp add`)는 **생략**한다. 예: `claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=... -e GITHUB_TOOLSETS=pull_requests -- npx -y @modelcontextprotocol/server-github` → §5-1-b의 inline `mcpServers.github` 블록으로 변환.
>
> 본 컬럼을 그대로 실행해도 되는 경우는 (1) 본 PoC처럼 도구 enumeration 검증 (2) §5-2의 3 예외 조건 — *그 외에는 §5-1 변환*.

---

## 4. 매핑 결정 트리

Phase 5에서 에이전트 명세를 받았을 때:

```
1. 에이전트 description에서 capability 추론
   → LLM이 후보 profile 1~N개 *제안*만 (다중 선택 가능)
   → 사용자 confirm 전엔 합성 금지

2. 사용자 confirm된 profile들에 대해 후보 MCP 열거
   → `claude mcp list`로 install 여부 체크

3. 분기 (default = inline `mcpServers:` parent 격리):
   a) toolset 필터 지원 MCP (github/playwright 등) → §5-1-b Layer A+B 결합형
      → inline `mcpServers:` 의 env/args에 toolset 필터 박음
      → 에이전트 frontmatter `tools:`엔 필터링된 도구명만 allowlist (Layer C)
      → parent 미적재 + 서버 측 advertise 축소 동시 달성
   b) toolset 미지원 MCP (fetch/sqlite 등) → §5-1-a Layer B 단독
      → 서브에이전트 inline `mcpServers:`로 격리
      → frontmatter `tools:`에 필요 도구만 열거
      → parent 미적재만 (서버 측 도구 풀은 그대로)
   c) MCP 미install (런타임 신규 채택 필요) → §10 dynamic adoption 진입
      → /harness:harness-mcp-adopt 5-step (discover → probe → confirm → install → reflect)
      → 자동 install·자동 키 발급 금지 (§6)
   d) parent 직접 호출 필연성 (드문 케이스) → §5-2 .mcp.json (anti-pattern)
      → §5-2의 3 예외 조건 충족 시에만, enabledMcpjsonServers allowlist 의무

4. 합성 산출물 (default 패치):
   - 에이전트 .md frontmatter `tools:` + inline `mcpServers:` (default)
   - 프로젝트 .claude/settings.json `permissions.allow/ask/deny`
   - 프로젝트 .mcp.json mcpServers (§5-2 예외 조건 시에만)
   - CLAUDE.md 변경 이력 1행 (Phase 7-4)
```

---

## 5. 합성 산출물 템플릿

> ✅ **9차 사이클 RESOLUTION (2026-05-10)** — 8차 EMPIRICAL CAVEAT(§11-2 spawn 시 도구 노출 0건)의 진짜 원인이 *frontmatter `mcpServers:` schema mismatch*임이 확정되었다. 공식 docs(`https://code.claude.com/docs/en/sub-agents` §"Scope MCP servers to a subagent") 발췌 결과 schema는 **list-of-dicts** 형태이며 inline definition에 `type: stdio`(또는 `http`/`sse`/`ws`) 필드가 *필수*. 우리 fixtures는 plain dict + type 누락이었음 → silent skip되어 inline MCP가 subagent에 connect되지 않았다. 9차 사이클에 모든 inline `mcpServers:` 예시를 list-of-dicts + `type:` 형태로 일괄 정정 완료. **재현 검증** (§11-2 spawn 재실행)으로 contradiction 해소를 확정 권장 — derived 프로젝트에서 정정된 fixture 사용 시 도구가 노출되어야 함.

### 5-1. 에이전트 frontmatter (Layer B 격리 — *권장*: inline `mcpServers`)

inline로 MCP 서버를 선언하면 parent 대화에 도구 정의가 적재되지 않는다 (공식 docs §"Configure MCP servers"). 반면 `.mcp.json`에 등록하면 parent에 적재되며, `tools:` allowlist는 *subagent 측 가시성만* 통제한다.

#### 5-1-a. Layer B 단독 (toolset 미지원 MCP — fetch/brave-search/sqlite 등)

```yaml
---
name: web-researcher
description: ...
model: opus
tools:
  - WebFetch
  - WebSearch
  - mcp__brave_search__web_search
  - mcp__fetch__fetch
mcpServers:
  - brave-search:
      type: stdio
      command: npx
      args: ["-y", "@modelcontextprotocol/server-brave-search"]
      env: { BRAVE_API_KEY: "${BRAVE_API_KEY}" }
  - fetch:
      type: stdio
      command: npx
      args: ["-y", "@modelcontextprotocol/server-fetch"]
---
```

> **Schema 정합 (9차 사이클 docs 발췌)**: `mcpServers:`는 **list-of-dicts** 형태 (`-`로 시작), 각 항목 안에 `<server-name>:` key + `type: stdio`(또는 `http`/`sse`/`ws`) 필수. dict-style (`-` 없음 + `type:` 누락)은 schema mismatch로 silent skip되어 inline MCP가 적재 안 됨이 §11-2 contradiction의 진짜 원인이었음.

#### 5-1-b. Layer A+B 결합형 (toolset 지원 MCP — github/playwright 등) — *최강 패턴*

inline `mcpServers:`의 `env:` 또는 `args:`에 toolset 필터까지 박으면 (1) 서버가 advertise하는 도구 자체가 줄고 (= **Layer A**, 진짜 토큰 절감) (2) 그 줄어든 풀이 subagent에만 connect됨 (= **Layer B**, parent 미적재) (3) 그 안에서도 `tools:` allowlist로 가시화 (= **Layer C**). **의도 ②③(세션 적재 최소화 + agent-only 접근)을 동시에 달성하는 정공법.**

```yaml
---
name: gh-pr-reviewer
description: GitHub PR 메타데이터 조회 + diff 리뷰 (read-only)
model: opus
tools:
  - Read
  - Grep
  - mcp__github__list_pull_requests
  - mcp__github__get_pull_request
  - mcp__github__get_pull_request_diff
mcpServers:
  - github:
      type: stdio
      command: npx
      args: ["-y", "@modelcontextprotocol/server-github"]
      env:
        GITHUB_PERSONAL_ACCESS_TOKEN: "${GH_TOKEN}"
        GITHUB_TOOLSETS: "pull_requests"   # 19종 default+추가 toolsets 중 PR만 advertise → Layer A 서버측 필터
---
```

**효과 (추정 — §11-3 측정 후 확정):**

| 패턴 | 서버 advertise | subagent 컨텍스트 적재 | parent 컨텍스트 적재 |
|------|---------------|----------------------|------------------|
| `.mcp.json` + 무토글 (anti-pattern) | 19 toolset × 평균 ~5 도구 ≈ **90+** | ≈ 90+ (inherit) | **≈ 90+** ❌ |
| 5-1-a (Layer B만) | (해당 없음 — toolset 미지원 MCP) | allowlist 도구만 | 0 ✓ |
| **5-1-b (Layer A+B 결합)** | **PR toolset만 ≈ 5~7 도구** | 5~7 (allowlist 일치) | **0** ✓ |

**toolset 필터 적용 가능 MCP** (§3 표 기준):

- `github` — `env: GITHUB_TOOLSETS=...` (19종, §3 footnote 카탈로그)
- `playwright` — `args: ["--caps=...", "--isolated", "--browser=chromium"]` 등 CLI flag
- 기타 toolset 미지원 MCP — 5-1-a 패턴 사용

> **선택 가이드:** 합성 대상 MCP가 toolset 필터를 지원하면 **무조건 5-1-b**. 미지원이면 5-1-a. 둘 다 inline `mcpServers:`라서 parent 미적재는 동일.

### 5-2. `.mcp.json` — *예외* 케이스 (anti-pattern, parent 적재 불가피한 경우만)

> ⚠️ **합성 default 아님 (의도 ②③ 위반 패턴)** — `.mcp.json` 등록은 parent 컨텍스트에도 도구 정의를 적재해 토큰을 소비하며, agent-only 접근 원칙도 깨진다. **합성 가이드의 default는 §5-1 inline `mcpServers:` 패턴**이며, 본 §5-2는 다음 *세 가지 예외 조건*에 한정해 사용한다:
>
> 1. **parent (메인 세션)가 해당 MCP 도구를 직접 호출**해야 하는 필연성 — 예: 슬래시 커맨드 본문에서 `mcp__<name>__<tool>` 직접 호출, 오케스트레이터가 subagent 위임 없이 직접 사용
> 2. **여러 subagent가 같은 MCP를 공유**해야 하고 inline 중복 비용이 더 큰 경우 (드문 케이스)
> 3. **개발팀 공유 (`-s project`)** — `.mcp.json`을 commit해서 모든 팀원이 동일 MCP 사용 (이 경우도 parent 적재 비용은 감수)
>
> 의심스러우면 §5-1로. 위 3 조건 어느 것도 명확히 충족 안 되면 **inline 패턴이 정답**.

```json
{
  "mcpServers": {
    "github": {
      "command": "...",
      "env": { "GITHUB_TOOLSETS": "issues,pull_requests,actions" }
    }
  }
}
```

> **본 패턴 사용 시 의무 사항:**
> - `enabledMcpjsonServers` allowlist를 명시 — 적재 도구 제한 (§11-3 토글 효과 측정 후 확정)
> - `permissions.deny`로 민감 도구 블랙리스트 동시 박제 (§5-3 + §6.3)
> - parent 컨텍스트의 토큰 비용을 `/harness:harness-mcp-status` §섹션 1·6에서 정기 점검

### 5-3. `.claude/settings.json` (모든 패턴 공통 — Layer C 게이트)

```jsonc
{
  "permissions": {
    "allow": [
      "mcp__fetch__fetch",
      "mcp__brave_search__web_search"
    ],
    "ask": [
      "mcp__github__create_issue"
    ],
    "deny": [
      "mcp__github__delete_repository"
    ]
  },
  "enabledMcpjsonServers": ["github", "brave-search", "fetch"]
}
```

> **`enabledMcpjsonServers` 적용 범위:** 본 키는 **§5-2 (`.mcp.json`) 패턴 사용 시에만 유효**. §5-1 inline `mcpServers:` 패턴은 본 키와 무관 — agent 시작 시 inline 정의로 직접 connect한다. 따라서 default 합성(§5-1)에서는 `enabledMcpjsonServers` 키 자체가 settings.json에 부재해도 무방 (`synthesis_example/settings.json` 박제 예시 참조).
>
> **`permissions.allow/ask/deny`**는 두 패턴 모두에 유효 — *호출 시점*에 적용되는 Layer C 게이트라서 inline·`.mcp.json` 무관하게 작동.

---

## 6. 안전 정책

1. **자동 install 금지** — MCP 등록은 항상 사용자 명시 동의. 에이전트 합성은 *제안*만.
2. **`allow` 자동 승급은 T0 한정** — T1·T2는 사용자 confirm 후에만 `allow`로, 기본값은 `ask`.
3. **민감 도구는 `deny`로 명시** — 삭제·force push·외부 메시지 발송 류는 화이트리스트가 아니라 *블랙리스트*로 박제 (`mcp__github__delete_*`, `mcp__slack__post_message` 등).
4. **dharness 본체 read-only invariant 보존** — Phase 5 합성은 *생성 대상 프로젝트*의 `.claude/`·`.mcp.json`만 건드리며, dharness의 `plugins/harness/`·`plugins/cm-harness/`는 절대 수정하지 않음.
5. **환각 봉쇄** — LLM 제안 후보는 본 문서의 인벤토리 표 또는 `claude mcp list` 결과로 교집합 검증. 표에 없고 인벤토리에도 없는 MCP는 사용자에게 별도 검토 요청.

---

## 7. Phase 5에서의 호출 절차

```
Phase 5-1: 기존 에이전트 정의 작성
Phase 5-2: 도구·MCP 합성 (이 문서 적용 지점)
  a. 에이전트 description 분석 → profile 후보 제안
  b. `claude mcp list` 실행 → 인벤토리 확인
  c. 사용자에게 매핑 confirm (AskUserQuestion)
     - 토글 지원 MCP는 §5-1-b (Layer A+B 결합) 권장
     - 미지원 MCP는 §5-1-a (Layer B 단독)
     - parent 직접 호출 필연성 확인되면 §5-2 (anti-pattern, 예외 조건 명시)
  d. 산출물 합성 (§4의 default 패치 4종)
  e. 변경 사항을 CLAUDE.md 변경 이력에 1줄로 기록
  f. 사후 정합 점검: `/harness:harness-mcp-status` (parent 적재 비용 ⚠️ 항목 확인)
```

---

## 8. 검증 상태

### 8-1. 공식 docs로 확정된 사실 ✓

- ✓ **Subagent는 자체 컨텍스트 윈도우를 가짐** (docs §sub-agents intro)
- ✓ **기본은 모든 도구 inherit (MCP 포함)** — `tools:` allowlist를 명시해야 제한됨 (docs §"Configure tools")
- ✓ **`tools:` allowlist에 MCP 도구를 안 적으면 subagent는 MCP 호출 불가**, 단 `.mcp.json` 등록 MCP는 *parent 컨텍스트에는 여전히 적재*됨
- ✓ **Inline `mcpServers:` frontmatter** — subagent 시작 시 connect, 종료 시 disconnect → **parent 컨텍스트에 도구 정의 미적재** (docs §"Configure MCP servers": *"Use the mcpServers field to give a subagent access to MCP servers that aren't available in the main conversation"*)
- ✓ **`disallowedTools`는 inherit pool에서 제거**, `tools` 명시 시엔 그것만 허용 (`disallowedTools` 우선 적용 후 `tools` resolve)

### 8-2. PoC 부분 완료 ✓ / 미완

**완료 (2026-05-10 PoC, 1·2·3·4차 사이클):**
- ✓ `fetch`(npm: mcp-server-fetch-typescript) install + connection 검증 (`✓ Connected`)
- ✓ `sequential-thinking` install + connection 검증
- ✓ `git` (Python, uvx) install + connection 검증 — uvx는 `py -m pip install --user uv` 경유, `%APPDATA%\Python\Python312\Scripts`를 PATH에 prepend하면 `claude mcp add` 인식 (3차 사이클)
- ✓ 도구 enumeration 누적 17종 — §3 표 확정 (fetch 4 + sequential-thinking 1 + git 12, 모두 JSON-RPC `tools/list` 직접 stdio 핑으로 검증; fetch는 npx cache source-grep과도 100% 일치)
- ✓ `claude mcp add` 기본 스코프 = `local` (이 프로젝트만, `~/.claude.json` projects.{path}.mcpServers에 적재) → 다른 프로젝트에 누수 없음 (실파일 inspect)
- ✓ uvx-기반 MCP는 `command:` 필드에 *uvx의 절대경로*를 넣어야 함 (PATH 미통과 시 spawn 실패) — `claude mcp add git C:\...\uvx.exe -- mcp-server-git --repository <repo-abs>` 형태로 검증됨
- ✓ Anthropic auto-mode classifier가 §6 정책("MCP install은 항상 사용자 명시 동의")을 자동 enforce함을 실측 (의도하지 않은 self-test) → §6 정책의 실효성 확인
- ✓ GitHub MCP 공식 toolsets 카탈로그 19종 확정 (§3 표 갱신) — default 5종(`context`/`repos`/`issues`/`pull_requests`/`users`) + 14 추가 + 특수 `all`/`default`
- ✓ Playwright MCP 패키지(@playwright/mcp 또는 microsoft/playwright-mcp)의 카테고리 매핑(navigation/click/screenshot/keyboard/tabs + browser_run_code) 확인 — toolset 필터는 `--isolated`/`--browser`/`--headless`/`--caps`/`--save-session` 등 CLI flag 형태 (env 아님)
- ✓ **mid-session MCP 등록은 본 세션 도구 풀에 미적재** (4차 사이클): 3개 MCP가 `claude mcp list`에서 `✓ Connected`인 동일 세션에서 (a) 부모 측 `ToolSearch` query `"mcp__"` → 0 hit (b) `Explore` 서브에이전트 spawn 후 inherit pool 점검 → 0 hit. **MCP 도구 풀은 세션 시작 시 1회 materialize되며 mid-session add는 다음 세션부터 반영**됨이 양면 empirical 확인 (subagent도 mid-session 추가분 inherit 안 함). → 운영 함의: Phase 5-2 합성 직후 즉시 사용 불가, 사용자에게 "다음 세션부터 사용 가능" 명시 필요.

**6차 사이클 추가 완료 (2026-05-10):**
- ✓ **다음 세션 노출 형태 확정 (§11-1)** — 본 세션 SessionStart deferred tool list로 측정. 17종 모두 §3 enumeration과 일치. **하이픈 보존** (`mcp__sequential-thinking__sequentialthinking`). 결과 박제: [`./fixtures/README.md`](./fixtures/README.md) 결과 로그.
- ✓ **deferred tool pool 모델 발견** (의도 ②에 자연 친화) — Claude Code 현 빌드는 MCP 도구를 *deferred*로 관리, schemas는 `ToolSearch select:<name>`로 lazy-fetch. SessionStart에서는 도구 *이름 + 짧은 description*만 system prompt에 적재되며, 전체 JSON schema는 호출 시점에만 적재. → **inline `mcpServers:` 패턴이 아니더라도 schemas는 lazy-load**되므로 의도 ②(적재 최소화)의 baseline 자체가 docs 추정보다 우호적. 단 *이름 + description* 적재 비용은 여전히 도구 수에 비례 — Layer A toolset 필터(§5-1-b)의 가치는 그대로 유효 (서버 advertise 단계에서 줄임). **§11-3 토글 측정의 정밀도 요구가 변경됨** — 도구 *목록* 변화가 아닌 *schema fetch 빈도* 측정이 더 정확.

**8차 사이클 추가 완료 (2026-05-10) — derived 프로젝트 e2e:**
- ✓ **§11-4 §10 5-step e2e 시연 — Steps 1-4 empirical 완료** (사용자 명시 동의 게이트 통과). derived 프로젝트(`C:\Users\user01\dharness-probe-test`)에서 sqlite MCP 채택 워크플로우 일회 reproducer:
  - **Step 1 Discover:** §3 인벤토리 sqlite 행 매칭 (T0/external-integration)
  - **Step 2 Pre-install probe:** `probe_sqlite.js`(JSON-RPC stdio 핑) → **6 도구 확정** (`read_query`, `write_query`, `create_table`, `list_tables`, `describe_table`, `append_insight`) — fixture comment의 추정 5종에 `create_table`이 추가로 발견됨 → §3 sqlite 행 정정
  - **Step 3 User confirm:** "차례대로 모두 진행해줘" 명시 동의 → §6 게이트 통과
  - **Step 4 Install:** `claude mcp add sqlite <uvx-abs> -- mcp-server-sqlite --db-path <db-rel>` 1차 실행 시 `✗ Failed to connect`. **`--db-path` 절대경로로 재install** 시 ✓ Connected. → **§10 Step 4에 "경로 인자는 절대경로 필수" caveat 박제**
  - **Step 5 Reflect 4 산출물 적용:** (a) §3 인벤토리 sqlite 행 enumeration ✓ (b) `<derived>/.claude/agents/data-analyst.md` 작성 ✓ (c) `<derived>/.claude/settings.json` permissions(allow=read 3종, deny=write_query/create_table/append_insight, ask=fetch) ✓ (d) `<derived>/CLAUDE.md` 변경 이력 1행 ✓
- ✓ **§6 자동 install 금지 정책 self-test 재확인** — derived 프로젝트에 inline `mcpServers:` 갖는 agent 파일을 처음 작성 시도 시 auto-mode classifier가 *untrusted external code execution outside trusted repo*로 차단. 사용자 명시 동의 후 통과. **classifier가 dharness root 외부에서도 동일 enforcement** 확인 → §6 정책의 실효성 영역이 dharness 외부까지 확장됨이 empirical.
- ✓ **§11-2 setup ready (실제 spawn은 외부 세션 의존)** — derived 프로젝트의 `.claude/agents/mcp-isolation-probe.md`에 inline `mcpServers: { fetch: { command: npx, args: ["-y", "mcp-server-fetch-typescript"] } }` 작성 완료. dharness 본 세션은 자기 디렉토리 스캔이라 derived 프로젝트의 agent를 인식할 수 없음 — 외부 실행자가 `cd <derived> && claude` 후 Agent tool spawn 시 본 fixture가 ready-to-run 상태.
- ✅ **§11-2 contradiction 해소 (9차 사이클, 2026-05-10)** — 8차 spawn 결과(도구 노출 0건)의 진짜 원인 확정: `mcpServers:` frontmatter schema가 잘못됨. 공식 docs 발췌(WebFetch `https://code.claude.com/docs/en/sub-agents`)로 schema가 **list-of-dicts** + 각 항목에 `type: stdio` 필수임을 확인. 우리 fixtures는 plain dict + type 누락 → silent skip. 후보 매트릭스: ~~(a) 필드명~~ ✓ `mcpServers` 자체는 맞음 / ~~(b) `tools:` 표기~~ ✗ 제외 (8차 측정) / ~~(c) subagent 인식~~ — 무관 추정 (schema 정정 후 재검증 필요) / ~~(d) 빌드 차이~~ — 무관 추정. **진짜 원인 = (a) 하위 항목 = inline definition schema format**. dharness fixture·synthesis_example·permission-profiles.md §5-1 예시 일괄 정정 완료 (list-of-dicts + `type: stdio`). §8-1 사실 empirical 확정은 정정된 fixture로 §11-2 재spawn 후 확정 가능. 결과 로그 박제: [`./fixtures/README.md`](./fixtures/README.md) 9차 사이클 행.

**여전히 미완 (외부 환경 필요):**
- 서브에이전트 inline `mcpServers:` 합성 산출물(§5-1)을 실제 spawn해서 (a) 해당 도구만 노출 + (b) parent 컨텍스트에는 안 실림 동시 실측 — **8차 사이클 spawn 보고 (외부 실행자, 2026-05-10)**: subagent에 `Bash` 외 도구 0개, allowlist 명시 `mcp__fetch__get_markdown`도 미노출. **§5-1 합성 자체가 작동 안 한 신호** — §8-1 사실 확정 *보류*, §5-1 템플릿 재검토 필요. 후속 9차 사이클 핵심 의제. **레시피: §11-2**.
- `tavily`/`exa`/`firecrawl`/`brave-search`의 키 발급 절차 + 무료 한도 → 사용자 측 키 보유 시점 별건
- `enabledMcpjsonServers` 토글이 컨텍스트 적재까지 막는지 vs 호출만 막는지 (재시작 필요). **레시피: §11-3 — fixture 본문 6차 사이클 갱신 완료 (M1=system prompt 토큰 / M2=deferred pool 카운트 / M3=schema fetch 빈도 3축 메트릭). 단, dharness 자체는 `~/.claude.json` `local` 스코프 적재라 본 토글의 영향권 *밖* — fixture 선조건에 `.mcp.json` `-s project` 등록 MCP가 있는 derived 프로젝트 필수. derived 프로젝트는 8차 사이클에 setup 완료, 외부 측정만 남음.**
- ~~§10 dynamic adoption 워크플로우의 e2e 시연~~ → **8차 사이클 ✓ 완료** (위 §11-4 항목 참조)

> **5차 사이클 진척:** 4종 fixture 박제 완료. **6차 사이클 진척:** §11-1 ✓ + deferred-pool 신규 사실. **7차 사이클 진척:** §11-3 fixture 본문 갱신 (3축 메트릭). **8차 사이클 진척:** §11-4 e2e 시연 ✓ (Steps 1-4 empirical, sqlite 6 도구 enumeration·abs-path caveat·§6 self-test 박제) + §11-2 derived 프로젝트 setup ready. §11-2 spawn·§11-3 측정은 외부 Claude Code 세션 의존 잔존.

### 8-3. 재사용 가능한 검증 기법

**stdio JSON-RPC `tools/list` 직접 핑** — Claude 세션 재시작 없이 MCP 서버의 도구 카탈로그를 empirical하게 enumerate하는 패턴. 임시 Node 스크립트로 (1) `initialize` (2) `notifications/initialized` (3) `tools/list` 3 메시지를 stdio에 write하고 응답을 파싱. 본 PoC에서 fetch 4종 + sequential-thinking 1종을 source-grep과 100% 일치로 검증. PoC 미완 MCP들의 도구 enumeration도 install 없이 일회성 npx로 같은 패턴 적용 가능.

---

## 9. Plugin subagent 제약

dharness `harness` 플러그인이 *생성하는* 에이전트는 **target 프로젝트의 `.claude/agents/`에 직접 작성**되므로 §5-1의 inline `mcpServers:` 패턴이 모두 작동한다. 그러나 만약 누군가 derived 하네스를 plugin 형태로 패키징하면, *plugin 내부* `agents/` 의 subagent에 대해서는 다음 필드가 무시된다 (docs §"Choose the subagent scope"):

- `mcpServers` (보안)
- `permissionMode`
- `hooks`

**이 경우의 우회**: 플러그인 install 후 파일을 `.claude/agents/`에 복사하거나, `.claude/settings.json` `permissions.allow` 패턴으로 세션 단위 허용을 명시. **즉 "MCP-owning subagent" 패턴은 *생성 산출물 위치가 .claude/agents/일 때만 완전 작동*** — 본 문서는 이 가정에 의존한다.

---

## 10. Dynamic MCP Adoption — 프로젝트 진행에 따른 MCP 신규 채택

§3 인벤토리는 정적 스냅샷. 실제 프로젝트는 (a) 도메인이 바뀌거나 (b) phase가 진행되면서 (c) 사용자가 직접 요구하면서 새 MCP가 필요해진다. 이 절차는 **합성 시점이 아닌 *런타임 시점*의 MCP 도입**을 다룬다.

> **적용 경계:** 본 §10 절차는 *derived 프로젝트의 `.claude/`* (= 사용자가 dharness 메타 스킬로 새로 합성한 프로젝트)를 대상으로 한다. **dharness root 자체는 self-host CM 격리 영역**(단계 A 이후) — `plugins/harness/`는 read-only invariant이고, 본 dharness 저장소의 `.claude/`는 자체 진화 기록자라 §10 채택 대상이 아니다. 단, 본 PoC를 위해 dharness 프로젝트에서 MCP를 install·검증하는 행위는 *예외적 검증 환경* — `~/.claude.json` `projects.{dharness}.mcpServers`에 격리되며 derived 프로젝트로 누수되지 않음.

### 10-1. 트리거 신호 (3종)

| # | 신호 | 발생 위치 | 자동 감지 가능? |
|---|------|---------|---------------|
| T1 | **도메인/phase 전환** — baseline 갱신 후 신규 capability 등장 (예: prototype→deploy로 이동하면서 cloud provider integration 필요) | Phase 1·9 / `_workspace/_baseline/*.md` diff | ✅ Phase 9에서 baseline 비교로 감지 |
| T2 | **에이전트 합성 시 인벤토리 미충족** — §4 결정 트리 분기 `c)` 발동 | Phase 5-2 | ✅ `claude mcp list` 결과 vs profile 후보 차집합 |
| T3 | **사용자 명시 요청** — "Slack 알림 보내는 에이전트", "DB 마이그레이션 검증" 등 | 임의 시점 | ❌ 항상 사용자 발화 기반 |

### 10-2. 5-step 채택 절차 (모든 트리거 공통)

```
Step 1. Discover — 후보 식별
  - 1차 출처: 본 문서 §3 인벤토리 (이미 검증된 항목)
  - 2차 출처: 공식 reference (github.com/modelcontextprotocol/servers)
  - 3차 출처: npm 레지스트리 검색 (`mcp-server-*`, `@*/mcp-*`), awesome-mcp-servers 류 큐레이션
  - LLM 환각 방지: 후보 이름은 반드시 위 3개 출처 중 하나에서 *원문 발췌* (URL 동봉)

Step 2. Pre-install probe — install 없이 도구 enumerate (§8-3 기법 재사용)
  - 일회성 spawn으로 stdio JSON-RPC `initialize` → `notifications/initialized` → `tools/list`
  - 명령 패턴:
      npx -y <pkg>            # npm 기반
      uvx <pkg> [-- <args>]   # Python 기반
      docker run --rm -i <img> # docker 기반
  - 결과: 도구 목록·required params·schema → 사용자 confirm 자료
  - install 영구화 전이라 부작용 0 (PATH 등록·config 수정 없음)

Step 3. User confirm gate (필수)
  - AskUserQuestion 으로 Tier 분류·필요 키·대안 빌트인 함께 제시
  - 자동 install 금지 (§6) — 사용자 클릭으로만 진행
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

Step 5. Reflect — 4 산출물 동시 패치
  a. **§3 인벤토리 표** — 새 행 추가 (Tier·카테고리·install 명령·도구 enumeration)
  b. **에이전트 frontmatter `tools:`** — 영향 받는 .claude/agents/*.md에 `mcp__<name>__<tool>` 추가 (subagent-only면 §5-1 inline `mcpServers:` 권장)
  c. **`.claude/settings.json` `permissions.{allow,ask,deny}`** — Tier 정책 반영 (T0=allow / T1·T2=ask / 민감 도구=deny)
  d. **CLAUDE.md 변경 이력** — Phase 7-4 형식 1행: `| {date} | MCP 채택: {name} | {tier}/{category} | {trigger 사유} |`
```

### 10-3. 프로젝트 유형별 채택 패턴 (참고)

| 프로젝트 유형 | phase별 자주 등장하는 MCP |
|--------------|----------------------|
| **Web 서비스** | prototype: `fetch`/`sequential-thinking` → develop: `git`/`playwright`/`chrome-devtools` → integrate: `github`(toolset=`pull_requests,actions`)/`postgres` → ops: `slack`/`linear` |
| **Data 파이프라인** | prototype: `sequential-thinking` → develop: `sqlite`/`filesystem` → integrate: `postgres`/`github` → ops: `slack` |
| **Mobile/Embedded** | develop: `git`/`filesystem` → integrate: `github`(toolset=`actions,issues`) → release: `notion`/`linear` |
| **Research/Analysis** | 전 phase: `fetch`/`brave-search`/`tavily`/`exa` + `sequential-thinking` + 후반 `firecrawl`/`memory` |
| **DevOps/Infra** | develop: `git`/`filesystem` → integrate: `github`(toolset=`actions,security_advisories,dependabot`) → ops: `slack` + custom webhooks |

> 위 매트릭스는 *제안 후보군*일 뿐 강제 아님. 사용자 confirm 게이트는 모든 케이스 동일.

### 10-4. Rollback 절차

기존 채택을 되돌릴 때 (성능 문제·정책 위반·미사용):

```
1. claude mcp remove <name> [-s local|project|user]
2. 영향 받는 에이전트 frontmatter `tools:`에서 해당 mcp__<name>__* 제거
3. .claude/settings.json `permissions.{allow,ask,deny}` 정리
4. §3 인벤토리는 KEEP (PoC 결과는 미래 재채택 자료) — 행 끝에 "(2026-MM-DD rolled back: 사유)" 부기
5. CLAUDE.md 변경 이력 1행: `| {date} | MCP 회수: {name} | {원래 채택일} | {회수 사유} |`
```

### 10-5. 자동화 한계와 권장 진입점

| 자동화 가능 | 자동화 금지 (사용자 게이트) |
|------------|------------------------|
| Trigger 감지 (T1·T2) | install 실행 |
| 후보 discovery + URL 발췌 | API 키 발급·등록 |
| Pre-install probe + 도구 enumeration 표시 | `permissions.allow` 등록 (T0 외) |
| 산출물 4종 *제안* | 산출물 4종 *적용* |

**권장 진입점:** Phase 5-2 합성 시 자연 발화 (T2 트리거) → 사용자 confirm → 채택. 별도 슬래시 커맨드(`/harness:harness-add-mcp`)는 *후속 도입 고려 대상*이며 본 문서 작성 시점엔 미구현.

---

## 11. 실증 가능한 테스트 레시피 — §8-2 미완 항목 reproducer

§8-2의 미완 항목 각각을 외부 환경(다음 세션·derived 프로젝트·API 키)에서 *복사 실행*만으로 재현할 수 있도록 박제. 각 레시피는 자기 완결적 — 본 문서 외 다른 컨텍스트 불필요.

> **적용 경계:** 본 §11 fixture들은 *외부 검증 환경*(다음 세션·derived 프로젝트·재시작·신규 install) 의존이라 dharness 본 세션에서는 mid-session 직접 실행 불가. §11-2의 `mcp-isolation-probe.agent.md`는 특히 *dharness 밖의 derived 프로젝트* `.claude/agents/`에 복사해야 하며, dharness root `.claude/agents/`에는 두지 않는다 (self-host CM 격리 위반). §10과 동일한 분계 — 본 fixture 결과는 derived 프로젝트 동작 검증이지 dharness 자체 동작 검증이 아니다.

### 11-1. `mcp__<server>__<tool>` 노출 패턴 검증 (다음 세션)

▶ **Fixture:** [`./fixtures/verify_11_1.md`](./fixtures/verify_11_1.md) — 다음 세션에서 첫 user 메시지로 입력할 프롬프트 + 결과 캡처 템플릿 + §3 표 갱신 액션 박제 완료.

**목적:** mid-session add된 MCP가 다음 세션 시작 시 실제 어떤 도구명으로 노출되는지 (특히 하이픈을 포함한 서버명 `sequential-thinking`이 `mcp__sequential-thinking__*` 또는 `mcp__sequential_thinking__*` 중 어느 것인지).

**선조건:** 본 세션에서 fetch/sequential-thinking/git 3개 MCP 등록 완료 (`claude mcp list`로 ✓ Connected 확인).

**절차:**
```
1. Claude Code 세션 종료 후 재시작 (같은 dharness 프로젝트)
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

**목적:** §5-1 합성 템플릿이 실제로 (a) subagent에는 도구 노출 (b) parent에는 미적재 — 양쪽 동시 검증.

**선조건:** dharness 본 폴더 *밖*의 derived 프로젝트 1개 (예: `~/myproject/`). dharness root는 self-host CM 격리 영역이라 부적합.

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

**기록처:** §1 표의 Layer 비교 컬럼 "컨텍스트 절감" 셀에 검증 결과 footnote 추가.

### 11-4. §10 Dynamic Adoption e2e 시연 — SQLite 분석 시나리오

▶ **Fixture:** [`./fixtures/probe_sqlite.js`](./fixtures/probe_sqlite.js) — Step 2 pre-install JSON-RPC stdio probe ready-to-run (UVX_PATH/DB_PATH만 환경 맞게 조정). Step 3 user confirm 통과 후 install 직전 도구 enumeration 자동 수행. (mcp_probe_git.js 동일 패턴, target만 sqlite로 교체)

**목적:** §10의 5-step 절차가 실제 흐름으로 동작함을 1회 reproducer로 박제.

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
  a. permission-profiles.md §3 sqlite 행 갱신 — 도구 enumeration 채움
  b. .claude/agents/data-analyst.md frontmatter `tools:`에:
       mcp__sqlite__read_query, mcp__sqlite__list_tables, mcp__sqlite__describe_table
     (write_query / append_insight는 의도적 제외 — Tier 정책상 ask)
  c. .claude/settings.json:
       "permissions": {
         "allow": ["mcp__sqlite__read_query", "mcp__sqlite__list_tables", "mcp__sqlite__describe_table"],
         "ask":   ["mcp__sqlite__write_query", "mcp__sqlite__append_insight"]
       }
  d. CLAUDE.md 변경 이력 1행:
       | {date} | MCP 채택: sqlite | T0/external-integration | data-analyst가 ./data/app.db 분석 필요 (T2 트리거) |
```

**검증 게이트:** 위 5-step을 *실제 derived 프로젝트*에서 1회 수행하여 (a) ✓ Connected (b) 다음 세션에서 `mcp__sqlite__read_query` 노출 (§11-1과 동일 검증) (c) settings.json `allow`로 read_query 무프롬프트 호출 (d) write_query 호출 시 ask 프롬프트 발생 — 4가지 동시 통과 시 §10 워크플로우 stable로 확정. 미통과 항목은 §10에 footnote로 박제.
