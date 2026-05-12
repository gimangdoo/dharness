# Harness — Team-Architecture Factory for Claude Code

> 도메인 한 문장을 **에이전트 팀 + 스킬 세트**로 변환하는 메타 스킬.
> A meta-skill that turns a domain description into an agent team and the skills they use.

---

## 무엇인가

`harness`는 도메인을 입력 받아 에이전트 3~5명 + 스킬 세트를 자동 생성하는 메타 스킬 팩토리입니다. 다른 단일 에이전트/프롬프트 프레임워크와 달리, harness는 **팀 아키텍처 팩토리** — 6가지 사전 정의된 팀 패턴 중 도메인에 맞는 것을 선택하고 에이전트 협업 프로토콜을 함께 설계합니다.

### 6 팀 아키텍처 패턴

| 패턴 | 적합한 작업 |
|------|----------|
| **Pipeline** | 단계별 순차 흐름 (분석 → 설계 → 검증) |
| **Fan-out / Fan-in** | 병렬 분기 → 결과 통합 (멀티 소스 리서치) |
| **Expert Pool** | 도메인별 전문가 풀에서 동적 선택 (티켓 라우팅) |
| **Producer-Reviewer** | 생성-비판 분리 (코드 작성 + 리뷰) |
| **Supervisor** | 메타 에이전트가 분배·모니터·종합 |
| **Hierarchical Delegation** | 상위 → 하위 위임, 결과 상위 통합 |

---

## 빠른 시작

### 1. 설치

```powershell
claude plugin marketplace add gimangdoo/dharness
claude plugin install harness@dharness
```

로컬 개발용 (marketplace 거치지 않음):

```powershell
claude --plugin-dir C:\path\to\dharness\plugins\harness
```

### 2. 새 도메인에 적용

```text
/harness:harness-new 코드 리뷰를 자동화하는 도메인
```

→ 사용자 프로젝트의 `.claude/agents/{name}.md`·`.claude/skills/{name}/SKILL.md`·`CLAUDE.md`에 산출물 생성.

---

## 호출 방식

| 방식 | 발동 | 비용 통제 | 용도 |
|---|---|---|---|
| **자연어 트리거** | "하네스 구성해줘" 등 자연 발화 ↔ skill description 매칭 | LLM이 자동 분기 | 자연스러운 발화, 일반 사용 |
| **Slash command** | `/harness:harness-new` 등 결정적 호출 | 사용자가 Phase 범위 직접 지정 | 비용 회피, 트리거 확률 의존 제거 |

### Slash command 카탈로그 (9개)

```
/harness:harness-new <도메인>          # Phase 0~8 전체 (신규 구축)
/harness:harness-add-agent <역할>      # Phase 4·5·7·8 (1·2·3 skip)
/harness:harness-add-skill <스킬>      # Phase 6·7·8 (1~5 skip)
/harness:harness-baseline              # Phase 1·2 재실행 + drift 분석
/harness:harness-audit                 # 정합성 감사 (read-only)
/harness:harness-evolve <피드백>       # Phase 9 수동 진화
/harness:harness-adapt                 # Phase 10 telemetry drift 점검
/harness:harness-mcp-adopt <사유>      # 런타임 시점 신규 MCP 채택 (§10 dynamic adoption)
/harness:harness-mcp-status            # MCP 상태 진단 — 인벤토리·매트릭스·정합 (read-only)
```

명령어 본문은 `plugins/harness/commands/`에 보관.

---

## 프로젝트 구조

```
.
├── .claude-plugin/
│   └── marketplace.json       # harness plugin 단일 카탈로그
├── plugins/
│   └── harness/               # PLUGIN — 메타 스킬 팩토리
│       ├── .claude-plugin/plugin.json
│       ├── skills/harness/    # SKILL.md + references/
│       └── commands/          # harness-* 9개
├── CLAUDE.md
└── README.md
```

---

## Skill 워크플로우 11단계

`harness` 메타 스킬은 다음 11단계로 동작합니다:

