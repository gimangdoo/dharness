# Intent Profile 인스턴스 예시

> **베이스 스키마:** [intent-profile-schema.md](./intent-profile-schema.md) — 본 문서는 greenfield/brownfield 인스턴스 예시 분리분 (2026-05-31 doc 분할). 필드 명세·필수 룰·검증 룰은 베이스 스키마 단일 출처.

Phase 2 Project Inquiry 출력 `intent_profile.md`의 완성 예시 2종. schema 필드 의미는 [intent-profile-schema.md §2](./intent-profile-schema.md#2-schema-풀-명세) 참조.

---

## 1. Greenfield 인스턴스 예시

가상 프로젝트: "사내 회의록 자동 요약 도구" (개인 사이드 프로젝트)

```markdown
---
version: 1
project_type: greenfield

vision:
  target_users:
    - "개인 (1차)"
    - "팀 동료 (2차, 검증 후)"

scope:
  must_have:
    - "음성 파일 업로드"
    - "화자 분리 + 요약"
    - "Markdown export"
  out_of_scope:
    - "실시간 전사"
    - "다국어 지원"

constraints:
  tech_stack:
    preferred: [Python, FastAPI, OpenAI Whisper API]
    forbidden: []
    locked_in: []
  team:
    size: solo
    expertise: senior
  timeline:
    horizon: prototype
    deadline: null

architecture:
  deployment_target: [web]
  scale_expectation: toy
  data_sensitivity: personal

quality:
  test_rigor: smoke
  documentation_level: code_comments
  security_requirements: []

workflow:
  collaboration_mode: solo
  review_style: self
  ci_cd: lint

meta:
  open_questions:
    - "scope.initial_milestone — '첫 회의록 요약 성공'으로 충분한지 추후 재검토"
  explicit_assumptions:
    - "OpenAI API 비용은 개인 부담 가능 범위"
    - "음성 파일은 1시간 이내 길이만 가정"
  inferred_fields: []
  user_confirmed_fields:
    - constraints.tech_stack
    - constraints.team.size
    - constraints.timeline.horizon
    - architecture.deployment_target
    - quality.test_rigor
---

# Intent Profile

## Vision

### Problem Statement
회의 후 30분~1시간씩 회의록 정리에 쓰는 시간을 5분 이내로 줄이고 싶다.
화자별 발언과 액션 아이템을 자동 추출해 Markdown으로 받는 것이 목표.

### Success Definition
- 1시간 회의 → 5분 이내 요약 생성
- 화자 분리 정확도 80% 이상 (체감 기준)
- 액션 아이템 누락 < 1건/회의

## Scope

### Initial Milestone
"녹음 파일 1개 업로드 → 화자 분리된 Markdown 회의록 출력"이 동작하는 최소 파이프라인.

## Meta

### Explicit Assumptions
- OpenAI API 비용은 개인 부담 범위 내 (월 $20 이하 가정)
- 입력 음성은 한국어 1시간 이내 파일만 지원
```

**주의 깊게 볼 점:**
- `inferred_fields`가 빈 배열 — greenfield는 추론 대상이 없음
- `user_confirmed_fields`에 INTENT_REQUIRED 5필드 모두 등록 — 사용자 raw 답변으로 채움 (W3 doctrine 강제, `chain.py:check_required_user_confirmed_fields`)
- `out_of_scope` 명시로 향후 scope creep 방지 신호
- `open_questions`에 미결정 항목을 솔직히 등록 → Phase 10이 추후 트리거 가능

---

## 2. Brownfield 인스턴스 예시

가상 프로젝트: "기존 Next.js 커머스 사이트에 추천 시스템 추가"

```markdown
---
version: 1
project_type: brownfield

vision:
  target_users:
    - "기존 구매 고객 (재방문)"
    - "신규 방문자 (회원 가입 전)"

scope:
  must_have:
    - "상품 상세 페이지 하단 추천 섹션"
    - "장바구니 연관 상품"
  out_of_scope:
    - "실시간 개인화 (1차 범위 제외)"
    - "외부 광고 네트워크 연동"

constraints:
  tech_stack:
    preferred: [PostgreSQL pgvector]
    forbidden: []
    locked_in: [Next.js 14, TypeScript, Prisma, Tailwind]
  team:
    size: small
    expertise: mixed
  timeline:
    horizon: production
    deadline: "2026-09-30"

architecture:
  deployment_target: [web]
  scale_expectation: smb
  data_sensitivity: personal

quality:
  test_rigor: integration
  documentation_level: api
  security_requirements:
    - "사용자 행동 로그는 익명화 후 저장"
    - "추천 모델 학습 데이터에서 PII 제거"

workflow:
  collaboration_mode: team
  review_style: peer
  ci_cd: full_pipeline

meta:
  open_questions:
    - "추천 알고리즘 선택 (협업 필터링 vs 임베딩 기반) — POC 후 결정"
    - "scope.must_have의 '연관 상품' 정의 — 함께 구매 vs 함께 조회 미정"
  explicit_assumptions:
    - "기존 구매 로그 6개월치 사용 가능"
    - "추천 응답 시간 < 200ms 요구"
  inferred_fields:
    - "constraints.tech_stack.locked_in"
    - "architecture.deployment_target"
    - "workflow.ci_cd"
    - "quality.test_rigor"
    - "workflow.collaboration_mode"
    - "constraints.team.size"
  user_confirmed_fields:
    - "constraints.tech_stack.locked_in"
    - "architecture.deployment_target"
    - "workflow.ci_cd"
    - "quality.test_rigor"
    - "constraints.team.size"
    - "constraints.timeline.horizon"
---

# Intent Profile

## Vision

### Problem Statement
구매 전환율이 정체. 상품 페이지 이탈률 높음. 추천을 통해
세션당 페이지뷰와 장바구니 추가율을 높이고자 함.

### Success Definition
- 상품 상세 페이지 이탈률 -10%p
- 추천 클릭률(CTR) ≥ 5%
- 장바구니 추가율 +15%

## Scope

### Initial Milestone
"상품 상세 페이지에 정적 추천 섹션 노출 + CTR 측정 가능" 상태 도달.
초기엔 인기 상품 기반 룰베이스도 허용 (POC).

## Constraints

### Tech Stack Locked-in
- Next.js 14 (App Router) — package.json 매니페스트에서 확인
- Prisma — schema.prisma 존재
- Tailwind — tailwind.config.ts 존재

### Forbidden
없음 (사용자 응답).

## Quality

### Security Requirements
- 사용자 행동 로그는 익명화 후 저장 (GDPR 대응 미흡 영역 보완)
- 추천 모델 학습 데이터에서 PII 제거

## Meta

### Open Questions
- 추천 알고리즘 선택 (협업 필터링 vs 임베딩 기반) — POC 후 결정
- "연관 상품" 정의 (함께 구매 vs 함께 조회) — 사용자 미결정

### Inferred Fields (자동 추론, 6개)
- `constraints.tech_stack.locked_in` ← package.json
- `architecture.deployment_target` ← next.config 빌드 설정
- `workflow.ci_cd` ← .github/workflows/ 디렉토리
- `quality.test_rigor` ← jest.config + 커버리지 67%
- `workflow.collaboration_mode` ← git contributors 5명
- `constraints.team.size` ← contributor 수 기반 추정

### User Confirmed Fields (6개 — INTENT_REQUIRED 5필드 모두 커버)
- locked_in (= `constraints.tech_stack`), deployment_target, ci_cd, test_rigor, team.size, timeline.horizon

### Inferred but NOT Confirmed (1개 — 신뢰도 낮음)
- `workflow.collaboration_mode`
  → Phase 10이 변경 시도할 때 우선 사용자 확인 트리거
```

**주의 깊게 볼 점:**
- `locked_in`이 채워짐 — brownfield의 식별 신호
- INTENT_REQUIRED 5필드(`constraints.tech_stack`/`team.size`/`timeline.horizon`/`architecture.deployment_target`/`quality.test_rigor`) 모두 `user_confirmed_fields` 등록 — W3 doctrine 강제 (`chain.py:check_required_user_confirmed_fields`). brownfield 자동 추론 항목도 *사용자 확인 답변* 받은 후에만 등록 — inferred-only는 doctrine 불충족.
- `inferred_fields − user_confirmed_fields = 1개` → 미확인 필드 명시
- `open_questions`에 코드 grounded 질문의 미결정 답변이 들어감
- frontmatter의 enum + 본문의 자유 서술이 자연스럽게 섞임
