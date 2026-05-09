# Changelog

이 프로젝트는 [Semantic Versioning](https://semver.org/)을 따릅니다.

## [Unreleased]

> 다음 릴리스 권장: **[1.3.0]** (Phase 10 Runtime Adaptation 신기능 + Phase 1·2 schema 신규 → minor bump). 컷 시 `.claude-plugin/plugin.json` · `.claude-plugin/marketplace.json` 버전 동기화 필요.

### Added

- **Phase 10: Runtime Adaptation** — 하네스 자동 진화 메커니즘 신규. 3 레이어(Capture/Diagnostic/Adapt) + telemetry 기반 drift 감지 + **제안+승인** 모델(자동 적용 없음). baseline drift(프로젝트 변화)와 사용 drift(하네스 사용 패턴 변화) 2종으로 분리 보고. 신뢰도 가중치 적용(`meta.inferred_fields − meta.user_confirmed_fields` 차집합). Phase 9(수동 진화)와 변경 이력 테이블 공유
- **Phase 1: Code Research 모듈화** — greenfield/brownfield 자동 감지 + 5축 조사(Stack/Architecture/Convention/Maturity/Pain Points) + Quick Scan(≤100 파일) vs Deep Audit(>100 또는 명시 요청) 모드 선택. 사용자 키워드 오버라이드("간단히/빠르게" → Quick, "전체 점검/깊이" → Deep). 결과 `_workspace/_baseline/project_profile.md`는 Phase 3 입력 + Phase 10 t=0 anchor
- **Phase 2: Project Inquiry 7섹션 스키마** — vision/scope/constraints/architecture/quality/workflow/meta. greenfield/brownfield 동일 schema(`project_type` 필드로 분기). 필수 5개 필드 강제(`tech_stack`, `team.size`, `timeline.horizon`, `deployment_target`, `test_rigor`). brownfield는 4단계(자동 추론 → 확인 → 갭 메우기 → 코드 grounded 질문)
- **신규 references 5종** — `code-research.md` (5축 조사 방법론), `project-profile-schema.md` (Phase 1 출력 스키마), `project-inquiry.md` (두 브랜치 채우기 전략 + 13종 코드 grounded 질문 패턴), `intent-profile-schema.md` (Phase 2 출력 스키마 + 인스턴스 예시), `runtime-adaptation.md` (Phase 10 telemetry · capture 7종 이벤트 · drift 룰 · 승인 UX)
- **루트 `README.md`** — 프로젝트 진입점. 6 팀 아키텍처 패턴 표 + Quickstart 3단계 + 프로젝트 구조 트리 + 문서 인덱스 + 11 Phase 미리보기. 이전 README.md / README_KO.md / README_JA.md 부재 상태 해소
- **`skills/README.md`** — 스킬 디렉토리 인덱스. 수록 스킬 표 + harness 워크플로우 11 Phase + references 11개 매핑 표(파일 ↔ Phase) + 산출물 위치 다이어그램(`{사용자 프로젝트}/.claude/agents/`, `_workspace/_baseline/`, `_workspace/_telemetry/`) + 새 스킬 추가 5단계
- **산출물 체크리스트 3항목** — `_workspace/_telemetry/` 디렉토리 사전 생성, 오케스트레이터에 telemetry capture 훅 삽입(매 실행마다 `{date}.jsonl` append), Phase 10 트리거 키워드("점검", "drift", "적응", "baseline 갱신")를 오케스트레이터 description에 포함
- **Slash command 진입점 7종** (`commands/`) — description 매칭 확률에 의존하지 않는 **명시적 호출** 방식 추가. Phase 0 매트릭스와 1:1 매핑:
  - `/harness-new <도메인>` (Phase 0~8 전체, 신규 구축)
  - `/harness-add-agent <역할>` (Phase 4·5·7·8, baseline 재분석 회피)
  - `/harness-add-skill <스킬>` (Phase 6·7·8, 에이전트 정의 보존)
  - `/harness-baseline` (Phase 1·2 재실행 + drift 분석 리포트)
  - `/harness-audit` (Phase 9-5 §1 정합성 감사, read-only)
  - `/harness-evolve <피드백>` (Phase 9 수동 진화, 9-2 매핑)
  - `/harness-adapt` (Phase 10 Diagnostic + Adapt, telemetry 기반)
- **`commands/README.md`** — slash command 카탈로그 + 의사결정 트리 + 설계 원칙(얇은 진입점, 4섹션 패턴: 컨텍스트/선조건/실행/범위 외) + L1(플러그인 진입점) vs L2(사용자 산출물 금지) 구분 명시
- **자연어 트리거와 양립** — 두 호출 방식 모두 동일 SKILL.md 로직을 따르며 사용자가 상황에 따라 선택 가능

### Changed

- **Phase 0를 Pre-flight 메타 단계로 명확화** — "프로젝트 코드가 아니라 기존 하네스 산출물(`.claude/agents/`, `.claude/skills/`, `CLAUDE.md`) 감사"임을 인트로에 명시. 항상 실행 + 건너뛸 수 없음을 못박음. baseline 갱신 트리거 추가(사용자 명시 / Phase 10 큰 변화 감지 / 마지막 분석 후 3개월 경과)
- **Phase 4-2 패턴 표 변환** — 슬래시 구분 한 줄(파이프라인 / 팬아웃·팬인 / 전문가 풀 / 생성-검증 / 감독자 / 계층적 위임) → 6행 표(패턴명 + 한 줄 설명)로 가독성 향상
- **Phase 8 검증을 7단계로 통합** — "6단계 + 반복 개선" 분리 구조 → §7 "반복 개선"으로 승격하여 번호 일관성 부여(구조/모드/실행/트리거/드라이런/시나리오/반복 개선)
- **SKILL.md 슬림화** — 612줄 → 344줄(44% 감소). 각 Phase를 "골격(목적 한 줄 + 표/리스트 + references 포인터)"으로 압축, 상세는 references/로 이관. 자기 참조 가이드라인(SKILL.md 본문 ≤500줄) 충족. 모든 Phase 헤딩(0~10)과 sub-section 번호(7-0~5, 9-1~5, 10-1~5) 보존하여 cross-reference 무결성 유지
- **Phase 9·10 인트로 중복 제거** — "하네스는 한 번 만들고 끝나는 정적 산출물이 아니다" 동일 문장이 두 Phase에 중복 → Phase 10은 "Phase 9가 수동 / Phase 10이 자동"로 차별화 시작
- **참고 섹션 확장** — references 11개 한 곳에 인덱싱(기존 8개 → 11개). 본문 인라인 포인터 + 마지막 §참고 통합 인덱스 이중 안전망
- **SKILL.md 산출물 체크리스트 L2 한정 명시** — 기존 ".claude/commands/ — 아무것도 생성하지 않음"의 적용 범위가 모호 → "**사용자 프로젝트의** `.claude/commands/`에는 아무것도 생성하지 않음 (harness 플러그인 본체의 `commands/`는 별개 — L1 진입점)"으로 변경. L1(플러그인) vs L2(사용자 산출물) 구분 명문화
- **루트 `README.md`** — "호출 방식 두 가지" 섹션 + slash command 카탈로그 7개 추가, 프로젝트 구조 트리에 `commands/` 추가, 문서 인덱스에 `commands/README.md` 추가
- **`skills/README.md`** — harness 트리거 예시에 "또는 Slash command로 명시적 호출" 단락 추가, `commands/README.md` cross-link

## [1.2.1] - 2026-04-18

### Fixed

- **버전 정합성 동기화** — README.md / README_KO.md / README_JA.md 뱃지가 `v1.0.1`, `.claude-plugin/marketplace.json`이 `1.1.0`, `.claude-plugin/plugin.json`이 `1.2.0`으로 3중 불일치 → 모두 **v1.2.0**으로 통일 (plugin.json 기준)
- **태그드 릴리스 0건 상태 해소 준비** — v1.0.0 / v1.0.1 / v1.1.0 / v1.2.0 소급 태그 계획 작성 (`_workspace/release/audit-2026-04-18.md` §4 참조)

### Added

- **포지셔닝 선언: "harness factory"** — README 상단에 카테고리 자기 규정 문구를 도입. "에이전트 + 스킬을 도메인별로 찍어내는 하네스 팩토리"로 카테고리 선점 (단일 에이전트/프롬프트 프레임워크 대비 차별화)
- **CONTRIBUTING.md** — 기여 가이드 및 SLA 명시 (PR 1차 응답 72h, Issue triage 48h). 커뮤니티 온보딩 장벽 해소
- **docs/ 디렉토리** — 장기 문서(아키텍처, 마이그레이션, 패턴 카탈로그) 이전 공간 신설. README 비대화 방지 및 검색성 향상
- **Issue #3 응답 정책** — 커뮤니티 이슈에 대한 공식 응답 템플릿 및 트리아지 프로세스 추가

### Changed

- `.claude-plugin/marketplace.json` version: `1.1.0` → `1.2.0`
- README 뱃지 (EN/KO/JA 3종): `Version-1.0.1` → `Version-1.2.0`
- **`.claude-plugin/plugin.json` description 재작성** — `"Agent Team & Skill Architect — Meta-skill that designs..."` → `"The team-architecture factory for Claude Code — a meta-skill that turns a domain description into an agent team and the skills they use, with six pre-defined team-architecture patterns..."` (EN+KO 병기, L3 Meta-Factory 포지셔닝 반영)
- **`.claude-plugin/plugin.json` keywords 확장** — 5개 → 17개 (`harness-factory`, `team-architecture-factory`, `claude-code-plugin`, `agent-scaffolding`, `multi-agent`, 6패턴 키워드 6종 추가)

## [1.2.0] - 2026-04-08

### Changed

- **CLAUDE.md 등록 정책 간소화 (중복 제거)** — Phase 5-4 "컨텍스트 등록"을 "포인터 등록"으로 전환. 에이전트 목록·스킬 목록·디렉토리 구조·실행 규칙 상세를 CLAUDE.md에서 제거하고 **트리거 규칙 + 변경 이력**만 남김. 에이전트/스킬 목록은 `.claude/agents/`, `.claude/skills/` 및 오케스트레이터 스킬에서 단일 출처로 관리
- **Phase 3/4 임시 동기화 단계 삭제** — CLAUDE.md 동기화 부담을 줄이기 위해 Phase 3/4의 임시 동기화 지시 제거. 최종 포인터 등록은 Phase 5-4에서 1회만 수행
- **핵심 원칙 3번 재정의** — "CLAUDE.md에 하네스 컨텍스트를 등록한다" → "CLAUDE.md에 하네스 포인터를 등록한다"
- **CLAUDE.md vs 오케스트레이터 역할 분담표 삭제** — 포인터 정책으로 단순화되어 표 자체가 불필요해짐

### Added

- **Phase 2-1: 하이브리드 실행 모드** — 에이전트 팀 / 서브 에이전트에 더해 Phase별로 모드를 섞는 하이브리드 패턴 추가. 자주 쓰이는 조합(병렬 수집→합의 통합, 팀 생성→검증, Phase 간 팀 재구성) 명시
- **Phase 2-1 실행 모드 비교표** — 팀/서브/하이브리드 3종 특성 및 의사결정 순서 3단계 제공
- **Phase 5-0 하이브리드 오케스트레이터 패턴** — 하이브리드 구성 시 각 Phase 상단에 실행 모드를 명시하는 규칙
- **Phase 5-1 반환값 기반 데이터 전달** — 서브 에이전트 모드 전용 데이터 전달 전략 추가 (기존 메시지/태스크/파일 + 반환값)
- **Phase 5-1 권장 조합 (서브/하이브리드)** — 팀 모드 외 서브 모드와 하이브리드에서의 데이터 전달 권장 조합 명시

## [1.1.0] - 2026-04-05

### Added

- **Phase 0: 현황 감사** — 트리거 시 기존 하네스 상태를 먼저 확인하고 신규 구축/기존 확장/운영·유지보수 3분기로 라우팅
- **기존 확장 Phase 선택 매트릭스** — 에이전트 추가/스킬 추가/아키텍처 변경별 필요 Phase를 명시한 결정표
- **Phase 3/4 CLAUDE.md 임시 동기화** — 에이전트·스킬 생성 직후 CLAUDE.md에 즉시 반영 (세션 중단 내성)
- **Phase 5-4: CLAUDE.md 하네스 컨텍스트 등록** — 에이전트 팀 구조·스킬 목록·실행 규칙·디렉토리 구조·변경 이력을 기록. CLAUDE.md vs 오케스트레이터 역할 분담표 포함
- **Phase 5-5: 후속 작업 지원** — 오케스트레이터 description에 후속 키워드 필수 포함, Phase 0 컨텍스트 확인 단계로 초기/부분재실행/새실행 자동 판별
- **Phase 5 오케스트레이터 수정 경로** — 기존 확장 시 오케스트레이터를 새로 만들지 않고 수정하는 가이드
- **Phase 7: 하네스 진화 메커니즘** — 실행 후 피드백 수집 → 피드백 유형별 수정 대상 매핑 → 변경 이력 기록 → 자동 진화 트리거
- **Phase 7-5: 운영/유지보수 워크플로우** — 현황 감사→점진적 수정→CLAUDE.md 동기화→변경 검증 4단계
- **description에 운영/유지보수 트리거** — '하네스 점검', '하네스 감사', '하네스 현황', '에이전트/스킬 동기화' 키워드
- **산출물 체크리스트 강화** — CLAUDE.md 동기화 완료, 변경 이력 기록, Phase 0 컨텍스트 확인 항목 추가
- 오케스트레이터 템플릿에 Phase 0 (컨텍스트 확인) 추가 — 에이전트 팀/서브 에이전트 모드 모두 적용
- 오케스트레이터 description 템플릿에 후속 작업 키워드 패턴 포함

### Changed

- 핵심 원칙 2개 → 4개로 확장 (CLAUDE.md 등록, 진화 시스템 추가)
- **"진화 로그" → "변경 이력" 통일** — 이름과 스키마(4컬럼: 날짜/변경내용/대상/사유)를 전 섹션에서 일원화
- **Phase 1 Step 3** — Phase 0 감사 결과를 기반으로 충돌 분석하도록 변경 (중복 제거)
- **5-4 CLAUDE.md 템플릿 코드 블록** — 중첩 렌더링 깨짐 수정 (3백틱→4백틱)
- **역할 분담표 확장** — 스킬 목록, 디렉토리 구조, 변경 이력 행 추가
- **오케스트레이터 템플릿** — Phase 0 컨텍스트 확인 단계, 후속 작업 키워드 가이드 추가

## [1.0.1] - 2026-03-28

### Changed

- SKILL.md ↔ references 간 중복 내용 제거 (330줄 → 285줄)
  - Phase 2-1: 실행 모드 비교표/불릿 → 핵심 원칙 + agent-design-patterns.md 포인터
  - Phase 2-3: 에이전트 분리 기준 불릿 → 4축 요약 + agent-design-patterns.md 포인터
  - Phase 3: 에이전트 정의 템플릿 코드블록 → 필수 섹션 나열 + references 포인터
  - Phase 5-2: 에러 핸들링 5행 테이블 → 핵심 원칙 + orchestrator-template.md 포인터

## [1.0.0] - 2026-03-27

### Added

- 6 Phase 워크플로우 기반 하네스 구성 메타 스킬
- 6가지 에이전트 아키텍처 패턴 (파이프라인, 팬아웃/팬인, 전문가 풀, 생성-검증, 감독자, 계층적 위임)
- 에이전트 팀 / 서브 에이전트 실행 모드 지원
- Progressive Disclosure 기반 스킬 생성 가이드
- 오케스트레이터 템플릿 (에이전트 팀 모드 + 서브 에이전트 모드)
- QA 에이전트 통합 가이드 (실제 프로젝트 7개 버그 사례 기반)
- 스킬 테스트/평가 방법론 (With-skill vs Without-skill 비교)
- 실전 팀 구성 예시 5종 (리서치, 소설, 웹툰, 코드리뷰, 마이그레이션)
