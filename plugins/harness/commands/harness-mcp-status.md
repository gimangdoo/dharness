---
description: 현재 derived 프로젝트의 MCP 상태 진단 — 등록 MCP·에이전트 도구 매트릭스·토큰 비용 추정·§3 인벤토리 정합·§10 trigger 신호 자동 감지. 읽기 전용.
argument-hint: (없음 또는 --verbose)
---

# Harness — MCP Status

기존 derived 프로젝트의 MCP·도구·권한 상태를 *읽기 전용*으로 진단한다. `/harness:harness-mcp-adopt`(쓰기)와 한 쌍을 이루는 진입점이며, §10 trigger 신호 자동 감지 + parent vs subagent 적재 토큰 비용 추정으로 채택 시점·격리 정합 판정을 보조한다. description 매칭이 아닌 명시적 호출.

## 컨텍스트
- **인자**: `$ARGUMENTS` (없거나 `--verbose` — verbose면 §3 인벤토리 전체와 도구 enumeration까지 출력)
- **입력**: derived 프로젝트의 `.claude/agents/`, `.claude/settings.json` (있으면), `claude mcp list` 출력, `plugins/harness/skills/harness/references/permission-profiles.md` §3 (있으면 dharness root 또는 install된 plugin 경로)
- **출력**: 텍스트 보고서 5섹션 (변경 0). 모든 발견은 *권고 수준* — 자동 수정 없음.

## 선조건 검증 (먼저 실행)

1. derived 프로젝트의 `.claude/agents/`에 기존 에이전트 1명 이상 — 미충족 시 "하네스 미합성" 안내 후 중단 (§5 합성 산출물이 없으면 진단 대상 자체가 없음).
2. **dharness root 자체에서 호출하지 않음** — `pwd`가 dharness 본 저장소면 사용자에게 "dharness root는 self-host CM 격리 영역" 안내 후 중단 (단, 사용자가 *예외적 검증 환경*임을 명시하면 진행).

## 진단 절차

### 섹션 1 — 등록 MCP 인벤토리

```bash
claude mcp list
```

각 서버를 표로 보고:

| 서버명 | 상태 | scope | 출처(추정) |
|--------|-----|-------|----------|
| (예) git | ✓ Connected | local | `~/.claude.json` projects.{cwd}.mcpServers |

- 미연결(`✗`) 서버는 별도 강조 — install 실패 또는 stale 등록 가능성.
- scope가 `user`인 경우 cross-project 영향 명시.
- **경로 인자 검증 (8차 사이클 abs-path 사실):** `~/.claude.json` 또는 `.mcp.json`의 등록 명령에서 `--db-path`/`--repository`/`--root` 등 path 인자가 *상대경로*(`./...`, `../...`, `~/...`)면 ⚠️ 경고 — health check 실행 시 cwd 차이로 `✗ Failed to connect` 가능. uvx 실행자(`command:`) 자체도 PATH 미통과면 ⚠️. 권고: `claude mcp remove <name>` 후 절대경로로 재install.

### 섹션 2 — 에이전트별 도구 매트릭스

`.claude/agents/*.md` frontmatter `tools:` 필드 파싱 → 각 에이전트가 사용 권한을 가진 `mcp__<server>__<tool>` 추출 → 표:

| 에이전트 | 빌트인 도구 수 | MCP 도구 (mcp__server__tool) | capability profile (추정) |
|---------|--------------|----------------------------|---------------------------|

- 빌트인 도구는 카운트만 (Read/Write/Edit/Bash/Grep 등).
- MCP 도구는 정확한 이름 나열 — Layer C(`permissions.allow/ask`)와의 정합 비교 입력.
- capability profile은 §4 4종 중 매칭 — 도구 mix 기반 추론 (web-research / code-test / external-integration / reasoning-aux).

### 섹션 3 — §3 인벤토리 vs 실제 비교

`permission-profiles.md` §3에 박제된 후보 MCP vs `claude mcp list` 결과 diff:

- **§3 박제 + 미설치**: 의도적일 수 있음 (보고만, 권고 없음).
- **설치 + §3 미박제**: §3 추가 권고 (dharness root 도입자가 추후 채택 시 참조 자료로). dharness root 측 편집 권한이 있으면 사용자에게 1행 추가 제안.
- **§3 정의된 도구 enumeration vs 실제 노출 도구**: mismatch면 §11-1 fixture로 검증 권고 (도구명 변환 패턴 등).

### 섹션 4 — settings.json permissions 정합

`.claude/settings.json`이 있으면 `permissions.allow` / `permissions.ask` vs 섹션 2 매트릭스 비교:

- **allow에 있지만 어떤 agent도 frontmatter `tools:`에 없음**: 잉여 권한 (Layer B 격리 우회 가능 — 권고: 제거).
- **agent `tools:`에 있는데 allow/ask 어디에도 없음**: 정합 결손 (Layer C 게이트 누락 — 권고: 적절한 buckets에 추가).
- **부수 효과 도구가 allow로 승급됨** (예: `mcp__sqlite__write_query`): 정책 위반 가능 — `ask`로 강등 권고.

`settings.json` 부재면 "기본 정책 (모두 ask) — Layer C 게이트 미구성" 표기 후 통과.

### 섹션 5 — §10 Trigger 신호 자동 감지

§10-1 트리거 3종 중 (a)·(b)는 자동 감지 가능:

