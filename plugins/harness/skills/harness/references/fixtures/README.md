# Permission-profiles fixtures — §11 reproducer 번들

`plugins/harness/skills/harness/references/permission-profiles.md` §11이 정의한 4종 실증 레시피를 *복사 실행만으로 끝낼 수 있는* 형태로 박제한 fixture 모음.

각 fixture는 외부 환경(다음 세션 / derived 프로젝트 / 새 MCP install) 의존이라 본 세션에서 직접 실행 불가 — fixture 자체는 재현 가능 자산이다.

| 파일 | §11 레시피 | 외부 환경 요구 | 실행 시점 |
|------|----------|---------------|----------|
| `verify_11_1.md` | §11-1 도구명 노출 패턴 | dharness 세션 재시작 | 다음 SessionStart 직후 |
| `mcp-isolation-probe.agent.md` | §11-2 subagent inline isolation | dharness *밖* 별도 derived 프로젝트 | derived 프로젝트의 `.claude/agents/`에 복사 후 spawn |
| `verify_11_3.md` | §11-3 `enabledMcpjsonServers` 토글 | 세션 재시작 (베이스라인 → 토글 → 재시작) | 비교 측정 2회 |
| `probe_sqlite.js` | §11-4 §10 5-step Step 2 (pre-install probe) | uvx 가용 + 사용자 sqlite install 승인 (§6) | Step 3 user confirm 통과 후 Step 4 install 직전 |
| `probe_filesystem.js` / `probe_time.js` / `probe_memory.js` | §10 Step 2 (P2 T0 batch — 14차 사이클) | node + npx/uvx (probe-only, install 불요) | dharness 본 세션 Bash에서 직접 실행 — enumeration만 |
| `synthesis_example/data-analyst/` | (별건) §5 + §10 Step 5 합성 산출물 1세트 — 단일 inline `mcpServers:` sqlite 시나리오 | derived 프로젝트 1개 | 외부 도입자가 자신의 도메인으로 매핑 시 *형태 참고* (단일 MCP 패턴) |
| `synthesis_example/web-research/` | (별건) §5 + §10 Step 5 합성 산출물 1세트 — 멀티 inline `mcpServers:` fetch + memory 시나리오 (14차 사이클) | derived 프로젝트 1개 | 외부 도입자가 자신의 도메인으로 매핑 시 *형태 참고* (멀티 MCP 동시 등재 패턴) |

## 결과 기록 규약

각 fixture 실행 결과는 본 README의 "결과 로그" 섹션에 누적 추가 — 시간순으로 한 행씩.

```
| 일자 | 레시피 | 환경 | 결과 요약 | 본문 §8-2 반영 |
|------|--------|------|----------|---------------|
| 2026-05-?? | §11-1 | dharness 다음 세션 | mcp__sequential-thinking__sequentialthinking (하이픈 보존) | §3 footnote 갱신 + §8-2 항목 완료 표시 |
```

(아직 미실행 — 첫 실행자가 채움)

## 결과 로그

