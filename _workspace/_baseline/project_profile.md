---
version: 1
project_type: brownfield
stack:
  languages:
    - { name: python, version: "3.11+", percent_loc: 70, source: "plugins/harness/scripts/**/*.py, .claude/hooks/*.py" }
    - { name: markdown, version: null, percent_loc: 30, source: "skills/**/*.md, commands/**/*.md, references/**/*.md" }
  frameworks:
    - { name: unittest, version: stdlib, role: test, source: "plugins/harness/scripts/validate/test_*.py" }
    - { name: sqlite3, version: stdlib, role: backend, source: ".claude/hooks/_schema.py" }
  build_tools: []
architecture:
  structure_pattern: layered
  entry_points:
    - plugins/harness/skills/harness/SKILL.md
    - plugins/harness/scripts/validate/chain.py
    - .claude/hooks/session_start.py
  key_directories:
    - { path: plugins/harness/, role: "harness plugin (메타 스킬 팩토리, 외부 install 대상)" }
    - { path: plugins/harness/scripts/validate/, role: "결정적 검증 chain (dev-time)" }
    - { path: plugins/harness/scripts/wiki/, role: "wiki bridge I/O (self-host runtime)" }
    - { path: .claude/, role: "Context Manager self-host 런타임 (dharness 본 폴더 한정)" }
convention:
  file_naming:
    case_style: kebab
    consistency_score: 0.9
  doctrine_ids: "S*/W*/C*/I*/R* — doctrine-registry.md 단일 출처, chain.py 결정적 검증"
maturity:
  test_coverage:
    tool: unittest
    line_coverage_percent: null
  test_suites:
    - plugins/harness/scripts/validate/test_chain.py
    - plugins/harness/scripts/validate/smoke_test_doctrine_registry.py
    - .claude/hooks/test_*.py
  versioning: "semver, marketplace.json + plugin.json 동기 (chain_version I1/I2)"
pain_points:
  churn_hotspots:
    - { path: plugins/harness/scripts/validate/chain.py, change_count: null }
    - { path: plugins/harness/skills/harness/SKILL.md, change_count: null }
  known_debt:
    - "doc bloat 분할 잔여 (team-examples.md 598 LOC, project-profile-schema.md 582 LOC)"
meta:
  unanalyzed: []
  inferred_fields: []
  source: {}
---

# Project Profile — dharness self-host

> **baseline 스냅샷** (2026-06-07, 묶음 C). dharness 본 폴더(brownfield Python/markdown 툴링)의
> 구조·성숙도 기준선. arch review L08-001/L11-1/L15-4 해소 + 향후 review diff 기준점.
> Phase 1·2 정규 경유 산출물 아님 — 수기 합성 스냅샷.

## Stack
Python 3.11+ (결정적 hooks·검증 chain) + Markdown (스킬·doctrine·레퍼런스). 표준 라이브러리만
사용 (unittest / sqlite3) — 외부 런타임 의존 0.

## Architecture
2-구성: **harness plugin**(외부 install 메타 팩토리) + **Context Manager**(self-host 전용 런타임).
layering: `validate/`=dev-time 검증, `wiki/`=self-host runtime I/O, `schema.py`=shared contract.

## Maturity
결정적 검증 chain(chain.py + 6 sub-module) + 회귀 test suite(test_chain / smoke / hook tests).
semver 버저닝, I1/I2 doctrine drift refit 인프라 가동.

## Pain Points
doc bloat 분할 잔여(#4 team-examples / #5 project-profile-schema). chain.py god-module 관찰(L11-6).
