# Dogfood E2E Verification — methodology-advisor v0.3.1 handoff + dharness v0.12.1 adapter

**날짜:** 2026-05-24
**대상:** methodology-advisor plugin v0.3.1 ↔ dharness v0.12.1 W8 doctrine + adapter
**모드:** static walkthrough (advisor SKILL.md + decision-matrix.md + handoff-template.md 결정성에 의존, runtime Skill 호출 0)

---

## 1. 합성 입력 신호 (synthetic Phase 0)

| 축 | 값 | 출처 |
|---|---|---|
| project_type | greenfield | `project_profile.md` frontmatter |
| purpose | product | `intent_profile_before.md` 본문 + `project_profile.md` Domain 섹션 |
| scale | solo | `team.size` 박제 |
| timeline | short (3M MVP) | `constraints.timeline.horizon` + Domain "3개월 MVP" |
| constraints | none | regulated 데이터 0, compliance 0 |

→ **decision-matrix.md R3 exact match.**

## 2. advisor 출력 yaml fragment (Phase 4-sub)

`advisor_output_fragment.yaml` 참조. handoff-template.md §2 패턴 + decision-matrix.md R3 row 결정적 결합. drift 사유 = 0 (matrix exact hit).

## 3. dharness v0.12.1 adapter 변환 결과

| 입력 (advisor 출력) | 변환 룰 | 출력 (dharness merge) |
|---|---|---|
| `methodology: ["Spec-driven", "TDD", "Trunk-based"]` | list[0] lowercase → primary scalar | `workflow.methodology: spec-driven` |
| (same) | list[1:] lowercase → secondary 보존 | `meta.advisor_secondary_methodologies: [tdd, trunk-based]` |
| `methodology_source: "methodology-advisor v0.3.1"` | free string → enum `advisor` | `workflow.methodology_source: advisor` |
| (same) | 원본 string → 메타 박제 | `meta.advisor_handoff_version: "methodology-advisor v0.3.1"` |
| `methodology_matrix_row: "R3"` | 그대로 | `workflow.methodology_matrix_row: "R3"` |
| `quality.test_rigor: tdd` | 그대로 (이미 enum) | `quality.test_rigor: tdd` |
| `meta.user_confirmed_fields` | merge (기존 4 + 추가 2) | 6 필드 박제 |

## 4. Cross-field 룰 검증 (intent-profile-schema.md §8, 5건)

| # | 룰 | 본 fixture 통과 여부 |
|---|----|---|
| 1 | `methodology_source = advisor` + `methodology_matrix_row = null` → 모순 | **PASS** (matrix_row = "R3", not null) |
| 2 | `methodology_source != advisor` + `methodology_matrix_row != null` → 모순 | **PASS** (source = advisor, rule N/A) |
| 3 | `methodology_source = advisor` + `meta.advisor_handoff_version` 미박제 → 모순 | **PASS** (handoff_version = "methodology-advisor v0.3.1" 박제) |
| 4 | `meta.advisor_secondary_methodologies != []` + `methodology_source != advisor` → 모순 | **PASS** (source = advisor, secondary list 2개 박제) |
| 5 | `methodology_source = advisor` + `methodology` non-enum-or-non-lowercase → 모순 | **PASS** (methodology = "spec-driven" lowercase enum hit) |

**5/5 PASS.**

## 5. dharness 5 필수 필드 채움 검증

| 필드 | 박제 상태 |
|---|---|
| `constraints.tech_stack` | ✅ `[Node.js, PostgreSQL, Fastify]` |
| `constraints.team.size` | ✅ `solo` |
| `constraints.timeline.horizon` | ✅ `mvp` |
| `architecture.deployment_target` | ✅ `api` |
| `quality.test_rigor` | ✅ `tdd` (advisor merge) |

5/5 박제. `meta.user_confirmed_fields`에 6개 등록 (5 필수 + workflow.methodology). Phase 2 종료 게이트 통과.

## 6. drift 노출 점검 (v0.12.0 → v0.12.1 회복 확인)

v0.12.0 단순 merge 시 (adapter 없음) drift 5건 발현 시뮬레이션:

| drift | v0.12.0 결과 | v0.12.1 adapter 결과 |
|---|---|---|
| list vs scalar | `methodology: ["Spec-driven", "TDD", "Trunk-based"]` (schema 위반: scalar enum 기대) | `methodology: spec-driven` (정합) |
| capitalization | "Spec-driven" (case 위반) | "spec-driven" (lowercase 정규화) |
| free source | `methodology_source: "methodology-advisor v0.3.1"` (enum 4 외 값) | `methodology_source: advisor` (enum 정합) + 원본 보존 |
| matrix_row sigil | "matrix-miss" 처리 미정의 (본 fixture는 hit이라 N/A) | "R3" 그대로 + sigil case는 §Advisor handoff 수신 시 변환 룰에 catalog-miss row로 명시 |
| handoff envelope | `intent_profile_patch:` top-level wrapper 처리 미정의 | adapter 변환 step에서 envelope 풀고 frontmatter merge |

**5/5 drift 회복.**

## 7. 결론

- adapter doctrine v0.12.1 end-to-end PASS (matrix-hit case)
- advisor v0.3.1 측 plugin 수정 0 — dharness 단독 회복 입증
- 미검증 영역:
  1. `[matrix-miss]` case (advisor LLM fallback 결정성 ↓) — 별도 fixture 필요
  2. `[catalog-miss]` case (사용자 자유 입력 dharness enum 외) — 별도 fixture 필요
  3. `methodology` 1개만 박제 case (advisor 단일 방법론 합성, 4축 축약 시) — secondary 빈 list 처리 검증 필요
  4. runtime Skill 호출 (advisor Phase 3 사용자 confirm 게이트) — 본 walkthrough 미커버
  5. dharness chain.py 자동 검증 회로 0 — adapter 변환 누락 시 silent pass 위험

## 8. 다음 단계 후보

- A. matrix-miss / catalog-miss case fixture 박제 + verification 2회 추가
- B. chain.py 결정적 검증 fn 신설 (`check_advisor_handoff_adapter_consistency`) — schema validator 강화
- C. runtime Skill 호출 dogfood (advisor Phase 3 게이트 사용자 응답 필요)
- D. 본 cycle closure — dogfood 1회 PASS로 충분 판단, 별 cycle 진입 보류
