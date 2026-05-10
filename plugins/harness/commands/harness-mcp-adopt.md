---
description: 프로젝트 진행 중 신규 MCP 채택 (런타임 시점). §10 dynamic adoption 전용 진입점 — discover → probe → confirm → install → reflect 5-step.
argument-hint: <채택 사유 한 문장 또는 검토 대상 MCP명>
---

# Harness — MCP Adopt

기존 derived 프로젝트가 *진행 중* 신규 MCP가 필요해질 때 호출하는 명령. Phase 5-2 합성 *시점*과 분리된 **런타임 시점**의 채택 채널이다. description 매칭이 아닌 명시적 호출.

## 컨텍스트
- **인자**: `$ARGUMENTS` (예: "playwright로 e2e 테스트 자동화 필요", "github MCP로 PR 메타데이터 조회", "tavily로 외부 리서치")
- **입력**: 기존 derived 프로젝트 (`.claude/agents/`, `CLAUDE.md`, 선택적 `.claude/settings.json`·`.mcp.json` 또는 `~/.claude.json`)
- **출력**: §10 Step 5 4 산출물 — `permission-profiles.md` §3 footnote / `.claude/agents/<name>.md` frontmatter 갱신 / `.claude/settings.json` permissions / `CLAUDE.md` 변경 이력 1행

## 선조건 검증 (먼저 실행)

1. derived 프로젝트의 `.claude/agents/`에 기존 에이전트 1명 이상 (= 하네스가 이미 합성됨) — `/harness:harness-new`가 미실행이면 합성 *시점*으로 돌아가서 처음부터 Phase 5-2를 따르라고 안내 후 중단.
2. `claude mcp list` 실행으로 현재 등록 MCP 카운트 확인 — 사용자에게 보고 (이미 등록된 것 중복 install 방지).
3. **dharness root 자체에서 호출하지 않음** — `pwd`가 dharness 본 저장소라면 사용자에게 "dharness root는 self-host CM 격리 영역, derived 프로젝트로 이동 후 재호출" 안내 후 중단. 단, 사용자가 *예외적 검증 환경*임을 명시하면 진행 (사유를 §3 footnote에 기록).

## 실행 절차

`plugins/harness/skills/harness/references/permission-profiles.md` §10의 5-step을 그대로 따른다 — 본 명령은 §10 워크플로우의 *진입점*이지 별도 워크플로우가 아니다.

### Step 1 — Discover

- `references/permission-profiles.md` §3 인벤토리에서 `$ARGUMENTS` 매칭 후보 검색.
  - 매칭이면: Tier·capability profile·install 명령·도구 enumeration 즉시 사용.
  - 미매칭이면: github.com/modelcontextprotocol/servers 또는 외부 카탈로그 검색 후 후보 1~3개 사용자에게 제시.
- **§10-1 트리거 신호 분류:** `$ARGUMENTS`가 (a) baseline-diff (b) profile-mismatch (c) 사용자-요청 중 어느 것인지 판정 → §10 Step 5 사유 컬럼 input.

### Step 2 — Pre-install probe

- `references/fixtures/probe_sqlite.js`를 템플릿으로 복사 → target MCP에 맞게 UVX_PATH/명령·인자 수정 → `node probe_<server>.js` 실행.
- 출력: `COUNT=N` + per-tool name·required·all-params.
- **install 없이** 도구 카탈로그 확정 — Step 3 user confirm 입력의 1차 자료.
- `uvx` 기반 MCP는 `command:` 필드에 *uvx의 절대경로* 필수 (PATH 미통과 시 spawn 실패 — empirical 3차 사이클).

### Step 3 — User confirm gate

`AskUserQuestion`으로 다음 4가지를 사용자에게 명시 표기 후 동의 받음:

1. **MCP 후보 + Tier**: 예 "playwright (T1, web-research/external-integration hybrid)"
2. **install 명령**: 예 `claude mcp add playwright npx -- @playwright/mcp@latest --browser chromium --isolated`
3. **도구 enumeration 카운트 + sample 2~3개**: probe 결과
4. **권한 정책 제안**: read 계열 `allow` / 부수 효과 있는 도구 `ask` / 절대 금지면 명시 거부