| 일자 | 레시피 | 환경 | 결과 요약 | 본문 §8-2 반영 |
|------|--------|------|----------|---------------|
| 2026-05-10 | §11-1 | dharness 본 세션 SessionStart deferred tool list | **17종 모두 §3 enumeration 일치** — fetch 4 + git 12 + sequential-thinking 1. **하이픈 보존** (`mcp__sequential-thinking__sequentialthinking`). **추가 발견:** Claude Code는 *deferred tool pool* 모델 — SessionStart에는 이름+description만 system prompt에 적재, JSON schema는 `ToolSearch select:<name>` 호출 시 lazy-fetch (의도 ② baseline 우호) | §3 footnote ✓ 갱신 / §8-2 §11-1 ✓ 이동 / §1 deferred-pool 박스 신설 |
| 2026-05-10 | §11-4 (Step 2) | dharness 본 세션 + derived 프로젝트의 sample DB | `probe_sqlite.js` JSON-RPC stdio 핑 → **sqlite MCP 6 도구 enumeration**: `read_query`/`write_query`/`create_table`/`list_tables`/`describe_table`/`append_insight`. fixture 주석의 추정 5종 대비 `create_table` 1종 추가 발견 | §3 sqlite 행 ✓ 갱신 (PoC 미완 → 6종 박제) |
| 2026-05-10 | §11-4 (Step 4) | derived 프로젝트(`C:\Users\user01\dharness-probe-test`) | `claude mcp add sqlite <uvx-abs> -- mcp-server-sqlite --db-path <db-rel>` → 1차 `✗ Failed to connect`. **abs-path로 재install** → ✓ Connected. → §10 Step 4에 *경로 인자 절대경로 필수* caveat 박제 | §10 Step 4 ✓ caveat 추가 / §3 sqlite 행 install 명령에 abs-path 명시 |
| 2026-05-10 | §6 self-test | derived 프로젝트 inline `mcpServers:` 작성 시도 | 첫 작성 → auto-mode classifier 차단 (*untrusted external code execution outside trusted repo*). 사용자 명시 동의 후 통과. **§6 정책의 enforcement가 dharness root 외부에서도 동일** 작동 확인 | §8-2 8차 사이클 ✓ self-test 박제 |
| 2026-05-10 | §11-2 (setup) | derived 프로젝트 setup | `<derived>/.claude/agents/mcp-isolation-probe.md` + `data-analyst.md` + `settings.json` + `data/sample.db` + `CLAUDE.md` + `probe_sqlite.js` 작성 완료. **spawn은 외부 Claude Code 세션 의존** — 외부 실행자는 `cd <derived> && claude` 후 Agent tool 호출 | §8-2 8차 사이클 ✓ setup ready 박제 |
| 2026-05-10 | §11-2 (spawn) | derived 프로젝트(`C:\Users\user01\dharness-probe-test`) 새 Claude Code 세션 | `mcp-isolation-probe` subagent spawn 결과: **[1] inline 합성 도구 노출 0건 / [2] allowlist 명시 1종(`mcp__fetch__get_markdown`) 실제 노출 0종 / [3] ToolSearch 가용 no**. subagent에 노출된 도구는 `Bash` 1개뿐 — frontmatter `tools:` allowlist + inline `mcpServers:` 양쪽 모두 적재 안 됨. **§5-1 합성 템플릿이 작동하지 않는 신호** — Layer A(frontmatter 합성) 단계 누락. 검증 1(도구 노출 ≥1건) 실패 → §8-1 사실 확정 보류 필요 | §8-1 inline isolation 사실: 적재 자체가 누락 → "isolation 통과" 이전에 "합성 미작동" 박제 / §5-1 합성 템플릿 재검토 큐 |
| 2026-05-10 | §11-2 후보 (b) | derived 프로젝트 새 세션 — `tools:` 표기 형식 변형 3종 spawn (bare / quoted / wildcard) | **3 형태 모두 `mcp__fetch__get_markdown` 노출 0건** — `tools:` allowlist 표기 형식은 contradiction의 원인이 *아님*. 후보 (b) 제외 확정. 진짜 원인은 (a) 필드명 / (c) subagent 인식 / (d) 빌드 차이 중 잔존. | permission-profiles.md §8-2 후보 (b) ✗ 박제 / 9차 의제 후보를 (a)·(c)·(d) 3종으로 축소 |
| 2026-05-10 | §11-3 (B2 부분 측정) | derived 프로젝트 — `enabledMcpjsonServers: []` 토글 OFF 후 측정 | **B2.M2 ≈ 6000~7000** (사용자 보고). 단위 모호 — 메트릭 정의상 M2는 deferred pool 도구 카운트이나 6-7천 도구는 비현실적, 실측값일 가능성: (i) M1(system prompt 토큰)을 잘못 보고 (ii) 시스템 프롬프트 *전체 길이* 또는 빌트인 포함 전체 도구 카운트 (iii) LLM 추정 응답(자가 시스템 프롬프트 정확 측정 불가). **B1 베이스라인 미측정** → 분기 판정 보류. | §11-3 측정 logs를 verify_11_3.md "측정 로그" 표에 1행 (단위 caveat 포함). B1 추가 측정 후 비교 가능 |
| 2026-05-10 | §A-(a) RESOLUTION | dharness 본 세션 + WebFetch 공식 docs `https://code.claude.com/docs/en/sub-agents` | **§11-2 contradiction 진짜 원인 확정** = `mcpServers:` schema mismatch. 공식 docs verbatim 발췌: schema는 **list-of-dicts** (`-` prefix) + 각 항목에 `type: stdio` (또는 `http`/`sse`/`ws`) 필수. 우리 fixture는 plain dict + type 누락 → silent skip. 후보 (a)의 *상위 필드명*(`mcpServers`)은 OK, *하위 schema format*이 원인. 후보 (c)·(d) 별도 검증 불요 (schema 정정으로 충분). | permission-profiles.md §5-1 + §5-1-a + §5-1-b + §8-2 ✓ 갱신 / SKILL.md callout ✓ 갱신 / synthesis_example/README.md EMPIRICAL CAVEAT → RESOLUTION 변경 / dharness fixture mcp-isolation-probe.agent.md + synthesis_example/data-analyst.agent.md 일괄 정정 |
| 2026-05-10 | §11-2 P0 재현 검증 ✅ | derived 프로젝트(`C:\Users\user01\dharness-probe-test`) 새 Claude Code 세션 + 정정 schema fixture(`_probe-mcp-isolation.md`, list-of-dicts + `type: stdio`) | **양면 검증 통과** — [1] subagent 도구 노출 4종 (`mcp__fetch__get_raw_text`/`get_rendered_html`/`get_markdown`/`get_markdown_summary` 모두) ✓, [2] parent ToolSearch query `mcp__fetch__` → 0 hit (deferred pool 적재 0) ✓. 9차 schema RESOLUTION이 *empirical 확정*으로 승급. **🆕 새 발견 (10차 사이클):** frontmatter `tools:`에 `mcp__fetch__get_markdown` 1종만 allowlist했는데도 inline 서버의 **4종 전부 노출** — 즉 `tools:` allowlist는 inline 서버 도구를 줄이지 못함 (Layer C 통제 채널이 inline에 무력). Layer C 게이트는 `settings.json permissions.deny`로 강제해야 한다는 운영 함의. | §1 [^B] 셀 ⚠️→✅ 승급 / §1 [^A]는 §11-3 측정 별도 / §8-1 inline parent isolation 사실 ✓ empirical / §8-2 §11-2 미완 → 완료 / §5-1 새 caveat (inline + tools allowlist 무력) 박제 / §5-3 deny 권고 강화 |
| 2026-05-10 | 11차 사이클 closure 박제 | dharness 본 세션 — 진단 명령 갱신 | 10차 P0 새 발견(`tools:` allowlist 무력 + `permissions.deny` default)을 진단 채널 `commands/harness-mcp-status.md`에 반영. **§2** 매트릭스에 `inline mcpServers: advertise 도구 (실노출)` 컬럼 추가 — `tools:` allowlist만 보고 정합 판정하던 이전 룰을 *advertise 도구 전체 vs deny* 비교로 격상. **§4** 정합 점검 2종 신규: (i) inline advertise 도구 vs `permissions.deny` 정합 (strict read-only 의도일 때 default 점검, 휴리스틱: `write_/insert_/update_/delete_/remove_/append_/create_/set_/commit_/push_/exec*/run_` prefix), (ii) allowlist vs advertise 도구 수 mismatch insight (Layer B 격리 가정 무력 가시화). **§7** 후속 명령어에 deny 누락 정정 안내 추가 — `harness-mcp-adopt`의 §10-5 inline 정의 갱신 절차 5-step 경유. | `commands/harness-mcp-status.md` §2/§4/후속 명령어 갱신 / `permission-profiles.md` §8-2 11차 사이클 진척 라인 1줄 추가 |
| 2026-05-10 | §11-3 P1 부분 진척 (12차 사이클) | derived 프로젝트 `dharness-probe-test` — `.mcp.json` (project-scope) 등록 sqlite + 다중 enable 키 동기화 시도 | **B1 베이스라인 미달** — `~/.claude.json` user-scope per-project entry `enabledMcpjsonServers=["sqlite"]` + `<derived>/.claude/settings.json={}` 동기화에도 deferred pool에 `mcp__sqlite__*` 0종(B1.M2=0/M1=?/M3=yes). 사용자 보고 `claude mcp get sqlite ✓ Connected` (Project config)인데도 적재 안 됨. **새 발견:** ① `enabledMcpjsonServers` 키는 *2 위치*에 동시 존재(user-scope per-project entry + project-scope settings.json) — 측정 단독 변수 아님, ② user-scope 단독 채움으로는 활성화 불충분 (또 다른 차단 mechanism 미확정). | verify_11_3.md "측정 환경 함정" 섹션 신설 (2 위치 동기화 권고 + 추가 차단 후보 4종 = CLI 인터랙티브 approval / `disabledMcpjsonServers` / `enableAllProjectMcpServers` 유사 키 / 빌드별 정책 / 즉시 우회 `-s local` 재등록) / verify_11_3.md "측정 로그" 1행 추가 / permission-profiles.md §1 [^A] footnote 12차 진척 1줄 / §8-2 P1 진척 라인 1개 추가. **다음 액션 (외부 1회 1분)**: `<derived>` 새 세션에서 `claude --debug` 출력 + `~/.claude.json` 추가 키 grep으로 차단 mechanism 확정. |
| 2026-05-11 | §11-3 P1 pre-flight (13차 사이클) | dharness 본 세션 read-only `~/.claude.json` 전수 grep | **차단 mechanism 4번째 키 식별 — `hasTrustDialogAccepted`** (per-project entry, `false`면 `.mcp.json` 신뢰 미승인 → 모든 project-scope MCP 적재 차단). `dharness-probe-test` entry 현재 값: enabledMcpjsonServers(user-scope)=["sqlite"] ✓ / disabledMcpjsonServers=[] ✓ / hasTrustDialogAccepted=true ✓ / `<derived>/.claude/settings.json` enabledMcpjsonServers=["sqlite"] ✓ — **gate 4종 모두 충족, B1 측정 ready**. 12차 측정 시 `.claude/settings.json={}` 였던 사실이 그 이후 `["sqlite"]`로 갱신됨. 본 세션은 derived 새 세션 spawn 불가 — 사용자 외부 1회(~5분)로 closure. | verify_11_3.md "측정 환경 함정" 섹션 4 gate 표 + "외부 액션 카드" Step 1-4 신설 / verify_11_3.md "측정 로그" 13차 pre-flight 행 추가 / permission-profiles.md §1 [^A] footnote 13차 pre-flight 박제 / §8-2 12차 다음 13차 진척 라인 추가. **다음 액션**: 외부 실행자가 `cd C:\Users\user01\dharness-probe-test && claude` → 첫 메시지 `system-reminder의 mcp__* deferred tool 명단을 원문 그대로 보고` → B1.M2 즉시 캡처 → verify_11_3.md "측정 로그"에 1행 추가. |
| 2026-05-11 | §11-3 P1 closure (13차 사이클 B1+B2 `claude -p`) | dharness 본 세션 Bash → `claude -p` derived 프로젝트 + 사용자 manual settings.json 토글 OFF | **🚨 결정적 empirical:** B1.M2=6 (gate ON, sqlite 6종 전부 적재 — `mcp__sqlite__{append_insight, create_table, describe_table, list_tables, read_query, write_query}` §3 인벤토리 100% 일치). **B2.M2=6 (gate `enabledMcpjsonServers=[]` 토글 OFF에도 6종 그대로 적재)** — *project-scope `.claude/settings.json` 토글은 deferred pool에 영향 0*. 토글-효과 가설 ✗ 부정. **caveat**: `-p` 모드 auto-trust 부수 효과로 settings.json 토글이 무시됨 가능성 잔존 (인터랙티브 비교 미완). | verify_11_3.md "측정 로그" 2행 (B1+B2) 추가 + permission-profiles.md §1 [^A] footnote ✗ 결과 + §8-2 §11-3 ✓ empirical 이동 (단, *project-scope settings.json 채널 한정* 부정 사실 명시) + 본 README 결과 로그 1행 추가. **다음 액션 (선택적)**: (i) 인터랙티브 `claude` 비교 측정으로 `-p` auto-trust 부수 효과 분리 (ii) `~/.claude.json` user-scope per-project entry 토글 측정으로 진짜 gate 채널 식별 (iii) 또는 P1 부분 closure로 마감하고 P2로 이동 |
| 2026-05-11 | P2 filesystem MCP probe-only (§10 Step 2, dharness 본 세션 Bash) | `node fixtures/probe_filesystem.js` (`@modelcontextprotocol/server-filesystem` 일회성 npx spawn, ALLOWED_DIR=`C:\Users\user01\dharness-probe-test\data`) | **COUNT=14 도구 ✓** — **read 10종**: `read_file`/`read_text_file`/`read_media_file`/`read_multiple_files`/`list_directory`/`list_directory_with_sizes`/`directory_tree`/`search_files`/`get_file_info`/`list_allowed_directories` + **write 4종**: `write_file`/`edit_file`/`create_directory`/`move_file`. dharness root에 영구 install 안 함 (§10 적용 경계 — self-host CM 격리). 빌트인 Read/Write/Edit과 도구 중복, 가치는 *path-roots 격리* (capability profile = code-test). | `probe_filesystem.js` fixture 신설 + `permission-profiles.md` §3 filesystem 행 enumeration·install 명령 박제 (PoC 미완 → ✓ 14종). 본 README 결과 로그 1행 추가. **다음 액션**: time MCP probe (T0 batch 2/3). |
| 2026-05-11 | P2 time MCP probe-only (§10 Step 2) | `node fixtures/probe_time.js` (`mcp-server-time` Python, uvx 경유 spawn) | **COUNT=2 ✓** — **read-only 2종**: `get_current_time` (required=[timezone]) / `convert_time` (required=[source_timezone, time, target_timezone]). §3 인벤토리의 "단일 도구 추정"이 *2종*으로 확정. 부수 효과 0 — default 권고: 2종 모두 `allow`. | `probe_time.js` fixture 신설 + `permission-profiles.md` §3 time 행 enumeration·install 명령 박제 (PoC 미완 → ✓ 2종). 본 README 결과 로그 1행 추가. **다음 액션**: memory MCP probe (T0 batch 3/3). |
| 2026-05-11 | P2 memory MCP probe-only (§10 Step 2) | `node fixtures/probe_memory.js` (`@modelcontextprotocol/server-memory` Knowledge Graph, npm 경유 spawn) | **COUNT=9 ✓** — **read 3종**: `read_graph`/`search_nodes`/`open_nodes` + **create/add write 3종**: `create_entities`/`create_relations`/`add_observations` + **delete write 3종**: `delete_entities`/`delete_observations`/`delete_relations`. default 권고: read 3 `allow` / create+add 3 `ask` / delete 3 `deny` (destructive). dharness CM은 자체 sqlite 사용 — memory MCP는 외부 derived 프로젝트의 persistent knowledge graph 용도. | `probe_memory.js` fixture 신설 + `permission-profiles.md` §3 memory 행 enumeration·install 명령·CRUD 분류 박제 (PoC 미완 → ✓ 9종). 본 README 결과 로그 1행 추가. **다음 액션**: T0 batch 3종 closure — P2 1차 종합 보고. |
| 2026-05-11 | **P2 1차 종합 보고 (14차 사이클 — T0 batch closure)** | dharness 본 세션 — 누적 검증 자료 합성 (외부 실행 0회, 코드 실행 0회 — pure 박제) | **T0 MCP 7종 / 48 도구 / 4 capability profile 매트릭스 박제 완료.** §3-1 신설: code-test(git+filesystem 26) / web-research(fetch+memory 13) / external-integration(sqlite 6 + T1+ github 별건) / reasoning-aux(sequential-thinking+time 3). 각 행에 *Layer 결합 권고 + default permissions bucket + mid-session 미전파 운영 함의* 동시 박제. 멀티 inline `mcpServers:` 패턴(여러 MCP 동시 등재) 예시 YAML도 §3-1에 박제. 미완 잔존(P3/P4)은 T1·T1+·T2~ MCP 7종 — 매트릭스 *외부* 영역으로 명시 분리. | (1) `permission-profiles.md` §3-1 매트릭스 신설(§3 뒤·§4 앞) + §8-2 closure 항목 추가 + §1 [^B] 셀 inline-멀티 패턴 cross-link / (2) `synthesis_example/` 서브디렉토리화 — 기존 `data-analyst/` 4 파일 + 신규 `web-research/` 4 파일(`web-research.agent.md` inline fetch+memory 멀티 + `settings.json` 7 allow / 3 ask / 3 deny + `CLAUDE_md_row.md` 멀티 inline 표기 + `README.md`) + top-level `README.md` 인덱스 재작성 / (3) `SKILL.md` Phase 5-2 단락에 14차 §3-1 매트릭스 한 줄 + web-research 2번째 synthesis_example 한 줄 / (4) 본 README 결과 로그 1행 추가. **다음 액션 (선택적, P3 수준)**: T1 MCP enumeration (playwright/chrome-devtools — CLI flag 형태 toolset 검증) / 인터랙티브 `claude` 측정으로 13차 `-p` auto-trust 분리 / `~/.claude.json` user-scope 토글 측정. |
| 2026-05-11 | **14차 self-verify — `harness-mcp-status` self-test (15차 사이클 — empirical 작동 확인)** | dharness 본 세션 Bash → `dharness-probe-test` (fixture 환경, read-only 진단) | **🎯 14차 cycle 산출물 4종 모두 의도대로 작동 empirical 확정.** 섹션 2 `inline advertise 도구 (실노출)` 컬럼 = mcp-isolation-probe의 `tools:` 1종 vs advertise 4종 mismatch 정확 감지 (10차 P0 발견 검증). 섹션 3 §3-1 정합 점검 = web-research profile 추정 + `memory` 누락 ⓘ로 보고(fixture 의도 = OK). 섹션 4 `permissions` 키 부재 시 fallthrough `ask` 룰 작동 + 부수 효과 도구 0종 → deny ⚠️ 발화 안 함 = 정상. 섹션 6 토큰 추정 = parent 적재 sqlite 6도구(300 tokens 고) — 임계 600 미달이라 ⚠️ 발화 안 함 = 정상. **본 fixture 환경 ⚠️ 0건이 *정상*임을 확인** — production derived 환경에서 의미 있는 ⚠️ 발화. | `permission-profiles.md` §8-2 14차 closure paragraph 끝에 self-verify ✓ 1줄 + `SKILL.md` Phase 5-2 진척 라인에 self-verify ✓ 추가 + 본 README 결과 로그 1행 추가. **다음 액션 (선택적, P3 수준)**: T1 MCP enum / 인터랙티브 `claude` / user-scope 토글 — 14차 cycle 외부 의제 그대로 이월. |

