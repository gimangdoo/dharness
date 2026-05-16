---
description: 하네스 진행 가시성 단일 진입점. 인벤토리·baseline 신선도·drift 점수·pending action·MCP 상태 통합 출력. 변경 0 (read-only).
argument-hint: [--verbose]
---

# Harness — Status

기존 하네스의 *진행 상태*를 단일 명령으로 통합 출력. 변경 0 (read-only). 사용자가 "지금 뭐 해야 하지?" 물을 때의 단일 답.

## 컨텍스트

- **인자**: `$ARGUMENTS` (선택)
  - `--verbose`: 5섹션 풀 출력 (default는 단축 요약)
- **입력**: `.claude/agents/`, `.claude/skills/`, `_workspace/_baseline/*.md`, `_workspace/_telemetry/*.jsonl`, `_workspace/_drafts/` (해당 시), CLAUDE.md
- **출력**: 5섹션 진단 보고 (콘솔 출력만, 파일 산출물 0)

## 선조건 검증

1. `.claude/` 디렉토리 존재?
2. baseline 존재? (없으면 "초기 상태" 모드로 출력)

**미충족 시도 출력 — 단 "초기 상태" 또는 "비어 있음" 표시**.

## 실행 절차

`/harness:harness-audit` (LLM 추론)·`/harness:harness-mcp-status` (MCP 진단)와 *상호 보완*. 본 명령은 **상위 요약** — 깊이 있는 진단은 audit / mcp-status로 위임.

### 5섹션 출력

#### §1 인벤토리 (결정적)

```
📦 하네스 인벤토리
  에이전트 N명:
    - {agent-1} (model: opus, tools: K종)
    - {agent-2} ...
  스킬 M개:
    - {skill-1} (트리거: "...")
    - {skill-2} ...
  훅: K종 (registered in `.claude/settings*.json`)
  오케스트레이터: {orchestrator-name}
```

산출 방법: `Glob` + frontmatter parse — LLM 없음.

#### §2 baseline 신선도 (결정적)

```
🕐 Baseline 신선도
  project_profile.md: {age_days}일 전 (확신: {high|medium|low})
  intent_profile.md: {age_days}일 전 (확신: {...})
  ⚠️ {age_days}일 ≥ 30 → `/harness:harness-baseline` 재실행 권고
```

산출 방법: 파일 mtime + frontmatter `confidence` 필드.

#### §3 drift 점수 (결정적 + LLM 추론 분리)

```
📊 Drift 점수
  Telemetry 이벤트: 마지막 adapt 이후 N건
    - harness_invocation: X
    - agent_invocation: Y (실패율: Z%)
    - agent_failure: K
  baseline 시그널 변화: {inferred from project_profile diff}
  drift 임계 초과: {YES|NO}
  ⚠️ 임계 초과 시 → `/harness:harness-adapt` 권고
```

산출 방법:
- 결정적: `_workspace/_telemetry/*.jsonl` 마지막 `_last_adapt` 이후 카운팅 (host 측 self-host CM 사용 중이면 `.claude/hooks/_schema.py:count_events_since_last_adapt()` 호출)
- LLM 보조: project signal 추정 (현재 코드 ↔ baseline diff). 추정 결과는 *advisory*.

#### §4 pending action (결정적)

```
📋 pending action
  draft 미적용: N건 (sid: {a,b,c})
    → `/cm-claudemd-apply <sid> [사유]` (host 측 self-host CM 운영 시)
  마지막 변경 이력 박제: {YYYY-MM-DD} ({N_days}일 전)
  Phase 10 alert: {ACTIVE | OK}
```

산출 방법:
- `_workspace/_drafts/*.md` (applied/discarded 제외) 카운팅
- CLAUDE.md "변경 이력" 표 마지막 row date parse

#### §5 권고 행동 (LLM 합성 — advisory)

```
🎯 권고
  1순위: {single most-impactful action — drift > baseline staleness > pending draft 우선}
  2순위: {next}
  3순위: {next}
```

§1~§4 신호로 단일 LLM 추론. **advisory only — 사용자가 결정.**

### --verbose 모드

`--verbose` 인자 시 §1~§5 풀 출력. default는 §3 drift + §4 pending + §5 권고 3섹션 단축.

## 범위 외

- **변경 0** — read-only. 모든 수정은 별도 명령 (`/harness:harness-adapt` / `/harness:harness-evolve` / `/cm-claudemd-apply` / ...)
- **MCP 풀스택 진단 X** — 본 명령은 §1에서 agent의 tools 카운트만. 풀 진단은 `/harness:harness-mcp-status`
- **LLM 추론 영역 일관성 X** — agent/skill cross-reference 깊이 검토는 `/harness:harness-audit`

## 사용자 확정 doctrine (2026-05-14)

본 명령은 사용자 "진행" 가시성 단일 진입점 결손(G26) 해소 결정에 따라 신설 (감사 plan A4). audit / mcp-status는 *깊이 진단*에 집중하고, 본 명령은 *얕고 빠른 단일 진입점*.
