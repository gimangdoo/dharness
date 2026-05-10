# §10 Step 5(d) — derived 프로젝트의 `CLAUDE.md` "변경 이력" 표 1행 박제

derived 프로젝트의 `CLAUDE.md`에 "변경 이력" 표가 이미 있다는 전제. 그 표 마지막에 다음 행을 그대로 복사한다 (날짜·트리거 사유는 실제 환경에 맞게 치환).

## 행 형식

```markdown
| {YYYY-MM-DD} | MCP 채택: sqlite | T0 / external-integration | data-analyst가 ./data/sales.db 분석 필요 (§10-1 트리거: 사용자 요청 + 도메인 변경) | inline mcpServers 패턴, read 3종 allow / write 2종 ask, 다음 세션부터 사용 가능 |
```

## 컬럼 의미

| 컬럼 | 본 행 값 | 일반 의미 |
|------|---------|----------|
| 1. 날짜 | `{YYYY-MM-DD}` | §10 Step 4 install 완료일 |
| 2. 변경 내용 | `MCP 채택: sqlite` | "MCP 채택: <서버명>" 형식 |
| 3. 대상 | `T0 / external-integration` | Tier + capability profile (§3 매핑) |
| 4. 사유 | `data-analyst가 ./data/sales.db 분석 필요 (§10-1 트리거: 사용자 요청 + 도메인 변경)` | §10-1 트리거 신호 + 사용처 |
| 5. 비고(선택) | `inline mcpServers 패턴, read 3종 allow / write 2종 ask, 다음 세션부터 사용 가능` | 패턴(inline vs .mcp.json) + 권한 요약 + mid-session 운영 함의 |

## 작성 정책

- **사유 컬럼은 placeholder 금지** — §10-1 트리거 신호 3종(baseline-diff / profile-mismatch / 사용자-요청) 중 어느 것이 발화했는지 명시.
- **사용자 직접 수정 영역** — 사유의 구체 맥락(어떤 데이터·어떤 분석 목표)은 합성 에이전트가 임의 작성하지 않고 사용자에게 1행 입력 요청 후 채움 (manual gate, dharness self-host CM Phase 5-2 D 관행 일관).
- **rollback 시:** §10-4에 따라 `claude mcp remove sqlite` 후 본 행 *삭제 대신 "rollback {date}" 라벨 추가* — 변경 이력은 append-only.

## 적용 경계

본 행은 *derived 프로젝트의* `CLAUDE.md`에 추가. dharness 본 저장소의 `CLAUDE.md`는 self-host CM 진화 기록자라 §10/§11 채택 행은 오지 않음 (§10 분계 박제).
