---
description: MCP 통합 진입점. 첫 인자 subcommand (recommend|adopt|status)로 분기. 기존 3 명령(`harness-mcp-recommend`/`-adopt`/`-status`)을 단일 명령에 라우팅 — UX 단순화. 기존 3 명령도 그대로 유지 (back-compat).
argument-hint: <recommend|adopt|status> [subcommand 인자...]
---

# Harness — MCP (unified)

3 MCP 명령(`recommend` / `adopt` / `status`)의 통합 진입점. 첫 인자가 subcommand이고 나머지는 해당 subcommand에 그대로 전달된다. 본 명령은 *라우터*이며, 실제 워크플로우는 각 subcommand 본문 정의를 따른다.

> **호환성 (2026-05-14, Mg2):** 기존 3 명령(`/harness:harness-mcp-recommend` / `-adopt` / `-status`)은 그대로 유지된다. 본 통합 명령은 *추가* 진입점으로, 기존 설치 사용자에 break-change 0. 신규 사용자에는 단일 진입점 권장.

## Subcommand 라우팅

| Subcommand | 라우팅 대상 | 목적 |
|---|---|---|
| `recommend <에이전트\|역할>` | [`harness-mcp-recommend.md`](./harness-mcp-recommend.md) | 합성 시점/후 MCP 후보 3축 점수 추천 (E·S·A). 채택은 인계. |
| `adopt <사유>` | [`harness-mcp-adopt.md`](./harness-mcp-adopt.md) | 런타임 시점 신규 MCP 채택 (§10 dynamic adoption 5-step). |
| `status [--verbose]` | [`harness-mcp-status.md`](./harness-mcp-status.md) | 등록 MCP·도구 매트릭스·토큰 비용 추정·정합 진단 (read-only). |

## 실행 절차

1. `$ARGUMENTS` 1st token 추출.
2. token 매칭:
   - `recommend` → `harness-mcp-recommend.md` 본문 그대로 따름. 잔여 인자(`$ARGUMENTS` 2nd token 이후)를 해당 명령의 `$ARGUMENTS`로 전달.
   - `adopt` → `harness-mcp-adopt.md` 본문 그대로 따름. 잔여 인자 전달.
   - `status` → `harness-mcp-status.md` 본문 그대로 따름. 잔여 인자 전달.
   - 미매칭(예: 빈 인자, 오타) → 본 §Subcommand 라우팅 표 출력 + "subcommand 명시 필요" 안내 후 중단.

## 예시

```text
/harness:harness-mcp recommend web-researcher
  → harness-mcp-recommend.md 의 R-1~R-7 실행 (인자: web-researcher)

/harness:harness-mcp adopt "playwright로 e2e 테스트 자동화 필요"
  → harness-mcp-adopt.md 의 §10 5-step 실행

/harness:harness-mcp status --verbose
  → harness-mcp-status.md 진단 (verbose 모드)
```

## 범위 외

- 본 명령 *자체*는 워크플로우 0 (라우팅만). 모든 산출물·선조건·결과는 각 subcommand 본문에 정의.
- 라우터 단순 dispatch이므로 인자 검증·선조건 체크도 dispatch 후 해당 subcommand 본문이 처리.

## 관련 명령

- 기존 3 명령(권장 — install 사용자 호환성): `/harness:harness-mcp-recommend`, `/harness:harness-mcp-adopt`, `/harness:harness-mcp-status`
- 채택 후 정합 진단: `/harness:harness-mcp status` (= `harness-mcp-status`)
- baseline 신호 변경 후 재추천: `/harness:harness-baseline` → `/harness:harness-mcp recommend --refresh`
