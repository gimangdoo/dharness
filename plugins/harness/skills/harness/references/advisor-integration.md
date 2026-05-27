# Advisor Integration — methodology-advisor v0.3.x handoff 변환

> **Read at phase:** Phase 2 (intent_profile 합성) — advisor 위임 분기 진입 시. 평시 read 불요.
>
> **목적:** `intent-profile-schema.md` §8에서 분리(2026-05-27 PB6) — advisor 수신 시 단방향 변환 룰 + cross-field invariant 단일 출처.

---

## §1. Advisor handoff 수신 시 변환 룰 (v0.12.1 adapter doctrine)

methodology-advisor plugin v0.3.x 출력 yaml fragment를 dharness `intent_profile.md` frontmatter에 merge할 때 적용. dharness 측 단방향 변환 — advisor 측 출력 형식 변경 0.

| advisor 출력 | dharness 변환 | 변환 대상 필드 |
|---|---|---|
| `workflow.methodology: ["DDD", "TDD", "Trunk-based"]` (mixed-case list) | primary = list[0] lowercase → scalar; secondary = list[1:] lowercase | `workflow.methodology` (scalar enum) + `meta.advisor_secondary_methodologies` (list) |
| `workflow.methodology_source: "methodology-advisor v0.3.1"` (free string) | enum 정규화 `"advisor"` + 원본 메타 박제 | `workflow.methodology_source` (enum) + `meta.advisor_handoff_version` (string) |
| `workflow.methodology_matrix_row: "R4"` 또는 `"matrix-miss"` sigil | 그대로 박제 | `workflow.methodology_matrix_row` (string\|null) |

변환 강제 트리거: SKILL.md §Phase 2 advisor 위임 doctrine 1 단락 + `grilling-loop.md §3-4` advisor delegation branch step 4 (yaml merge 직전).

**카탈로그 외 방법론 처리:** advisor `[catalog-miss]` sigil 또는 dharness enum 11개 외 값 시 → `workflow.methodology: "unknown"` + secondary에 원 문자열 보존 + `meta.open_questions`에 "advisor 추천 '<원본>' dharness enum 외 — 진화 단계 재합성" 박제.

## §2. Cross-field invariant (deterministic, chain_advisor.py 강제)

| 조합 | 룰 |
|---|---|
| `workflow.methodology_source = advisor` + `workflow.methodology_matrix_row = null` | 모순: advisor handoff 시 decision-matrix row id 필수 |
| `workflow.methodology_source != advisor` + `workflow.methodology_matrix_row != null` | 모순: 비-advisor source는 matrix row id 보유 금지 |
| `workflow.methodology_source = advisor` + `meta.advisor_handoff_version` 미박제 | 모순: advisor 수신 시 원본 free-string source는 `meta.advisor_handoff_version`에 보존 박제 필수 — 재현성 손실 차단 |
| `meta.advisor_secondary_methodologies != []` + `workflow.methodology_source != advisor` | 모순: secondary list는 advisor 수신 시에만 박제 (사용자 직접 응답 시 list 합성 X) |
| `workflow.methodology_source = advisor` + `workflow.methodology` non-enum-or-non-lowercase | 모순: advisor 출력 list `["DDD", "TDD", ...]`는 dharness 수신 시 primary 첫 원소를 lowercase 정규화 강제. 비정규 값 박제 시 변환 step 누락 |

정합 점검: `chain_advisor.py:check_advisor_handoff_adapter_consistency` (5 cross-field 룰).

## §3. cross-reference

- 트리거 본체: `SKILL.md §Phase 2 방법론 위임 doctrine`
- 분기 step: `grilling-loop.md §3-4` advisor delegation branch
- enum/필드 정의: `intent-profile-schema.md §2 workflow`
- 결정적 검증: `plugins/harness/scripts/validate/chain_advisor.py`
