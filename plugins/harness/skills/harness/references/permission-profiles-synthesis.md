# Permission Profiles — 합성 산출물 §5-1 (agent frontmatter)

> **Read at phase:** Phase 5-2 (에이전트 합성 시 — inline `mcpServers:` 작성·model 선택).
>
> P7 분리(2026-05-23) — `permission-profiles.md` §5-1·5-1-a·5-1-b·5-1-c를 본 파일로 흡수. main 본문엔 pointer만 잔존. §5-2 (.mcp.json 예외) 및 §5-3 (settings.json Layer C) 는 main에 유지.

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
> - **§5-1-b Layer A+B 결합형 권고가 더 강해짐** — toolset 필터 지원 MCP는 *반드시* args/env로 advertise 축소. 미지원 MCP(fetch 등)는 `permissions.deny`로 부수 효과 도구 차단 (`permission-profiles.md §5-3` deny 권고 강화).
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

> **Schema 정합 (9차 사이클 docs 발췌)**: `mcpServers:`는 **list-of-dicts** 형태 (`-`로 시작), 각 항목 안에 `<server-name>:` key + `type: stdio`(또는 `http`/`sse`/`ws`) 필수. dict-style (`-` 없음 + `type:` 누락)은 schema mismatch로 silent skip되어 inline MCP가 적재 안 됨이 `permission-profiles.md §11-2` contradiction의 진짜 원인이었음.

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

**효과 (추정 — `permission-profiles.md §11-3` 측정 후 확정):**

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

| capability profile (`permission-profiles.md §2`) | 전형 role | recommended |
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
