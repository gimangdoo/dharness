---
description: 하네스 구조·schema·chain 결정적 검증. LLM 호출 0. plugin scripts 번들 — host-agnostic.
argument-hint: [--json] [--strict]
---

# Harness — Validate

하네스 구조·schema·chain을 **결정적 스크립트**로 검증한다. LLM 호출 0. `/harness:harness-audit`(LLM 추론)과 *분리* — audit이 본 명령 결과를 input으로 받는 구조.

## 컨텍스트

- **인자**: `$ARGUMENTS` (선택)
  - `--json`: JSON 출력 (`_workspace/_audit_validate_{ts}.json`에도 박제)
  - `--strict`: 1건 이상 fail 시 exit code 1 (CI 진입점 활용)
- **입력**: `.claude/agents/`, `.claude/skills/`, `_workspace/_baseline/*.md`, `_workspace/_telemetry/*.jsonl`
- **출력**: 3섹션 검증 보고 + (옵션) JSON report

## 선조건 검증

1. `.claude/` 디렉토리 존재?
2. `plugins/harness/scripts/validate/{structure,schema,chain}.py` 3 스크립트 가용?

**미충족 시 즉시 중단** — 안내:
- (1) "하네스 미존재 — `/harness:harness-new` 먼저 실행하세요."
- (2) "plugin scripts 누락 — plugin 재설치 권고."

## 실행 절차

LLM 호출 0. 3 스크립트를 순차 호출 후 결과 합성.

### Step 1: structure 검증

```
py plugins/harness/scripts/validate/structure.py [--json]
```

검증 항목:
- 모든 agent `.md` frontmatter `name:` + 본문 필수 섹션 존재 (핵심 역할 / 작업 원칙 / 입력·출력 프로토콜 / 에러 핸들링 / 협업 / 팀 통신 프로토콜)
- 모든 skill `SKILL.md` frontmatter `name:` + `description:` 필드 + 본문 워크플로우 섹션 존재
- 오케스트레이터 스킬 식별 가능 (CLAUDE.md 포인터 또는 `.claude/skills/*-orchestrator/`)
- YAML frontmatter 파싱 오류 0

### Step 2: schema 검증

```
py plugins/harness/scripts/validate/schema.py [--json]
```

검증 항목:
- `_workspace/_baseline/project_profile.md` 5축 필수 필드 (stack / architecture / convention / maturity / pain_points)
- `_workspace/_baseline/intent_profile.md` 필수 5필드 (constraints.tech_stack / constraints.team.size / constraints.timeline.horizon / architecture.deployment_target / quality.test_rigor)
- 모든 `inferred_fields` 항목이 `source` 필드 보유 (P6-4 doctrine — 인용 0이면 schema 위반)
- 필드 type 정합 (enum / array / scalar 등)

### Step 3: chain 검증

```
py plugins/harness/scripts/validate/chain.py [--json]
```

검증 항목:
- 오케스트레이터 본문의 agent/skill 인용이 실제 파일과 1:1 매핑 (dangling reference 0)
- agent의 `tools:` allowlist의 MCP 인용이 `.claude/settings*.json` permissions 또는 inline `mcpServers:`와 정합
- references/ 인용 link가 존재 (orphan reference 0, phantom reference 0)
- telemetry capture 호출 — orchestrator 본문이 `_workspace/_telemetry/{date}.jsonl` append 명령 보유 (lines 박제 검증)
- runtime-adaptation.md §6 chain 표 기준 dangling 0

### Step 4: 출력 보고

```
✅ Validate — deterministic 검증 결과

§1 structure: PASS (N agents / M skills, 0 errors)
§2 schema: PASS (baseline 5+5 필드 OK, inferred_fields source 인용율 100%)
§3 chain: PASS (dangling 0, telemetry capture 박제 OK)

(--json 옵션 시) report → _workspace/_audit_validate_{ts}.json
```

실패 시:

```
❌ Validate — deterministic 검증 실패

§1 structure: FAIL (3 errors)
  - .claude/agents/researcher.md: frontmatter `name:` 누락
  - .claude/agents/editor.md: 필수 섹션 "에러 핸들링" 누락
  - .claude/skills/code-review/SKILL.md: YAML frontmatter 파싱 오류 line 4

§2 schema: PASS
§3 chain: FAIL (2 errors)
  - {orchestrator}.md line 47: dangling agent reference "old-agent-name"
  - .claude/agents/researcher.md `tools:`의 "Brave_Search" — settings.json permissions에 미정합

📋 다음 행동:
  - structure 실패 → 수동 또는 `/harness:harness-evolve` 수정
  - chain 실패 → `/harness:harness-remove` (dangling) 또는 `/harness:harness-mcp-adopt` (MCP 미정합)
```

`--strict` 시 fail 1건 이상에서 exit code 1.

## audit ↔ validate 분리 doctrine

| 명령 | 검증 영역 | 호출 방식 |
|---|---|---|
| `harness-validate` | **deterministic** — 구조·schema·chain | LLM 0, plugin scripts 번들 |
| `harness-audit` | **LLM 추론** — 책임 중복·트리거 정합·통신 프로토콜 의미·orchestrator 워크플로우 일관성 | LLM 추론 + (옵션) validate 결과 input |

**doctrine (2026-05-13C — LLM·deterministic hybrid)**: 결정·persistence는 deterministic, 추론·합성은 LLM. 본 명령은 결정적 영역만 전담, audit은 추론 영역만 전담.

audit이 validate 결과를 input으로 받는 패턴 — audit 본문에서:
1. `harness-validate --json`을 먼저 호출 가능 안내
2. validate가 PASS면 audit이 *LLM 추론에만 집중*
3. validate가 FAIL이면 audit이 *구조 실패 우선 권고* 후 추론 영역 skip

## 범위 외

- **자동 fix 0** — 결정적 검증만. fix는 별도 명령 (remove / evolve / mcp-adopt)
- **drift 점수 X** — `/harness:harness-status` §3
- **LLM 추론 영역 X** — `/harness:harness-audit`

## 사용자 확정 doctrine (2026-05-14)

본 명령은 사용자 의도 "결정적 일관성 검증" 결손(G2, P3-4 미진행) 해소 결정에 따라 신설 (감사 plan A2 = P3-4). plugin scripts 번들 — host-agnostic 결정성.
