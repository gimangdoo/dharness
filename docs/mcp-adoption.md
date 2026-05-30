# 추가 MCP 설치 (런타임 시점 채택)

> [README](../README.md)로 돌아가기

derived 프로젝트 진행 중 신규 MCP가 필요해질 때(예: "playwright로 e2e 테스트", "github MCP로 PR 메타 조회") 사용하는 절차. **dharness root 자체는 self-host CM 격리 영역이라 적용 대상 아님** — 본 절차는 `/harness:harness-new`로 합성된 *derived 프로젝트의 `.claude/`*만 다룬다.

## 채택 트리거 (3종)

| 신호 | 발생 | 자동 감지 |
|------|------|----------|
| **T1 도메인/phase 전환** | baseline 갱신 후 신규 capability 필요 (prototype→deploy 등) | ✅ Phase 9 baseline diff |
| **T2 합성 시 인벤토리 미충족** | Phase 5-2 §4 결정 트리 분기 `c)` | ✅ `claude mcp list` vs profile 후보 차집합 |
| **T3 사용자 명시 요청** | "Slack 알림 보내는 에이전트" 등 발화 | ❌ 사용자 발화 기반 |

## 두 가지 설치 경로

| | 권장 | 수동 |
|---|------|------|
| 진입점 | `/harness:harness-evolve "X MCP 붙여"` (내부 mcp-adopt op) | `claude mcp add ...` 직접 |
| 절차 | discover → probe → confirm → install → reflect (5-step) | 사용자 책임 |
| 산출물 동시 패치 | ✅ 4 산출물 (`§3 인벤토리`/`agent frontmatter`/`settings.json`/`changelog.md` 변경 이력) | ❌ 사용자가 직접 |
| 안전 게이트 | 출처 검증·pre-install probe·user confirm·rollback 절차 포함 | 사용자 책임 |
| 추천 | `/harness:harness-status --mcp [<agent>]`로 3축(E/S/A) 점수 후보 도출 (Phase 5-2 자동 호출 + on-demand) | 사용자 책임 |
| 진단 | `/harness:harness-status --mcp`로 read-only 점검 | 동일 |

