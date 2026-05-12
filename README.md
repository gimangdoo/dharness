# Harness — Team-Architecture Factory for Claude Code

> 도메인 한 문장을 **에이전트 팀 + 스킬 세트**로 변환하는 메타 스킬.
> A meta-skill that turns a domain description into an agent team and the skills they use.

---

## 무엇인가

`dharness`는 다음 두 부분으로 구성된 단일 저장소입니다:

1. **`harness` plugin** (`plugins/harness/`) — 도메인을 입력 받아 에이전트 3~5명 + 스킬 세트를 자동 생성하는 메타 스킬 팩토리. **외부 프로젝트에 install 가능.**
2. **Context Manager** (root `.claude/` + `_workspace/`) — dharness *자체*의 진화를 기록·영속화하는 self-host 런타임. 결정적 hooks 3종 + `/cm-*` 5 슬래시 커맨드 + `memory-search` 1 스킬. PostToolUse가 dharness 작업 단위(skill/agent/hook/command/manifest 변경)를 자동 분류해 누적하고, SessionEnd가 CLAUDE.md "변경 이력" 표 행 draft를 자동 적재. **dharness 본 폴더에서만 동작** (외부 install 미지원).

다른 단일 에이전트/프롬프트 프레임워크와 달리, harness는 **팀 아키텍처 팩토리** — 6가지 사전 정의된 팀 패턴 중 도메인에 맞는 것을 선택하고 에이전트 협업 프로토콜을 함께 설계합니다.

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

### 1. 저장소 가져오기 (CM도 함께 사용하려면)

```powershell
git clone https://github.com/gimangdoo/dharness.git C:\path\to\dharness
```

CM은 dharness 본 폴더에서 자동 동작 — `.claude/settings.local.json`이 hooks 3종을 직접 등록하고 있어 별도 install 없이 다음 Claude Code 세션부터 발화합니다.

### 2. harness plugin 설치 (외부 프로젝트용)

```powershell
claude plugin marketplace add gimangdoo/dharness
claude plugin install harness@dharness
```

로컬 개발용 (marketplace 거치지 않음):

```powershell
claude --plugin-dir C:\path\to\dharness\plugins\harness
```

### 3. 새 도메인에 적용

```text
/harness:harness-new 코드 리뷰를 자동화하는 도메인
```

→ 사용자 프로젝트의 `.claude/agents/{name}.md`·`.claude/skills/{name}/SKILL.md`·`CLAUDE.md`에 산출물 생성.

---

## 호출 방식

| 방식 | 발동 | 비용 통제 | 용도 |
|---|---|---|---|
| **자연어 트리거** | "하네스 구성해줘" 등 자연 발화 ↔ skill description 매칭 | LLM이 자동 분기 | 자연스러운 발화, 일반 사용 |
| **Slash command** | `/harness:harness-new`, `/cm-status` 등 결정적 호출 | 사용자가 Phase 범위 직접 지정 | 비용 회피, 트리거 확률 의존 제거 |

### Slash command 카탈로그 (`harness` 9개 + CM 5개 = 14개)

```
# harness plugin (메타 스킬 팩토리, 외부 install 가능)
/harness:harness-new <도메인>          # Phase 0~8 전체 (신규 구축)
/harness:harness-add-agent <역할>      # Phase 4·5·7·8 (1·2·3 skip)
/harness:harness-add-skill <스킬>      # Phase 6·7·8 (1~5 skip)
/harness:harness-baseline              # Phase 1·2 재실행 + drift 분석
/harness:harness-audit                 # 정합성 감사 (read-only)
/harness:harness-evolve <피드백>       # Phase 9 수동 진화
/harness:harness-adapt                 # Phase 10 telemetry drift 점검
/harness:harness-mcp-adopt <사유>      # 런타임 시점 신규 MCP 채택 (§10 dynamic adoption)
/harness:harness-mcp-status            # MCP 상태 진단 — 인벤토리·매트릭스·정합·trigger 자동 감지 (read-only)

# CM (dharness self-host, root .claude/commands/)
/cm-status                              # 메모리 통계 + DB 행 수 (dharness_event/pending draft 포함)
/cm-sessions [--limit N]                # 최근 세션 목록
/cm-reset                               # 메모리 전체 삭제 (확인 필수)
/cm-claudemd-apply <sid> [사유...]      # SessionEnd가 만든 draft를 CLAUDE.md "변경 이력" 표에 삽입
/cm-claudemd-discard [sid]              # draft 폐기 (인자 없으면 모두)
```