## 미실행 — 외부 환경 의존 unblock 절차

> **🚨 dharness Phase 5-2 회로의 *critical empirical hole* — 0건 잔존 (13차 부분 closure)**
>
> 10차 사이클에 식별된 외부 액션 2건 모두 closure 단계 진입:
>
> | 우선순위 | 액션 | 결과 | 상태 |
> |---|---|---|---|
> | ~~🔴 P0~~ | ~~§11-2 spawn 재현 검증~~ | inline `mcpServers:` parent isolation 양면 ✓ | ✅ 10차 사이클 완료 |
> | ~~🟠 P1~~ | §11-3 토글 측정 (B1·B2 M2) | **B1=6, B2=6 — project-scope settings.json 토글은 deferred pool 영향 0** | ✅ 13차 사이클 부분 closure (`claude -p` 모드 한정 — caveat 잔존) |
>
> **13차 closure 함의:**
> 1. `<derived>/.claude/settings.json` `enabledMcpjsonServers`는 토큰 절감 채널이 *아니다* (적어도 `-p` 모드에서). 합성 가이드의 "settings.json 토글로 적재 제어" 권고 ✗ 박제됨.
> 2. 진짜 gate 채널 후보 = `~/.claude.json` user-scope per-project entry의 `enabledMcpjsonServers` (or `hasTrustDialogAccepted`) — 별도 측정 미완.
> 3. `-p` 모드 auto-trust 부수 효과 가설은 미해소 — 인터랙티브 비교 측정으로 확정 가능.
>
> 후속 의제 (선택적, P3 수준): 인터랙티브 `claude` 측정 / user-scope toggle 측정 / `--strict-mcp-config` 분리 측정.

