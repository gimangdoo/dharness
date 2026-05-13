# CLAUDE.md — dharness

## 저장소 구성

dharness는 두 구성요소로 이뤄진다:

1. **`harness` plugin** (`plugins/harness/`) — 도메인 한 문장 → 에이전트 팀 + 스킬 세트로 변환하는 메타 스킬 팩토리. 외부 install 대상.
   - `skills/harness/SKILL.md` — 메타 스킬 본체 (Phases 0-10)
   - `skills/harness/references/` — 설계 가이드 (permission-profiles, design-patterns 등)
   - `commands/harness-*.md` — `/harness:harness-*` 슬래시 커맨드 7종
2. **Context Manager** (root `.claude/` + `_workspace/`) — dharness 본 폴더 한정 self-host 런타임. 결정적 hooks 3종 + `/cm-*` 5 슬래시 커맨드 + `memory-search` 1 스킬. PostToolUse가 dharness 작업 단위(skill/agent/hook/command/manifest 변경)를 자동 분류해 누적하고, SessionEnd가 CLAUDE.md "변경 이력" 표 행 draft를 자동 적재. **dharness 본 폴더 영구 부속** — 외부 install 미지원.

- `.claude-plugin/marketplace.json` — `harness` plugin 단일 카탈로그

신규 사용자 단일 출처: [`README.md`](./README.md) + [`plugins/harness/skills/harness/SKILL.md`](./plugins/harness/skills/harness/SKILL.md).

---

## 하네스: context-management

**목표:** Claude Code 세션 간 컨텍스트 손실 해소, 도구 출력 캡처, 메모리 영속화.

**트리거:** context-management 관련 작업은 결정적 hooks가 자동 처리. 사용자 측 호출 채널은 `/cm-*` 5종 (status/sessions/reset/claudemd-apply/claudemd-discard). 과거 메모리 자연어 검색 시에만 LLM이 `memory-search` 스킬 규칙을 따른다.

**구성 산출물 (에이전트 0종 / 스킬 1종 / 훅 3종 / `/cm-*` 5종):** 상세 카탈로그·역할 표는 [`README.md` "Context Manager (dharness self-host)"](./README.md#context-manager-dharness-self-host) 섹션을 단일 출처로 본다. hooks는 `.claude/settings.local.json`이 직접 등록 — 외부 install 경로 없음.

---

## In-session 컨텍스트 가드라인

세션 *내부*의 토큰 부피는 워크플로우 선택으로 줄인다. CM은 사후 캡처·영속화에 집중하며 in-session 압축은 수행하지 않는다 — Claude Code의 자동 컨텍스트 압축·subagent 격리·도구별 truncation에 위임.

| 상황 | 권장 |
|------|------|
| 5+ 파일 cross-cutting 조사 | `Agent` (Explore/general-purpose) 위임 — 요약만 반환 |
| 큰 디렉토리 탐색 | `Glob`/`Grep` 우선 → 위치 확인 후 `Read` offset/limit |
| 큰 commit history | `git log -p` 대신 `git log --oneline` + 타겟 commit만 `git show` |
| 큰 diff | `git diff --stat` 우선 → 관심 영역만 `git diff -- <path>` |
| 같은 파일 반복 read | 한 번 읽고 conversation 내 재참조 — 재read는 mtime 변경 시만 |

이 룰은 LLM 행동 가이드일 뿐 hook이 강제하지 않는다 (사후 PostToolUse는 토큰을 줄이지 못함). 측정은 `_workspace/_telemetry/*.jsonl`의 `tool_output_captured` 이벤트(`raw_size`)로 가능.

---

## 변경 이력

CM의 SessionEnd가 자동으로 적재한 draft를 `/cm-claudemd-apply <sid> [사유...]`로 이 표에 삽입한다. 동작 흐름은 [`README.md` "CLAUDE.md 변경 이력 자동 회로"](./README.md#claudemd-변경-이력-자동-회로) 참조. 과거 누적 기록(2026-05 Phase 5-2 24 cycles)은 `archive/full-history` branch에 보존.

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-05-12 | plugin abstraction 디톡스 — host-agnostic 환원 (commit `93b362c`) | `plugins/harness/{SKILL.md, commands/harness-{adapt,mcp-{adopt,recommend,status}}.md}` + 신규 `.harness-host` marker + 신규 `plugins/harness/README.md` | plugin 외부 install user 환경에서 dead reference 4건 환원. host repo guard를 marker file로 추상화. plugin install user 단일 진입점 README 신설 (host-specific 콘텐츠 미포함). |
| 2026-05-13 | references/fixtures 디톡스 Pass 1-3 — host-agnostic 환원 (commit `6425b78`) | `plugins/harness/skills/harness/references/{orchestrator-template, mcp-recommendation, runtime-adaptation}.md` + `fixtures/{probe_filesystem.js, probe_chrome_devtools.js, probe_playwright.js, verify_phase10_derived_dogfood.md, README.md}` + `synthesis_example/` 8 files | 17 files / 33 hits 환원. 동작 가드("dharness self-host CM" → "host 측 self-host CM 운영 시"), example 분계 표현, fixture 사이클/세션 박제를 plugin install user에 정합한 표현으로 환원. probe_filesystem.js ALLOWED_DIR placeholder화. env var `CM_ADAPT_THRESHOLD_*` 코드 정합 동시 정정. |
| 2026-05-13 | permission-profiles.md 디톡스 sub-cycle — host-agnostic 환원 (commit `40fbcda`) | `plugins/harness/skills/harness/references/permission-profiles.md` 23 hits | doctrine 박제 영역 단독 처리. 인벤토리 표 메타 인용 3건, 합성 안전 룰, §10 적용 경계, atomic 분계 가드, §10-7 병렬 세션 doctrine, §11 fixture 경계를 plugin host (운영 시 self-host CM) 표현으로 환원. 박제 evidence(cycle 13/15/22/23차 empirical)는 전부 유지. 검증: `dharness self-host\|dharness root\|dharness 본` 인용 0 hits, test_schema 37/37 pass. |
| 2026-05-13 | README §1 settings.local.json template 박제 (commit `12a012f`) | `README.md` | 본 세션에서 settings.local.json 부재로 PostToolUse hook 미발화 → dharness_event 누적 0 영구 손실 발견. doctrine상 user-local(.gitignore)이라 clone 직후 부재 — 최초 1회 작성 template + py 사용 이유 + env 오버라이드 패턴 + `/cm-status` 검증 절차를 README §1에 명시. 동일 hook 미등록 재발 방지. |