권장 경로는 [§10 Dynamic MCP Adoption](../plugins/harness/skills/harness/references/permission-profiles.md#10-dynamic-mcp-adoption--프로젝트-진행에-따른-mcp-신규-채택) 워크플로우를 그대로 따른다.

## 수동 설치 — `claude mcp add` 명령

```powershell
# 기본형
claude mcp add <name> <command> [args...] [-e KEY=VAL ...] [-s local|project|user]

# 예시 — fetch (T0, npm)
claude mcp add fetch -- npx -y mcp-server-fetch-typescript

# 예시 — git (T0, uvx / 경로는 절대경로 필수)
claude mcp add git C:\Users\<user>\AppData\Roaming\Python\Python312\Scripts\uvx.exe -- mcp-server-git --repository C:\path\to\repo

# 예시 — sqlite (T0, uvx / --db-path 절대경로 필수)
claude mcp add sqlite C:\...\uvx.exe -- mcp-server-sqlite --db-path C:\path\to\data.db

# 예시 — github (T1+, Docker / PAT 필요)
claude mcp add github -- docker run -i --rm `
  -e GITHUB_PERSONAL_ACCESS_TOKEN=<pat> `
  -e GITHUB_TOOLSETS=context,repos,issues,pull_requests,users `
  ghcr.io/github/github-mcp-server
```

**검증:** `claude mcp list` → `✓ Connected` 확인.

> ⚠️ **경로 인자는 절대경로 필수** — `--db-path ./...`, `--repository ./...` 등 상대경로는 health check cwd 차이로 `✗ Failed to connect` 발생.

## 스코프 선택

| 스코프 | 위치 | 용도 |
|--------|------|------|
| `local` (default) | `~/.claude.json` `projects.{cwd}.mcpServers` | 이 프로젝트, 본인 머신만 |
| `project` | `./.mcp.json` (commit 대상) | 팀 공유 필요 시 |
| `user` | `~/.claude.json` 전역 | 본인 모든 프로젝트 공유 |

## 권장 패턴 — inline `mcpServers:` (서브에이전트 격리)

parent 컨텍스트에 도구 정의를 적재하지 않으려면 `claude mcp add` 대신 **에이전트 frontmatter에 inline 정의**한다. Phase 5-2 합성의 default이며, 토큰 비용 최소화 + 권한 격리를 동시 달성.

```yaml
---
name: <agent-name>
description: ...
mcpServers:
  - <server>:
      type: stdio
      command: npx
      args: ["-y", "@modelcontextprotocol/server-filesystem", "C:\\path\\to\\allowed"]
tools:
  - mcp__<server>__<tool>
---
```

> **schema 필수:** **list-of-dicts + `type: stdio`** 형태. 누락 시 silent skip 되어 도구 미노출. 합성 템플릿은 [§5-1](../plugins/harness/skills/harness/references/permission-profiles.md#5-1-에이전트-frontmatter-layer-b-격리--권장-inline-mcpservers).

## Pre-install probe (install 없이 도구 enumeration)

trusted source 확인 후, install 영구화 전 stdio JSON-RPC `tools/list`로 도구 카탈로그를 미리 확인:

```powershell
# fixture 복사 → target에 맞게 UVX_PATH·인자 수정 → 실행
node plugins\harness\skills\harness\references\fixtures\probe_sqlite.js
```

→ `COUNT=N` + per-tool `name·required·all-params` 출력. install 부작용 0 (단 패키지 코드는 1회 spawn). [§8-3 참조](../plugins/harness/skills/harness/references/permission-profiles.md#8-3-재사용-가능한-검증-기법).

## 권한 Tier 정책 (요약)

| Tier | 정의 | 자동 적용 |
|------|------|----------|
| **T0** | 무키·로컬 only (fetch/git/sqlite/filesystem/memory/time/sequential-thinking) | 사용자 1회 동의 후 `allow` 가능 |
| **T1** | 무료 API 키 또는 PAT (github/playwright/chrome-devtools/brave-search/tavily/exa) | 키 등록 + 명시 동의 → `allow` |
| **T2** | 유료 또는 민감 외부 (firecrawl/slack/postgres) | 항상 `ask`, 자동 `allow` **금지** |

**자동 install·자동 `allow` 승급 금지** ([§6 안전 정책](../plugins/harness/skills/harness/references/permission-profiles.md#6-안전-정책)). T0이라도 user confirm 게이트 필수.

## 채택 후 mid-session 미전파

`claude mcp add` 또는 inline `mcpServers:` 갱신은 **본 세션에 미적재** — 새 도구가 LLM에 노출되려면 **세션 재시작** 필수. 합성 시점 install된 신규 MCP도 동일.

## 자세한 참조

| 주제 | 위치 |
|------|------|
| Tier별 MCP 인벤토리 (도구 enumeration·install 명령) | [`permission-profiles-inventory.md` §3](../plugins/harness/skills/harness/references/permission-profiles-inventory.md) (P7 분리, 2026-05-23) |
| 검증 완료 T0 MCP × capability profile 매트릭스 | [`permission-profiles-inventory.md` §3-1](../plugins/harness/skills/harness/references/permission-profiles-inventory.md#3-1-검증-완료-t0-mcp--capability-profile-매트릭스) |
| 5-step 채택 절차 (Discover→Probe→Confirm→Install→Reflect) | [`permission-profiles-dynamic-adoption.md` §10-2](../plugins/harness/skills/harness/references/permission-profiles-dynamic-adoption.md#10-2-5-step-채택-절차-모든-트리거-공통) (P7 분리, 2026-05-23) |
| Rollback / inline 정의 갱신 | [`permission-profiles-dynamic-adoption.md` §10-4·§10-5](../plugins/harness/skills/harness/references/permission-profiles-dynamic-adoption.md#10-4-rollback-절차) |
| 합성 결과 예시 (4 산출물 1세트) | [`fixtures/synthesis_example/`](../plugins/harness/skills/harness/references/fixtures/synthesis_example/) |
