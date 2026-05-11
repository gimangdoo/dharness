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

`.claude/agents/*.md` frontmatter `tools:` 필드 + `mcpServers:` 필드 파싱 → 각 에이전트의 도구 허용/노출 매트릭스 추출 → 표:

| 에이전트 | 빌트인 도구 수 | `tools:` allowlist (mcp__) | inline `mcpServers:` advertise 도구 (실노출) | capability profile (추정) |
|---------|--------------|--------------------------|--------------------------------------------|---------------------------|

- 빌트인 도구는 카운트만 (Read/Write/Edit/Bash/Grep 등).
- **`tools:` allowlist**: frontmatter `tools:`에 명시된 `mcp__<server>__<tool>` 정확한 이름 나열 — Layer C(`permissions.allow/ask/deny`)와의 정합 비교 입력.
- **inline `mcpServers:` advertise 도구**: `mcpServers:`에 정의된 서버를 §8-3 JSON-RPC stdio probe(또는 §3 인벤토리 enumeration)로 enumerate한 *실노출* 도구 전체. **10차 P0 empirical 확정 — `tools:` allowlist에 1종만 명시해도 inline 서버의 advertise 도구 N종 *모두* subagent에 노출됨** (Layer B는 도구 카운트 통제에 무력 / parent isolation에만 작동). 따라서 §4 정합 점검은 `tools:` allowlist가 아닌 *advertise 도구 전체* vs `permissions.deny`로 비교해야 함.
- capability profile은 §4 4종 중 매칭 — 도구 mix 기반 추론 (web-research / code-test / external-integration / reasoning-aux).

### 섹션 3 — §3 인벤토리 vs 실제 비교

`permission-profiles.md` §3에 박제된 후보 MCP vs `claude mcp list` 결과 diff:

- **§3 박제 + 미설치**: 의도적일 수 있음 (보고만, 권고 없음).
- **설치 + §3 미박제**: §3 추가 권고 (dharness root 도입자가 추후 채택 시 참조 자료로). dharness root 측 편집 권한이 있으면 사용자에게 1행 추가 제안.
- **§3 정의된 도구 enumeration vs 실제 노출 도구**: mismatch면 §11-1 fixture로 검증 권고 (도구명 변환 패턴 등).

### 섹션 4 — settings.json permissions 정합

`.claude/settings.json`이 있으면 `permissions.allow` / `permissions.ask` / `permissions.deny` vs 섹션 2 매트릭스 비교:

- **allow에 있지만 어떤 agent도 frontmatter `tools:` 또는 `mcpServers:`에 없음**: 잉여 권한 (cross-project 노출 가능 — 권고: 제거).
- **agent `tools:`에 있는데 allow/ask 어디에도 없음**: 정합 결손 (Layer C 게이트 누락 — 권고: 적절한 buckets에 추가).
- **부수 효과 도구가 allow로 승급됨** (예: `mcp__sqlite__write_query`): 정책 위반 가능 — `ask` 또는 `deny`로 강등 권고 (strict read-only 패턴은 `deny` 권고).
- **🆕 10차 사이클 — inline advertise 도구 vs `deny` 정합 (strict read-only 의도일 때 default 점검)**:
  agent가 inline `mcpServers:`로 정의한 서버의 *실노출 도구 전체* 중, 부수 효과 도구(write/insert/update/delete/append/exec 등)가 `permissions.deny`에 박제되어 있는가? 누락 시 ⚠️.
  - **이유**: `tools:` allowlist는 inline 서버의 도구 카운트를 줄이지 못함 (10차 P0 empirical) — agent는 advertise된 모든 도구를 호출 가능. 따라서 *strict read-only* 의도라면 부수 효과 도구를 `deny`에 명시 박제하는 것이 default 패턴 (`ask`는 사용자 confirm으로 통과되므로 부족).
  - **검출 룰 (휴리스틱)**: advertise 도구 이름에 다음 prefix/keyword 포함 시 부수 효과 의심 — `write_`, `insert_`, `update_`, `delete_`, `remove_`, `append_`, `create_`, `set_`, `commit_`, `push_`, `exec*`, `run_`. 이름은 의심 신호일 뿐 — 최종 판정은 §3 인벤토리 또는 사용자 도메인 지식.
  - **권고 형식**: `agent X의 inline 서버 Y는 read-only 의도로 보이나 deny 누락 도구 발견: [list]. settings.json `permissions.deny`에 추가 권고.`

