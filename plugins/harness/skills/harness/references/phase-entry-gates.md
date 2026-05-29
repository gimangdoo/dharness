# Phase Entry Gates — anti-premature-judgment + 중단 factory run + cardinality

> **Read at phase:** Phase 0 / 0.5 / 1 / 2 / 5 진입 직전 (entry gate). SKILL.md 본문에서
> 본 reference 포인터 1줄로 분리된 entry gate 박스 모음. SKILL.md ≤500 LOC cap 정합
> (P2-A 박제, 2026-05-23 review patch). 본 reference 미read 시 phase 진입 doctrine 위반.

---

## Phase 0 — 중단된 factory run 감지 doctrine (mattpocock handoff 흡수, 2026-05-21)

step 1에서 `_workspace/_baseline/` 또는 `_workspace/_critique_phase*_*.md`는 존재하는데 `.claude/agents/`·`.claude/skills/`가 비었거나 불완전하면, 이전 factory 세션이 중간에 멈춘 것이다 (context 한계·세션 종료 등). 이 경우 step 2의 신규/기존/운영 분기보다 *먼저* 판정한다:

1. **재개 지점 판정**: 존재하는 phase 산출물 중 최대 N — `_critique_phase{N}` 최대값, 없으면 `_workspace/_baseline/intent_profile.md` 존재 시 Phase 2까지, `_workspace/_baseline/project_profile.md`만 존재 시 Phase 1까지 완료로 본다.
2. **사용자 게이트**: "이전 구축이 Phase {N}까지 완료됨 — Phase {N+1}부터 재개할까, 처음부터 다시 할까?"를 제시한다.
3. **handoff 문서 불요**: phase 산출물(`_workspace/_baseline/*.md`, `_critique_phase*`)이 구조화된 채 박제돼 있어 그 자체가 handoff다 — 별도 요약 문서를 만들지 않는다. 재개 세션은 해당 파일을 *재read*하여 컨텍스트를 복원한다.

**이유:** 15-phase factory(12 base + 3 critique/sim)는 긴 워크플로우 — context 한계로 중간 종료 시 처음부터 재실행은 Phase 1·2 재분석 비용 낭비. 산출물이 이미 파일로 박제돼 있으므로 재개가 정답. mattpocock `handoff` 스킬의 "대화 → handoff 문서" 개념을 factory에 적용하되, 산출물 파일이 이미 handoff 역할을 하므로 별도 문서 생성은 생략.

---

## Phase 0.5 — 🛑 Anti-premature-judgment doctrine (2026-05-15, 사용자 요구)

본 Phase 진입 시점부터 Phase 3 합성 직전까지, 다음 단서 *단독*으로 프로젝트의 도메인·유형·기능·기술 스택을 **단정 금지**:

- cwd 디렉토리 이름 (예: `/Users/.../my-fintech-app` → "fintech" 단정 금지)
- 디렉토리 내 파일·폴더 이름 (예: `payment.py` 존재 → "결제 시스템" 단정 금지)
- `$ARGUMENTS` 문자열의 키워드만으로 도메인 확정 (예: "ML pipeline" → ML 도메인 확정 금지 — Phase 2에서 검증)
- README.md 한 줄 문장 (스캔만 가능, "단정"은 금지)

**단정 허용 조건 (둘 다 만족 필수):**

1. **Phase 1 산출물** `_workspace/_baseline/project_profile.md`이 실제 파일로 박제되어 있고, manifest/source/git 신호 ≥2 기반 5축 (또는 Quick 3축) 데이터 포함
2. **Phase 2 산출물** `_workspace/_baseline/intent_profile.md`이 실제 파일로 박제되어 있고, 필수 5필드(`constraints.tech_stack`, `constraints.team.size`, `constraints.timeline.horizon`, `architecture.deployment_target`, `quality.test_rigor`)가 *사용자 raw 답변*(= `meta.user_confirmed_fields`)으로 채워져 있음

**위반 시:** Phase 3 진입 전 자기 점검 — "본 도메인 추론의 evidence가 위 2 조건을 만족하는가?" NO일 경우 Phase 1 또는 Phase 2로 회귀. 단서 강도가 강해 보여도 단정 표현(`이 프로젝트는 X다`, `domain: X로 확정`) 사용 금지 — 가설 표현(`X로 추정, 확인 필요`)만 허용.

**이유:** 디렉토리 이름·파일 이름은 사용자가 임의로 붙인 라벨이지 의도의 source of truth 아님. 사용자가 명시한 vision/scope/constraints가 도메인 정의의 권위. 본 doctrine 미준수 시 잘못된 도메인으로 Phase 3-6 전체 산출물이 오염 → Phase 8 검증 단계에서야 발견되어 rework 비용 폭증.

---

## Phase 1 — 🚧 entry 게이트 (2026-05-15, 사용자 요구)

본 Phase는 **항상 실행되며 silent skip 차단**. 진입 시점부터 다음 강제 회로:

1. **실 파일 read 강제**: 디렉토리 트리 + manifest(package.json/pyproject.toml/Cargo.toml/...) + git log 첫 페이지 + README.md를 *실제로* read. Glob/Grep 결과만으로 합성 금지. greenfield 분류로 가더라도 위 신호 부재를 *명시적*으로 박제 (`signals: {manifest: absent, git: absent, source: absent}`).
2. **산출물 강제**: 모드(greenfield/Quick/Deep)와 무관하게 `_workspace/_baseline/project_profile.md`가 실제 파일로 *반드시* 생성. greenfield는 빈 stub 허용 — 단 `project_type: greenfield`, `signals: ...`, `directory_tree: ...`, `inferred_domain: null` 필드 채움. **본 파일 미생성 시 Phase 2 진입 차단**.
3. **단정 표현 금지**: 산출물 내 `domain`, `purpose`, `function` 등 의도 필드는 Phase 2 완료 전까지 `null` 또는 `hypothesis: "X로 추정"`만 허용. `domain: fintech`와 같은 단정 표현 금지.

