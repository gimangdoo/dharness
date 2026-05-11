# CLAUDE.md — dharness

## 이 저장소에 대해

**dharness**는 외부 install 가능한 plugin 1종 + dharness 본 폴더 한정 self-host CM으로 구성된다 (단계 A 이후).
- `plugins/harness/` — `harness` plugin: 메타 스킬 팩토리 (Phases 0-10), 외부 install 대상
  - `skills/harness/SKILL.md` — 메타 스킬 본체
  - `skills/harness/references/` — 설계 가이드 문서
  - `commands/harness-*.md` — `/harness:harness-*` 슬래시 커맨드 7종
- `.claude/` (root, self-host CM): dharness 자체의 진화 기록자. 외부 install 미지원.
  - `hooks/` — 3종 lifecycle 훅 (SessionStart/PostToolUse/SessionEnd) + `_schema.py` (DDL 단일 진실 원천, REPO_ROOT 결정적 계산) + `cm_commands.py` (결정적 커맨드 핸들러)
  - `commands/cm-*.md` — `/cm-*` 슬래시 커맨드 5종 (status/sessions/reset/claudemd-apply/claudemd-discard)
  - `skills/memory-search/` — 1종 (LLM이 자연어 메모리 검색 시 따르는 3-tool progressive disclosure 규칙)
  - `settings.local.json` — hooks 등록 (gitignore이라 사용자 로컬)
- `.claude-plugin/marketplace.json` — `harness` plugin 단일 카탈로그
- `_workspace/` — DATA (dharness root 고정 — `${CLAUDE_PROJECT_DIR}` 분기 / projects.json / walk-up fallback 폐지)

---

## 하네스: context-management

**목표:** Claude Code 세션 간 컨텍스트 손실 해소, 도구 출력 캡처, 메모리 영속화

**트리거:** context-management 관련 작업은 결정적 hooks가 자동 처리. 사용자 측 호출 채널은 `/cm-*` 5종 (status/sessions/reset/claudemd-apply/claudemd-discard). 과거 메모리 자연어 검색 시에만 LLM이 `memory-search` 스킬 규칙을 따른다.

