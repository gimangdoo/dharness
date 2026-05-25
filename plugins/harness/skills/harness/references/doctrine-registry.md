> **Read at phase:** 도메인 무관 — (a) 신규 doctrine 박제 시 중복/충돌 점검, (b) 기존 doctrine 갱신 시 모든 hit 일관성 맞춤, (c) refit/audit 시 위반 영역 enumeration, (d) 새 contributor 온보딩 시 핵심 doctrine 인벤토리.

# Doctrine Registry

dharness 전 영역에 박제된 doctrine 단일 색인. SKILL.md + 22 reference + 17 command + chain.py + schema.py 분산 hit(~120건)를 id·이름·박제 위치·근거 commit·정합 점검 명령 표로 집계.

본 registry는 *catalog*이지 *doctrine 본문*이 아님 — 본문은 각 박제 위치를 단일 출처로 한다. 본 표는 *어느 doctrine이 어디 박제됐는가*를 추적할 뿐.

**박제 위치 표기:** `파일:section` (예: `SKILL.md:Phase 0.5` 또는 `phase-entry-gates.md:§Phase 0.5`).
**정합 점검 표기:** `chain.py:<fn>` (deterministic) / `LLM cross-review` (자동화 불가) / `manual` (사용자 게이트).

---

## §1. Workflow Gate doctrine (phase 진입 invariant)

phase 진입 직전 LLM이 따라야 할 행동 invariant. 결정적 강제 여부 표시.

| id | doctrine | 박제 위치 (단일 출처) | 박제 commit | 정합 점검 |
|---|---|---|---|---|
| W1 | Anti-premature-judgment (cwd/파일/`$ARGUMENTS` 단독 도메인 단정 금지, evidence 2조건) | `phase-entry-gates.md:§Phase 0.5` | 2026-05-15 사용자 요구 | `chain.py:check_intent_profile_grilling_log` (W1-grilling 영역만) / LLM cross-review (전 영역) |
| W2 | Phase 1 entry — 실 파일 read 강제 + `project_profile.md` 박제 (greenfield라도 stub) + silent skip 차단 | `phase-entry-gates.md:§Phase 1` | 2026-05-15 사용자 요구 | LLM cross-review |
| W3 | Phase 2 entry — 질문 폭격 + 필수 5필드 user_confirmed_fields raw 인용 + brownfield 4단계 + Grilling 분기 (5필드 정본: `schema.py:INTENT_REQUIRED`, doc 3곳 sync 결정적 강제) | `phase-entry-gates.md:§Phase 2`, `schema.py:INTENT_REQUIRED` | 2026-05-15 사용자 요구 / 2026-05-24 P12 deterministic 강제 / 2026-05-24 doc sync 확장 | `chain.py:check_required_user_confirmed_fields` (5필드 모두 user_confirmed_fields 등록 강제, prefix 매칭) + `chain.py:check_intent_required_doc_sync` (doc ↔ schema list drift 차단) / LLM (raw 인용 영역) |
| W4 | Phase 5 — Cardinality justification (4컬럼 표 + `single-use → inline` 룰 + 이름 유일성 사전 점검) | `phase-entry-gates.md:§Phase 5` | 2026-05-15 A6/M9 | `chain.py:check_orchestrator_agent_coverage` (dead agent FAIL) |
| W5 | Phase 0 — 중단된 factory run 감지 (`_baseline/`·`_critique_phase*` 박제 + agents/skills 빈 상태 시 재개 게이트) | `phase-entry-gates.md:§Phase 0` | 2026-05-21 mattpocock handoff | manual (Phase 0 entry) |
| W6 | Progressive disclosure (references lazy load — Phase 진입 시점에만 read, 무차별 prefetch 금지) | `SKILL.md:§참고` "Progressive disclosure doctrine" | 2026-05-14 M8 | LLM 행동 |
| W7 | Grilling 분기 (Phase 2 low confidence + Phase 9 모호 피드백 — 1q + recommended answer, recommendation 출처 anti-premature-judgment 정합) | `grilling-loop.md`, `phase-entry-gates.md:§Phase 2` step 5 | 2026-05-19 Phase B/C, mattpocock grill-me 흡수 | `chain.py:check_intent_profile_grilling_log` (source enum 강제) |
| W8 | methodology-advisor 위임 + adapter 변환 (workflow.methodology 모호 / 사용자 "추천해줘"·"모르겠음" 응답 시 → advisor sub-skill 호출 → handoff yaml fragment 수신 → dharness 측 단방향 adapter 변환(list→scalar primary lowercase / free source→enum advisor / 원본 source string→meta.advisor_handoff_version 보존 / list[1:]→meta.advisor_secondary_methodologies 보존) → intent_profile merge, 사용자 confirm 게이트 필수, advisor 1회 호출 = grilling cap 5 중 1 question 카운트) | `SKILL.md:§Phase 2 방법론 위임 doctrine`, `grilling-loop.md:§3-4`, `intent-profile-schema.md:§2 workflow`, `intent-profile-schema.md:§Advisor handoff 수신 시 변환 룰` | 2026-05-24 v0.12.0 doctrine + v0.12.1 adapter + v0.12.2 deterministic check (advisor v0.3.x handoff, contract drift dogfood 회복) | `chain.py:check_advisor_handoff_adapter_consistency` (v0.12.2 신설, 5 cross-field 룰 + methodology/source enum 결정적 검증) + manual (Phase 2 grilling 사용자 confirm) |
| W9 | intent_profile §8 필수 룰 + cross-field 결정적 검증 (cycle 4) — `version` 존재 / `project_type` enum / brownfield→`inferred_fields` 1+ / greenfield+`locked_in`≠[] 모순. cross-field 경고 3종(C15-1/2/3)은 LLM-only annotation으로 명시 (`meta.explicit_assumptions` 통과 허용) | `intent-profile-schema.md:§8`, `chain.py:check_intent_profile_*` | 2026-05-25 cycle 4 C14/C15 hybrid 정합 | `chain.py:check_intent_profile_version` + `chain.py:check_intent_profile_project_type` + `chain.py:check_intent_profile_brownfield_inferred` + `chain.py:check_intent_profile_greenfield_locked_in` + LLM (C15-1/2/3 annotation) |

