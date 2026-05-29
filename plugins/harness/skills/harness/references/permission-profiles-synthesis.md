# Permission Profiles — 합성 산출물 §5 + §7 호출 절차

> **Read at phase:** Phase 5-2 (에이전트 합성 시 — inline `mcpServers:` 작성·model 선택·`.mcp.json` 예외 판정·settings.json Layer C 박제·Phase 5 호출 절차).
>
> P7 분리(2026-05-23) — `permission-profiles.md` §5-1·5-1-a·5-1-b·5-1-c를 본 파일로 흡수.
>
> P7 추가 분리(2026-05-28, PA5) — §5-2 (.mcp.json 예외) + §5-3 (settings.json Layer C) + §7 (Phase 5 호출 절차) 본문도 본 파일로 흡수. main 본문엔 pointer만 잔존.

## §5-1. 에이전트 frontmatter (Layer B 격리 — *권장*: inline `mcpServers`)

inline로 MCP 서버를 선언하면 parent 대화에 도구 정의가 적재되지 않는다 (공식 docs §"Configure MCP servers"). 반면 `.mcp.json`에 등록하면 parent에 적재되며, `tools:` allowlist는 *subagent 측 가시성만* 통제한다.

> 🆕 **10차 사이클 새 발견 — `tools:` allowlist는 inline 서버 도구를 줄이지 못한다 (P0 P0 재현 검증 empirical)**
>
> P0 재현 검증 결과: frontmatter `tools:`에 `mcp__fetch__get_markdown` *1종만* allowlist했는데도 inline 서버의 **4종 전부** (`get_raw_text`/`get_rendered_html`/`get_markdown`/`get_markdown_summary`) 모두 subagent 도구 풀에 노출됨.
>
> **함의:**
> - `tools:` allowlist는 빌트인 도구·`.mcp.json` 등록 inherit pool은 줄이지만, **inline `mcpServers:` 정의의 도구는 advertise되는 모든 도구가 자동 노출**됨.
> - 따라서 *inline 서버의 도구 카운트 통제*는 두 채널뿐:
>   1. **Layer A** — 서버 측 toolset 필터 (`args:`/`env:`로 `--toolsets=...` / `GITHUB_TOOLSETS=...` 박음, §5-1-b 패턴) — 서버가 advertise 자체를 안 하면 connect 후에도 도구 0종
>   2. **Layer C** — `settings.json permissions.deny`로 호출 시점 차단 (적재는 그대로지만 호출 불가)
> - **§5-1-b Layer A+B 결합형 권고가 더 강해짐** — toolset 필터 지원 MCP는 *반드시* args/env로 advertise 축소. 미지원 MCP(fetch 등)는 `permissions.deny`로 부수 효과 도구 차단 (본 문서 §5-3 deny 권고 강화).
>
> **합성 가이드 갱신 (10차 cycle):** Phase 5-2 합성 시 `tools:` allowlist는 *의도 표현* (작성자가 어떤 도구를 사용할 의도인지 명시)으로 박제하되, **실제 도구 풀 통제는 Layer A 또는 deny에 의존**. allowlist에 1종만 적었다고 해서 다른 도구가 호출 *불가*가 되는 게 아님 — 여전히 호출 가능하므로 deny가 강제 채널.

### §5-1-a. Layer B 단독 (toolset 미지원 MCP — fetch/brave-search/sqlite 등)

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

> **Schema 정합 (9차 사이클 docs 발췌)**: `mcpServers:`는 **list-of-dicts** 형태 (`-`로 시작), 각 항목 안에 `<server-name>:` key + `type: stdio`(또는 `http`/`sse`/`ws`) 필수. dict-style (`-` 없음 + `type:` 누락)은 schema mismatch로 silent skip되어 inline MCP가 적재 안 됨이 `permission-profiles-empirical.md §11-2` contradiction의 진짜 원인이었음.

### §5-1-b. Layer A+B 결합형 (toolset 지원 MCP — github/playwright 등) — *최강 패턴*

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

**효과 (추정 — `permission-profiles-empirical.md §11-3` 측정 후 확정):**