**구성 산출물 카탈로그(에이전트 0종 / 스킬 1종 / 훅 3종 / `/cm-*` 5종):** 본 파일은 포인터만 유지한다 — 상세 카탈로그·역할 표는 [`README.md` "Context Manager (dharness self-host — 결정적 모델)"](./README.md#context-manager-dharness-self-host--결정적-모델) 섹션을 단일 출처로 본다. hooks는 `.claude/settings.local.json`이 직접 등록 — 외부 install 경로 없음 (단계 A 이후).

---

## In-session 컨텍스트 가드라인

세션 *내부*의 토큰 부피는 워크플로우 선택으로 줄인다. CM은 사후 캡처·영속화에 집중하며 in-session 압축은 수행하지 않는다 — Claude Code의 자동 컨텍스트 압축·subagent 격리·도구별 truncation에 위임한다.

| 상황 | 권장 |
|------|------|
| 5+ 파일 cross-cutting 조사 | `Agent` (Explore/general-purpose) 위임 — 본문은 부모 컨텍스트로 새지 않고 요약만 반환 |
| 큰 디렉토리 탐색 | `Glob`/`Grep` 우선 → 위치 확인 후 `Read` offset/limit으로 필요한 부분만 |
| 큰 commit history | `git log -p` 대신 `git log --oneline` + 타겟 commit만 `git show` |
| 큰 diff | `git diff --stat` 우선 → 관심 영역만 `git diff -- <path>` |
| 같은 파일 반복 read | 한 번 읽고 conversation 내 재참조 — 재read는 mtime이 바뀐 경우만 |

이 룰은 LLM 행동 가이드일 뿐 hook이 강제하지 않는다 (사후 PostToolUse는 토큰을 줄이지 못함). 측정은 `_workspace/_telemetry/*.jsonl`의 `tool_output_captured` 이벤트(`raw_size`)로 가능.

**변경 이력:**

> **현재 아키텍처는 단계 A 이후 단순화된 형태입니다** — `harness` plugin (외부 install) + dharness self-host CM (root `.claude/` + `_workspace/`, 결정적 hook 3 + skill 1 + commands 5). 신규 사용자는 [`README.md`](./README.md)와 [`plugins/harness/skills/harness/SKILL.md`](./plugins/harness/skills/harness/SKILL.md)를 단일 출처로 보세요. 본 표는 **최근 활동 행만** 유지 — 폐기된 산출물(cm-harness plugin / Phase 10 / cm-orchestrator·curator·digester / dashboard worker / daily\_summary 자동 생성 / tool-output-compress) 포함 *어떻게 여기까지 왔는가* 회고는 [`CHANGES_ARCHIVE.md`](./CHANGES_ARCHIVE.md) (27행, 2026-05-09 ~ 2026-05-10 Phase 5-2 7차).

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-05-10 | dharness_event 자동 draft — harness_reference_edit:32 / harness_skill_edit:3 / harness_command_edit:2 / git_add:2 / git_commit:2 / cm_hook_edit:1 / harness_other_edit:1 / git_push:1 | `.claude/hooks/session_end.py`, `plugins/harness/skills/harness/references/permission-profiles.md`, `plugins/harness/skills/harness/references/fixtures/README.md`, `plugins/harness/skills/harness/SKILL.md`, `plugins/harness/commands/harness-mcp-adopt.md`, `plugins/harness/commands/harness-mcp-status.md`, `plugins/harness/skills/harness/references/fixtures/synthesis_example/settings.json`, `plugins/harness/skills/harness/references/fixtures/synthesis_example/README.md` (+3 more) | Phase 5-2 cycles 2-9 누적 — §10 dynamic adoption + §11 fixtures 4종 + harness-mcp-adopt/status 한 쌍 + synthesis_example/data-analyst + §11-2 schema RESOLUTION (list-of-dicts + type:stdio) + §11-3 3축 메트릭 박제 |
| 2026-05-10 | dharness_event 자동 draft — harness_command_edit:4 / harness_reference_edit:3 / harness_skill_edit:1 | `plugins/harness/commands/harness-mcp-status.md`, `plugins/harness/skills/harness/references/permission-profiles.md`, `plugins/harness/skills/harness/references/fixtures/README.md`, `plugins/harness/skills/harness/SKILL.md`, `plugins/harness/commands/harness-add-agent.md` | Phase 5-2 cycle 11 — 10차 P0 새 발견(tools allowlist는 inline 서버 도구 통제에 무력)을 harness-mcp-status §2/§4 진단 룰 + harness-add-agent cross-link에 박제 |
| 2026-05-11 | dharness_event 자동 draft — harness_reference_edit:10 / git_add:4 / git_mv:2 / git_commit:1 / harness_other_edit:1 / harness_skill_edit:1 | `plugins/harness/skills/harness/references/permission-profiles.md`, `plugins/harness/skills/harness/references/fixtures/synthesis_example/README.md`, `plugins/harness/skills/harness/references/fixtures/synthesis_example/web-research/web-research.agent.md`, `plugins/harness/skills/harness/references/fixtures/synthesis_example/web-research/settings.json`, `plugins/harness/skills/harness/references/fixtures/synthesis_example/web-research/CLAUDE_md_row.md`, `plugins/harness/skills/harness/references/fixtures/synthesis_example/web-research/README.md`, `plugins/harness/skills/harness/references/fixtures/synthesis_example/data-analyst/data-analyst.agent.md`, `plugins/harness/skills/harness/references/fixtures/synthesis_example/data-analyst/README.md` (+2 more) | Phase 5-2 14차 P2 1차 종합 보고 — synthesis_example/ 서브디렉토리화 (data-analyst 단일 inline + web-research 멀티 inline fetch+memory 평행 비교) + §3-1 매트릭스 cross-link |
| 2026-05-11 | dharness_event 자동 draft — harness_reference_edit:14 / cm_hook_edit:9 / cm_schema_edit:1 / git_add:1 / git_push:1 | `plugins/harness/skills/harness/references/fixtures/verify_11_3.md`, `plugins/harness/skills/harness/references/permission-profiles.md`, `plugins/harness/skills/harness/references/fixtures/README.md`, `.claude/hooks/_transcript_utils.py`, `.claude/hooks/session_end.py`, `.claude/hooks/session_start.py`, `.claude/hooks/_schema.py`, `.claude/hooks/post_tool_use.py` (+2 more) | CM minor 정합 픽스 8건 (_schema/post_tool_use/cm_commands/session_end/session_start 정리 + _transcript_utils.py 신설 + test_schema.py 단위 테스트) + Phase 5-2 §11-3 측정 환경 함정 박제 (4 gate 표 + 외부 액션 카드) |
| 2026-05-11 | dharness_event 자동 draft — harness_reference_edit:7 / git_add:2 / git_commit:2 / readme_edit:2 / harness_other_edit:1 / harness_skill_edit:1 | `plugins/harness/skills/harness/references/fixtures/probe_firecrawl.js`, `README.md`, `plugins/harness/skills/harness/references/permission-profiles.md`, `plugins/harness/skills/harness/SKILL.md`, `plugins/harness/skills/harness/references/fixtures/README.md` | Phase 5-2 18차+19차 사이클 — T1+ probe fixture 5종(brave/tavily/exa/github/firecrawl) 신설(JSON-RPC stdio 핑 + env 키 + deprecated 자동 태깅) + §3/§8-2/SKILL.md cross-link 박제 (병렬 세션 commit 분담 — README.md 영역 회피) |