요약 표 (각 항목의 상세 playbook은 아래 §A·B·C 참조):

| 레시피 | 우선순위 | 환경 | 결과 박제처 |
|--------|---------|------|-----------|
| **§11-2 spawn 재현 검증 (정정 schema)** | 🔴 P0 — 즉시 | derived 프로젝트 새 세션 1회 | 본 README 결과 로그 + permission-profiles.md §1 [^B] 셀 ✅로 승급 |
| §11-3 토글 측정 (3축 M1/M2/M3) | 🟠 P1 — 후속 | derived 프로젝트 + `.mcp.json` `-s project` 등록 + 세션 재시작 ×2 | `verify_11_3.md` 측정 로그 + permission-profiles.md §1 [^A] 셀 ✅로 승급 |
| §11-4 e2e | ✓ 완료 (8차) | (재적용 시 reproducer로 활용) | — |

---

### §A. §11-2 spawn — 4 후보 검증 (9차 핵심 의제) ✅ RESOLVED

**배경**: 8차 사이클에 derived 프로젝트(`C:\Users\user01\dharness-probe-test`)에서 `mcp-isolation-probe` subagent를 spawn한 결과, **subagent 도구 풀에 `Bash` 1개만 노출** + `mcp__fetch__get_markdown`(allowlist 명시)도 inline `mcpServers:`도 모두 미적재.