## §2. 책임 분리 doctrine (LLM ↔ deterministic ↔ user-gate)

명령·기능별 역할 경계. 위반 시 silent drift 또는 책임 중복.

| id | doctrine | 박제 위치 | 박제 commit | 정합 점검 |
|---|---|---|---|---|
| R1 | audit ↔ validate 분리 (LLM·deterministic hybrid — audit는 추론, validate는 결정, adapt는 telemetry) | `harness-audit.md:§3개 명령 분리 doctrine`, `harness-validate.md:§audit ↔ validate 분리 doctrine` | 2026-05-13C, 2026-05-14 | manual (명령 호출자 책임) |
| R2 | 진화 명령 3분기 (`evolve` 수동 / `audit` 추론 / `adapt` 자동) | `harness-evolve.md:§진화 명령 3분기 doctrine`, `harness-adapt.md:§진화 명령 3분기 doctrine` | 2026-05-14 | manual |
| R3 | 사용자 확정 doctrine (도메인 단정·중요 합성 결정은 사용자 명시 confirm 후만) | `harness-new.md:§모드 분기`, `harness-remove.md:§사용자 확정`, `harness-merge.md`, `harness-split.md`, `harness-status.md`, `harness-validate.md` | 2026-05-14 | manual (각 명령 confirm gate) |
| R4 | 명령 분기 (README 표 — 변경 유형별 17 슬래시 커맨드 매핑) | `README.md:§명령 분기 doctrine` | 2026-05-14, 2026-05-23 v0.11.0 추가 | manual |
| R5 | P2 self-host (`chain.py`는 harness plugin 본체 내부 cross-reference만 검증 — derived 프로젝트 검증은 별도 산출) | `chain.py:check_plugin_internal_references` | 2026-05-15 | `chain.py` 본체 |
| R6 | doctrine-registry fn명 + 역색인 정합 ((a) registry 인용 `chain.py:<fn>` ↔ 실제 fn 존재 검증, (b) §1-5 module 인용 ↔ §6 inverse index 매핑 정합 — drift 영구 차단) | `doctrine-registry.md`, `chain.py:check_doctrine_registry_fn_refs`, `chain.py:check_doctrine_registry_inverse_index` | 2026-05-24 review patch + 2026-05-24 R6 확장 | `chain.py:check_doctrine_registry_fn_refs` + `chain.py:check_doctrine_registry_inverse_index` |

