# §10 Step 5(d) — derived 프로젝트의 `CLAUDE.md` "변경 이력" 표 1행 박제

derived 프로젝트의 `CLAUDE.md`에 "변경 이력" 표가 이미 있다는 전제. 그 표 마지막에 다음 행을 그대로 복사한다 (날짜·트리거 사유는 실제 환경에 맞게 치환).

## 행 형식

```markdown
| {YYYY-MM-DD} | MCP 채택: fetch + memory | T0 / web-research | web-research 에이전트가 외부 URL 정제 + 누적 사실 KG 박제 (§10-1 트리거: 사용자 요청 + 프로젝트 phase=research) | inline mcpServers 멀티 패턴, fetch 4종 allow + memory read 3종 allow / create+add 3종 ask / delete 3종 deny (KG 영구성), 다음 세션부터 사용 가능 |
```

## 컬럼 의미

| 컬럼 | 본 행 값 | 일반 의미 |
|------|---------|----------|
| 1. 날짜 | `{YYYY-MM-DD}` | §10 Step 4 실행 완료일 (inline 패턴은 install 생략 — *agent 파일 작성일*) |
| 2. 변경 내용 | `MCP 채택: fetch + memory` | "MCP 채택: <서버명> [+ <서버명> ...]" — 멀티 inline 등재 시 `+`로 나열 |
| 3. 대상 | `T0 / web-research` | Tier + capability profile (§3-1 매트릭스 매핑) |
| 4. 사유 | `web-research 에이전트가 외부 URL 정제 + 누적 사실 KG 박제 (§10-1 트리거: 사용자 요청 + 프로젝트 phase=research)` | §10-1 트리거 신호 + 사용처 |
| 5. 비고(선택) | `inline mcpServers 멀티 패턴, fetch 4종 allow + memory read 3종 allow / create+add 3종 ask / delete 3종 deny (KG 영구성), 다음 세션부터 사용 가능` | 패턴(inline 멀티 vs .mcp.json) + 권한 요약 + mid-session 운영 함의 |

> **권한 표기 정합 룰:** 비고 컬럼의 `allow / ask / deny` 카운트는 **반드시 동 세트 `settings.json` `permissions` 항목과 1:1 일치**시킨다 (도구 카운트 + bucket 모두). 본 web-research 예시는 settings.json이 7 allow / 3 ask / 3 deny이라 비고도 동일. 만약 KG destructive 도구를 `ask`로 완화하면 본 비고도 동시 갱신 — drift 시 외부 도입자가 한 세트로 복사 후 두 산출물이 어긋남.

## 작성 정책

- **사유 컬럼은 placeholder 금지** — §10-1 트리거 신호 3종(baseline-diff / profile-mismatch / 사용자-요청) 중 어느 것이 발화했는지 명시.
- **사용자 직접 수정 영역** — 사유의 구체 맥락(어떤 도메인 리서치·어떤 KG 누적 목표)은 합성 에이전트가 임의 작성하지 않고 사용자에게 1행 입력 요청 후 채움 (manual gate, dharness self-host CM Phase 5-2 D 관행 일관).
- **rollback 시:** §10-4에 따라 *inline 패턴*이라 `claude mcp remove`는 적용 불가 — 대신 본 행 *삭제 대신 "rollback {date} (agent 정의에서 inline mcpServers 제거 + tools allowlist 정리)" 라벨 추가*. 변경 이력은 append-only.

## 멀티 inline 패턴의 행 표기 변형

| 시나리오 | 변경 내용 컬럼 |
|---|---|
| 단일 MCP (예: data-analyst) | `MCP 채택: sqlite` |
| 멀티 inline 같은 cycle (예: 본 web-research) | `MCP 채택: fetch + memory` |
| 멀티 inline 다른 cycle (예: web-research에 brave-search 후속 추가) | `MCP 정의 갱신: web-research (brave-search inline 추가)` — §10-5 "MCP 정의 갱신" 형식 |

## 적용 경계

본 행은 *derived 프로젝트의* `CLAUDE.md`에 추가. dharness 본 저장소의 `CLAUDE.md`는 self-host CM 진화 기록자라 §10/§11 채택 행은 오지 않음 (§10 분계 박제).
