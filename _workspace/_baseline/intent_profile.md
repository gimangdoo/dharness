---
version: 1
project_type: greenfield
vision:
  problem_statement: "도메인 한 문장을 에이전트 팀 + 스킬 세트로 변환하는 메타 스킬 팩토리를 제공하고, Claude Code 세션 간 컨텍스트 손실을 결정적 hooks로 해소한다."
  target_users: ["Claude Code 파워 유저", "dharness 유지보수자"]
  success_definition: "도메인 1줄 입력에서 검증 가능한 하네스(에이전트·스킬·관측 인프라)가 결정적으로 합성되고, self-host CM이 세션 간 컨텍스트를 무손실 영속화."
scope:
  initial_milestone: "harness plugin Phase 0-10 + Context Manager 결정적 3 hooks 가동"
  must_have: ["메타 스킬 팩토리 (harness-new/evolve/adapt)", "결정적 검증 chain", "Context Manager 세션 영속화", "wiki bridge 실행 자동화"]
  out_of_scope: ["Context Manager 외부 install", "derived 런타임에 CM 주입", "LLM 기반 in-session 압축"]
constraints:
  tech_stack:
    preferred: [Python, Markdown]
    forbidden: []
    locked_in: []
  team:
    size: solo
    expertise: senior
  timeline:
    horizon: production
    deadline: null
  compliance:
    regulatory: [none]
    data_handling:
      pii: false
      phi: false
      pci: false
      financial: false
    audit_retention_days: null
architecture:
  deployment_target: [desktop]
  scale_expectation: toy
  data_sensitivity: none
quality:
  test_rigor: unit
  documentation_level: full
  security_requirements: []
workflow:
  collaboration_mode: solo
  review_style: self
  ci_cd: test
  methodology: none
  methodology_source: none
  methodology_matrix_row: null
meta:
  open_questions: []
  explicit_assumptions:
    - "dharness self-host baseline — Phase 1·2 미경유 수기 합성 스냅샷 (2026-06-07 묶음 C, arch L08-001 해소)"
  inferred_fields: []
  user_confirmed_fields:
    - constraints.tech_stack
    - constraints.team.size
    - constraints.timeline.horizon
    - architecture.deployment_target
    - quality.test_rigor
  confidence_low: []
  source: {}
  dharness_version: "0.18.4"
---

# Intent Profile — dharness self-host

> **baseline 스냅샷** (2026-06-07, 묶음 C). 팩토리 자신의 의도 기준선. `meta.dharness_version`이
> I2 doctrine drift refit anchor(t=0). Phase 1·2 정규 경유 산출물 아님 — 수기 합성.

## Vision
dharness = 도메인 한 문장 → 에이전트 팀 + 스킬 팩토리 (harness plugin) + 세션 컨텍스트 무손실
영속화 (Context Manager self-host). 단일 출처: README.md + SKILL.md.

## Scope
must-have: 메타 스킬 팩토리 / 결정적 검증 chain / CM 세션 영속화 / wiki bridge 실행 자동화.
out-of-scope: CM 외부 install · derived 런타임 CM 주입 · LLM in-session 압축.

## Meta
greenfield (원작 메타-툴, 기존 코드베이스 역공학 아님). `dharness_version: 0.18.4` = 현 plugin
version과 일치 → drift 0. 필수 5필드 user_confirmed (W3 strict invariant).
