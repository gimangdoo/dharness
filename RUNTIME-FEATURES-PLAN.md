# Runtime Features Plan — dharness 5 기능 구축

> **작성 2026-05-30.** 세션 시작 시 사용자가 요구한 5 기능 중 미구축분을 *순차 실행* 하기 위한 단일 출처 plan. compact 생존용 — 각 Phase는 goal / deliverable / verify / done 기준을 독립 보유한다. 재개 시 본 문서의 "진행 상태" 표에서 다음 Phase를 찾아 그대로 이어간다.

---

## 0. 배경 — 왜 이 plan인가

dharness `harness` 플러그인 = **빌드타임 메타 팩토리** (Phase 0-10). 도메인 한 문장 → 에이전트 팀 *생성*. 하네스를 *만들* 뿐 프로젝트 작업을 *실행* 하지 않는다. 사용자 5 기능 중:

| # | 기능 | 막힘 지점 |
|---|---|---|
| 1 | brownfield 소규모 작업 선택적 작동 (규모 판단 → 도구 생성/사용 결정) | 런타임 레이어 부재 |
| 2 | per-task 전체 plan + atomic 분해 + todo | 런타임 레이어 부재 |
| 3 | methodology-advisor 산출물 생성 | 빌드타임 methodology 선택만 존재, 런타임 생성 부재 |
| 4 | 진행 중 신규 기능 grillme 재질문 | **`harness-feature`로 부분 충족 (2026-05-30)** |
| 5 | [CORE] wiki/harness 공명 (pull/push·trend·benchmark·양방향 진화) | plugin↔wiki 다리 레이어 부재 |

**근본 원인:** 1·2·3은 *런타임 레이어* 부재, 5는 *wiki 다리 레이어* 부재. 본 plan이 이 두 레이어를 단계적으로 구축한다.

---

## 1. 확정 아키텍처 결정 (lock)

| 결정 | 값 | 근거 |
|---|---|---|
| **런타임 레이어 위치** | **합성 산출물에 굽기** — dharness가 만드는 오케스트레이터/스킬 본문에 runtime gate 블록을 *주입*. dharness 자체는 빌드타임 팩토리로 유지. | 사용자 확정 2026-05-30. 별도 런타임 command/플러그인 신설 회피 → command 7 유지, 관심사 일관. |
| **구축 순서** | 기초(P0) → #1(P1) → #2(P2) → #3(P3) → #5 wiki(P4) | 사용자 확정. 의존성 순방향 — 런타임 골격이 1·2·3의 토대, wiki는 산출물이 풍부해진 뒤 양방향. |
| **구현 표면** | 신규 reference + Phase 5/6/7 합성 워크플로우 hook + 결정적 검증 회로 + output-checklist 항목 + doctrine-registry 등재 + fixture 회귀 | dharness 자기 doctrine 정합 (단일 출처·결정적 강제·박제 추적). |

**중요 제약 (phase count):** runtime gate를 SKILL.md 새 `### Phase` 헤더로 만들면 **S16 phase-count sync** 발화 → 4 ad 위치(marketplace.json/plugin.json/plugin README/루트 README) 광고 갱신 필수. **→ 권장: runtime gate는 기존 Phase 7 오케스트레이션의 sub-step으로 둔다 (phase count 불변).** 새 Phase 신설이 불가피하면 4 ad 위치 동시 갱신.

---

## 2. 진행 상태 (재개 지점)

| Phase | 기능 | 상태 | 산출물 |
|---|---|---|---|
| **P0** | 런타임 레이어 기초 | ✅ 완료(green) | `references/runtime-execution.md` 골격 + orchestrator-template 주입점 + `chain.py:check_runtime_gate_block` (S17) + output-checklist must(8→9) + doctrine-registry S17 — chain PASS·smoke 8/8·test_chain 159 |
| **P1** | #1 brownfield 규모 선택적 작동 | ✅ 완료(green) | runtime-execution §2 G1 규모분류(small/medium/large + 신호 + 분기 + 경계 confirm + worked example) + 게이트 inline self-contained + check G1/G2/G3 완전성 확장 — chain PASS·smoke 8/8·test_chain 160 |
| **P2** | #2 plan+todo 분해 | ✅ 완료(green) | runtime-execution §3 G2 plan분해(plan→atomic task→`TodoWrite` todo + 규모별 적용 + worked example) + 게이트 G2 sub-section inline self-contained(§1·§5) + SKILL 7-6/output-checklist wording — chain PASS·smoke 8/8·test_chain 160 |
| **P3** | #3 advisor 산출물 생성 | ✅ 완료(green) | runtime-execution §4 G3(methodology 11종→task당 deliverable 형태·순서 매핑 + 적용 규약 + worked example) + 게이트 G3 sub-section inline self-contained(§1·§5, 게이트 완성) + advisor-integration §3 런타임 확장 cross-ref + SKILL 7-6/output-checklist wording — chain PASS·smoke 8/8·test_chain 160 |
| **P4** | #5 wiki 양방향 다리 [CORE] | ⬜ | `references/wiki-bridge.md` + M1/M4/M5 + schema gate + fixture |