| Phase | 이름 | 출력 |
|-------|------|------|
| 0 | Pre-flight 감사 | 신규/확장/유지보수 분기 |
| 1 | Code Research | 프로젝트 baseline (코드 인벤토리 + 도메인 sense) |
| 2 | Project Inquiry | 사용자 의도 + 도메인 sense 정합 |
| 3 | 도메인 분석 | 작업 유형 + 충돌 분석 |
| 4 | 팀 아키텍처 | 모드 + 패턴 + 분리 기준 |
| 5 | 에이전트 정의 | `.claude/agents/{name}.md` |
| 6 | 스킬 생성 | `.claude/skills/{name}/SKILL.md` |
| 7 | 오케스트레이션 | 통합 스킬 + CLAUDE.md 포인터 |
| 8 | 검증 (7단계) | 구조·실행·트리거·드라이런·반복 개선 |
| 9 | 진화 (수동) | 사용자 피드백 → 에이전트/스킬 갱신 |
| 10 | Runtime Adaptation | telemetry → drift 감지 → 제안+승인 |

상세는 [`plugins/harness/skills/harness/SKILL.md`](./plugins/harness/skills/harness/SKILL.md).

---

## 추가 MCP 설치 (런타임 시점 채택)

derived 프로젝트 진행 중 신규 MCP가 필요해질 때(예: "playwright로 e2e 테스트", "github MCP로 PR 메타 조회") 사용하는 절차.

### 채택 트리거 (3종)

| 신호 | 발생 | 자동 감지 |
|------|------|----------|
| **T1 도메인/phase 전환** | baseline 갱신 후 신규 capability 필요 (prototype→deploy 등) | ✅ Phase 9 baseline diff |
| **T2 합성 시 인벤토리 미충족** | Phase 5-2 §4 결정 트리 분기 `c)` | ✅ `claude mcp list` vs profile 후보 차집합 |
| **T3 사용자 명시 요청** | "Slack 알림 보내는 에이전트" 등 발화 | ❌ 사용자 발화 기반 |

### 두 가지 설치 경로

| | 권장 | 수동 |
|---|------|------|
| 진입점 | `/harness:harness-mcp-adopt <사유>` | `claude mcp add ...` 직접 |
| 절차 | discover → probe → confirm → install → reflect (5-step) | 사용자 책임 |
| 산출물 동시 패치 | ✅ 4 산출물 (`§3 인벤토리`/`agent frontmatter`/`settings.json`/`CLAUDE.md` 변경 이력) | ❌ 사용자가 직접 |
| 안전 게이트 | 출처 검증·pre-install probe·user confirm·rollback 절차 포함 | 사용자 책임 |
| 진단 | `/harness:harness-mcp-status`로 read-only 점검 | 동일 |