명령어 본문(`.md`)은 harness는 `plugins/harness/commands/`, CM은 `.claude/commands/`에 보관.

---

## 프로젝트 구조

```
.
├── .claude-plugin/
│   └── marketplace.json       # harness plugin 단일 카탈로그
├── .claude/                   # CM (dharness self-host)
│   ├── hooks/                 # SessionStart/PostToolUse/SessionEnd + _schema.py + cm_commands.py
│   ├── skills/memory-search/  # on-demand 메모리 검색 (LLM-time)
│   ├── commands/              # cm-* 5개
│   └── settings.local.json    # hooks 등록 (gitignore — 사용자 로컬)
├── plugins/
│   └── harness/               # PLUGIN — 메타 스킬 팩토리
│       ├── .claude-plugin/plugin.json
│       ├── skills/harness/    # SKILL.md + references/
│       └── commands/          # harness-* 9개
├── _workspace/                # DATA — CM 런타임 산출물 (gitignore)
│   ├── _telemetry/            # 라이프사이클 이벤트 append-only JSONL
│   ├── _memory/               # 세션·클러스터·observations.db (dharness_event 포함)
│   ├── _tool_outputs/         # PostToolUse 10KB 초과 원본 보존
│   └── _drafts/               # SessionEnd가 적재한 CLAUDE.md 표 행 draft (apply/discard 게이트)
├── CLAUDE.md
└── README.md
```

**핵심 원칙:** `plugins/harness/` = 외부 install 대상 (read-only when installed). `.claude/` = dharness self-host CM (외부 install 미지원). `_workspace/` = dharness 데이터.

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

derived 프로젝트 진행 중 신규 MCP가 필요해질 때(예: "playwright로 e2e 테스트", "github MCP로 PR 메타 조회") 사용하는 절차. **dharness root 자체는 self-host CM 격리 영역이라 적용 대상 아님** — 본 절차는 `/harness:harness-new`로 합성된 *derived 프로젝트의 `.claude/`*만 다룬다.

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
| 합성 결과 예시 (4 산출물 1세트) | [`fixtures/synthesis_example/`](./plugins/harness/skills/harness/references/fixtures/synthesis_example/) |

---

## 도입 후 권한 경계

`harness` plugin은 사용자 프로젝트의 `.claude/commands/`에 **아무것도 생성하지 않습니다** (read-only invariant). harness 메타 스킬이 만드는 산출물은 사용자 프로젝트의 `.claude/agents/`·`.claude/skills/`·`CLAUDE.md`에만 떨어집니다.

---

## Context Manager (dharness self-host)

CM은 **LLM 호출 없는 결정적 데이터 파이프라인**으로 동작합니다. 캡처·집계 모두 hooks가 담당하며, 사용자 측 조회는 `/cm-status`·`/cm-sessions` 또는 SQLite 직접 열람으로 한다. 메모리 검색만 LLM이 on-demand로 호출 가능 (`memory-search` 스킬).

### 결정적 산출물

