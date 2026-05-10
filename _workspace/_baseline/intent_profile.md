---
version: 1
project_type: greenfield

vision:
  target_users:
    - "Claude Code 헤비 유저 (장기 프로젝트 운영자)"
    - "컨텍스트 손실로 반복 설명 부담을 겪는 단독 개발자"

scope:
  must_have:
    - "5개 라이프사이클 훅 점유 + telemetry 이벤트 발행"
    - "PostToolUse 출력 압축 (>10KB만)"
    - "SessionEnd 다이제스트 + 클러스터링"
    - "progressive disclosure 검색 (3-tool 패턴)"
    - "로컬 dashboard 4개 뷰"
  out_of_scope:
    - "클라우드 동기화 (단일 머신만 지원)"
    - "실시간 협업 메모리"

constraints:
  tech_stack:
    preferred: [Python, SQLite, sqlite-vec, FastAPI]
    forbidden: [Chroma]
    locked_in: []
  team:
    size: solo
    expertise: mid
  timeline:
    horizon: prototype
    deadline: null

architecture:
  deployment_target: [server]
  scale_expectation: toy
  data_sensitivity: personal

quality:
  test_rigor: smoke
  documentation_level: code_comments
  security_requirements:
    - "모든 데이터 로컬 저장, 외부 송신 없음"

workflow:
  collaboration_mode: solo
  review_style: self
  ci_cd: lint

meta:
  open_questions:
    - "sqlite-vec 버전 호환성 — sqlite 3.x와의 pinning 필요 여부"
  explicit_assumptions:
    - "단일 머신(로컬) 운영 가정 — 네트워크 접근 없음"
    - "Claude Code의 SessionStart / PostToolUse / SessionEnd 훅이 정상 동작하는 환경"
    - "Python 3.11+ 설치 가정"
    - "Chroma 제외 이유: 별도 서비스 실행 부담, SQLite 단일 파일로 충분"
  inferred_fields: []
  user_confirmed_fields: []
---

# Intent Profile

## Vision

### Problem Statement

Claude Code 세션 간 컨텍스트 손실, 도구 출력의 컨텍스트 점유,
프로젝트별 도구/세션/메모리의 가시성 부재.

### Success Definition

- 세션당 토큰 사용량 30% 감소 (PostToolUse 압축 기준)
- 메모리 검색 응답 시간 < 2초
- 승격된 skill memory가 월 5개 이상 누적 (S5 이후)

## Scope

### Initial Milestone

S1 완료: SessionStart에서 직전 세션 한 단락 인젝션이 동작한다.

### Must Have

1. SessionStart hook → cm-injector: 직전 N세션 digest 읽고 메타 컨텍스트 주입
2. PostToolUse hook → cm-compressor: 10KB 초과 출력만 압축, raw 보존
3. SessionEnd hook → cm-digester + cm-curator 팀: what/when/do/warn digest 생성 + 클러스터링
4. on-demand → cm-retriever: 3-tool progressive disclosure 검색
5. dashboard-render skill + background worker: 4개 뷰 localhost 렌더

### Out of Scope

- 클라우드 동기화: 단일 머신 운영으로 충분
- 실시간 협업 메모리: 멀티 유저 시나리오 제외

## Constraints

### Tech Stack

- preferred: Python, SQLite (FTS5 + sqlite-vec), FastAPI (dashboard API)
- forbidden: Chroma (별도 서비스 부담 — SQLite로 대체)
- locked_in: 없음 (greenfield)

### Security

- 모든 데이터 `_workspace/` 하위 로컬 저장
- 외부 API 호출 없음 (Claude Code의 LLM 호출은 별도 인프라)

## Meta

### Explicit Assumptions

- Claude Code hook 인프라 정상 동작 가정
- Python 3.11+ 설치 가정
- 단일 머신 로컬 운영

### Open Questions

- sqlite-vec 버전 pinning 필요성 → S4 구현 시 결정

### Resolved

- S6 dashboard worker 프로세스 관리 방식 → **수동 실행으로 결정** (`_workspace/_worker/README.md`, `dashboard-render` 스킬). `/cm-dashboard`는 worker 미실행 감지 + 시작 명령 안내로 한정.