**9차 사이클 해소 (2026-05-10)**: 공식 docs(`https://code.claude.com/docs/en/sub-agents` §"Scope MCP servers to a subagent") WebFetch로 진짜 원인 확정 — `mcpServers:` schema가 **list-of-dicts** (`-` prefix) + 각 항목에 `type: stdio` (또는 `http`/`sse`/`ws`) 필수임. 우리 fixture는 plain dict + type 누락이라 silent skip. 후보 (b) ✗ 제외 + 후보 (a) 상위는 OK·하위 schema가 원인 + 후보 (c)·(d) 무관 추정 (schema 정정으로 충분).

**남은 액션 (재현 검증, 1회 1분)**:
1. `cd C:\Users\user01\dharness-probe-test` (cleanup된 경우 §11-2 fixture를 dharness에서 다시 복사)
2. `mcp-isolation-probe.md` 본문이 정정 schema(`mcpServers: - fetch: type: stdio ...`)인지 확인
3. `claude` 실행 → 첫 메시지: `Agent tool로 subagent_type: "mcp-isolation-probe" spawn해서 책임 수행 결과 받아줘`
4. [1] inline 합성 도구 노출이 ≥1건 (`mcp__fetch__get_markdown` 포함)이면 ✅ 해소 empirical 확정
5. 결과를 본 README "결과 로그"에 1행 추가 (검증 ✓ 또는 추가 후보 발생 시 그 내용)

