# Phase 5-2 + §10 합성 산출물 구체 예시 — `reasoning-aux` 시나리오

§5 합성 템플릿이 §10 Step 5의 4 산출물로 결합되는 정합 결과 1세트. **네 번째 시나리오** — 4 capability profile 매트릭스의 마지막 박제. *완전 read-only profile* — 권한 모델이 가장 단순한 합성 예시.

> ✅ **박제 근거** — sequential-thinking(1종 ✓ — 2차 사이클 PoC enum) + time(2종 ✓ — 14차 사이클 P2 T0 batch) 두 MCP 모두 [§3 인벤토리](../../../permission-profiles.md#3-mcp-후보-인벤토리-tier-분류)에 검증 완료 박제. [§3-1 매트릭스](../../../permission-profiles.md#3-1-검증-완료-t0-mcp--capability-profile-매트릭스-14차-사이클-p2-1차-종합-보고)의 `reasoning-aux` profile 권고 조합.

## 시나리오

**가상 derived 프로젝트:** "글로벌 팀의 의사결정 어시스턴트 — 복합 트레이드오프 분석을 단계별 reasoning chain으로 전개 + 다중 timezone 참석자의 미팅·기한 계산. write/destructive 작업이 없는 *순수 reasoning 보조*."

**자동 합성 결과:**
- 에이전트 `multistep-planner` 1명 (capability profile = `reasoning-aux`)
- 매핑 MCP: `sequential-thinking` (T0, 1 도구 — read-only) + `time` (T0, 2 도구 — read-only)
- 패턴: **inline `mcpServers:` 멀티 등재 (uvx + npx 혼합)** (§5-1 권장 — Layer B subagent 격리, parent 컨텍스트 미적재)

## 산출물 4종 (§10 Step 5 = "Reflect")

| 산출물 | 파일 | 위치(derived 프로젝트 기준) | 비고 |
|--------|------|---------------------------|------|
| (a) 카탈로그 footnote | (메타) | `plugins/harness/skills/harness/references/permission-profiles.md` §3 sequential-thinking/time 행 | §3-1 매트릭스 `reasoning-aux` 행과 동시 갱신 |
| (b) 에이전트 정의 | [`multistep-planner.agent.md`](./multistep-planner.agent.md) | `.claude/agents/multistep-planner.md` | inline `mcpServers:` 멀티 패턴 (sequential-thinking npx + time uvx) |
| (c) 권한 게이트 | [`settings.json`](./settings.json) | `.claude/settings.json` | 3종 모두 allow / ask 0 / deny 0 — 완전 read-only |
| (d) 변경 이력 1행 | [`CLAUDE_md_row.md`](./CLAUDE_md_row.md) | derived 프로젝트의 `CLAUDE.md` "변경 이력" 표 | 멀티 inline 표기 ("MCP 채택: sequential-thinking + time") |

## 관찰 포인트

1. **완전 read-only profile — destructive 차단 패턴이 불필요한 케이스** — 4 시나리오 중 본 예시가 유일하게 `permissions.deny`가 *비어 있음*. 이는 *깜빡한 누락*이 아니라 *advertise 도구 전체가 read-only*라는 의도 — settings.json `$comment_5`에 명시 박제. 다른 profile(`data-analyst`/`web-research`/`code-test`)은 모두 destructive 도구를 advertise하므로 deny 박제 필수, 본 profile은 그 부담 0.

2. **future drift 가드 — placeholder deny rule 미박제 이유** — time MCP가 향후 `set_local_timezone` 같은 write 도구를 advertise하기 시작했을 때를 가정한 *예방용 placeholder deny*는 의도적으로 두지 않음. 이유: 현재 advertise 0인데 deny rule이 있으면 *false signal* (실제 destructive 있는데 차단 중인 것으로 오인). `CLAUDE_md_row.md`의 "future drift 가드" 섹션에 *그 시점*에 추가할 행을 미리 박제 — 발생 시점에만 add.

3. **uvx + npx 혼합 멀티 inline 패턴 (code-test와 동일)** — sequential-thinking은 npx-기반(placeholder 0), time은 uvx-기반(`<UVX_ABS_PATH>` + `<IANA_TZ>` placeholder 2개). PATH 가용성 차이 박제는 `code-test` 시나리오 README와 동일 — *반복 패턴 박제로 일관성 유지*.

4. **chain 발화 cap — 토큰 부풀림 surface** — `sequentialthinking` 도구는 무제한 chain 가능. `multistep-planner.agent.md` "보안 정책"에 "단계 한도 N=5 권장" 박제. **본 profile의 *유일한 운영 함의*** — 다른 profile은 권한 분포로 안전성 확보, 본 profile은 *발화 길이 cap*으로 토큰 안전성 확보.

5. **3 도구 vs 26 도구 (code-test) — capability profile별 *복잡도 차이*** — `reasoning-aux`(3) vs `external-integration`(6 sqlite) vs `web-research`(13) vs `code-test`(26)로 capability profile별 권한 매트릭스 규모가 약 9배 차이. derived 프로젝트가 *어느 profile부터 시작할지*는 *복잡도 대응* 측면에서 `reasoning-aux` → `external-integration` → `web-research` → `code-test` 순으로 단계적 채택 권고 가능 (단 사용자 요구가 우선).

## 적용 경계

- 본 예시는 *derived 프로젝트* 대상. dharness root에는 적용하지 않음 (§10/§11 분계 — dharness root의 reasoning 작업은 메인 세션 LLM이 직접 처리하며 별도 reasoning subagent 미도입).
- "multistep-planner"는 가상 이름 — 실제 도메인에 맞게 이름·도메인 specific 책임을 교체. **예시 변형**: `decision-thinker` (트레이드오프 분석 전용) / `meeting-scheduler` (timezone 변환 + 가능 슬롯 제안 전용) / `hypothesis-tester` (가설 검증 chain 전용).
- *완전 read-only profile*의 형태 참고 — `permissions.deny`를 의도적으로 비우는 패턴은 본 시나리오가 유일.

## 사용 흐름

1. `reasoning-aux/` 디렉토리 전체를 *derived 프로젝트*로 복사 후 다음 매핑:
   - `multistep-planner.agent.md` → `<derived>/.claude/agents/multistep-planner.md`
   - `settings.json` → `<derived>/.claude/settings.json` (기존 키와 deep merge — 덮어쓰지 말 것)
   - `CLAUDE_md_row.md`의 한 행 → `<derived>/CLAUDE.md` "변경 이력" 표 끝에 추가
2. **placeholder 치환** (`multistep-planner.agent.md` 본문 끝 표 참조):
   - `<UVX_ABS_PATH>` → `uvx` 실행 파일 절대경로 (`where uvx` 또는 `which uvx`로 확인)
   - `<IANA_TZ>` → 팀 default IANA timezone (예: `Asia/Seoul`) — 미박제 시 system tz fallback
3. **`claude mcp add`는 생략 가능** — inline `mcpServers:` 패턴은 spawn 시 connect되므로 parent 등록 불요 (§5-1 권장).
4. 세션 재시작 후 `Agent` tool로 `subagent_type: "multistep-planner"` spawn 검증. 첫 spawn 시 subagent의 도구 풀에 `mcp__sequential-thinking__sequentialthinking` + `mcp__time__get_current_time` + `mcp__time__convert_time` 3종 노출 확인.

## 권한 모델 정합 매트릭스 (참고)

| 도구 | bucket | 사유 |
|---|---|---|
| `mcp__sequential-thinking__sequentialthinking` | allow | reasoning chain, read-only, 부수 효과 0 (단 토큰 비용은 chain 길이에 비례 — 발화 cap은 에이전트 본문에서 권고) |
| `mcp__time__get_current_time` | allow | 시간 read, 부수 효과 0 |
| `mcp__time__convert_time` | allow | timezone 변환 read, 부수 효과 0 |

> **bucket 변경 시 양면 갱신:** 위 표를 갱신하면 동 디렉토리의 `settings.json` `permissions.{allow,ask,deny}` + `CLAUDE_md_row.md` 비고 컬럼 카운트도 동시 정합. **본 profile은 변경 시점이 *향후 time/sequential-thinking MCP가 write 도구를 advertise할 때*** — 그 시점에 `$comment_5` 가드대로 deny 추가.

> 본 파일은 `plugins/harness/skills/harness/references/fixtures/synthesis_example/reasoning-aux/`의 박제 예시. 본 시나리오는 `synthesis_example/README.md` 카탈로그에 *네 번째 행*으로 등재 권고 (다음 통합 박제 시).
