# CLAUDE.md "변경 이력" 표 1행 박제 — `reasoning-aux` 시나리오

derived 프로젝트의 `CLAUDE.md` "변경 이력" 표 마지막 row 다음에 다음 행을 그대로 추가 (날짜·세션 id는 실제 값으로 치환):

```
| 2026-05-?? | MCP 채택: sequential-thinking + time (inline mcpServers: 멀티 패턴) — multistep-planner 에이전트 신설 | sequential-thinking 1 도구 + time 2 도구 = 3 도구 (모두 read-only, Layer B 단독 + Layer C settings.json `permissions.allow` 3종 / `ask` 0 / `deny` 0) | reasoning-aux capability profile (Phase 5-2 §3-1 매트릭스) 적용. dharness 본체 read-only invariant 보존. 본 profile은 advertise 도구가 모두 read-only라 *destructive 차단 패턴이 불필요한 단순 케이스* — 4 profile 중 가장 간소한 합성. 운영 함의: mid-session MCP add는 본 세션 미전파 — 합성 직후 새 세션에서 사용 가능. |
```

## 컬럼 의미

| 컬럼 | 채움 룰 |
|---|---|
| **날짜** | YYYY-MM-DD (실제 합성 일자) |
| **변경 내용** | "MCP 채택: sequential-thinking + time (inline mcpServers: 멀티 패턴) — multistep-planner 에이전트 신설" — 멀티 inline 패턴이 핵심 정보 |
| **대상** | 도구 카운트(3) + Layer 결합 (Layer B subagent 격리 + Layer C permissions.allow 3종) + 권한 bucket 분포 (deny 0 / ask 0 / allow 3) — *완전 read-only profile* 명시 |
| **사유** | "Phase 5-2 §3-1 매트릭스 `reasoning-aux` profile 적용" + read-only invariant 명시 + "destructive 차단 패턴 불필요한 단순 케이스" 1줄 + 운영 함의(mid-session 미전파) 1줄 |

## append-only 룰

본 행은 derived 프로젝트의 변경 이력에 **추가** — 기존 행을 수정하지 않음. dharness `CLAUDE.md`의 "변경 이력" 표와 동일 규약.

## rollback 절차

만약 `multistep-planner` 에이전트가 derived 프로젝트의 요구와 어긋나 제거할 경우:

1. `.claude/agents/multistep-planner.md` 삭제
2. `.claude/settings.json`의 `permissions.allow`에서 `mcp__sequential-thinking__*` + `mcp__time__*` 항목 제거 (다른 에이전트가 같은 MCP를 공유하지 않는다면)
3. 본 CLAUDE.md "변경 이력" 표 행은 *유지* (rollback 사실을 다음 행으로 추가)

dharness 본체 `CLAUDE.md` 변경 이력 표의 append-only 규약과 동일.

## future drift 가드

time MCP가 향후 write 계열 도구(`set_local_timezone` 등)를 advertise하기 시작하면, 그 시점에 본 행 다음 다음 행(rollback 행이 아닌 *update* 행)으로 다음을 추가:

```
| 2026-??-?? | reasoning-aux 시나리오 — time MCP write 도구 추가 차단 | settings.json `permissions.deny`에 `mcp__time__set_*` 패턴 추가 | time MCP v? 부터 advertise되는 destructive 도구 차단. 본 profile의 read-only 특성 유지. |
```

이런 future-aware 패턴은 *placeholder rule을 미리 두지 않는* 의도(현재 settings.json의 `$comment_5`)와 일관 — 실제 도구가 advertise되는 시점에만 deny 박제.
