---
version: 1
project_type: greenfield
scan_mode: minimal
scanned_at: 2026-05-10T00:00:00Z
scan_root: "."

stack: {}
architecture:
  structure_pattern: unknown
  entry_points: []
  key_directories:
    - "skills/harness/"
    - ".claude/agents/"
    - ".claude/skills/"
    - "commands/"
    - "_workspace/_hooks/"
    - "_workspace/_worker/"
  module_boundaries: []
convention: {}

meta:
  unanalyzed: [stack, architecture, convention, maturity, pain_points]
  source_file_count: 0
  total_loc: 0
  detection_signals:
    - "no package manifests found (package.json, requirements.txt, go.mod, Cargo.toml absent)"
    - "directory contents: skills/, commands/, .claude/, _workspace/, CLAUDE.md, README.md"
    - "Python hook scripts under _workspace/_hooks/ (stdlib only) — runtime infrastructure for the CM harness"
    - "FastAPI dashboard worker under _workspace/_worker/ — single optional external dependency"
    - "repo is the harness skill plugin itself + CM reference implementation — not a user application codebase"
---

# Project Profile

## Greenfield Detection

이 프로젝트는 다음 신호로 greenfield로 분류되었다:

- 패키지 매니페스트: 부재
- 소스 파일: harness skill 정의 파일 + CM 에이전트/스킬 정의 + Python hook/worker 스크립트
- 역할: dharness repo는 harness 메타 스킬 플러그인이며, 그 위에 context-management 도메인 하네스를 reference implementation으로 구축한다

## Next Step

5축 조사를 건너뛰고 Phase 2 intent_profile(사전 작성됨)을 그대로 사용한다.
