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

| MCP | Tier | 카테고리 | toolset 필터 지원 |
|-----|------|---------|-----------------|
| `fetch` * | T0 | research | (단일 도구) |
| `filesystem` * | T0 | code-test | path roots로 제한 |
| `git` * | T0 | code-test | (검증 미완) |
| `time` * | T0 | reasoning-aux | (단일 도구) |
| `sequential-thinking` * | T0 | reasoning-aux | (단일 도구) |
| `memory` * | T0 | reasoning-aux | (단일 도구) |
| `sqlite` * | T0 | external-integration | path 제한 |
| `playwright` | T1 | code-test | ✅ (browser/api 분리 가능) |
| `chrome-devtools` | T1 | code-test | (검증 미완) |
| `brave-search` * | T1+ | research | (검증 미완) |
| `tavily` | T1+ | research | (검증 미완) |
| `exa` | T1+ | research | (검증 미완) |
| `github` | T1+ | external-integration | ✅ `GITHUB_TOOLSETS` |
| `firecrawl` | T2~ | research | (검증 미완) |
| `slack` | T2~ | external-integration | (검증 미완) |
| `postgres` * | T2~ | external-integration | DB 접속 문자열로 제한 |

> "검증 미완"은 본 문서 작성 시점에 실제 install·도구 enumeration·옵션 확인이 안 된 항목 — PoC에서 채워야 함.

---

## 4. 매핑 결정 트리

Phase 5에서 에이전트 명세를 받았을 때:

```
1. 에이전트 description에서 capability 추론
   → LLM이 후보 profile 1~N개 *제안*만 (다중 선택 가능)
   → 사용자 confirm 전엔 합성 금지

2. 사용자 confirm된 profile들에 대해 후보 MCP 열거
   → `claude mcp list`로 install 여부 체크

3. 분기:
   a) MCP install됨 + toolset 필터 지원 → Layer A 사용
      → `.mcp.json`에 toolset env 명시
      → 에이전트 frontmatter엔 필터링된 도구명만 allowlist
   b) MCP install됨 + toolset 미지원 → Layer B 사용
      → 서브에이전트로 격리, frontmatter `tools:`에 필요 도구만 열거
   c) MCP 미install → 사용자에게 3택 제시
      → install 안내 / 빌트인 대체 / 스킵
   d) 어느 경우에도 자동 install·자동 키 발급 금지

4. 합성 산출물 3종 동시 패치:
   - 에이전트 .md frontmatter `tools:`
   - 프로젝트 .claude/settings.json `permissions.allow/ask`
   - 프로젝트 .mcp.json mcpServers (필요 시)
```

---

## 5. 합성 산출물 템플릿

### 5-1. 에이전트 frontmatter (Layer B 격리 케이스)

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
---
```

### 5-2. `.mcp.json` (Layer A 필터 케이스 — github 예)

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

### 5-3. `.claude/settings.json`

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
  d. 산출물 3종(§5) 합성
  e. 변경 사항을 CLAUDE.md 변경 이력에 1줄로 기록
```

---

## 8. 검증 미완 — 후속 PoC 항목

본 문서의 다음 항목은 실제 install 없이 작성됨, PoC 후 갱신 필요:

- `playwright`/`chrome-devtools`의 toolset 옵션 정확한 이름·env 문법
- `git`/`fetch` MCP의 도구 enumeration 결과 (실제 도구명 prefix 패턴)
- `tavily`/`exa`/`firecrawl`/`brave-search`의 키 발급 절차 + 무료 한도
- 서브에이전트 `tools:` allowlist에 MCP 도구명 직접 열거 시 *parent 컨텍스트에는 정의가 안 실리는지* — Claude Code 문서 vs 실측 검증
- `enabledMcpjsonServers` 토글이 컨텍스트 적재까지 막는지(완전 차단) vs 호출만 막는지(정의는 적재)

> PoC 우선순위: §2-2 `web-research` 프로파일에 `fetch` + `brave-search` 조합 (무키·무료) → 가장 빨리 end-to-end 검증 가능.
