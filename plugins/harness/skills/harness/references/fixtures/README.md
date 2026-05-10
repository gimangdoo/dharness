# Permission-profiles fixtures — §11 reproducer 번들

`plugins/harness/skills/harness/references/permission-profiles.md` §11이 정의한 4종 실증 레시피를 *복사 실행만으로 끝낼 수 있는* 형태로 박제한 fixture 모음.

각 fixture는 외부 환경(다음 세션 / derived 프로젝트 / 새 MCP install) 의존이라 본 세션에서 직접 실행 불가 — fixture 자체는 재현 가능 자산이다.

| 파일 | §11 레시피 | 외부 환경 요구 | 실행 시점 |
|------|----------|---------------|----------|
| `verify_11_1.md` | §11-1 도구명 노출 패턴 | dharness 세션 재시작 | 다음 SessionStart 직후 |
| `mcp-isolation-probe.agent.md` | §11-2 subagent inline isolation | dharness *밖* 별도 derived 프로젝트 | derived 프로젝트의 `.claude/agents/`에 복사 후 spawn |
| `verify_11_3.md` | §11-3 `enabledMcpjsonServers` 토글 | 세션 재시작 (베이스라인 → 토글 → 재시작) | 비교 측정 2회 |
| `probe_sqlite.js` | §11-4 §10 5-step Step 2 (pre-install probe) | uvx 가용 + 사용자 sqlite install 승인 (§6) | Step 3 user confirm 통과 후 Step 4 install 직전 |
| `synthesis_example/` | (별건) §5 + §10 Step 5 합성 산출물 1세트 (data-analyst 시나리오) | derived 프로젝트 1개 | 외부 도입자가 자신의 도메인으로 매핑 시 *형태 참고* |

## 결과 기록 규약

각 fixture 실행 결과는 본 README의 "결과 로그" 섹션에 누적 추가 — 시간순으로 한 행씩.

```
| 일자 | 레시피 | 환경 | 결과 요약 | 본문 §8-2 반영 |
|------|--------|------|----------|---------------|
| 2026-05-?? | §11-1 | dharness 다음 세션 | mcp__sequential-thinking__sequentialthinking (하이픈 보존) | §3 footnote 갱신 + §8-2 항목 완료 표시 |
```

(아직 미실행 — 첫 실행자가 채움)

## 결과 로그

(empty — 실행 시 위 표 형식으로 추가)
