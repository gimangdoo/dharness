# Intent Profile Advisory — LLM-only 룰

> **Read at phase:** Phase 2 합성 직전 final review 시점. LLM이 intent_profile 자기검증 후 위반 시 `meta.explicit_assumptions`에 사용자 이유 박제 후 통과.
>
> **목적:** `intent-profile-schema.md` §8에서 분리(2026-05-27 PB5) — chain.py 결정적 검증 불가 LLM-only 권장 룰 + cross-field 경고 단일 출처.
>
> **enforce 채널:** chain.py 비강제. Phase 2 합성 시 LLM이 본 reference read 후 자기검증, 위반 시 `meta.explicit_assumptions`에 "{룰} 의도적 위반: {사용자 이유}" 박제 후 통과 — deterministic invariant 아님.

---

## §1. 권장 룰 (실패 시 경고, 사용자 확인)

| 룰 | 의미 |
|----|------|
| `meta.explicit_assumptions` 1개 이상 | 모든 프로젝트는 가정이 있다. 비어있으면 사용자가 충분히 사고하지 않은 신호 |
| `scope.out_of_scope` 1개 이상 | scope creep 방지를 위한 명시적 제외 항목 |
| `vision.success_definition`이 측정 가능 | "사용자 만족도 향상" 같은 측정 불가 표현 회피 권장 |

## §2. Cross-field LLM-only annotation (경고, 통과 허용)

| 조합 | 경고 |
|------|----|
| `timeline.horizon = production` + `quality.test_rigor = none` | production에 테스트 없음은 위험 (C15-1) |
| `team.size = solo` + `workflow.review_style = strict` | 1인이 strict 리뷰 불가능 (C15-2) |
| `data_sensitivity = regulated` + `quality.security_requirements = []` | regulated 데이터인데 보안 요구사항 미정의 (C15-3) |

각 위반은 hard fail 아닌 *경고* — 사용자가 의도된 것이라 응답하면 `meta.explicit_assumptions`에 "{룰} 의도적 위반: {사용자 이유}" 기록 후 통과.

## §3. cross-reference

- 필드 정의 + 필수 enum + deterministic invariant: `intent-profile-schema.md §8`
- 결정적 검증: `chain_intent.py:check_intent_profile_*` (4 fn)
- advisor 모드 cross-field: `advisor-integration.md §2` (PB6 분리)
