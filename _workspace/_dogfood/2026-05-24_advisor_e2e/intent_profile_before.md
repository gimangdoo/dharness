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
    horizon: mvp     # MVP / short timeline

architecture:
  deployment_target: api

quality:
  test_rigor: unknown   # methodology advisor 위임 대기

workflow:
  collaboration_mode: solo
  review_style: self
  ci_cd: lint
  # methodology 미박제 — 사용자 "모르겠음" 응답, advisor 위임 진입점

meta:
  dharness_version: "0.12.1"
  open_questions:
    - "workflow.methodology — 사용자 '추천해줘' 응답, advisor v0.3.1 위임 대상"
    - "quality.test_rigor — methodology 합성 결과로부터 매핑 (handoff-template §3.1)"
  user_confirmed_fields:
    - constraints.tech_stack
    - constraints.team.size
    - constraints.timeline.horizon
    - architecture.deployment_target
  inferred_fields: []
  confidence_low: []
  source: {}
  explicit_assumptions: []
---

# Intent Profile — Phase 2 중단 상태 (DOGFOOD FIXTURE)

dharness factory `harness-new` Phase 2 grilling 진행 중. 필수 5필드 중 4개 채움, `quality.test_rigor` + `workflow.methodology` 미박제. 사용자 응답 "방법론 모르겠음 — 추천해줘" 수령 → grilling-loop.md §3-4 advisor delegation branch 진입.

## Vision

- 솔로 개발자가 운영하는 전자상거래 백엔드 API
- 3개월 MVP 후 5명 small_team 확장 검토

## Scope (out)

- 결제 게이트웨이 자체 구현 X (외부 PG 위임)
- 모바일 앱 X (API 단독)

## Open Questions

- workflow.methodology (advisor 위임)
- quality.test_rigor (advisor handoff 매핑 대기)