**이유:** 본 Phase가 사용자 의도와 독립적인 *객관* baseline의 단일 출처. 본 단계 silent skip 또는 디렉토리 이름 기반 단정은 Phase 0.5 anti-premature-judgment doctrine 직접 위반. 빈 stub이라도 박제하면 Phase 10 drift 감지의 t=0 anchor가 확보됨.

---

## Phase 2 — 🚧 entry 게이트 (2026-05-15, 사용자 요구)

Phase 1 산출물 `project_profile.md` 미존재 시 본 Phase **진입 차단** — Phase 1로 회귀. 진입 후 다음 강제 회로:

1. **필수 6필드 사용자 답변 raw 인용 강제**: `constraints.tech_stack`, `constraints.team.size`, `constraints.timeline.horizon`, `architecture.deployment_target`, `quality.test_rigor`, `meta.dharness_version` (정본 `scripts/validate/schema.py:INTENT_REQUIRED`) — 사용자 raw 답변 5필드 + LLM 박제 1필드 (`meta.dharness_version` = 합성 시점 `plugins/harness/.claude-plugin/plugin.json` `version` 자동 박제, 2026-05-28 audit2 PA8 격상). 사용자 raw 답변 5필드는 `meta.user_confirmed_fields` 리스트 등록 — brownfield 자동 추론 결과는 *제시만* 가능, 사용자 확인 답변 없이 user_confirmed_fields에 등록 금지.
2. **질문 폭격 강제**: 필수 6필드 (사용자 raw 5 + LLM 박제 1) 미답변 상태에서 Phase 3 진입 차단. 사용자가 "다 알아서 하라" 등 답변 거부 시 → 추론값으로 채우되 `meta.inferred_fields`에 박제 + 별도 confirm 게이트(추론값 표 출력 → "이대로 진행?" 명시 인가 후만 Phase 3).
3. **단정 표현 금지 (Phase 2 미완 상태에서)**: Phase 1과 동일 — `domain: X` 단정 출력 금지. Phase 2 완료(필수 5필드 `user_confirmed_fields` 등록 + `meta.dharness_version` LLM 박제 — `chain.py:check_required_user_confirmed_fields` 결정적 검증)된 후에만 Phase 3에서 단정 표현 허용. brownfield 자동 추론값은 별도 confirm 게이트(추론값 표 출력 → "이대로 진행?" 명시 인가) 통과 시 그 답변이 user_confirmed_fields 등록 트리거.
4. **brownfield 4단계 강제 순서**: 자동 추론 → *사용자 확인* → 갭 → 코드 grounded 질문. 1단계(자동 추론)만 수행하고 2단계 skip 금지.
5. **Grilling 모드 분기**: `meta.confidence_low` 항목 ≥1 OR 필수 5필드 1차 거부 시 `references/grilling-loop.md` 1q-at-a-time + recommended answer 패턴 적용. cap 5 question, 초과 시 batch 자동 fallback. 추천 답안 출처는 `project_profile.md` signals ≥2 또는 §3-1 직접 매핑만 허용 — 디렉토리·파일 이름 단독 추천 doctrine 위반.

**이유:** Phase 0.5 anti-premature-judgment doctrine의 evidence 조건 #2 ("Phase 2 산출물 필수 5필드 user_confirmed_fields") 충족 회로. 본 게이트 미준수 시 디렉토리/파일 이름 기반 단정이 silent로 Phase 3-6에 유출되어 잘못된 하네스 산출.

---

## Phase 5 — 🚧 entry 게이트 — Cardinality justification (2026-05-15, A6/M9 doctrine)

Phase 4 팀 패턴 선택 직후, Phase 5 합성 *진입 전* 사용자 confirm 게이트 강제.

1. **에이전트 cardinality 표 출력 강제** — 제안할 에이전트 N개 각각에 대해 다음 4 컬럼 박제:
   - `name` (kebab-case slug, 전역 유일)
   - `핵심 책임` (1줄)
   - `근거` (Phase 1·2·3 산출물 인용 — 어느 신호/요구에서 본 에이전트가 도출됐는지)
   - `inline 대안 검토` (이 책임이 단일 호출만 필요하면 별도 에이전트 대신 parent prompt 직접 삽입 가능한지 — 답 `inline-OK` 시 cardinality 1 감소. 판정 논리 = deletion test, `references/agent-design-patterns.md` "에이전트 깊이" 참조)
2. **`single-use → inline` 룰**: `inline 대안 검토`에서 `inline-OK` 판정 시 에이전트 생성 금지. parent prompt에 직접 삽입.
3. **이름 유일성 사전 점검**: 제안 N개 slug + 기존 `.claude/agents/*.md` 파일 slug 전역 grep. 중복 시 rename 강제 (chain.py `check_agent_name_uniqueness` 회로가 사후 검출하나 사전 차단이 비용 ↓).
4. **사용자 응답 enum**: `OK / N 감소 / N 증가 / 수정` — 게이트 통과 전 sub-agent 병렬 dispatch 금지.
5. **Grilling 옵션 (Phase C, 2026-05-19)**: `inline 대안 검토` 컬럼 답이 모호한 후보 1~2개 (예: "단일 호출인지 다중인지 경계 모호") 한정 — `references/grilling-loop.md` 1q + recommended answer 패턴으로 후보별 challenge. 전체 N개 grilling은 합성 시간 폭증 — 모호 후보 cap 2.

**위반 시:** Phase 5.5 self-critique에서 책임 중복·gap 검출되어 cycle 재진입 — 사전 게이트가 비용 ↓.
