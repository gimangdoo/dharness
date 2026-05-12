# Intent Profile Schema

Phase 2 Project Inquiry의 표준 출력 형식. 사용자의 주관적 의도·제약·우선순위를 7개 섹션으로 구조화한 schema.

---

## 목차

1. [개요](#1-개요)
2. [Schema 풀 명세](#2-schema-풀-명세)
3. [필수 vs 선택 필드](#3-필수-vs-선택-필드)
4. [파일 형식](#4-파일-형식)
5. [메타 필드 의미](#5-메타-필드-의미)
6. [Greenfield 인스턴스 예시](#6-greenfield-인스턴스-예시)
7. [Brownfield 인스턴스 예시](#7-brownfield-인스턴스-예시)
8. [검증 룰](#8-검증-룰)

---

## 1. 개요

### 왜 표준 schema인가

Phase 3 이후의 모든 단계(Domain Analysis, Team Architecture, Skill 생성, Validation)는 사용자 의도를 입력으로 받는다. 이 입력이 자유 텍스트면 매번 다른 형태로 들어와 다운스트림 로직이 ad-hoc 파싱에 의존하게 된다. **schema가 단일 contract여야 Phase 3-9가 결정적이고 테스트 가능해진다.**

### 핵심 설계 원칙

1. **greenfield/brownfield schema 공유** — `project_type` 필드만 다르다. 채우는 전략은 다르지만 출력 contract는 동일.
2. **enum 우선** — 자유 텍스트는 최소화. 가능한 한 선택지 기반으로 사용자 입력을 받는다. 모바일에서 타이핑 부담 감소 + 다운스트림 분기 결정성 향상.
3. **추론과 명시 구분** — brownfield에서 자동 추론된 필드와 사용자가 직접 확인한 필드를 `meta`에서 구분 추적. Phase 10 Runtime Adaptation의 가중치 결정에 사용.
4. **누락 명시** — 스킵된 필드는 침묵하지 않고 `meta.open_questions`에 등록. 미래의 보완 시점을 위한 신호.

---

## 2. Schema 풀 명세

```yaml
version: 1                              # schema 버전. 향후 마이그레이션 추적용
project_type: greenfield | brownfield   # 분기 결정 (Phase 1에서 결정됨)

vision:
  problem_statement: string             # 이 프로젝트가 해결하려는 문제 (1-2문장)
  target_users: [string]                # 주 사용자 그룹. 예: ["내부 운영팀", "B2B 고객사"]
  success_definition: string            # 성공의 정의. 측정 가능한 형태 권장

scope:
  initial_milestone: string             # 첫 번째 검증할 가설 또는 마일스톤
  must_have: [string]                   # MVP 핵심 기능 목록
  out_of_scope: [string]                # 명시적으로 제외할 기능. "지금은 안 함"

constraints:
  tech_stack:
    preferred: [string]                 # 선호 기술. 예: ["Next.js", "PostgreSQL"]
    forbidden: [string]                 # 사용 금지. 예: ["jQuery"], 라이선스 이슈 등
    locked_in: [string]                 # brownfield 전용. 이미 도입되어 변경 불가
  team:
    size: solo | small | medium | large # solo=1, small=2-5, medium=6-15, large=16+
    expertise: junior | mid | senior | mixed
  timeline:
    horizon: prototype | mvp | production
    deadline: string | null             # ISO 날짜 또는 자유 텍스트("Q3 2026")

architecture:
  deployment_target: [web | mobile | desktop | server | embedded]   # 다중 선택 가능
  scale_expectation: toy | smb | enterprise   # toy=개인/실험, smb=중소규모, enterprise=대규모
  data_sensitivity: none | personal | regulated  # regulated=GDPR/HIPAA 등 법적 규제

quality:
  test_rigor: none | smoke | unit | integration | tdd
  documentation_level: none | code_comments | api | full
  security_requirements: [string]       # 자유 텍스트 가능. 예: ["OAuth2", "암호화 저장"]

workflow:
  collaboration_mode: solo | pair | team
  review_style: none | self | peer | strict   # strict=2인 이상 승인 필요
  ci_cd: none | lint | test | full_pipeline

meta:
  open_questions: [string]              # 스킵되거나 미결정된 항목
  explicit_assumptions: [string]        # 사용자가 명시한 전제. 예: "팀이 React 익숙함"
  inferred_fields: [string]             # brownfield 전용. dot-path로 표기 (예: "constraints.tech_stack.locked_in")
  user_confirmed_fields: [string]       # 사용자가 직접 확인/수정한 필드. dot-path
```

### Enum 값 의미 보충

| 필드 | 값 | 의미 |
|------|-----|------|
| `team.size` | solo / small / medium / large | 1 / 2-5 / 6-15 / 16+ |
| `timeline.horizon` | prototype | 검증용. 일회성 가능, 코드 품질 후순위 |
| | mvp | 실사용자 대상. 핵심 기능 동작 보장 |
| | production | 장기 운영. 안정성·확장성 우선 |
| `scale_expectation` | toy | 개인/실험. 동시 사용자 < 10 |
| | smb | 중소 규모. 동시 사용자 ~수천 |
| | enterprise | 대규모. 가용성·SLA 요구 |
| `test_rigor` | none / smoke / unit / integration / tdd | 점차 강화. tdd=test-first |
| `review_style` | none / self / peer / strict | 코드 리뷰 강도 |

---

## 3. 필수 vs 선택 필드

### 필수 5개 (스킵 불가)

다운스트림 Phase가 이 값 없이는 결정을 내릴 수 없는 핵심 필드:

| 필드 | 사용처 |
|------|--------|
| `constraints.tech_stack` | Phase 6 스킬 생성 시 프레임워크 관용구 결정 |
| `constraints.team.size` | Phase 4 팀 크기 가이드라인 적용 |
| `constraints.timeline.horizon` | Phase 5 QA 에이전트 강도, Phase 8 검증 깊이 결정 |
| `architecture.deployment_target` | Phase 4 에이전트 분리 축 결정 |
| `quality.test_rigor` | Phase 5 QA 에이전트 포함 여부 결정 |

이 5개가 비어 있으면 Phase 2를 종료하지 않고 재질문한다.

### 선택 필드

나머지 모든 필드. 스킵 시 `meta.open_questions`에 항목 추가:

```yaml
meta:
  open_questions:
    - "vision.target_users (미결정 — Phase 2-2 단계 1에서 스킵)"
    - "scope.out_of_scope (사용자 응답: '나중에 결정')"
```

이렇게 등록된 open_questions는 Phase 10 Runtime Adaptation이 적절한 시점에 보충 질문을 트리거할 후보가 된다.

---

## 4. 파일 형식

### 위치
`_workspace/_baseline/intent_profile.md`

### 구조
YAML frontmatter (구조화 enum/list 필드) + 마크다운 본문 (자유 텍스트 서술 필드).

```markdown
---
version: 1
project_type: greenfield
constraints:
  tech_stack:
    preferred: [Next.js, PostgreSQL]
    forbidden: []
  team:
    size: small
    expertise: mid
  ...
---

# Intent Profile

## Vision

### Problem Statement
{자유 텍스트로 서술}

### Target Users
- 내부 운영팀 (1차 사용자)
- 외부 파트너 (2차 사용자, 6개월 후)

### Success Definition
{자유 텍스트}

## Scope
...

## Meta

### Open Questions
- ...

### Explicit Assumptions
- ...
```

자유 텍스트 필드(`problem_statement`, `success_definition`, `initial_milestone`)는 본문 섹션에, 구조화 필드는 frontmatter에. 다운스트림 파서는 frontmatter를 우선 읽고, 자유 텍스트는 헤딩 기반으로 추출한다.

---

## 5. 메타 필드 의미

`meta` 섹션은 schema의 다른 섹션과 성격이 다르다 — 사용자의 의도가 아니라 **수집 과정 자체에 대한 메타데이터**이다.

| 필드 | 채우는 시점 | 다운스트림 활용 |
|------|-----------|--------------|
| `open_questions` | 사용자가 스킵하거나 "모르겠음" 응답 시 | Phase 10이 보충 질문 시점 결정 |
| `explicit_assumptions` | 사용자가 자유 입력으로 추가 | Phase 3 도메인 분석 시 가정 명시 |
| `inferred_fields` | brownfield 자동 추론 직후 | "신뢰도 낮음" 표시 |
| `user_confirmed_fields` | 사용자가 추론 결과를 확인/수정 시 | "신뢰도 높음" 표시 |

### 신뢰도 차집합

> **`inferred_fields − user_confirmed_fields` = 자동 추론만 된 미확인 필드**

이 차집합이 클수록 baseline 신뢰도가 낮음. Phase 10 Runtime Adaptation이 이 필드들을 변경할 때는 가중치를 낮추거나 우선 사용자 확인을 트리거한다.

---

## 6. Greenfield 인스턴스 예시

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
  user_confirmed_fields: []
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
- `inferred_fields`, `user_confirmed_fields`가 빈 배열 — greenfield는 추론 대상이 없음
- `out_of_scope` 명시로 향후 scope creep 방지 신호
- `open_questions`에 미결정 항목을 솔직히 등록 → Phase 10이 추후 트리거 가능

---

## 7. Brownfield 인스턴스 예시

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

### User Confirmed Fields (4개)
- locked_in, deployment_target, ci_cd, test_rigor

### Inferred but NOT Confirmed (2개 — 신뢰도 낮음)
- `workflow.collaboration_mode`, `constraints.team.size`
  → Phase 10이 변경 시도할 때 우선 사용자 확인 트리거
```

**주의 깊게 볼 점:**
- `locked_in`이 채워짐 — brownfield의 식별 신호
- `inferred_fields − user_confirmed_fields = 2개` → 미확인 필드 명시
- `open_questions`에 코드 grounded 질문의 미결정 답변이 들어감
- frontmatter의 enum + 본문의 자유 서술이 자연스럽게 섞임

---

## 8. 검증 룰

Phase 2 종료 시 intent_profile.md가 다음 룰을 통과해야 한다.

### 필수 룰 (실패 시 Phase 2 재진입)

| 룰 | 검증 방법 |
|----|---------|
| `version` 존재 | frontmatter 최상위에 `version: 1` |
| `project_type` 존재 | `greenfield` 또는 `brownfield` |
| 필수 5개 필드 채워짐 | 위 [3장](#3-필수-vs-선택-필드) 참조 |
| brownfield는 `inferred_fields` 비어있지 않음 | Code Research 결과가 반드시 1개 이상 추론 가능 |

### 권장 룰 (실패 시 경고)

| 룰 | 의미 |
|----|------|
| `meta.explicit_assumptions` 1개 이상 | 모든 프로젝트는 가정이 있다. 비어있으면 사용자가 충분히 사고하지 않은 신호 |
| `scope.out_of_scope` 1개 이상 | scope creep 방지를 위한 명시적 제외 항목 |
| `vision.success_definition`이 측정 가능 | "사용자 만족도 향상" 같은 측정 불가 표현 회피 권장 |

### Cross-field 룰

| 조합 | 룰 |
|------|----|
| `timeline.horizon = production` + `quality.test_rigor = none` | 경고: production에 테스트 없음은 위험 |
| `team.size = solo` + `workflow.review_style = strict` | 경고: 1인이 strict 리뷰 불가능 |
| `data_sensitivity = regulated` + `quality.security_requirements = []` | 경고: regulated 데이터인데 보안 요구사항 미정의 |
| `project_type = greenfield` + `constraints.tech_stack.locked_in != []` | 모순: greenfield인데 locked-in이 있음 |

검증 실패 시 사용자에게 해당 룰과 이유를 제시하고 응답을 요구한다. 사용자가 의도된 것이라 응답하면 `meta.explicit_assumptions`에 "{룰} 의도적 위반: {사용자 이유}"로 기록.
