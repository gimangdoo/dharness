---
description: 하네스 read-only 진단 통합 — 기본은 인벤토리·기준선 신선도·drift·대기 작업; --deep는 LLM 추론 정합 감사; --mcp는 MCP 매트릭스·후보 추천. 수정 0.
argument-hint: [--verbose] [--deep] [--mcp]
allowed-tools: Read, Glob, Grep, Bash(ls:*), Bash(claude mcp list:*), WebSearch
---

# Harness — Status (read-only 진단 통합)

기존 하네스의 *진행 상태·정합성·MCP 상태*를 단일 명령으로 통합 출력. **변경 0 (read-only).** 사용자가 "지금 뭐 해야 하지?" 물을 때의 단일 답.

> **read-only 진단 통합 doctrine (2026-05-30, command 병합):** 이전의 `harness-audit`(LLM 추론 감사) / `harness-mcp-status`(MCP 진단) / `harness-mcp-recommend`(MCP 후보 추천) 별도 슬래시 커맨드를 폐기하고 **본 명령의 모드 플래그로 흡수**했다. 기본 = 얕고 빠른 결정적 가시성. `--deep` = LLM 추론 정합 감사. `--mcp` = MCP 매트릭스 + 후보 추천. 셋 다 *수정 0* — 발견 사항은 사용자에게 보고만 하고, 적용은 `/harness:harness-evolve`·`/harness:harness-adapt`로.

## 컨텍스트

- **인자**: `$ARGUMENTS` (선택)
  - `--verbose`: 기본 4섹션 풀 출력 (default는 §3 drift + §4 pending 단축)
  - `--deep`: LLM 추론 정합 감사 추가 (구 audit — 5 검사 항목, `_workspace/_audit_{ts}.md` 박제)
  - `--mcp`: MCP 매트릭스 + 후보 추천 추가 (구 mcp-status + mcp-recommend)
- **입력**: `.claude/agents/`, `.claude/skills/`, `_workspace/_baseline/*.md`, `_workspace/_telemetry/*.jsonl`, `_workspace/_drafts/`, `_workspace/_baseline/changelog.md`, (`.mcp.json`/`settings*.json` — `--mcp` 시)
- **출력**: 진단 보고 (콘솔). `--deep` 시 `_workspace/_audit_{ts}.md` 1건 박제, 그 외 파일 산출 0.

## 선조건 검증

1. `.claude/` 디렉토리 존재?
2. baseline 존재? (없으면 "초기 상태" 모드로 출력)

## 기본 모드 — 4섹션 (결정적)

#### §1 인벤토리

```
📦 하네스 인벤토리
  에이전트 N명: - {agent-1} (model: opus, tools: K종) ...
  스킬 M개: - {skill-1} (트리거: "...") ...
  훅: K종 · 오케스트레이터: {orchestrator-name}
```
산출: `Glob` + frontmatter parse — LLM 없음.

#### §2 baseline 신선도

```
🕐 Baseline 신선도
  project_profile.md: {age_days}일 전 (확신: {high|medium|low})
  intent_profile.md: {age_days}일 전
  dharness plugin version: baseline `{baseline_version}` ↔ 현 `{current_version}` {(match|MISMATCH)}
  ⚠️ {age_days} ≥ 30 → baseline 갱신 권고 (`/harness:harness-evolve "baseline 갱신"`)
  ℹ️ version MISMATCH 시 → doctrine refit 권고 (본 명령 `--deep` + `/harness:harness-validate` 진단 후 항목별 `/harness:harness-evolve`로 수정)
```
산출: 파일 mtime + frontmatter `confidence` + `intent_profile.md` `meta.dharness_version` ↔ `plugin.json` `version` (chain.py `check_dharness_version_drift()` 재사용).

#### §3 drift 점수

```
📊 Drift 점수
  Telemetry 이벤트: 마지막 adapt 이후 N건
    - harness_invocation: X · agent_invocation: Y (실패율: Z%) · agent_failure: K
  baseline 시그널 변화: {project_profile diff 추정 — advisory}
  ⚠️ 누적 신호 큼 → 사용자 판단 시 `/harness:harness-adapt` 호출 (자동 발화 아님)
```
산출: 결정적 — `_workspace/_telemetry/*.jsonl` `_last_adapt` 이후 카운팅 (host self-host CM 시 `.claude/hooks/_schema.py:count_events_since_last_adapt()`). LLM 보조 project signal 추정은 *advisory*.