**선조건 공통:**
1. `cd C:\Users\user01\dharness-probe-test` (derived 프로젝트로 이동)
2. `claude --version` 출력 기록 (후보 d의 입력)
3. `claude` 실행으로 새 세션 시작

#### 후보 (a) — frontmatter 필드명 정합

> 공식 docs schema에서 `mcpServers`가 정확한 필드명인지, 또는 `mcp_servers` / `mcps` / 다른 형태인지 확인.

**실행:**
1. 새 세션 첫 user 메시지:
   ```
   Anthropic 공식 docs(https://docs.claude.com 또는 docs.anthropic.com)의 "subagent" 또는 "Configure MCP servers" 페이지를 WebFetch로 가져와서, .claude/agents/<name>.md frontmatter에서 MCP 서버를 inline 선언하는 정확한 필드명과 schema를 발췌해줘.
   ```
2. 결과 발췌가 `mcpServers:`이면 (a) 무관 → 후보 (b)로 이동
3. 발췌가 다른 필드명(`mcp_servers:` 등)이면 → derived 프로젝트의 `.claude/agents/mcp-isolation-probe.md` + `data-analyst.md`에서 필드명을 정정 후 §B의 spawn 재실행

**결과 기록 위치:**
- 본 README "결과 로그"에 1행: `| 일자 | §11-2 후보 (a) | derived | 공식 필드명: <X> | permission-profiles.md §5-1 일괄 정정 |`
- 정정 후 spawn 재실행 결과를 §11-2 (spawn) 갱신 행으로 추가

#### 후보 (b) — `tools:` allowlist의 MCP 도구 표기 형식