상태 범례: ⬜ 미착수 · 🔶 진행 중 · ✅ 완료(chain green).

---

## 3. Phase 상세

각 Phase 공통 **done 템플릿** (dharness 자기 doctrine 정합 — 매 Phase 끝 전부 충족):

1. **단일 출처 reference 박제** — 신규/확장 reference에 doctrine 본문 1곳만.
2. **합성 워크플로우 hook** — Phase 5/6/7 중 적합 지점에서 본 reference를 read하고 산출물에 주입하도록 SKILL.md 박스 추가.
3. **결정적 검증 회로** — `chain*.py`에 신규 함수: 합성된 산출물(derived 한정)에 runtime gate 블록 존재/형식 확인. self-host(plugin-only) repo에선 silent skip.
4. **output-checklist 항목** — must/should 추가 시 **S13 count sync** (output-checklist.md 정본 + 헤더 + SKILL.md + harness-new.md 인용 동기).
5. **doctrine-registry 등재** — §1-5 적합 axis에 행 + §6 역색인 + (fn 추가 시) `chain*.py:<fn>` 인용. **R6 fn-ref/inverse-index 정합 필수.**
6. **fixture 회귀** — `references/fixtures/synthesis_example/` 4 fixture에 영향 회귀 평가 (I8 doctrine). 신규 게이트는 1 fixture에 주입 시연.
7. **chain 전체 green** — `py -3 chain.py` PASS + smoke 8/8 + lint/chain_intent/chain_advisor exit 0. **pre-existing structure/schema FAIL(memory-search 워크플로우 섹션·`_workspace/_baseline` 미존재)은 무관 — 건드리지 않음.**

### P0 — 런타임 레이어 기초

- **goal:** 합성 산출물이 런타임에 따르는 의사결정 *스캐폴드* 박제. 3 게이트(규모분류/plan분해/산출물생성)의 공통 틀 + 주입 메커니즘 + 검증.
- **deliverable:**
  - `references/runtime-execution.md` — 런타임 게이트 doctrine 단일 출처. §0 개요 + §게이트 주입 규약 (오케스트레이터 본문 어느 위치에, 어떤 마커로). P1-P3 본문은 후속 Phase가 채운다.
  - `orchestrator-template.md` — "Runtime Gate" 주입점 정의 (Phase 7-4 산출 시 박제).
  - `SKILL.md` Phase 7 sub-step — runtime gate 블록 합성 강제 (phase count 불변 유지).
  - `chain.py` 신규 fn `check_runtime_gate_block` — derived 오케스트레이터에 게이트 마커 존재 확인. plugin-only repo silent skip.
  - output-checklist 신규 must 1: "오케스트레이터에 runtime gate 블록 박제".
  - doctrine-registry 신규 id (예: **S17 runtime-gate 박제**) + §6 역색인.
- **verify:** chain green + fixture 1개에 게이트 마커 주입 확인 + smoke (S13 count sync 통과).
- **done:** 빈 골격이지만 주입 메커니즘 + 검증 회로 동작. 후속 P1-P3가 §본문만 채우면 되는 상태.

### P1 — #1 brownfield 규모 선택적 작동

- **goal:** 들어온 작업 규모를 분류해, 소규모면 기존 도구 직접 사용(합성 skip), 대규모면 도구/에이전트 합성 트리거.
- **deliverable:**
  - `runtime-execution.md §규모분류` — small(1-file/patch) / medium(module) / large(arch) 휴리스틱. `heuristics-baseline.md` 규모 신호 재사용.
  - §분기 doctrine — small → 직접 사용, large → 합성. 경계 case 사용자 confirm.
  - 오케스트레이터 runtime gate 블록에 본 분기 박제.
  - 검증 fn 확장 + checklist 항목 + registry 등재.
  - fixture: small/large 작업 2 케이스 분기 시연.