#### §4 pending action

```
📋 pending action
  draft 미적용: N건 (sid: {a,b,c}) → `/cm-claudemd-apply <sid>` (host self-host CM 시)
  마지막 변경 이력 박제: {YYYY-MM-DD} ({N_days}일 전)
```
산출: `_workspace/_drafts/*.md`(applied/discarded 제외) 카운팅 + changelog "변경 이력" 표 마지막 row date.

`--verbose` 시 §1~§4 풀 출력. default는 §3+§4 단축.

## `--deep` 모드 — LLM 추론 정합 감사 (구 audit)

> **read-only doctrine:** `--deep`는 *의미·일관성·표현 quality*만 추론한다. 결정적 검증(파일 존재·frontmatter·dangling·필수 필드)은 `/harness:harness-validate`. **자동 수정 절대 금지.**

권장 호출 순서: 먼저 `/harness:harness-validate --json`(결정적) → 본 `--deep`가 그 JSON을 input으로 받아, PASS 시 추론 영역 집중 / FAIL 시 구조 실패 우선 보고.

5 검사 항목 (각 발견 🔴차단/🟡경고/🟢OK 분류, `_workspace/_audit_{ts}.md` 박제):
1. **에이전트 책임 중복·gap** — N명 역할 본문 추론, overlap/gap, 통신 프로토콜 의미 정합, `model:` 누락 *권고 사유*
2. **스킬 description 트리거 quality** — 키워드 빈약(<3 flag), 트리거 충돌(동일 발화 동시 매칭), pushy 평가, orphan skill 제거 vs 유지 권고
3. **변경 이력 의미 정합** — 사유 열 맥락 충분도, 파일 mtime > 마지막 이력 날짜 시 미기록 변경 회상 요청, Phase 9/10 출처 정합
4. **baseline 추론 정합** — 필수 5필드 *내용* quality, `inferred` vs `user_confirmed` 분리, 3개월 초과 flag
5. **Phase 10 인프라 의미 정합** — capture 신호 충분도, 런타임 시그널 부족 추론

발견 후속(보고만, 적용은 사용자): orphan agent → `/harness:harness-evolve "X 제거"` · baseline stale → `/harness:harness-evolve "baseline 갱신"` · 변경이력 누락 → 회상 요청.

## `--mcp` 모드 — MCP 매트릭스 + 후보 추천 (구 mcp-status + mcp-recommend)

read-only. 두 블록:

1. **상태 매트릭스 (구 mcp-status)** — 등록 MCP(`claude mcp list` / `.mcp.json`) × 에이전트 `tools:` allowlist 매트릭스, parent vs subagent 적재 토큰 비용 추정, 인벤토리 정합(`references/permission-profiles-inventory.md` §3), `permission-profiles.md` §10 trigger 신호.
2. **후보 추천 (구 mcp-recommend)** — 에이전트/역할별 "효율성·확장성·정확도" 3축 점수로 후보 정렬 (`references/mcp-recommendation.md` 엔진, 10 신호 S1~S10). `--mcp <에이전트|역할>` 인자 시 해당 대상 한정. 외부 검색 가능(WebSearch). **추천만 — 실제 채택은 `/harness:harness-evolve "X MCP 붙여"`(내부 `mcp-adopt` op).**

## 범위 외

- **변경 0** — read-only. 모든 수정은 `/harness:harness-evolve` / `/harness:harness-adapt` / `/cm-claudemd-apply`.
- 결정적 구조·schema·chain 검증은 `/harness:harness-validate` (LLM 0).

## 사용자 확정 doctrine

본 명령은 사용자 "진행" 가시성 단일 진입점 결손(G26) 해소로 신설(감사 plan A4), 2026-05-30 audit/mcp-status/mcp-recommend 흡수로 read-only 진단 단일 진입점이 됐다.