권장 경로는 [§10 Dynamic MCP Adoption](./plugins/harness/skills/harness/references/permission-profiles.md#10-dynamic-mcp-adoption--프로젝트-진행에-따른-mcp-신규-채택) 워크플로우를 그대로 따른다.

### 수동 설치 — `claude mcp add` 명령

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

### 스코프 선택

| 스코프 | 위치 | 용도 |
|--------|------|------|
| `local` (default) | `~/.claude.json` `projects.{cwd}.mcpServers` | 이 프로젝트, 본인 머신만 |
| `project` | `./.mcp.json` (commit 대상) | 팀 공유 필요 시 |
| `user` | `~/.claude.json` 전역 | 본인 모든 프로젝트 공유 |

### 권장 패턴 — inline `mcpServers:` (서브에이전트 격리)

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

> **schema 필수:** **list-of-dicts + `type: stdio`** 형태. 누락 시 silent skip 되어 도구 미노출. 합성 템플릿은 [§5-1](./plugins/harness/skills/harness/references/permission-profiles.md#5-1-에이전트-frontmatter-layer-b-격리--권장-inline-mcpservers).

### Pre-install probe (install 없이 도구 enumeration)

trusted source 확인 후, install 영구화 전 stdio JSON-RPC `tools/list`로 도구 카탈로그를 미리 확인:

```powershell
# fixture 복사 → target에 맞게 UVX_PATH·인자 수정 → 실행
node plugins\harness\skills\harness\references\fixtures\probe_sqlite.js
```

→ `COUNT=N` + per-tool `name·required·all-params` 출력. install 부작용 0 (단 패키지 코드는 1회 spawn). [§8-3 참조](./plugins/harness/skills/harness/references/permission-profiles.md#8-3-재사용-가능한-검증-기법).

### 권한 Tier 정책 (요약)

| Tier | 정의 | 자동 적용 |
|------|------|----------|
| **T0** | 무키·로컬 only (fetch/git/sqlite/filesystem/memory/time/sequential-thinking) | 사용자 1회 동의 후 `allow` 가능 |
| **T1** | 무료 API 키 또는 PAT (github/playwright/chrome-devtools/brave-search/tavily/exa) | 키 등록 + 명시 동의 → `allow` |
| **T2** | 유료 또는 민감 외부 (firecrawl/slack/postgres) | 항상 `ask`, 자동 `allow` **금지** |

**자동 install·자동 `allow` 승급 금지** ([§6 안전 정책](./plugins/harness/skills/harness/references/permission-profiles.md#6-안전-정책)). T0이라도 user confirm 게이트 필수.

### 채택 후 mid-session 미전파

`claude mcp add` 또는 inline `mcpServers:` 갱신은 **본 세션에 미적재** — 새 도구가 LLM에 노출되려면 **세션 재시작** 필수. 합성 시점 install된 신규 MCP도 동일.

### 자세한 참조

| 주제 | 위치 |
|------|------|
| Tier별 MCP 인벤토리 (도구 enumeration·install 명령) | [`permission-profiles.md` §3](./plugins/harness/skills/harness/references/permission-profiles.md#3-mcp-후보-인벤토리-tier-분류) |
| 검증 완료 T0 MCP × capability profile 매트릭스 | [`permission-profiles.md` §3-1](./plugins/harness/skills/harness/references/permission-profiles.md#3-1-검증-완료-t0-mcp--capability-profile-매트릭스) |
| 5-step 채택 절차 (Discover→Probe→Confirm→Install→Reflect) | [`permission-profiles.md` §10-2](./plugins/harness/skills/harness/references/permission-profiles.md#10-2-5-step-채택-절차-모든-트리거-공통) |
| Rollback / inline 정의 갱신 | [`permission-profiles.md` §10-4·§10-5](./plugins/harness/skills/harness/references/permission-profiles.md#10-4-rollback-절차) |
| Pre-install probe fixture | [`fixtures/probe_*.js`](./plugins/harness/skills/harness/references/fixtures/) |
| 합성 결과 예시 (4 산출물 1세트) | [`fixtures/synthesis_example/`](./plugins/harness/skills/harness/references/fixtures/synthesis_example/) |

---

## 도입 후 권한 경계

`harness` plugin은 사용자 프로젝트의 `.claude/commands/`에 **아무것도 생성하지 않습니다** (read-only invariant). harness 메타 스킬이 만드는 산출물은 사용자 프로젝트의 `.claude/agents/`·`.claude/skills/`·`CLAUDE.md`에만 떨어집니다.

---

## 문서 인덱스

| 문서 | 용도 |
|------|------|
| [`plugins/harness/skills/harness/SKILL.md`](./plugins/harness/skills/harness/SKILL.md) | 메타 스킬 정의 (11 Phase 워크플로우) |
| [`plugins/harness/skills/harness/references/permission-profiles.md`](./plugins/harness/skills/harness/references/permission-profiles.md) | MCP·도구 권한 카탈로그 (Tier 분류 / §3 인벤토리 / §10 dynamic adoption) |
| [`CLAUDE.md`](./CLAUDE.md) | 저장소 구성 + In-session 가드라인 |