| 위치 | 역할 |
|------|------|
| `.claude/hooks/_schema.py` | DDL 단일 진실 원천 (4 테이블 + FTS5 + observations에 category/artifact_kind/phase 컬럼) + REPO_ROOT 결정적 계산 + `classify_dharness_event()` 도메인 분류기 + `ensure_migrations()` ALTER 마이그레이션 |
| `.claude/hooks/session_start.py` | SessionStart: ID 발급, dangling 세션 finalize, **4 블록 의미적 inject (session_id + 직전 N=3 세션 dharness_event + 미적용 draft + git status --short, 토큰 budget 2000자)** |
| `.claude/hooks/post_tool_use.py` | PostToolUse: raw.jsonl append + 10KB 초과 시 `_tool_outputs/`에 원본 보존 + **dharness 도메인 분류기 호출 후 매칭 시 `observations.dharness_event`로 자동 INSERT** |
| `.claude/hooks/session_end.py` | SessionEnd: transcript 평탄화, sessions UPDATE + **이번 세션 dharness_event를 모아 CLAUDE.md "변경 이력" 표 행 draft를 `_workspace/_drafts/{date}_{sid}.md`에 자동 적재** |
| `.claude/hooks/cm_commands.py` | `/cm-*` 결정적 커맨드 핸들러 (status/sessions/reset/claudemd-list/claudemd-apply/claudemd-discard) |
| `.claude/skills/memory-search/SKILL.md` | dharness 진화 이력 자연어 검색 — **5 source(observations_fts + dharness_event 필터 + CLAUDE.md "변경 이력" 표 + git log + clusters/skill 본문) 3-tool progressive disclosure** |

### 동작 흐름

```
SessionStart hook
  → session_id 발급 + DB 부트스트랩 + ensure_migrations (ALTER 안전망)
  → 직전 dangling 세션 finalize
  → 4 블록 deterministic carry-over를 additionalContext로 inject (≤ 2000자)
      ① session_id
      ② 직전 N=3 세션의 dharness_event category 카운트
      ③ 미적용 CLAUDE.md draft 목록 (있으면)
      ④ git status --short (uncommitted/unstaged)

PostToolUse hook
  → raw.jsonl에 메타 append
  → output > 10KB이면 _tool_outputs/{sid}/에 원본 보존
  → tool_input 분류 (Edit/Write/MultiEdit/Bash git) → 매칭 시
      observations 테이블에 section='dharness_event' INSERT
      (category/artifact_kind/content/tags) — LLM 호출 없음

SessionEnd hook
  → transcript.md 평탄화
  → sessions.ended_at / duration_min / tools_used UPDATE
  → 이번 세션 dharness_event 집계 → CLAUDE.md "변경 이력" 표 행 draft를
      _workspace/_drafts/{date}_{sid}.md에 markdown row + 본문으로 자동 적재
      (이벤트 0건이면 skip)

다음 세션에서 사용자 명시 게이트:
  → /cm-claudemd-apply <sid> [사유...]   CLAUDE.md 표에 draft row 삽입 + applied/로 이동
  → /cm-claudemd-discard [sid]           draft 폐기 → discarded/로 이동
```

---

## CLAUDE.md 변경 이력 자동 회로

dharness의 진화는 [`CLAUDE.md`](./CLAUDE.md) "변경 이력" 표에 사람이 읽는 행으로 기록됩니다. CM이 이 표 행을 **자동으로 draft 적재하고, 사용자가 명시 게이트로 적용**합니다.

### 회로 4 단계

1. **PostToolUse** — Edit/Write/MultiEdit/Bash(git*) 호출마다 file path 또는 git subcommand를 분류해 `observations.dharness_event`에 INSERT
2. **SessionEnd** — 이번 세션의 dharness_event를 집계해 markdown 표 행 draft + 본문(카테고리 카운트 / 변경 대상 / 메타)을 `_workspace/_drafts/{date}_{sid}.md`에 작성 (이벤트 0건이면 skip)
3. **다음 SessionStart** — 미적용 draft가 있으면 `additionalContext`에 한 블록으로 inject:
   ```
   [CM] 미적용 CLAUDE.md draft 1건 — apply: /cm-claudemd-apply <sid>, discard: /cm-claudemd-discard
     · 2026-05-10 abc123
   ```
4. **사용자 명시 게이트** — `/cm-claudemd-apply <sid> [사유...]` 또는 `/cm-claudemd-discard [sid]`

### 사용 예시

```text
# pending 목록 보기
/cm-status                              # "CLAUDE.md draft: 1 pending" 표시
py .claude/hooks/cm_commands.py claudemd-list

# draft 본문 미리 보기 (apply 전 권장)
cat _workspace/_drafts/2026-05-10_abc123.md

# CLAUDE.md "변경 이력" 표 마지막 row 다음에 삽입 (사유 즉시 치환)
/cm-claudemd-apply abc123 Phase 9 e2e 검증 후 적용

# 또는 placeholder 그대로 두고 나중 수동 편집
/cm-claudemd-apply abc123

# 폐기 (discarded/ 보관)
/cm-claudemd-discard abc123             # 단일 sid
/cm-claudemd-discard                    # 모든 pending
```

