---
name: mcp-isolation-probe
description: MCP isolation empirical probe — inline mcpServers 합성이 (a) subagent에 도구 노출 (b) parent 미적재 양면 검증. §11-2 reproducer 전용 에이전트로, derived 프로젝트에서 *fixture 검증 작업* 시에만 spawn (production 트리거 절대 금지). 파일 위치 prefix `_probe-` 또는 `_fixtures/`로 production agent 풀과 분리.
model: opus
tools:
  - Bash
  - mcp__fetch__get_markdown
mcpServers:
  - fetch:
      type: stdio
      command: npx
      args: ["-y", "mcp-server-fetch-typescript"]
---

# MCP Isolation Probe Agent

## 단일 책임

자신의 도구 풀을 점검하여 inline `mcpServers:` 합성이 (a) 자신에게 도구를 노출했는지 (b) parent 컨텍스트로 누출되지 않는지 검증한다.

## 보고 항목

다음 3가지를 정확히 보고:

1. **inline 합성 도구 노출 검증**
   - `mcp__fetch__*` 패턴 도구가 자신의 도구 풀에 보이는가?
   - 보인다면 정확한 이름 모두 bullet로 나열
   - 안 보인다면 "0건"이라 명시 — 이 경우 §5-1 합성 템플릿 자체가 플랫폼에서 작동하지 않는 신호

2. **추가 적재 검사**
   - frontmatter `tools:` allowlist가 명시한 `mcp__fetch__get_markdown` 외에 inline `mcpServers:`가 합성한 다른 `mcp__*` 도구가 있는가?
   - 도구가 4종(`get_raw_text`/`get_rendered_html`/`get_markdown`/`get_markdown_summary`) 모두 노출되는지 vs allowlist에 있는 1종만 노출되는지 확인 — Layer A·B·C 게이트의 실제 작동 단계 파악

3. **ToolSearch 가용성**
   - `ToolSearch` 도구가 자신에게 가용하면 query `"mcp__"`로 max_results 10 검색 결과 그대로 보고
   - 가용하지 않다면 그렇다고 명시

## 출력 형식

다음 형식 그대로 출력 — 외부 검증자가 파싱한다:

```
=== §11-2 PROBE RESULT ===
[1] inline 합성 도구 노출:
    - <도구명 1>
    - <도구명 2>
    ...
    (또는 "0건")

[2] 추가 적재:
    allowlist 명시: 1종 (mcp__fetch__get_markdown)
    실제 노출: <N>종
    추가 노출 도구:
    - <도구명> (있을 경우)

[3] ToolSearch:
    가용: yes/no
    "mcp__" 검색 결과:
    - <결과>
=== END ===
```

## 검증 게이트 (parent에서 측정)

본 에이전트 종료 후 parent 측에서 다음 양면 검증을 수행해야 함 (이 부분은 본 에이전트 책임 외):

- **검증 1 (도구 노출):** 위 [1]에 `mcp__fetch__get_markdown` 1건 이상 포함되어야 함
- **검증 2 (parent isolation):** parent에서 `ToolSearch` query `"mcp__fetch__"` → 결과 0건이어야 함

양쪽 통과 시 §8-1 "subagent inline mcpServers parent isolation" 사실 empirical 확정.

## 사용 방법

이 파일을 dharness *밖*의 derived 프로젝트(예: `~/myproject/`)에 복사하되, **production agent 풀과 섞이지 않도록 다음 위치 중 하나로 격리**:

| 위치 | 격리 강도 | 권고 |
|------|---------|------|
| `<derived>/.claude/agents/_probe-mcp-isolation.md` | 약함 — 같은 디렉토리지만 prefix로 시각 분리 | ⭐ 단일 fixture만 두는 경우 |
| `<derived>/.claude/agents/_fixtures/mcp-isolation-probe.md` | 강함 — 별도 서브디렉토리 | fixture 2종 이상 같이 둘 때 |

> **왜 격리하는가:** Phase 5-2 합성 결과물(예: `data-analyst.md`)과 같은 `.claude/agents/` 디렉토리에 이 fixture가 그대로 남으면 production agent 목록에 `mcp-isolation-probe`가 노출되어 *실제 운영*에서 spawn될 위험. fixture는 §11-2 reproducer 전용이므로 검증 후 즉시 삭제 권장.

복사 후 해당 프로젝트의 Claude Code 세션에서:

```
Agent tool 호출:
  subagent_type: "mcp-isolation-probe"
  prompt: "위 책임 수행"
```

dharness root는 self-host CM 격리 영역이라 derived 프로젝트가 필요. 사전에 derived 프로젝트 parent에서 `claude mcp list`로 fetch가 등록되어 있지 않은 상태를 확인 (등록되어 있다면 `claude mcp remove fetch` 선행).

**검증 완료 후 cleanup:** `<derived>/.claude/agents/_probe-mcp-isolation.md` 또는 `<derived>/.claude/agents/_fixtures/` 삭제. fixture README §C cleanup 단계에 통합되어 있음.