**자동 install·자동 `allow` 승급 금지** (§6). T0(무키·로컬)이라도 Step 3 통과 필수.

### Step 4 — Install

- 사용자 동의 후 Step 3 명령 그대로 `Bash`로 실행.
- `claude mcp list` 재실행 → 새 서버가 `✓ Connected`인지 확인.
- 실패 시 stderr 첨부 후 사용자에게 보고 — install 실패는 silent fallback 금지.
- **경로 인자는 절대경로 필수** (8차 사이클 sqlite empirical) — `--db-path`, `--repository` 등 디렉토리/파일을 가리키는 인자에 상대경로(`./...`)를 사용하면 health check 실행 시 cwd 차이로 `✗ Failed to connect` 발생. uvx 실행자(`%APPDATA%\Python\Python312\Scripts\uvx.exe`) 자체도 PATH 미통과 시 spawn 실패하므로 절대경로 사용.
- **첫 install이 ✗ Failed로 떴다면 잘못된 등록이 `~/.claude.json` 또는 `.mcp.json`에 남으므로 `claude mcp remove <name>` 후 절대경로로 재install** — silent fix 금지, 사용자에게 1차 실패 사실과 정정 명령을 보고.

### Step 5 — Reflect (4 산출물)

| | 대상 | 내용 |
|---|------|------|
| (a) | `permission-profiles.md` §3 sqlite/playwright/... 행 | 도구 enumeration 채움 + install 명령 footnote (Step 2 결과 그대로) |
| (b) | `<derived>/.claude/agents/<agent-name>.md` frontmatter | `tools:` allowlist에 신규 `mcp__<server>__*` 추가 — Step 3 user confirm 결과만 |
| (c) | `<derived>/.claude/settings.json` | `permissions.allow` / `permissions.ask` 갱신 (deep merge — 기존 키 보존) |
| (d) | `<derived>/CLAUDE.md` 변경 이력 표 | 1행 추가. 형식은 `references/fixtures/synthesis_example/CLAUDE_md_row.md` 참조 |

`references/fixtures/synthesis_example/`이 sqlite 시나리오의 (b)·(c)·(d) 박제 예시.

## 검증 게이트

Step 4 완료 직후 다음 사실을 사용자에게 명시:

> **다음 세션부터 사용 가능** — mid-session `claude mcp add`는 본 세션 도구 풀에 미적재 (empirical 4차 사이클 — 양면 검증). 새 도구가 LLM에 노출되려면 세션 재시작 필수. 합성 시점에 install된 신규 MCP도 동일.

다음 세션 시작 후 `references/fixtures/verify_11_1.md` fixture로 노출 패턴 검증 권장 (도구명에 하이픈 보존 vs 변환 등).

## Rollback

채택 후 부적합 판정 시 §10-4 절차:

1. `claude mcp remove <server>` — 등록 해제
2. (b) frontmatter `tools:`에서 해당 `mcp__<server>__*` 제거
3. (c) `settings.json` `permissions`에서 해당 패턴 제거
4. (d) `CLAUDE.md` 변경 이력 1행은 *삭제 대신* "rollback {date}" 라벨 추가 (append-only)

## 범위 외

- **합성 시점** (= Phase 5-2 1회 합성): `/harness:harness-new` 또는 `/harness:harness-add-agent` — 본 명령 아님.
- **MCP 서버 자체 디버깅** (connection 실패·도구 에러): MCP 서버 issue tracker 또는 사용자 측 점검.
- **API 키 발급** (T1+): 사용자 측 절차. 본 명령은 *키가 이미 있다는 전제* — `${API_KEY}` placeholder를 settings.json·shell env에 두고 사용자가 채움.
- **dharness 본 저장소의 `.claude/`**: 선조건 (3)으로 차단. self-host CM 격리.

## 후속 명령어

- 합성 시점 신규 에이전트 추가: `/harness:harness-add-agent <역할>`
- 채택 전후 상태 진단(read-only): `/harness:harness-mcp-status`
- drift 점검: `/harness:harness-adapt`
- baseline 갱신: `/harness:harness-baseline`
