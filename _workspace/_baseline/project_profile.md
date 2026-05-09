---
version: 1
project_type: greenfield
scan_mode: minimal
scanned_at: 2026-05-09T00:00:00Z
scan_root: "."

stack: {}
architecture:
  structure_pattern: unknown
  entry_points: []
  key_directories: []
  module_boundaries: []
convention: {}

meta:
  unanalyzed: [stack, architecture, convention, maturity, pain_points]
  source_file_count: 0
  total_loc: 0
  detection_signals:
    - "no package manifests found (package.json, requirements.txt, go.mod, Cargo.toml absent)"
    - "directory contents: skills/, commands/, reference-file-for-context-manager/, README.md"
    - "repo is the harness skill plugin itself — not a user application codebase"
---

# Project Profile

## Greenfield Detection

이 프로젝트는 다음 신호로 greenfield로 분류되었다:

- 패키지 매니페스트: 부재
- 소스 파일: 없음 (harness skill 정의 파일과 참고 문서만 존재)
- 역할: dharness repo는 harness 메타 스킬 플러그인이며, 그 위에 context-management 도메인 하네스를 새로 구축한다

## Next Step

5축 조사를 건너뛰고 Phase 2 intent_profile(사전 작성됨)을 그대로 사용한다.