## §3. 합성·구조 doctrine (Phase 4·5·5-2·6·7 산출물 invariant)

에이전트·스킬·오케스트레이터 합성 시 강제 룰. 일부는 `chain.py` 결정적 검증.

| id | doctrine | 박제 위치 | 박제 commit | 정합 점검 |
|---|---|---|---|---|
| S1 | Sub-agent 격리 (P6-3) — Phase 1/5/6/8 합성을 N sub-agent 병렬, parent는 통합·합성만 담당 | `SKILL.md:§Phase 1·5·6·8` 박스 (4 hit) | 2026-05-14 P6-3 | LLM 행동 |
| S2 | Q1 Orchestrator agent coverage — 모든 agent는 오케스트레이터에서 1회 이상 참조 (dead agent FAIL) | `orchestrator-template.md:§Q1 doctrine` | 2026-05-15 Q1 | `chain.py:check_orchestrator_agent_coverage` |
| S3 | Q2 모델 선택 by role — frontmatter `model:` 필드는 *role 축*으로 결정 (`opus` 기본, read-only는 `sonnet`) | `permission-profiles-synthesis.md:§5-1-c` (P7 분리, 2026-05-23) | 2026-05-16 Q2 | `chain.py:check_agent_model_field` |
| S4 | Q3 CLAUDE.md HOW 본문 draft (코드 도메인 한정 권장, `project_profile.md`에서 추출 + 사용자 게이트) | `orchestrator-template.md:§CLAUDE.md HOW 본문 draft` | 2026-05-16 Q3 | manual (사용자 confirm gate) |
| S5 | A7 writes path 충돌 (agents/*.md `writes:` 경로 per-agent exclusivity) | `chain.py:check_agent_write_path_overlap` | 2026-05-15 A7 | `chain.py:check_agent_write_path_overlap` |
| S6 | N-C-1 입력 신뢰 경계 (외부 입력·부작용 도구 보유 agent ↔ 본문 `입력 신뢰 경계` 절 존재) | `agent-design-patterns.md:§입력 신뢰 경계`, `SKILL.md:§Phase 5` | 2026-05-14 N-C-1 | `chain.py:check_agent_injection_guard` |
| S7 | P6-4 inferred_fields source 인용 (모든 `inferred_fields` 항목 `source` 필드 보유 — 인용 0이면 schema 위반) | `intent-profile-schema.md`, `schema.py:find_inferred_fields_without_source` | 2026-05-14 P6-4 | `schema.py:find_inferred_fields_without_source` |
| S8 | 8 profile 분류 (P6-11) — 범용 4종(§2-1~§2-4 PoC 완료) + 도메인 4종(§2-5~§2-8 PoC 진행) | `permission-profiles.md:§2` | 2026-05-14 P6-11 | manual (분류 합성) |
| S9 | 도메인 4 신호 (P6-11) — ml-pipeline / devops-infra / mobile-native / data-eng signal 매핑 | `mcp-recommendation.md:§1 P6-11`, `trigger-keyword-catalog.md` | 2026-05-14 P6-11 | manual (signal 추출) |
| S10 | 합성 default 풀 (P6-9) — Phase 5-2 inline `mcpServers:` 자동 합성 시 ✓ 외 status는 금지 | `permission-profiles-inventory.md:§3-0 P6-9` (P7 분리, 2026-05-23) | 2026-05-14 P6-9 | manual (R-7 confirm gate) |
| S11 | catalog 확장 (trigger-keyword) — 새 signal·키워드 박제 시 `trigger-keyword-catalog.md`가 단일 출처 | `trigger-keyword-catalog.md:§5` | 2026-05-14 P6-8 | manual |
| S12 | P0-2 빈 스킬 금지 — 스킬 디렉토리 생성 = `SKILL.md` 본문까지 채워 박제 (디렉토리만/frontmatter만 금지) | `SKILL.md:§Phase 6`, `skill-writing-guide.md:§최소 본문 골격` | 2026-05-22 P0 | `structure.py:check_skills_dir` |
| S13 | output-checklist 인용 카운트 sync — `output-checklist.md` 본문 must/should `- [ ]` 항목 카운트 정본 ↔ 헤더·SKILL.md·harness-new.md 인용 박제 동기 (체크리스트 항목 추가/삭제 시 cross-doc drift 차단) | `output-checklist.md`, `SKILL.md:§Phase 8`, `harness-new.md` | 2026-05-25 cycle 1 stale count 정합 | `chain.py:check_output_checklist_count_sync` |
| S14 | 슬래시 커맨드 카탈로그 sync — `plugins/harness/commands/harness-*.md` glob count 정본 ↔ `README.md` `Slash command 카탈로그 (N개)` 헤더 ↔ `doctrine-registry.md` R4 본문 `N 슬래시 커맨드` 인용 (명령 추가/제거 시 cross-doc drift 차단, R4 manual → deterministic 격상) | `README.md:§Slash command 카탈로그`, `doctrine-registry.md:§2 R4` | 2026-05-25 cycle 1' command count 결정적 sync | `chain.py:check_command_count_sync` |

## §4. 보안·회수 doctrine (Phase 5-2 MCP·permission 합성)

권한 합성 시 강제 룰. 비가역 도구·외부 surface·자동 install 차단.

| id | doctrine | 박제 위치 | 박제 commit | 정합 점검 |
|---|---|---|---|---|
| P1 | default 권한 (per-profile) — dataset read `allow`, model write `ask`, 외부 hub fetch `ask`; production 변경 `ask`/`deny`; mobile signing/upload `ask`; db drop/truncate dry-run+confirm 2단 | `permission-profiles.md:§2-5/2-6/2-7/2-8` | 2026-05-14 P6-11 | manual (Phase 5-2 합성) |
| P2 | 회수 불가 명령 — `kubectl delete` / `terraform destroy` / `drop`·`truncate`·`delete` 등 비가역은 사전 dry-run gate 필수 (rollback 회수 불가) | `permission-profiles.md:§2-6, §2-8` | 2026-05-14 P6-11 | manual |
| P3 | mcp 출처 verify gate (R2) — 모든 MCP 후보 npm Author + GitHub org cross-check 필수 | `mcp-recommendation.md:§2 R2 doctrine`, `permission-profiles.md:§8-3` | 2026-05-14 P6-9 | manual (Phase 5-2 R-7 gate) |
| P4 | multi-writer 운영 (§10-7) — CM 자체 세션 병렬 시 단일 writer 강제 (host self-host 한정, 외부 install user는 단일 writer 권장만) | `permission-profiles-dynamic-adoption.md:§10-7` (P7 분리, 2026-05-23) | 2026-05-14 13차 cycle | manual |
| P5 | 자동 install 금지 — T0(무키·로컬) 한정으로 `allow` 자동 승급 가능, 외 T1+ 사용자 명시 confirm | `permission-profiles.md:§6 자동 install 금지 doctrine` | 2026-05-14 | manual |

## §5. 인프라·meta doctrine (CM·관측·refit 회로)

dharness 자체 진화 메커니즘. baseline 박제·drift 감지·refit 워크플로우.

| id | doctrine | 박제 위치 | 박제 commit | 정합 점검 |
|---|---|---|---|---|
| I1 | doctrine drift refit (v0.11.0) — plugin doctrine 업그레이드 후 기존 derived harness 끌어올리는 절차 (validate + audit 진단 → evolve/add-*/remove 수정) | `README.md:§Doctrine drift refit`, `chain.py:check_dharness_version_drift` | 2026-05-23 v0.11.0 (eba9d21) | `chain.py:check_dharness_version_drift` (info 1줄) |
| I2 | meta.dharness_version anchor — `intent_profile.md` frontmatter에 합성 시점 plugin version 박제 (refit 진단 t=0) | `intent-profile-schema.md`, `harness-new.md`, `harness-baseline.md`, `SKILL.md:§Phase 2` | 2026-05-23 doctrine drift refit 인프라 | `chain.py:check_dharness_version_drift` |
| I3 | P2-A 박제 — Phase entry gate 박스(Phase 0/0.5/1/2/5)를 `phase-entry-gates.md`로 분리 (SKILL.md ≤500 LOC cap 정합) | `phase-entry-gates.md` | 2026-05-23 P2-A (00177f0, c856629) | manual (LOC cap 미자동 검증, 향후 chain.py 함수 후보) |
| I4 | 상태 표기 — ✓/📜/⚠️ status 의미 단일 정의 (PoC 완료 / 후보 제안 / dynamic adoption 진입) | `team-tools-api.md:§0` | 2026-05-14 | manual |
| I5 | P1-1 AC 검증 — team-tools-api §9 — 본 reference는 P1-1 진행 중 ❓ inferred → ✅ verified로 격상, 의사코드 영역은 본 reference cross-link 유지 | `team-tools-api.md:§9` | 2026-05-14 P1-1 | manual |
| I6 | QA host-agnostic 환원 (P2-2) — `qa-agent-guide.md` §1~§5는 framework 무관 doctrine, §6은 도메인 카탈로그 (web-app/ML/data/mobile/devops) | `qa-agent-guide.md:§0 doctrine` | 2026-05-14 P2-2 | LLM (Phase 5 합성) |
| I7 | cycle 누적 (qa-agent-guide §6) — 새 버그 패턴 발견 시 §6에 행 추가 (닫힌 spec 아닌 누적 catalog) | `qa-agent-guide.md:§6 doctrine` | 2026-05-14 | manual |
| I8 | 합성 산출물 회귀 평가 — plugin 변경 후 `synthesis_example/` 4 fixture에 영향 회귀 평가 강제 | `_workspace/_plans/` 적용 cycle 산출 | 2026-05-19 a641b76 | manual (cycle별 plan 박제) |