- **🆕 inline advertise 도구 수 vs `tools:` allowlist 수 mismatch (insight, 권고 아님)**:
  agent의 `tools:` allowlist에 명시된 inline MCP 도구가 *advertise 도구 일부*만 포함하면 (예: 4종 중 1종) 보고 — *Layer B 격리 가정이 무력*임을 사용자에게 가시화. 정정 권고는 위 deny 항목으로.

`settings.json` 부재면 "기본 정책 (모두 ask) — Layer C 게이트 미구성, inline 서버의 부수 효과 도구가 사용자 confirm 1회로 통과 가능 ⚠️" 표기 후 통과.

### 섹션 5 — §10 Trigger 신호 자동 감지

§10-1 트리거 3종 중 (a)·(b)는 자동 감지 가능:

- **(a) baseline-diff**: `_workspace/_baseline/project_profile.md` (있으면) detection_signals 리스트 vs 현재 코드 grep — 새 키워드(예: `package.json`에 `playwright` 추가, `requirements.txt`에 `sqlalchemy` 등장) 검출 시 후보 MCP 제안.
  - **baseline 부재 fallback**: `_workspace/_baseline/project_profile.md`이 없으면 (= 사용자가 dharness 메타 스킬 없이 손으로 만든 derived 프로젝트) 본 (a) 분기를 *skip*하고 메시지에 표기:
    ```
    ⓘ baseline 미수립 — `/harness:harness-baseline`로 t=0 anchor 생성 시 (a) 자동 감지 활성화. 현재는 (b)·(c)만 사용.
    ```
  - skip된 동안에도 (b) profile-mismatch와 (c) 사용자 요청은 정상 작동.
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

**추정 토큰 룰 (deferred-pool 모델 — 6차 사이클 발견 반영):**

Claude Code 현 빌드는 MCP 도구를 *deferred tool pool*로 관리한다. SessionStart 시 system prompt에 *이름 + 짧은 description*만 적재되고, 전체 JSON schema는 `ToolSearch select:<name>` 호출 시점에 lazy-fetch. 즉 토큰 비용이 두 단계로 분리된다.

| 단계 | 비용 | 적용 빈도 |
|------|------|---------|
| **Baseline (deferred pool)** | 도구 1종당 **30~50 tokens** (이름+description) | SessionStart 1회 + 매 user turn system prompt 재적재 |
| **Per-call schema fetch** | 도구 1종당 **200~500 tokens** (JSON schema 본문) | 해당 도구 *호출 시점에만* (호출 빈도 × 도구 수) |

표에는 baseline (저=30 / 고=50)과 per-call 합산 후 (저=230 / 고=550) 양쪽을 같이 출력 — *이 도구가 turn당 평균 K회 호출된다*는 K 가중치는 user-side 추정이라 default K=0.3(=3 turn당 1회) 가정.

**출력 형식:**

```
| 위치               | MCP    | 도구 수 | baseline (저/고) | per-turn (K=0.3, 저/고) | 정합 평가                          |
|--------------------|--------|--------|------------------|-------------------------|----------------------------------|
| parent (적재됨)    | git    |     12 |    360 / 600     |     1,080 / 2,580       | ⚠️ 슬래시 커맨드 직접 호출 없으면 inline 이전 권고 |
| parent (적재됨)    | fetch  |      4 |    120 / 200     |       360 /   860       | ⚠️ §5-2 예외 조건 미충족 → §5-1로 |
| subagent only      | sqlite |      3 |     90 / 150     |       270 /   645       | ✓ data-analyst inline (§5-1-a)   |
|--------------------|--------|--------|------------------|-------------------------|----------------------------------|
| 합계 parent        |        |     16 |  **480 / 800**   |    1,440 / 3,440        | (매 turn baseline 고정 + 호출 시점 lazy) |
| 합계 subagent only |        |      3 |     90 / 150     |       270 /   645       | (해당 subagent spawn 시에만)      |
```

