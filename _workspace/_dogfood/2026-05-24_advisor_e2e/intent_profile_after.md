---
version: 1
project_type: greenfield
dogfood_fixture: true

constraints:
  tech_stack:
    preferred: [Node.js, PostgreSQL, Fastify]
    forbidden: []
    locked_in: []
  team:
    size: solo
    expertise: mid
  timeline:
    horizon: mvp

architecture:
  deployment_target: api

quality:
  test_rigor: tdd                              # advisor merge — TDD core (R3)

workflow:
  collaboration_mode: solo
  review_style: self
  ci_cd: lint
  methodology: spec-driven                     # adapter 변환: list[0] "Spec-driven" → lowercase scalar enum hit
  methodology_source: advisor                  # adapter 변환: free string → enum
  methodology_matrix_row: "R3"                 # 그대로 박제

meta:
  dharness_version: "0.12.1"
  advisor_secondary_methodologies:             # adapter 변환: list[1:] lowercase 보존
    - tdd
    - trunk-based
  advisor_handoff_version: "methodology-advisor v0.3.1"   # adapter 변환: 원본 source string 보존 (재현성)
  open_questions: []                           # advisor가 해결
  user_confirmed_fields:
    - constraints.tech_stack
    - constraints.team.size
    - constraints.timeline.horizon
    - architecture.deployment_target
    - quality.test_rigor                       # advisor merge
    - workflow.methodology                     # advisor merge
  inferred_fields: []
  confidence_low: []
  source: {}
  explicit_assumptions: []
  advisor_recommended_but_overridden: false    # 사용자 confirm 통과 (override 없음)
---

# Intent Profile — Phase 2 종료 상태 (DOGFOOD FIXTURE)

advisor v0.3.1 위임 후 adapter 변환 적용 결과. 필수 5필드 전부 박제 완료 → Phase 3 도메인 분석 진입 가능.

## Vision

- 솔로 개발자가 운영하는 전자상거래 백엔드 API
- 3개월 MVP 후 5명 small_team 확장 검토

## Methodology (advisor 박제 + adapter 변환)

- Primary: **Spec-driven** (설계 축, lowercase 정규화)
- Secondary: TDD (테스트 축), Trunk-based (워크플로우 축) — `meta.advisor_secondary_methodologies` 보존
- Matrix row: R3
- 출처: methodology-advisor v0.3.1 dharness-sub mode handoff

## Phase 3 진입 신호

- `workflow.methodology = spec-driven` → Phase 5 에이전트 정의에 spec 산출물 박제 의무화 (handoff-template §3.4)
- `meta.advisor_secondary_methodologies` 내 `tdd` → Phase 4 패턴 "생성-검증 (Producer-Reviewer)" 후보
- `meta.advisor_secondary_methodologies` 내 `trunk-based` → orchestrator-template Phase 4 single-branch 강제 룰