> `tools:` 배열에 MCP 도구 이름을 적을 때 어떤 형식이 인식되는지 측정.

**실행:**
1. derived 프로젝트의 `.claude/agents/mcp-isolation-probe.md` 사본 3개 만들기:
   - `probe-bare.md` — `tools: [Bash, mcp__fetch__get_markdown]` (현재 형태)
   - `probe-quoted.md` — `tools: [Bash, "mcp__fetch__get_markdown"]` (인용 추가)
   - `probe-mixed.md` — `tools: [Bash, "mcp__fetch__*"]` (와일드카드)
   각 사본의 frontmatter `name:`도 변경 (예: `mcp-isolation-probe-bare`).
2. 새 세션 첫 user 메시지:
   ```
   다음 3 subagent를 차례로 spawn해서 결과를 모아줘:
   - subagent_type: mcp-isolation-probe-bare
   - subagent_type: mcp-isolation-probe-quoted
   - subagent_type: mcp-isolation-probe-mixed
   각각 책임 수행 후 [1] 노출 도구 목록만 1줄로 보고.
   ```
3. 어느 형태에서 `mcp__fetch__get_markdown`이 노출되는지 비교
4. 노출된 형태가 있다면 그것이 표준 → 본 fixture 일괄 정정

**결과 기록:**
- 본 README "결과 로그" + permission-profiles.md §5-1 형식 정정

#### 후보 (c) — Agent tool의 file-based subagent 인식

> `subagent_type` 인자가 (1) frontmatter `name:` 값 (2) 파일명 (3) 다른 식별자 중 어느 것을 매칭하는지 + 인식 자체가 되는지.

**실행:**
1. `claude /agents` (슬래시 커맨드) 또는 세션 첫 메시지로 `현재 세션에서 사용 가능한 file-based subagent 목록을 보여줘` 입력
2. 응답에 `mcp-isolation-probe`가 *나타나는가*?
   - **나타남** → 인식 OK, 후보 (c) 무관, 후보 (a)/(b)/(d) 검증
   - **안 나타남** → file-based subagent 인식 실패. 다음 시도:
     a. `subagent_type` 인자에 frontmatter `name:` 값 대신 파일명 (`mcp-isolation-probe.md` 또는 `mcp-isolation-probe`) 사용
     b. agent 파일 위치를 `.claude/agents/`가 아닌 다른 경로(`agents/`, `~/.claude/agents/` 등)로 시도
     c. `claude /agents create` (만약 해당 명령 존재) 또는 `claude /agents register <file>` 시도
3. 인식 실패가 dharness root에서도 동일한지 확인 (대조군) — `cd C:\Users\user01\awesome-files\dharness && claude` 후 같은 질문

**결과 기록:**
- subagent 인식 메커니즘이 일반 docs와 다르면 그것이 가장 큰 발견 — permission-profiles.md §9에 후속 박제

#### 후보 (d) — Claude Code 빌드 차이

> 외부 실행자와 dharness 본 세션의 Claude Code 버전이 다를 가능성. 실측 환경의 빌드 차이로 inline `mcpServers:` 지원 여부가 변할 수 있음.

**실행:**
1. dharness 본 세션 (이 세션)에서 `claude --version` 출력 기록
2. derived 프로젝트 새 세션의 첫 user 메시지로 `Bash로 claude --version을 실행해줘` → 출력 기록
3. 두 버전이 다르면 — 새 빌드에서 schema 변경 가능성. release notes(`https://docs.anthropic.com/en/docs/claude-code/release-notes` 또는 GitHub `anthropics/claude-code` releases) WebFetch로 `mcpServers` 또는 `subagent` 관련 변경 검색
4. 두 버전이 같으면 → 후보 (d) 무관 → (a)/(b)/(c)에 집중

**결과 기록:**
- 버전 차이 + release notes 발췌를 §8-2에 박제 (외부 실측 fact)

#### §A 완료 후 액션

4 후보 중 1개라도 hit하면 `permission-profiles.md` §5-1 / SKILL.md callout / synthesis_example의 EMPIRICAL CAVEAT 박스 일괄 제거. 4 후보 모두 hit 안 하면 → §5-1을 *non-default*로 강등 + 새 default 패턴 모색 (예: §5-2 `.mcp.json` + `enabledMcpjsonServers` 조합).

---

### §B. §11-3 토글 측정 (3축 메트릭)

**배경**: `.claude/settings.json`의 `enabledMcpjsonServers` 배열이 (A) 컨텍스트 적재 자체를 차단하는지 vs (B) 호출만 차단하는지 분기 측정. 6차 사이클의 deferred-pool 발견으로 측정 메트릭이 *3축 조합*으로 재정의됨.

**선조건:**
- derived 프로젝트(이미 setup된 `dharness-probe-test`) 활용
- 해당 프로젝트의 sqlite MCP는 8차 사이클에 `local` 스코프 등록 → §11-3 측정에는 *`-s project` 등록*이 별도 필요