- **done:** fixture에서 규모 분기 동작 + chain green.

### P2 — #2 per-task plan + atomic 분해 + todo

- **goal:** 작업 → 전체 plan → atomic task → todo list 생성 런타임.
- **deliverable:**
  - `runtime-execution.md §plan분해` — 작업 수령 시 plan 작성 → atomic 분해 → todo 박제 doctrine. Claude Code todo 도구 활용 규약.
  - 오케스트레이터 runtime gate에 박제.
  - 검증 + checklist + registry + fixture.
- **done:** fixture에서 plan+todo 생성 시연 + chain green.

### P3 — #3 methodology-advisor 산출물 생성

- **goal:** 빌드타임 methodology *선택*(W8)을 런타임 *산출물 생성*으로 확장. `intent_profile.workflow.methodology`에 따라 deliverable 생성.
- **deliverable:**
  - `runtime-execution.md §산출물생성` — 방법론별 산출물 템플릿 매핑.
  - `advisor-integration.md` 확장 — 런타임 산출물 생성 hook.
  - 오케스트레이터 runtime gate에 박제.
  - 검증 + checklist + registry + fixture.
- **done:** fixture에서 methodology→산출물 생성 시연 + chain green.

### P4 — #5 wiki/harness 양방향 다리 [CORE]

- **goal:** plugin↔wiki bridge spec **M1-M5 중 plugin 측 C-F** 구현. (wiki 측 Phase A/B는 별도 "wiki/harness" 프로젝트에서 완료 — [[dharness-audit2-2026-05-27]] 참고.)
- **deliverable:**
  - `references/wiki-bridge.md` — 다리 doctrine 단일 출처.
  - **M1 Emit** — 합성 도구/스킬을 wiki `candidates/`로 push.
  - **M4 Feedback** — wiki promotion 결과(Static/LLM-Judge/MonteCarlo tier) pull → Phase 5-2 후보 반영.
  - **M5 Schema gate** — push/pull schema 결정적 검증 회로.
  - 검증 fn + checklist + registry + fixture.
- **주의:** push 소스(런타임 산출물)가 P1-P3로 풍부해진 뒤라 양방향 가치 발생. 가장 큰 작업, 마지막.
- **done:** schema gate green + Emit/Feedback 시연 + chain 전체 green.

---

## 4. Cross-cutting 주의 (매 Phase 적용)

- **python = `py -3`** (bare `python`은 Windows Store stub).
- **작업 위치** = working repo `C:\Users\user01\awesome-files\dharness-project\dharness\`, branch `command-consolidation-trigger-overhaul` (또는 신규 branch). 마켓 캐시 read-only.
- **S13 count sync** — output-checklist 항목 추가마다 4곳(정본+헤더+SKILL.md+harness-new.md) 동기.
- **S16 phase count** — 새 `### Phase` 헤더 신설 시에만 발화. sub-step 유지하면 불변. 신설 불가피하면 4 ad 위치 갱신.
- **R6 registry** — 신규 `chain*.py:<fn>` 인용 시 §6 역색인 등재 (smoke fn-ref/inverse-index 강제).
- **I8 fixture 회귀** — plugin 변경 후 synthesis_example/ 4 fixture 영향 평가.
- **pre-existing FAIL 불변** — structure(memory-search 워크플로우 섹션·오케스트레이터 식별), schema(`_workspace/_baseline` 미존재). 내 변경 아님 — 손대지 않음.
- **commit 단위** — Phase 1개 = commit 1개 권장. 사용자 push 요청 전 push 금지.

---

## 5. 재개 프로토콜 (compact 후)

1. 본 문서 §2 진행 상태 표에서 ⬜/🔶 최상단 Phase 확인.
2. 해당 Phase §3 상세의 deliverable 목록 + §3 공통 done 템플릿 7항목 수행.
3. `py -3 plugins/harness/scripts/validate/chain.py` + smoke green 확인.
4. §2 표 상태 갱신(✅) + memory `dharness-runtime-features-plan-2026-05-30.md` 갱신.
5. 다음 Phase로.