---

## §6. 박제 위치 ↔ doctrine 역색인

새 contributor가 *파일을 read하다 doctrine 키워드를 만났을 때* 본 표로 어느 id인지 역추적.

| 파일 | 박제된 doctrine id |
|---|---|
| `SKILL.md` | W1·W2·W3·W4·W6·W8·S1·S12·S13 (포인터·박스) |
| `output-checklist.md` | S13 (must/should 정본 카운트) |
| `phase-entry-gates.md` | W1·W2·W3·W4·W5·W7 (본문) |
| `permission-profiles.md` (main) | S8·P1·P2·P5 |
| `permission-profiles-inventory.md` (P7 분리) | S10 (§3-0 합성 default 풀) |
| `permission-profiles-synthesis.md` (P7 분리) | S3 (§5-1-c Q2 model by role) |
| `permission-profiles-dynamic-adoption.md` (P7 분리) | P4 (§10-7 multi-writer) |
| `orchestrator-template.md` | S2·S4 |
| `agent-design-patterns.md` | S6 |
| `qa-agent-guide.md` | I6·I7 |
| `trigger-keyword-catalog.md` | S11 |
| `mcp-recommendation.md` | S9·P3 |
| `intent-profile-schema.md` | S7·I2·W8·W9 (§8 hybrid 정합 채널 표) |
| `grilling-loop.md` | W7·W8 |
| `team-tools-api.md` | I4·I5 |
| `skill-writing-guide.md` | S12 (최소 본문 골격) |
| `chain.py` | W1·W3·W4·W7·W8·W9·S2·S3·S5·S6·S13·S14·I1·I2·R5·R6 (결정적 검증) |
| `structure.py` | S12 (빈 스킬 디렉토리 검출) |
| `schema.py` | W3 (INTENT_REQUIRED 정본)·S7 |
| `harness-audit.md` | R1 |
| `harness-validate.md` | R1·R3·I1·I2 |
| `harness-evolve.md` / `harness-adapt.md` | R2 |
| `harness-new.md` / `remove.md` / `merge.md` / `split.md` / `status.md` | R3·W1·W4·S13 (`harness-new.md`만) |
| `README.md` | R4·I1·S14 |

---

## §7. 갱신 절차

새 doctrine 박제 또는 기존 doctrine 갱신 시:

1. **본 registry 먼저 read** — 중복/충돌 id 존재 여부 점검
2. 박제 위치를 §1~§5 중 적합한 axis에 행 1개 append (또는 기존 행 update)
3. 박제 위치 컬럼은 *단일 출처*만 — 동일 doctrine 다른 파일은 *pointer*로 처리
4. §6 역색인에 박제 위치 ↔ id 매핑 행 추가/업데이트
5. 정합 점검 가능하면 `chain.py`에 함수 추가 (deterministic 영역 확대)

doctrine *삭제* (deprecation) 시:

1. 박제 위치 본문에 `> **DEPRECATED <date> — 이유: ...**` 박제
2. 본 registry 행 삭제 *금지* — id 컬럼에 `~~Wx~~` strikethrough + 사유 행 유지 (역사 추적)
3. 모든 박제 위치의 pointer 갱신