**실행:**
1. derived 프로젝트로 이동: `cd C:\Users\user01\dharness-probe-test`
2. `.mcp.json` 등록 (project scope):
   ```
   claude mcp remove sqlite        # local scope 등록 제거
   claude mcp add sqlite C:\Users\user01\AppData\Roaming\Python\Python312\Scripts\uvx.exe -- mcp-server-sqlite --db-path C:\Users\user01\dharness-probe-test\data\sample.db -s project
   ```
   → `<derived>/.mcp.json` 생성 확인
2.5. **🆕 12차 사이클 추가 — enable 키 2 위치 동기화 + B1 ground truth 캡처 (필수):**
   - `~/.claude.json`의 `projects.{<derived-abs>}.enabledMcpjsonServers`도 함께 갱신 (B1 측정 시 `["sqlite"]`, B2 측정 시 `[]`)
   - 새 세션 첫 user 메시지로 `system-reminder의 deferred tool 명단을 mcp__로 시작하는 것만 골라 그대로 보고해줘` 입력 → ground truth 캡처 (LLM 추정 응답이 아닌 system-reminder 원문)
   - B1.M2 = 0이면 — 추가 차단 mechanism 잔존. 즉시 진단 분기:
     - `<derived>` 첫 메시지로 `Bash로 claude --debug --version 또는 claude mcp list -s project 실행 결과 보고` (CLI 적재 로그 단서)
     - `~/.claude.json`에서 `disabledMcpjsonServers` / `enableAllProjectMcpServers` / `mcpServerApproved` 유사 키 grep
     - **즉시 우회**: `claude mcp add sqlite ... -s local`로 재등록 (의도와 분리된 별도 측정 행으로 박제)
3. `verify_11_3.md` 본문 1~4단계를 그대로 따름:
   - **1단계 (베이스라인 B1)**: `enabledMcpjsonServers` 키 없는 상태로 `claude` 실행 → 첫 user 메시지로 fixture가 지정한 3축 측정 입력
     ```
     다음 3가지를 알려줘:
     (1) 시스템 프롬프트에 등장하는 mcp__* 도구 이름의 총 개수
     (2) 첫 도구의 description 길이 (문자 수)
     (3) ToolSearch select:<name> 호출이 시스템 프롬프트에 명시된 사용법인지 (yes/no)
     ```
   - **2단계 (토글 OFF B2)**: 세션 종료 → `<derived>/.claude/settings.json`에 `{"enabledMcpjsonServers": []}` 추가 → 새 세션 → 동일 측정
   - **3단계 (분기 판정)**: B1 vs B2 비교 표를 fixture의 분기 표에 따라 채움
   - **4단계 (복원)**: `enabledMcpjsonServers` 키 제거
4. 결과 기록: `verify_11_3.md` "측정 로그" 표에 1행 + 본 README "결과 로그"에 1행

**예상 분기:**
- `B2.M2 == 0` AND `B2.M1 << B1.M1` → Layer A 진짜 효과 ✓ (settings.json 토글이 토큰 절감 채널)
- `B2.M2 == B1.M2` AND `B2.M1 ≈ B1.M1` → Layer A는 Layer C와 동급 (호출 게이트만, 토큰 무용) — §1 표 갱신 필요

---

### §C. cleanup (검증 완료 후)

§A·§B 모두 완료 후:

```powershell
# 1. derived 프로젝트의 sqlite MCP 등록 해제
cd C:\Users\user01\dharness-probe-test
claude mcp remove sqlite

# 2. probe fixture 파일 삭제 (production agent 풀에 잔존하지 않도록)
#    — _probe- prefix 또는 _fixtures/ 서브디렉토리 위치
Remove-Item -Force C:\Users\user01\dharness-probe-test\.claude\agents\_probe-*.md -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force C:\Users\user01\dharness-probe-test\.claude\agents\_fixtures -ErrorAction SilentlyContinue

# 3. derived 프로젝트 디렉토리 자체 삭제 (전체 cleanup인 경우)
cd C:\Users\user01
Remove-Item -Recurse -Force C:\Users\user01\dharness-probe-test

# 4. ~/.claude.json에서 stale projects 항목 자동 정리 확인
#    (claude CLI가 자동 cleanup 수행 — 수동 편집 불필요)
```

> **부분 cleanup (derived 프로젝트는 유지하고 probe만 제거):** Step 2만 실행. fixture 파일 위치를 `_probe-` prefix 또는 `_fixtures/` 서브디렉토리로 두면 production agent와 자동 분리됨 (`mcp-isolation-probe.agent.md` "사용 방법" 단락 권고 위치).

§11-2 contradiction이 §A로 해소되면 본 README의 "결과 로그" 마지막 행 §11-2 부정 결과 위에 ✓ 결과를 1행 더 추가하여 *contradiction 해소* 사실을 명시 (이전 행은 append-only 보존).
