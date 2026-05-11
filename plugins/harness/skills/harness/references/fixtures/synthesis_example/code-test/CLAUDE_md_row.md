# CLAUDE.md "변경 이력" 표 1행 박제 — `code-test` 시나리오

derived 프로젝트의 `CLAUDE.md` "변경 이력" 표 마지막 row 다음에 다음 행을 그대로 추가 (날짜·세션 id는 실제 값으로 치환):

```
| 2026-05-?? | MCP 채택: filesystem + git (inline mcpServers: 멀티 패턴) — code-explorer 에이전트 신설 | filesystem 14 도구 / git 12 도구 (Layer B 단독 — toolset 필터 미지원 + Layer C settings.json `permissions` 게이트로 destructive git_reset deny / write 8종 ask / read 17종 allow) | code-test capability profile (Phase 5-2 §3-1 매트릭스) 적용. dharness 본체 read-only invariant 보존 — 본 에이전트는 *이 derived 프로젝트*의 path-roots(ALLOWED_DIR) 범위 내 read·git 한정. 운영 함의: mid-session MCP add는 본 세션 미전파 — 합성 직후 새 세션에서 사용 가능. |
```

## 컬럼 의미

| 컬럼 | 채움 룰 |
|---|---|
| **날짜** | YYYY-MM-DD (실제 합성 일자) |
| **변경 내용** | "MCP 채택: filesystem + git (inline mcpServers: 멀티 패턴) — code-explorer 에이전트 신설" — 멀티 inline 패턴이 핵심 정보 |
| **대상** | 도구 카운트 + Layer 결합 (Layer B subagent 격리 + Layer C permissions 게이트) + 권한 bucket 분포 (deny 1 / ask 8 / allow 17 합 26) |
| **사유** | "Phase 5-2 §3-1 매트릭스 `code-test` profile 적용" + read-only invariant 명시 + 운영 함의(mid-session 미전파) 1줄 |

## append-only 룰

본 행은 derived 프로젝트의 변경 이력에 **추가** — 기존 행을 수정하지 않음. dharness `CLAUDE.md`의 "변경 이력" 표와 동일 규약.

## rollback 절차

만약 `code-explorer` 에이전트가 derived 프로젝트의 요구와 어긋나 제거할 경우:

1. `.claude/agents/code-explorer.md` 삭제
2. `.claude/settings.json`의 `permissions.allow`/`ask`/`deny`에서 `mcp__filesystem__*` + `mcp__git__*` 항목 제거 (다른 에이전트가 같은 MCP를 공유하지 않는다면)
3. 본 CLAUDE.md "변경 이력" 표 행은 *유지* (rollback 사실을 다음 행으로 추가)

dharness 본체 `CLAUDE.md` 변경 이력 표의 append-only 규약과 동일.
