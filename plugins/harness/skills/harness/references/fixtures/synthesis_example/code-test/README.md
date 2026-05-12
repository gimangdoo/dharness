# Phase 5-2 + §10 합성 산출물 구체 예시 — `code-test` 시나리오

§5 합성 템플릿이 §10 Step 5의 4 산출물로 결합되는 정합 결과 1세트. **세 번째 시나리오** — `data-analyst` 단일 MCP 패턴, `web-research` npx 기반 멀티 inline 패턴에 이어 *uvx + npx 혼합 멀티 inline 패턴*을 박제. 외부 도입자가 자신의 도메인으로 매핑할 때 *형태 참고*.

> ✅ **박제 근거** — filesystem(14종 ✓ — 14차 사이클 P2 T0 batch) + git(12종 ✓ — 3차 사이클 git MCP install + JSON-RPC enum) 두 MCP 모두 [§3 인벤토리](../../../permission-profiles.md#3-mcp-후보-인벤토리-tier-분류)에 검증 완료 박제. [§3-1 매트릭스](../../../permission-profiles.md#3-1-검증-완료-t0-mcp--capability-profile-매트릭스-14차-사이클-p2-1차-종합-보고)의 `code-test` profile 권고 조합.

## 시나리오

**가상 derived 프로젝트:** "중간 규모 codebase의 코드 review + commit 어시스턴트 — 사용자 질의에 따라 코드 read·search + git diff/log/show + 안전한 add/commit 워크플로우. destructive 작업(git_reset)은 차단, write 계열은 사용자 ask 게이트."

**자동 합성 결과:**
- 에이전트 `code-explorer` 1명 (capability profile = `code-test`)
- 매핑 MCP: `filesystem` (T0, 14 도구 — read 10 + write 4) + `git` (T0, 12 도구 — read 7 + write 5)
- 패턴: **inline `mcpServers:` 멀티 등재 (uvx + npx 혼합)** (§5-1 권장 — Layer B subagent 격리, parent 컨텍스트 미적재)

## 산출물 4종 (§10 Step 5 = "Reflect")

| 산출물 | 파일 | 위치(derived 프로젝트 기준) | 비고 |
|--------|------|---------------------------|------|
| (a) 카탈로그 footnote | (메타) | `plugins/harness/skills/harness/references/permission-profiles.md` §3 filesystem/git 행 | §3-1 매트릭스 `code-test` 행과 동시 갱신 |
| (b) 에이전트 정의 | [`code-explorer.agent.md`](./code-explorer.agent.md) | `.claude/agents/code-explorer.md` | inline `mcpServers:` 멀티 패턴 (filesystem npx + git uvx) |
| (c) 권한 게이트 | [`settings.json`](./settings.json) | `.claude/settings.json` | filesystem 14종(read 10 allow / write 4 ask) + git 12종(read 7 allow / write 4 ask / git_reset 1 deny) |
| (d) 변경 이력 1행 | [`CLAUDE_md_row.md`](./CLAUDE_md_row.md) | derived 프로젝트의 `CLAUDE.md` "변경 이력" 표 | 멀티 inline 표기 ("MCP 채택: filesystem + git") |

## 관찰 포인트

1. **uvx + npx 혼합 멀티 inline 패턴** — 본 예시는 `filesystem`(npx) + `git`(uvx 절대경로)을 같은 `mcpServers:` list에 박음. **PATH 가용성 차이**: npx는 Node.js install 시 자동 PATH 등록, uvx는 pip user-install이라 PATH 수동 추가 필요 → uvx-기반은 절대경로 placeholder 필수. `web-research`(npx 단일)의 placeholder 0개 vs 본 예시 2개 차이가 이 함의의 박제.

2. **권한 bucket 분포 — destructive 차단의 정밀화** — git MCP write 5종 중 `git_reset`만 deny, 나머지 4종(`add`/`commit`/`create_branch`/`checkout`)은 ask. **이유**: `git_reset --hard`는 working tree 손실 surface로 *복구 불가에 가까운* 영구 작업, 다른 4종은 모두 reflog로 복구 가능. 정밀 차단으로 워크플로우 유연성 + 안전성 양립. filesystem write 4종은 모두 ask — `write_file`/`edit_file`은 *기존 파일 덮어쓰기*에 작동하지만 git tracked 파일은 `git checkout`으로 복원 가능하므로 deny까지는 과한 차단.

3. **빌트인 도구와의 분리** — 본 에이전트는 빌트인 `Write`/`Edit`을 `tools:` allowlist에 *포함하지 않음*. 모든 write는 `mcp__filesystem__write_file`/`edit_file`을 거치므로 *Layer C `permissions.ask`로 일관 게이팅*. 빌트인 `Read`/`Grep`은 path-roots 격리가 없어 보조 read는 가능하나, *코드베이스 내부 탐색*은 filesystem MCP 우선 권고 (감사 로그 일관성).

4. **mid-session 운영 함의** — 두 MCP 모두 inline 패턴이라 `claude mcp add` 등록 자체 생략. 그래도 합성 직후 *현재 세션*에서는 도구 풀에 미적재 (4차 cycle empirical — inline 등록도 spawn 시점에야 connect). 사용자에게 "다음 세션부터 사용 가능" 안내 필수.

5. **N-MCP 시 권한 매트릭스 폭증** — 본 시나리오는 26 도구 권한 분포. `web-research`(13) + `data-analyst`(6)에 비해 약 2~4배. **운영 권고**: derived 프로젝트의 settings.json은 *capability profile별 분리 파일*(`.claude/settings.code-test.json`) 패턴이 가능하면 유지보수 우위. 단 Claude Code의 settings.json은 단일 파일이 default — 본 예시는 `.allow`/`.ask`/`.deny` 카테고리만 분리.

## 적용 경계

- 본 예시는 *derived 프로젝트* 대상. dharness root에는 적용하지 않음 (§10/§11 분계 — dharness root의 git 작업은 본체 self-host CM이 deterministic 분류기로 다루며, 별도 에이전트 채널 미도입).
- "code-explorer"는 가상 이름 — 실제 도메인에 맞게 이름·도메인 specific 책임을 교체. **예시 변형**: `react-reviewer` (filesystem ALLOWED_DIR = `src/components/`) / `db-migration-helper` (filesystem + git + sqlite 트리플 결합) / `monorepo-navigator` (filesystem ALLOWED_DIR = 모노레포 루트).
- *uvx + npx 혼합 패턴*의 형태 참고 — `reasoning-aux` profile의 `sequential-thinking`(npx) + `time`(uvx) 결합도 동일 패턴.

## 사용 흐름

1. `code-test/` 디렉토리 전체를 *derived 프로젝트*로 복사 후 다음 매핑:
   - `code-explorer.agent.md` → `<derived>/.claude/agents/code-explorer.md`
   - `settings.json` → `<derived>/.claude/settings.json` (기존 키와 deep merge — 덮어쓰지 말 것)
   - `CLAUDE_md_row.md`의 한 행 → `<derived>/CLAUDE.md` "변경 이력" 표 끝에 추가
2. **placeholder 치환** (`code-explorer.agent.md` 본문 끝 표 참조):
   - `<ABS_PROJECT_DIR>` → derived 프로젝트 루트 절대경로 (예: `C:\Users\<user>\myproject`)
   - `<UVX_ABS_PATH>` → `uvx` 실행 파일 절대경로 (`where uvx` 또는 `which uvx`로 확인)
3. **`claude mcp add`는 생략 가능** — inline `mcpServers:` 패턴은 spawn 시 connect되므로 parent 등록 불요 (§5-1 권장).
4. 세션 재시작 후 `Agent` tool로 `subagent_type: "code-explorer"` spawn 검증. 첫 spawn 시 subagent의 도구 풀에 `mcp__filesystem__*` 14종 + `mcp__git__*` 12종 노출 확인 (parent ToolSearch에는 미노출 = 10차 cycle P0 양면 검증과 동일).

## 권한 모델 정합 매트릭스 (참고)

| 도구 | bucket | 사유 |
|---|---|---|
| `mcp__filesystem__read_file` ~ `read_multiple_files` (3종) | allow | read-only, path-bounded |
| `mcp__filesystem__list_directory*` / `directory_tree` / `search_files` / `get_file_info` / `list_allowed_directories` (6종) | allow | 메타데이터 read, 부수 효과 0 |
| `mcp__filesystem__read_media_file` (1종) | allow | binary read, 부수 효과 0 |
| `mcp__filesystem__write_file` / `edit_file` / `create_directory` / `move_file` (4종) | ask | tracked 파일 덮어쓰기 가능 — git checkout으로 복원 가능하나 사용자 확인 |
| `mcp__git__git_status` / `diff` / `diff_staged` / `diff_unstaged` / `log` / `show` / `branch` (7종) | allow | git read, 부수 효과 0 |
| `mcp__git__git_add` / `commit` / `create_branch` / `checkout` (4종) | ask | 작업 트리/스테이지/HEAD 변경 — reflog로 복구 가능하나 사용자 확인 |
| `mcp__git__git_reset` (1종) | deny | working tree 손실 surface — 실수 ask confirm 시 영구 손실 |

> **bucket 변경 시 양면 갱신:** 위 표를 갱신하면 동 디렉토리의 `settings.json` `permissions.{allow,ask,deny}` + `CLAUDE_md_row.md` 비고 컬럼 카운트도 동시 정합 — drift 시 외부 도입자가 한 세트 복사 후 어긋남.

> 본 파일은 `plugins/harness/skills/harness/references/fixtures/synthesis_example/code-test/`의 박제 예시. 본 시나리오는 `synthesis_example/README.md` 카탈로그에 *세 번째 행*으로 등재 권고 (다음 통합 박제 시).