| 패턴 | 서버 advertise | subagent 컨텍스트 적재 | parent 컨텍스트 적재 |
|------|---------------|----------------------|------------------|
| `.mcp.json` + 무토글 (anti-pattern) | 19 toolset × 평균 ~5 도구 ≈ **90+** | ≈ 90+ (inherit) | **≈ 90+** ❌ |
| 5-1-a (Layer B만) | (해당 없음 — toolset 미지원 MCP) | allowlist 도구만 | 0 ✓ |
| **5-1-b (Layer A+B 결합)** | **PR toolset만 ≈ 5~7 도구** | 5~7 (allowlist 일치) | **0** ✓ |

**toolset 필터 적용 가능 MCP** (`permission-profiles-inventory.md §3` 표 기준):

- `github` — `env: GITHUB_TOOLSETS=...` (19종, §3 footnote 카탈로그)
- `playwright` — `args: ["--caps=...", "--isolated", "--browser=chromium"]` 등 CLI flag
- 기타 toolset 미지원 MCP — 5-1-a 패턴 사용

> **선택 가이드:** 합성 대상 MCP가 toolset 필터를 지원하면 **무조건 5-1-b**. 미지원이면 5-1-a. 둘 다 inline `mcpServers:`라서 parent 미적재는 동일.

### §5-1-c. 모델 선택 by agent role (Q2 doctrine, 2026-05-16)

frontmatter `model:` 필드는 *capability profile 단독*이 아니라 *agent role 축*으로 결정한다. 과거 "전 에이전트 `model: opus` 일괄" 박제는 비용 ~7배. 본 doctrine은 합성 시 *역할*에 매핑.

| agent role 축 | recommended `model:` | 근거 |
|---|---|---|
| **synthesis / 추론 합성** (메인 작성자·QA boundary check·orchestrator) | `opus` | 다중 신호 통합 + 정합성 결정 — 추론 깊이 직결 |
| **review / 비판** (code-reviewer·security-auditor·design-reviewer) | `opus` | cross-artifact 비교 + edge case 발굴 |
| **write / 생성** (code-author·schema-migration·doc-author) | `opus` | 산출물 품질 회복 비용 큼 |
| **read-only / 탐색** (`Explore` 타입·log-grepper·codebase-mapper) | `sonnet` | summarization 위주 — 비용 ~7배 ↓, 품질 손실 미미 |
| **read-only / 요약** (web-researcher·doc-summarizer·log-analyst) | `sonnet` | input parsing + 압축 — sonnet 충분 |
| **결정성 검증** (validate script 호출·structure check) | (모델 불요 — script) | LLM 호출 0 |

**Profile × role 매트릭스:**

| capability profile (`permission-profiles-profiles.md §2`) | 전형 role | recommended |
|---|---|---|
| `code-test` | synthesis (PR 작성) / review (PR 리뷰) | opus |
| `web-research` | read-only 요약 | **sonnet** |
| `external-integration` | write (DB migration / API 통합) | opus |
| `reasoning-aux` | synthesis (단계별 추론) | opus |
| `ml-pipeline` | synthesis (실험 설계) / read-only (결과 요약) | opus / sonnet 혼합 |
| `devops-infra` | write (배포·rollback) | opus |
| `mobile-native` | write (빌드 디버깅) | opus |
| `data-eng` | write (마이그레이션) / read-only (집계 요약) | opus / sonnet 혼합 |

**합성 시 절차:**

1. Phase 5 에이전트 정의 작성 시 본 §5-1-c 표로 role 매핑
2. `model:` 필드 박제 — opus default, read-only 명시 시 sonnet
3. `permissions.deny`에 변경 도구 박제는 동일 (model 선택과 무관)
4. 사용자 명시 override 가능 — "보수적으로 전부 opus로" / "비용 우선 sonnet 최대화"

> **위반 시 검출:** `validate/chain.py` `check_agent_model_field()`가 frontmatter `model:` 누락을 FAIL (P0-2 doctrine 정합). 단 sonnet 매핑이 적절한지의 *판정*은 LLM 영역 — Phase 5.5 self-critique에서 다룬다.

---

## §5-2. `.mcp.json` — *예외* 케이스 (anti-pattern, parent 적재 불가피한 경우만)

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
> - `enabledMcpjsonServers` allowlist를 명시 — 적재 도구 제한 (`permission-profiles-empirical.md §11-3` 토글 효과 측정 후 확정)
> - `permissions.deny`로 민감 도구 블랙리스트 동시 박제 (§5-3 + `permission-profiles.md §6.3`)
> - parent 컨텍스트의 토큰 비용을 `/harness:harness-mcp-status` 섹션 1·6에서 정기 점검