### 사유 컬럼

draft가 자동 생성하는 행의 "사유" 컬럼은 인자 미제공 시 `(apply 전 작성 — 사유/맥락)` placeholder. apply 시 `<사유...>` 인자로 즉시 치환 가능 (공백 join, `|` escape 자동). *왜 변경했는가*는 deterministic으로 추출 불가능하므로 사람이 보강.

### 적재 디렉토리

| 위치 | 용도 |
|------|------|
| `_workspace/_drafts/{date}_{sid}.md` | pending — 다음 SessionStart가 inject |
| `_workspace/_drafts/applied/` | apply 후 보관 (CLAUDE.md에 행 추가됨) |
| `_workspace/_drafts/discarded/` | discard 후 보관 (영구 삭제는 수동 또는 `/cm-reset`) |

`.gitignore`에 등록되어 commit에 포함되지 않습니다 (사용자 로컬 데이터).

---

## CM 데이터 직접 조회

sqlite 클라이언트로 직접 열거나 `/cm-*` 커맨드로 조회.

```powershell
# 통계 한 줄 — pending draft / dharness_event 카운트 포함
py .claude/hooks/cm_commands.py status

# 최근 세션 30개
py .claude/hooks/cm_commands.py sessions --limit 30

# DB 직접 열기 (예: sqlite3 CLI)
sqlite3 _workspace/_memory/observations/observations.db
sqlite> SELECT category, COUNT(*) FROM observations
        WHERE section='dharness_event' GROUP BY category ORDER BY 2 DESC;

# 자연어 회고 — Claude Code 안에서
"이전에 단계 D에서 뭐 했어?"   # → memory-search 스킬이 5 source 조회
```

라이프사이클 telemetry (`tool_output_captured` 등)는 `_workspace/_telemetry/*.jsonl`을 직접 grep:

```powershell
findstr /C:"tool_output_captured" _workspace\_telemetry\*.jsonl
```

---

## 트러블슈팅 (CM 시스템)

| 증상 | 해결 |
|------|------|
| 훅이 동작하지 않음 | `py --version` 확인 → `.claude/settings.local.json`의 `command`를 `py ...`로 변경 (Microsoft Store 스텁 회피) |
| `/cm-status`가 빈 결과 | 새 Claude Code 세션을 한 번 열어 SessionStart 훅 발동 확인 |
| transcript는 있는데 digest가 없음 | digest 자동 생성은 도입되지 않음 — `memory-search` 스킬이 transcript.md / git log / observations FTS를 직접 fallback 조회 |
| `/cm-claudemd-apply`가 "변경 이력 표를 찾지 못함" | CLAUDE.md의 "변경 이력" heading 또는 strong 직후에 markdown 표가 있어야 — 헤더-구분선 깨졌는지 확인 |
| SessionStart inject가 잘림 | budget 2000자 — `.claude/hooks/session_start.py:INJECT_BUDGET` 기본값 |

---

## 문서 인덱스

| 문서 | 용도 |
|------|------|
| [`plugins/harness/skills/harness/SKILL.md`](./plugins/harness/skills/harness/SKILL.md) | 메타 스킬 정의 (11 Phase 워크플로우) |
| [`plugins/harness/skills/harness/references/permission-profiles.md`](./plugins/harness/skills/harness/references/permission-profiles.md) | MCP·도구 권한 카탈로그 (Tier 분류 / §3 인벤토리 / §10 dynamic adoption) |
| [`.claude/skills/memory-search/SKILL.md`](./.claude/skills/memory-search/SKILL.md) | 과거 메모리 LLM 검색 규칙 (3-tool progressive disclosure) |
| [`CLAUDE.md`](./CLAUDE.md) | 저장소 구성 + CM 포인터 + In-session 가드라인 |
