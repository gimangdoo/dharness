# CLAUDE.md — dharness

## 저장소 구성

dharness는 두 구성요소로 이뤄진다:

1. **`harness` plugin** (`plugins/harness/`) — 도메인 한 문장 → 에이전트 팀 + 스킬 세트로 변환하는 메타 스킬 팩토리. 외부 install 대상.
   - `skills/harness/SKILL.md` — 메타 스킬 본체 (Phases 0-10)
   - `skills/harness/references/` — 설계 가이드 (permission-profiles, design-patterns 등)
   - `commands/harness-*.md` — `/harness:harness-*` 슬래시 커맨드 16종
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

CM의 SessionEnd가 자동으로 적재한 draft를 `/cm-claudemd-apply <sid> [사유...]`로 이 표에 삽입한다. 동작 흐름은 [`README.md` "CLAUDE.md 변경 이력 자동 회로"](./README.md#claudemd-변경-이력-자동-회로) 참조.

> **Archive doctrine (2026-05-13 정합):** commit `951b444` (2026-05-11 Phase 5-2 24차) **이전** 사이클 박제는 `archive/full-history` branch에 동결 보존(read-only). 이후 작업은 main + 본 표 단일 경로로 누적한다. 과거 "history branch에 cycle 디테일 적재 후 main에 pure 기능 분리" doctrine은 951b444 시점 이후 자연 소멸 — retroactive 복원 비용이 회수 가치를 초과해 폐기 결정(2026-05-13).

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-05-12 | plugin abstraction 디톡스 — host-agnostic 환원 (commit `93b362c`) | `plugins/harness/{SKILL.md, commands/harness-{adapt,mcp-{adopt,recommend,status}}.md}` + 신규 `.harness-host` marker + 신규 `plugins/harness/README.md` | plugin 외부 install user 환경에서 dead reference 4건 환원. host repo guard를 marker file로 추상화. plugin install user 단일 진입점 README 신설 (host-specific 콘텐츠 미포함). |
| 2026-05-13 | references/fixtures 디톡스 Pass 1-3 — host-agnostic 환원 (commit `6425b78`) | `plugins/harness/skills/harness/references/{orchestrator-template, mcp-recommendation, runtime-adaptation}.md` + `fixtures/{probe_filesystem.js, probe_chrome_devtools.js, probe_playwright.js, verify_phase10_derived_dogfood.md, README.md}` + `synthesis_example/` 8 files | 17 files / 33 hits 환원. 동작 가드("dharness self-host CM" → "host 측 self-host CM 운영 시"), example 분계 표현, fixture 사이클/세션 박제를 plugin install user에 정합한 표현으로 환원. probe_filesystem.js ALLOWED_DIR placeholder화. env var `CM_ADAPT_THRESHOLD_*` 코드 정합 동시 정정. |
| 2026-05-13 | permission-profiles.md 디톡스 sub-cycle — host-agnostic 환원 (commit `40fbcda`) | `plugins/harness/skills/harness/references/permission-profiles.md` 23 hits | doctrine 박제 영역 단독 처리. 인벤토리 표 메타 인용 3건, 합성 안전 룰, §10 적용 경계, atomic 분계 가드, §10-7 병렬 세션 doctrine, §11 fixture 경계를 plugin host (운영 시 self-host CM) 표현으로 환원. 박제 evidence(cycle 13/15/22/23차 empirical)는 전부 유지. 검증: `dharness self-host\|dharness root\|dharness 본` 인용 0 hits, test_schema 37/37 pass. |
| 2026-05-13 | README §1 settings.local.json template 박제 (commit `12a012f`) | `README.md` | 본 세션에서 settings.local.json 부재로 PostToolUse hook 미발화 → dharness_event 누적 0 영구 손실 발견. doctrine상 user-local(.gitignore)이라 clone 직후 부재 — 최초 1회 작성 template + py 사용 이유 + env 오버라이드 패턴 + `/cm-status` 검증 절차를 README §1에 명시. 동일 hook 미등록 재발 방지. |
| 2026-05-15 | reviewer risk batch + A6/M9/A7 doctrine + glob∩glob 정밀화 + P7-2/Q2 측정 회로 scaffold (commits `1fc3af0`~`4e1680f`) | `.claude/hooks/{session_start,cm_commands,post_tool_use,test_schema}.py` + `plugins/harness/scripts/{validate/{structure,schema,chain},poc/measure_dogfood,uplift/measure_session}.py` + `plugins/harness/skills/harness/{SKILL.md, references/{orchestrator-template,poc-dogfood-protocol,uplift-protocol}.md}` | reviewer 8 risk 결정적 회복 + agent name/cardinality/write-path-exclusivity 박제 + glob∩glob single-* analytical fallback + P7-2 EN POC 정적 56% reduction 측정 회로 + Q2 no-harness vs harness uplift baseline scaffold. tests 71/71 PASS, chain.py self-host 0 errors. |
| 2026-05-16 | P7-2 옵션 B dogfood runtime 측정 + doctrine 결정 박제 (B-b 채택) | `plugins/harness/skills/harness/SKILL.md` (L484 P7-2 박스 결정 line +2 LOC) + `_workspace/_telemetry/poc_dogfood_runtime.jsonl` (B-a/B-b 2 row) + plan §7-20 박제 | 사용자 dogfood 2 세션 실측 (B-a sid `70f972` raw 14540B quality=4 / B-b sid `af990d` raw 13123B quality=4). 정적 token ratio 0.5037 (agent-design-patterns) / 0.5763 (4-file agg) < 0.60 + 양 세션 quality ≥ 4.0 → 결정 gate 충족 → **옵션 B-b 채택 doctrine**. 실 swap 운영 적용은 별도 cycle (test_schema 2 invariant 재정의 동반). tests 74/74 PASS 유지. |
| 2026-05-16 | Q2 uplift baseline 옵션 A doctrine 박제 (측정 보류 + scaffold 유지) | `plugins/harness/skills/harness/SKILL.md` L498 Uplift line 결정 append + plan §7-21 박제 | 단발 페어 측정 = 모집단 1 (`uplift-protocol.md` L56 자체 인정) + dharness 외부 sandbox fixture 부재 + 10KB `tool_output_captured` threshold noise → 결정 게이트 즉시 적용 보류. `measure_session.py` + `uplift_sessions.jsonl` scaffold 유지 — 외부 sandbox 다중 fixture 누적 시 재진입. 본 plan **잔여 사용자 결정 0건 → 완전 closure**. tests 74/74 PASS 유지. |
| 2026-05-19 | grill-me 측정 결과 박제 — static scaffold + synthetic detection 100%, 실 effectiveness 보류 doctrine | `_workspace/_drafts/measure_grill_scaffold.py` (untracked, fixture 5 entry × 1 valid + 4 violation 패턴) | static 측정: `references/grilling-loop.md` 152 LOC / `commands/harness-grill.md` 65 LOC / chain.py grilling 함수 126 LOC / test_chain.py 6 case 100% PASS / phase coverage 4/4 / enum cardinality 13 (4 phase + 3 source + 6 required key). synthetic fixture 검출률 4/4 violation = 100%, false positive 0 (valid entry [0] 통과). **실 effectiveness 측정 보류 doctrine** — dharness self-host에 `_workspace/_baseline/` 부재 + 5-17~19 telemetry 파일 0 + `harness-grill` 실 호출 0. 재진입 조건: `meta.grilling_log[]` 누적 ≥5 entry OR `harness-grill` 세션 ≥3. Q2 uplift baseline doctrine (2026-05-16, 옵션 A 측정 보류) 동일 패턴 — 모집단 1 vs scaffold 결정성 trade-off에서 결정성 우선. |
| 2026-05-19 | mattpocock grill-me Phase B/C 흡수 — schema 정식 편입 + chain 검사 + P5/P9-1 doctrine + slash command + version 0.5.0 → 0.6.0 (commit `5ab1e12` 이후) | `references/intent-profile-schema.md` (meta.grilling_log[] schema + grilling_entry 구조 + §5 활용 row) + `scripts/validate/chain.py` (check_intent_profile_grilling_log + _extract_grilling_log_block + _parse_grilling_entries 함수 신설, 70+ LOC) + `scripts/validate/test_chain.py` (CheckIntentProfileGrillingLog 6 케이스, 21/21 PASS) + `SKILL.md` (Phase 5 cardinality 게이트 doctrine 5번 line 신규 + Phase 9-1 grilling 분기 박스 신규 + 7-4 트리거 카탈로그에 harness-grill 추가) + `commands/harness-grill.md` 신규 (~50 LOC, phase 인자 0.5/2/5/9 분기) + version bump | Phase A 흡수 완료 후 사용자 결정에 따라 즉시 진입. anti-premature-judgment doctrine 가드를 chain.py 결정적 검사로 박제 — recommended_source ∈ {signals>=2, section_3_1_direct, section_3_2_estimate} 외 시 schema 위반. `harness-grill` slash command가 P0.5/P2/P5/P9-1 명시 진입점 제공. cap 5 question + 자동 batch fallback 룰 그대로 유지. test 21/21 PASS, chain.py self-host 0 errors. dogfood 1-2 cycle 후 effectiveness 측정 예정. |
| 2026-05-19 | mattpocock grill-me Phase A 흡수 — Low confidence·필수 5필드 1차 거부 진입점 grilling 1q-at-a-time 패턴 + plugin version 0.4.0 → 0.5.0 | `plugins/harness/skills/harness/references/grilling-loop.md` 신규 (~150 LOC, 9 섹션 — 4 패턴/모드 분기/recommended answer guard/codebase fallback/cap 5/skip merge/Phase 진입점/`meta.grilling_log[]` 박제/검증 게이트) + `references/project-inquiry.md` §4-4-b 신설 + §6-3 grilling 포인터 + §7-1 wording 통일 (기본값 = recommended answer) + `SKILL.md` Phase 2 lazy-load 표 + Phase 2 entry 게이트 박스 doctrine line +1 + Phase 2 본문 reference 포인터 +1 + `.claude-plugin/marketplace.json` + `plugins/harness/.claude-plugin/plugin.json` version bump | mattpocock/skills `grill-me` 흡수 분석 결과 4 패턴 중 anti-premature-judgment doctrine 정합 영역만 Phase A 진입. Phase B/C (P5 cardinality grilling, P9-1 진화 grilling, `/harness:harness-grill` slash command)는 dogfood 1-2 cycle 후 결정. `meta.grilling_log[]` 옵션 필드 — `intent-profile-schema.md` schema 변경 0. chain.py `check_plugin_internal_references` 자동 검증으로 신규 reference dangling 0 확인. |
| 2026-05-16 | Tier A 5 lever 적용 — 합성 산출물 품질 향상 (Q2/Q12/Q5/Q11/Q3) + plugin version 0.2.0 → 0.3.0 | `plugins/harness/skills/harness/SKILL.md` (Phase 5 model 박제 갱신 + Phase 7-4.5 신설) + `references/permission-profiles.md` §5-1-c 신규 (model selection by role) + `scripts/validate/chain.py` 4 함수 신설 (check_agent_model_field/check_agent_tools_mcp_consistency/check_skill_description_overlap/check_skill_signal_coverage) + `scripts/validate/test_chain.py` 신규 (15 tests) + `.claude/hooks/_schema.py` migration silent swallow → stderr 로그 회복 + `.claude-plugin/marketplace.json` + `plugins/harness/.claude-plugin/plugin.json` version bump | 외부 검토 2건(referencefilesfordharness/1.md/2.md) + 자체 review 합성 — 필수성 판정 결과 16건 중 0건 필수, 사용자 의도(산출물 품질) 정합 lever 14건 검토. Tier A 6 lever 중 Q10(필수 섹션 검사)는 structure.py L32-39에 기 박제 redundant 판정 → drop, 5 lever 진행. derived 합성 시 frontmatter `model:` 강제 + tools↔mcpServers 정합 + skill description 트리거 명확성 + CLAUDE.md HOW 본문 draft 회로 추가. self-host chain.py PASS, test_chain 15/15 + test_schema 58/58. plan doc은 archive/full-history branch 단독 박제 (cycle detail 분리). |
| 2026-05-22 | 합성 산출물 회귀 평가 기반 plugin fix 9패치 (Stage 1 P0 + Stage 2 P1 + Stage 3 P2) — plugin version 0.7.0 → 0.8.0 | `plugins/harness/skills/harness/{SKILL.md, references/{agent-design-patterns, skill-writing-guide, orchestrator-template, runtime-adaptation}.md}` + `scripts/validate/{structure, chain}.py` + `scripts/validate/test_structure.py` 신규 + `scripts/validate/test_chain.py` + `commands/harness-validate.md` + `.claude-plugin/marketplace.json` + `plugins/harness/.claude-plugin/plugin.json` version bump | ko01-50 회귀 평가(`dharness-rating/PATCH_SCHEDULE.md`) 결과 반영. Stage 1 P0(FAIL 직결): PATCH-01 빈 스킬 금지 invariant / PATCH-02 인젝션 가드 본체 강제 / PATCH-03 harness-validate 결정적 검증(빈 스킬·인젝션 가드 정합). Stage 2 P1(CONDITIONAL 동인): PATCH-04 few-shot 예시 의무 / PATCH-05 명세 슬롯(스키마 버전·루프 방지·타임아웃) / PATCH-06 파일명 `SKILL.md` 대문자 고정·변종 검출. Stage 3 P2(품질): PATCH-07 telemetry 비코드 graceful(Phase 10-7) / PATCH-08 면책 고지 도메인 확장(재무·세무·의료·투자)·스킬 개수 흡수·분리 사유 / PATCH-09 팀 크기·검증 게이트 토폴로지 가이드. 검증 test 37/37 PASS (test_chain 30 + test_structure 7), chain self-host dangling 0. |