- **(a) baseline-diff**: `_workspace/_baseline/project_profile.md` (있으면) detection_signals 리스트 vs 현재 코드 grep — 새 키워드(예: `package.json`에 `playwright` 추가, `requirements.txt`에 `sqlalchemy` 등장) 검출 시 후보 MCP 제안.
- **(b) profile-mismatch**: 섹션 2의 capability profile 추정 vs 에이전트 description의 명시 capability — 어긋나면 reflect 또는 도구 보강 권고.
- **(c) 사용자-요청**: 본 명령은 자동 감지 X — 사용자가 명시 호출 시 `/harness:harness-mcp-adopt <사유>`로 입력.

각 신호별로 *권고 수준*만 출력 — 자동 채택 금지 (§6).

### 섹션 6 — 토큰 비용 추정 (parent vs subagent 적재)

의도 ②(세션 적재 최소화) + ③(agent-only 접근)의 *측정 채널*. 각 MCP 도구 정의가 어느 컨텍스트에 적재되는지 분류 후 추정 토큰을 표로 출력.

**적재 위치 판정 룰:**

| 위치 | 출처 | parent 적재 | subagent 적재 |
|------|------|------------|---------------|
| `~/.claude.json` projects.{cwd}.mcpServers (= `claude mcp add -s local`) | parent + spawn된 모든 subagent (inherit) | ✓ | ✓ (inherit) |
| `.mcp.json` (= `claude mcp add -s project`) + `enabledMcpjsonServers` allow | parent + 모든 subagent | ✓ | ✓ |
| `.claude/agents/<name>.md` frontmatter `mcpServers:` (inline) | 해당 subagent만, 시작 시 connect / 종료 시 disconnect | ✗ | ✓ (해당 agent만) |

**추정 토큰 룰:** 도구 1종당 200~500 tokens (name + description + JSON schema의 평균 길이). 표에는 저(200) / 고(500) 양 끝을 같이 출력.

**출력 형식:**

```
| 위치               | MCP    | 도구 수 | 추정 tokens (저/고) | 정합 평가                          |
|--------------------|--------|--------|---------------------|----------------------------------|
| parent (적재됨)    | git    |     12 |    2,400 / 6,000    | ⚠️ 슬래시 커맨드 직접 호출 없으면 inline 이전 권고 |
| parent (적재됨)    | fetch  |      4 |      800 / 2,000    | ⚠️ §5-2 예외 조건 미충족 → §5-1로 |
| subagent only      | sqlite |      3 |      600 / 1,500    | ✓ data-analyst inline (§5-1-a)   |
|--------------------|--------|--------|---------------------|----------------------------------|
| 합계 parent        |        |     16 |  **3,200 / 8,000**  | (매 user turn마다 적재)           |
| 합계 subagent only |        |      3 |      600 / 1,500    | (해당 subagent spawn 시에만)      |
```

**권고 트리거:**

- **parent 적재 합계 > 5,000 tokens (고 추정)**: §5-1 inline로 이전 권고 — 적재 대상별로 §5-2의 3 예외 조건(parent 직접 호출 필연성 / 다중 subagent 공유 / 팀 commit) 충족 여부 사용자에게 질의.
- **inline `mcpServers:` 가진 agent가 0개**인데 parent 적재가 있음: **격리 무결성 미구성** (의도 ③ 위반) — 합성 가이드 §5-1로 재구성 권고.
- **§3 인벤토리 토글 지원 MCP가 toolset 필터 없이 적재됨** (예: github가 `GITHUB_TOOLSETS` 미설정으로 19종 toolset × 평균 5도구 ≈ 90+ 도구 전체 적재): §5-1-b Layer A+B 결합형으로 갱신 권고.

**한계:**

- 추정 tokens은 ±2.5x 변동 (실측은 Claude Code 빌드별로 다름). §11-3 fixture 결과 누적 후 보정 권고.
- inline `mcpServers:`는 spawn 시에만 토큰 소비 → user turn당 누적 비용은 *agent 호출 빈도*에 비례. parent 적재는 매 turn 고정 비용 → 누적 격차가 큼.

## 출력 형식

6섹션 보고서를 단일 메시지로 출력. `--verbose` 인자가 있으면 §3 인벤토리 전체 dump와 각 MCP의 도구 enumeration, 섹션 6의 도구별 추정 토큰 분포까지 포함 (없으면 카운트와 sample 2~3개만).

## 후속 명령어

- 신규 MCP 채택 권고가 있으면: `/harness:harness-mcp-adopt <사유>`
- 정합 결손(섹션 4) 정정: 사용자가 `.claude/settings.json` / agent frontmatter 직접 수정 (자동 수정 금지)
- §3 미박제 보고가 있고 dharness root 접근 가능하면: 사용자에게 footnote 추가 안내
- 섹션 6의 parent 적재 ⚠️ 항목 정정: §5-2 예외 조건 미충족이면 해당 MCP를 §5-1 inline 패턴으로 이전 (사용자 수동 — 자동 수정 금지)

## 범위 외

- **자동 수정 0** — 모든 발견은 권고. `harness-mcp-adopt` 또는 사용자 수동 편집 필요.
- **MCP 서버 자체 디버깅** (connection 실패): MCP 서버 issue tracker.
- **dharness 본 저장소의 `.claude/`**: 선조건 (2)로 차단.