---

## §5-3. `.claude/settings.json` (모든 패턴 공통 — Layer C 게이트)

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

> **`enabledMcpjsonServers` 적용 범위:** 본 키는 **§5-2 (`.mcp.json`) 패턴 사용 시에만 유효**. §5-1 inline `mcpServers:` 패턴은 본 키와 무관 — agent 시작 시 inline 정의로 직접 connect한다. 따라서 default 합성(§5-1)에서는 `enabledMcpjsonServers` 키 자체가 settings.json에 부재해도 무방 (`fixtures/synthesis_example/settings.json` 박제 예시 참조).
>
> **`permissions.allow/ask/deny`**는 두 패턴 모두에 유효 — *호출 시점*에 적용되는 Layer C 게이트라서 inline·`.mcp.json` 무관하게 작동.

> 🆕 **10차 사이클 deny 권고 강화 — inline 서버 + 부수 효과 도구 (P0 새 발견 함의)**
>
> P0 재현 검증으로 확정: inline `mcpServers:` 정의의 도구는 frontmatter `tools:` allowlist로 *줄지 않는다* (4종 전부 노출). 따라서 부수 효과 도구를 *확실히* 차단하려면 다음 두 채널 중 하나 *반드시* 적용:
>
> 1. **Layer A 서버 측 advertise 필터** — toolset 필터 지원 MCP(github/playwright)는 `args:`/`env:`로 advertise 도구 자체를 줄임 (§5-1-b 패턴). 미지원 MCP는 이 채널 사용 불가.
> 2. **Layer C `permissions.deny`** — toolset 미지원 MCP(fetch/sqlite 등)에서 부수 효과·DDL·write 도구는 *반드시* `deny` 박제. `ask`로 두면 사용자가 prompt에서 실수로 confirm 시 호출됨 — *strict read-only*가 의도라면 `deny`만 안전.
>
> **권고 패턴 (sqlite 같은 read/write 양면 MCP):**
>
> ```jsonc
> {
>   "permissions": {
>     "allow": ["mcp__sqlite__read_query", "mcp__sqlite__list_tables", "mcp__sqlite__describe_table"],
>     "deny":  ["mcp__sqlite__write_query", "mcp__sqlite__create_table", "mcp__sqlite__append_insight"]
>   }
> }
> ```
>
> *왜 `ask`가 아닌 `deny`인가:* `ask`는 prompt 발생 → 사용자 confirm 시 통과. read-only가 *의도된 정책*이라면 confirm 자체를 차단하는 `deny`가 정합. `ask`는 사용자 판단을 매번 묻고 싶은 경계 case에만.
>
> **진단 채널** (11차 사이클 박제): 본 deny 정합 누락은 `/harness:harness-mcp-status` §4의 신규 점검 항목 — agent별 inline `mcpServers:` advertise 도구를 enumerate(`permission-profiles-inventory.md §3` 인벤토리 또는 `permission-profiles-empirical.md §8-3` stdio probe) 후 부수 효과 도구가 `permissions.deny`에 박제되어 있는지 검출. 휴리스틱 prefix(`write_/insert_/update_/delete_/remove_/append_/create_/set_/commit_/push_/exec*/run_`)는 의심 신호일 뿐, 최종 판정은 사용자 도메인 지식. 합성 *후* 정정은 §10-E inline 정의 갱신 절차 5-step.

---

## §7. Phase 5에서의 호출 절차

```
Phase 5-1: 기존 에이전트 정의 작성
Phase 5-2: 도구·MCP 합성 (본 문서 + permission-profiles.md 적용 지점)
  a. 에이전트 description 분석 → profile 후보 제안
  b. `claude mcp list` 실행 → 인벤토리 확인
  c. 사용자에게 매핑 confirm (AskUserQuestion)
     - 토글 지원 MCP는 §5-1-b (Layer A+B 결합) 권장
     - 미지원 MCP는 §5-1-a (Layer B 단독)
     - parent 직접 호출 필연성 확인되면 §5-2 (anti-pattern, 예외 조건 명시)
  d. 산출물 합성 (permission-profiles.md §4의 default 패치 4종)
  e. 변경 사항을 _workspace/_baseline/changelog.md 변경 이력에 1줄로 기록
  f. 사후 정합 점검: `/harness:harness-mcp-status` (parent 적재 비용 ⚠️ 항목 확인)
```
