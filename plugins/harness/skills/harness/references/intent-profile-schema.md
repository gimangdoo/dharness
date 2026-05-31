# Intent Profile Schema

> **Read at phase:** Phase 2 (Project Inquiry 출력 형식). `required:` 배열 + `confidence_low` + `source` 박제 (2026-05-14 M2 + P6-4 + P6-6).

Phase 2 Project Inquiry의 표준 출력 형식. 사용자의 주관적 의도·제약·우선순위를 7개 섹션으로 구조화한 schema.

---

## 목차

1. [개요](#1-개요)
2. [Schema 풀 명세](#2-schema-풀-명세)
3. [필수 vs 선택 필드](#3-필수-vs-선택-필드)
4. [파일 형식](#4-파일-형식)
5. [메타 필드 의미](#5-메타-필드-의미)
6. [인스턴스 예시](#6-인스턴스-예시) — greenfield/brownfield 예시는 [intent-profile-examples.md](./intent-profile-examples.md)로 분리
7. [검증 룰](#7-검증-룰)

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
  compliance:                           # P6-10 신규 (2026-05-14) — regulatory 박제
    regulatory: [string]                # enum 다중: GDPR | HIPAA | PCI-DSS | SOX | SOC2 | ISO27001 | KISA | GxP | none
    data_handling:                      # 처리 데이터 민감도
      pii: bool | unknown
      phi: bool | unknown
      pci: bool | unknown
      financial: bool | unknown
    audit_retention_days: int | null    # 감사 로그 보존 기간 (compliance-driven)

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
  methodology: tdd | bdd | ddd | spec-driven | trunk-based | kanban | scrum | shape-up | xp | none | unknown   # 2026-05-24, methodology-advisor plugin handoff 수신. 자유 텍스트 enum 외 값 시 schema 위반.
  methodology_source: advisor | user | inferred | none   # 채움 출처. advisor=methodology-advisor plugin handoff, user=사용자 직접 응답, inferred=brownfield 자동 추론(jest.config·gherkin·OpenAPI 등 signal), none=미수집.
  methodology_matrix_row: string | null         # advisor handoff 시 decision-matrix.md row id (예: "row-07"). 비-advisor source 시 null.

meta:
  open_questions: [string]              # 스킵되거나 미결정된 항목
  explicit_assumptions: [string]        # 사용자가 명시한 전제. 예: "팀이 React 익숙함"
  inferred_fields: [string]             # brownfield 전용. dot-path로 표기 (예: "constraints.tech_stack.locked_in")
  user_confirmed_fields: [string]       # 사용자가 직접 확인/수정한 필드. dot-path
  confidence_low: [string]              # P6-6 신규 (2026-05-14) — confidence 낮은 필드 dot-path. Phase 10 drift 가중치 0.7 이하 룰 활성
  source: { string: string }            # P6-4 신규 (2026-05-14) — inferred_fields 항목별 source 인용. dot-path → manifest 경로 매핑. 인용 0이면 schema 위반 → Phase 1 재합성 트리거.
  grilling_log: [grilling_entry]        # 옵션 (2026-05-19, grill-me 흡수 Phase B). grilling 진입 시에만 박제. 미박제 시 schema 위반 아님 — 정합 검사 silent skip.
  dharness_version: string              # 합성 시점 plugin `version` (`plugins/harness/.claude-plugin/plugin.json` `version` 값). harness-new·harness-evolve(baseline op)가 박제. doctrine drift 진단의 기준점 — `harness-validate`/`harness-status`가 현 plugin version과 비교해 upgrade 여부 1줄 보고 (2026-05-23, doctrine drift refit 인프라).
  advisor_secondary_methodologies: [string]   # 2026-05-24, v0.12.1 adapter doctrine. advisor가 list로 반환한 4축 합성 중 primary(첫 번째 lowercase 정규화) 외 secondary 박제 (재현성·진화 비교용). `methodology_source: advisor` 외 시 미박제 (=schema 위반 아님, 옵션 필드).
  advisor_handoff_version: string             # 2026-05-24, v0.12.1 adapter doctrine. advisor가 출력한 free string `methodology_source` 원본 (예: "methodology-advisor v0.3.1"). dharness 측은 `workflow.methodology_source`를 enum `advisor`로 정규화하면서 원 문자열을 본 필드에 박제 — re-grilling 시 버전 회상 가능.

# grilling_entry 구조 (meta.grilling_log[] 원소)
grilling_entry:
  phase: "0.5" | "2" | "5" | "9"        # grilling 진입 phase
  field: string                          # 대상 필드 dot-path (예: "constraints.team.size")
  mode: "grilling"                       # 고정값 — batch 분기는 본 로그 미박제
  recommended: string                    # LLM이 제시한 추천 답안 값
  recommended_source: string             # 추천 출처 — "signals>=2" / "section_3_1_direct" / "section_3_2_estimate" 중 1개. 디렉토리·파일 이름 단독 시 schema 위반
  user_response: string                  # 사용자 raw 응답 (예: "맞음" / "수정 — solo" / "모르겠음" / "코드 봐")
  timestamp: string                      # ISO8601

required:                               # P6-10 / M2 (2026-05-14) — 다운스트림 hard-code 신뢰 박제
                                        # 정본: scripts/validate/schema.py:INTENT_REQUIRED.
                                        # doc ↔ schema sync은 chain.py:check_intent_required_doc_sync 결정적 검증.
                                        # 2026-05-28 audit2 PA8 — meta.dharness_version 필수 격상 (I2 anchor 강제).
  - constraints.tech_stack
  - constraints.team.size
  - constraints.timeline.horizon
  - architecture.deployment_target
  - quality.test_rigor
  - meta.dharness_version
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
| `methodology` | tdd / bdd / ddd / spec-driven / trunk-based / kanban / scrum / shape-up / xp / none / unknown | 개발 방법론. methodology-advisor plugin handoff 또는 사용자 직접 응답으로 채움. `unknown`=advisor 호출 미수행 + 사용자 미응답. |
| `methodology_source` | advisor / user / inferred / none | 채움 출처. `advisor` 시 `methodology_matrix_row` 필수. |

---

## 3. 필수 vs 선택 필드

### 필수 6개 (스킵 불가)

다운스트림 Phase가 이 값 없이는 결정을 내릴 수 없는 핵심 필드:

| 필드 | 사용처 |
|------|--------|
| `constraints.tech_stack` | Phase 6 스킬 생성 시 프레임워크 관용구 결정 |
| `constraints.team.size` | Phase 4 팀 크기 가이드라인 적용 |
| `constraints.timeline.horizon` | Phase 5 QA 에이전트 강도, Phase 8 검증 깊이 결정 |
| `architecture.deployment_target` | Phase 4 에이전트 분리 축 결정 |
| `quality.test_rigor` | Phase 5 QA 에이전트 포함 여부 결정 |
| `meta.dharness_version` | I2 doctrine drift refit anchor — `harness-validate`/`harness-status`가 upgrade 진단의 t=0 기준 (2026-05-28 audit2 PA8 격상) |

이 6개가 비어 있으면 Phase 2를 종료하지 않고 재질문한다. `meta.dharness_version`은 `harness-new`/`harness-evolve`(baseline op)가 합성 시점 plugin version으로 자동 박제 — 사용자 raw 답변 불요 (LLM 박제).

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
| `grilling_log` | grilling 모드 진입 시 question별 1 entry 박제 (2026-05-19, `grilling-loop.md`) | Phase 10 사용 drift 분석 — 같은 필드 반복 grilling 시 baseline 갱신 시그널. 미박제 시 검사 silent skip. |
| `dharness_version` | `harness-new`·`harness-evolve`(baseline op) 합성·갱신 시점 | `harness-validate`/`harness-status`가 현 plugin version과 비교 → upgrade 발생 시 사용자에게 doctrine refit 권고 1줄 (status --deep + validate 조합 → 발견 항목별 evolve 내부 op로 수정). |

### 신뢰도 차집합

> **`inferred_fields − user_confirmed_fields` = 자동 추론만 된 미확인 필드**

이 차집합이 클수록 baseline 신뢰도가 낮음. Phase 10 Runtime Adaptation이 이 필드들을 변경할 때는 가중치를 낮추거나 우선 사용자 확인을 트리거한다.

---

## 6. 인스턴스 예시

> greenfield/brownfield 완성 인스턴스 예시 2종은 [intent-profile-examples.md](./intent-profile-examples.md) 단일 출처로 분리 (2026-05-31 doc 분할). 필드 의미는 [§2 Schema 풀 명세](#2-schema-풀-명세) 참조.

---

## 7. 검증 룰

Phase 2 종료 시 intent_profile.md가 다음 룰을 통과해야 한다.

### 필수 룰 (실패 시 Phase 2 재진입)

| 룰 | 검증 방법 |
|----|---------|
| `version` 존재 | frontmatter 최상위에 `version: 1` |
| `project_type` 존재 | `greenfield` 또는 `brownfield` |
| 필수 5개 필드 채워짐 | 위 [3장](#3-필수-vs-선택-필드) 참조 |
| brownfield는 `inferred_fields` 비어있지 않음 | Code Research 결과가 반드시 1개 이상 추론 가능 |

### 권장 룰 + LLM-only cross-field 경고

LLM-only 권장 룰(`meta.explicit_assumptions`/`scope.out_of_scope`/`vision.success_definition` 측정성) + cross-field 경고 3종(prod+test=none / solo+strict / regulated+empty-security) → `intent-profile-advisory.md` 단일 출처 (2026-05-27 PB5 분리). chain.py 비강제 — Phase 2 LLM 자기검증.

### Cross-field deterministic invariant

| 조합 | 룰 | 채널 |
|------|----|---|
| `version` 존재 | C14-1 — frontmatter 최상위 `version: 1` | `chain_intent.py:check_intent_profile_version` |
| `project_type` enum | C14-2 — `greenfield`/`brownfield` | `chain_intent.py:check_intent_profile_project_type` |
| brownfield → `inferred_fields` 1+ | C14-3 — Code Research 결과 1+ | `chain_intent.py:check_intent_profile_brownfield_inferred` |
| `project_type = greenfield` + `constraints.tech_stack.locked_in != []` | C15-4 모순 — greenfield인데 locked-in 보유 | `chain_intent.py:check_intent_profile_greenfield_locked_in` |
| advisor cross-field invariant 5종 | → `advisor-integration.md §2` 단일 출처 (PB6 분리) | `chain_advisor.py:check_advisor_handoff_adapter_consistency` |

검증 실패 시 사용자에게 해당 룰과 이유를 제시하고 응답을 요구한다. 사용자가 의도된 것이라 응답하면 `meta.explicit_assumptions`에 "{룰} 의도적 위반: {사용자 이유}"로 기록.

### Advisor handoff 변환 룰

methodology-advisor plugin v0.3.x 출력 yaml → dharness intent_profile frontmatter 단방향 변환 룰은 `advisor-integration.md §1` 단일 출처 (2026-05-27 PB6 분리).