**권고 트리거 (deferred-pool 보정):**

- **parent baseline 합계 > 600 tokens (고 추정)**: §5-1 inline로 이전 권고 — *baseline은 매 turn 고정 비용*이므로 turn 누적이 클수록 격차 큼.
- **parent per-turn 합계(K=0.3) > 2,500 tokens**: 호출 빈도가 높은 도구가 parent에 적재됨 — 호출이 잦은 MCP일수록 inline 격리의 schema fetch 절감 효과 큼.
- **inline `mcpServers:` 가진 agent가 0개**인데 parent 적재가 있음: **격리 무결성 미구성** (의도 ③ 위반) — 합성 가이드 §5-1로 재구성 권고.
- **§3 인벤토리 toolset 지원 MCP가 toolset 필터 없이 적재됨** (예: github가 `GITHUB_TOOLSETS` 미설정으로 19종 toolset × 평균 5도구 ≈ 90+ 도구 전체 advertise): §5-1-b Layer A+B 결합형으로 갱신 권고. baseline에서만 *수십 배* 차이.

**한계:**

- baseline 30~50 / per-call 200~500 추정은 §1 deferred-pool 박스 + 6차 사이클 근사. 실측은 Claude Code 빌드별로 다름. **§11-3 fixture(3축 메트릭 M1/M2/M3) 결과 누적 후 보정 권고.**
- K(turn당 호출 빈도) 추정은 user workload 의존 — 실제 telemetry가 있으면 `_workspace/_telemetry/*.jsonl`의 도구별 호출 카운트로 보정 가능.
- inline `mcpServers:`는 spawn 시에만 baseline 비용 → *agent 호출 빈도 × baseline + 호출당 schema fetch*의 누적. parent 적재는 매 turn baseline 고정 → 격차 누적.

## 출력 형식

6섹션 보고서를 단일 메시지로 출력. `--verbose` 인자가 있으면 §3 인벤토리 전체 dump와 각 MCP의 도구 enumeration, 섹션 6의 도구별 추정 토큰 분포까지 포함 (없으면 카운트와 sample 2~3개만).

## 후속 명령어

- 신규 MCP 채택 권고가 있으면: `/harness:harness-mcp-adopt <사유>`
- 정합 결손(섹션 4) 정정: 사용자가 `.claude/settings.json` / agent frontmatter 직접 수정 (자동 수정 금지)
- §3 미박제 보고가 있고 dharness root 접근 가능하면: 사용자에게 footnote 추가 안내
- 섹션 6의 parent 적재 ⚠️ 항목 정정: §5-2 예외 조건 미충족이면 해당 MCP를 §5-1 inline 패턴으로 이전 (사용자 수동 — 자동 수정 금지)
- **🆕 섹션 4 deny 누락 정정**: strict read-only 의도면 settings.json `permissions.deny`에 advertise 도구 중 부수 효과 후보 박제 (사용자 도메인 지식 기반 최종 판정 — 자동 추가 금지). 합성 시점이라면 §10-5 inline 정의 갱신 절차 5-step으로 처리.

## 범위 외

- **자동 수정 0** — 모든 발견은 권고. `harness-mcp-adopt` 또는 사용자 수동 편집 필요.
- **MCP 서버 자체 디버깅** (connection 실패): MCP 서버 issue tracker.
- **dharness 본 저장소의 `.claude/`**: 선조건 (2)로 차단.
