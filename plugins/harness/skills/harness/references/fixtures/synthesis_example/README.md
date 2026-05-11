# Phase 5-2 + §10 합성 산출물 구체 예시 — 시나리오 인덱스

§5 합성 템플릿이 §10 Step 5의 4 산출물(에이전트 정의 / settings.json / CLAUDE.md 1행 / §3 인벤토리 footnote)로 결합되는 *형태 참고*. 외부 도입자가 자신의 도메인으로 매핑할 때 출발점.

각 시나리오는 [§3-1 매트릭스](../../permission-profiles.md#3-1-검증-완료-t0-mcp--capability-profile-매트릭스-14차-사이클-p2-1차-종합-보고)의 capability profile 1개를 *전형 사례*로 박제. **16차 사이클 누적으로 4 capability profile *완전 박제 매트릭스 달성*** — 외부 도입자는 자신의 도메인에 가장 가까운 예시 1종을 출발점으로 그대로 복사.

## 시나리오 카탈로그

| 시나리오 | capability profile | MCP | 도구 카운트 | Layer 결합 | 사이클 |
|----|----|----|----|----|----|
| [`data-analyst/`](./data-analyst/) | external-integration | `sqlite` | 6 (read 3 / write 3) | §5-1-a Layer B 단독 (단일 inline) | 8차 (sqlite enum 확정) |
| [`web-research/`](./web-research/) | web-research | `fetch` + `memory` | 4 + 9 | §5-1-a Layer B 단독 (npx 멀티 inline) | 14차 (P2 종합 보고 — fetch·memory 둘 다 enum ✓) |
| [`code-test/`](./code-test/) | code-test | `git` + `filesystem` | 12 + 14 | §5-1-a Layer B 단독 (**uvx + npx 혼합** 멀티 inline) | 16차 (4-profile 매트릭스 완전 박제) |
| [`reasoning-aux/`](./reasoning-aux/) | reasoning-aux | `sequential-thinking` + `time` | 1 + 2 | §5-1-a Layer B 단독 (완전 read-only 멀티 inline) | 16차 (4-profile 매트릭스 완전 박제) |

## 사용 흐름 (공통)

각 시나리오 폴더 안에 4 파일 (`README.md` + `<agent-name>.agent.md` + `settings.json` + `CLAUDE_md_row.md`)이 동일 구조로 박제. 다음 매핑으로 복사:

1. **에이전트 정의 파일** → `<derived>/.claude/agents/<agent-name>.md`
2. **`settings.json`** → `<derived>/.claude/settings.json` (기존 키와 *deep merge* — 덮어쓰지 말 것)
3. **`CLAUDE_md_row.md`의 행** → `<derived>/CLAUDE.md` "변경 이력" 표 끝에 추가
4. (a) §3 인벤토리 footnote + §3-1 매트릭스 행은 dharness 본 저장소 PR 영역 (§10 Step 5 atomic 분계 — 도입자는 권고만 보고). 새 MCP가 PoC enumeration 통과 후 §3-1 매트릭스 closure 기준(`tier·profile·도구 카운트·default permissions·Layer 결합` 5컬럼)을 충족하면 *§3과 §3-1 동시* 갱신.

복사 후 §10 Step 4의 `claude mcp add ...` 실행은 *생략* — inline `mcpServers:` 패턴은 parent 컨텍스트에 적재하지 않으므로 등록 자체가 불요 (§5-1 권고). 단 inline 정의의 `command:` / `args:`는 OS·환경별 placeholder 치환 필수 (각 시나리오 README의 "placeholder 치환 표" 참조).

## 4 시나리오의 차이 — Layer 결합 형태

| | `data-analyst` (external-integration) | `web-research` (web-research) | `code-test` (code-test) | `reasoning-aux` (reasoning-aux) |
|---|---|---|---|---|
| MCP 수 | 1 (sqlite) | 2 (fetch + memory) | 2 (git + filesystem) — **uvx + npx 혼합** | 2 (sequential-thinking + time) — **완전 read-only** |
| 실행자 | uvx (Python) | npx (Node) — 양쪽 | uvx + npx 혼합 | npx (Node) — 양쪽 |
| Layer | B 단독 (toolset 필터 미지원) | B 단독 (둘 다 toolset 필터 미지원) | B 단독 (둘 다 toolset 필터 미지원) | B 단독 (둘 다 toolset 필터 미지원) |
| 부수 효과 차단 | `deny` 3종 (sqlite write) | `deny` 3종 (memory delete) + `ask` 3종 (memory create/add) | `deny` 다수 (git push/reset + filesystem write) | `deny` 0종 — 모든 도구 `allow` (완전 read-only) |
| placeholder 수 | 2개 (uvx-path + db-abs) | 0개 (npx 기반) | 1+ (uvx-path) | 0개 |
| 부모↔서브 데이터 흐름 | 사용자 질의 → 분석 리포트 | 사용자 URL/질의 → fetched markdown + KG 누적 | 사용자 코드 질의 → diff/탐색 결과 | 사용자 multistep 질의 → 단계별 추론 + 시간 변환 |

## 적용 경계 (공통)

- 4 시나리오 모두 *derived 프로젝트* 대상. dharness root에는 적용하지 않음 (§10/§11 분계).
- 시나리오 이름(`data-analyst` / `web-research` / `code-test` / `reasoning-aux`)은 *형태 참고용* — 실제 도메인에 맞게 이름·세부 책임을 교체.
- 본 4종으로 §3-1 매트릭스 4 capability profile 완전 박제 — **외부 도입자는 별도 시나리오 작성 없이 가장 가까운 예시 복사·치환만으로 합성 출발**.
