# Project Inquiry 가이드

Phase 2 Project Inquiry의 실행 가이드. `project_profile.md`(객관 신호, 선택)와 사용자 발화를 입력으로 `intent_profile.md`(`references/intent-profile-schema.md`의 schema 준수)를 채우는 절차·추론 매핑·질문 생성 룰.

---

## 목차

1. [개요](#1-개요)
2. [두 브랜치 채우기 전략](#2-두-브랜치-채우기-전략)
3. [자동 추론 매핑 테이블](#3-자동-추론-매핑-테이블)
4. [질문 생성 룰](#4-질문-생성-룰)
5. [섹션별 질문 카탈로그](#5-섹션별-질문-카탈로그)
6. [코드 grounded 질문 패턴](#6-코드-grounded-질문-패턴)
7. [필수 필드 재질문 룰](#7-필수-필드-재질문-룰)
8. [검증 룰](#8-검증-룰)

---

## 1. 개요

### 이 문서의 목적

Phase 2의 두 가지 표준 산출물 — **(a) 채우기 전략**과 **(b) 매핑 테이블** — 을 한 곳에 정리한다. SKILL.md Phase 2-2 / 2-3은 이 문서를 호출하는 진입점이며, 실제 매핑·질문 패턴·예시 응답은 여기에 위치한다.

### 입력 / 출력

| | greenfield | brownfield |
|---|---|---|
| 입력 | 사용자 발화만 | `project_profile.md` + 사용자 발화 |
| 출력 | `intent_profile.md` (frontmatter + body) | 동일 |
| `meta.inferred_fields` | `[]` | 1개 이상 |
| `meta.user_confirmed_fields` | `[]` | inferred 중 사용자가 확인한 부분집합 |

### 핵심 원칙

1. **schema 공유, 전략 분기** — 출력 contract는 동일. 다운스트림은 `project_type` 필드만 보고 분기한다 (SKILL.md 2-1).
2. **enum 우선, 자유 텍스트 최소화** — 모바일 타이핑 부담 + 다운스트림 분기 결정성.
3. **추론은 근거와 함께** — 자동 추론된 필드는 항상 source(파일 경로·신호)를 제시한다. 근거 없는 추론은 사용자 신뢰를 잃는다.
4. **스킵은 침묵하지 않는다** — 비워둔 필드는 `meta.open_questions`에 등록하여 Phase 10이 추후 보충할 수 있게 한다.

---

## 2. 두 브랜치 채우기 전략

### 2-1. Greenfield 전략

baseline이 없으므로 schema의 모든 필드를 사용자 입력으로 채운다.

**진행 절차:**

| 단계 | 동작 |
|------|------|
| 1. 인사 + 프로젝트 한 줄 소개 요청 | 첫 응답으로 `vision.problem_statement`의 초안 확보 |
| 2. 7개 섹션 순차 진행 | vision → scope → constraints → architecture → quality → workflow → meta |
| 3. 매 섹션 시작 시 진행률 표시 | "**3/7 — Constraints**" 형태 |
| 4. 필드 타입별 입력 방식 적용 | [§4-1](#4-1-필드-타입별-입력-방식) |
| 5. 필수 5개 검증 | 비어 있으면 [§7](#7-필수-필드-재질문-룰) 룰로 재질문 |
| 6. 종료 시 요약 보여주고 확인 | 최종 frontmatter 출력 후 "이대로 저장할까요?" |

**스킵 처리:** 필수 5개를 제외한 모든 필드는 "건너뛸게요" / "모르겠어요" 응답을 허용. 스킵된 필드는 `meta.open_questions`에 다음 형식으로 등록:

```yaml
open_questions:
  - "vision.target_users (Phase 2 단계에서 스킵)"
  - "scope.out_of_scope (사용자 응답: '나중에 결정')"
```

### 2-2. Brownfield 전략

`project_profile.md`가 schema의 60~70%를 자동 채운 상태에서 시작. 4단계로 진행.

| 단계 | 동작 | 사용자 부담 | 출력 |
|------|------|-----------|------|
| **1. 자동 추론** | [§3](#3-자동-추론-매핑-테이블) 매핑으로 schema 채움 | 없음 | `meta.inferred_fields` 등록 |
| **2. 확인** | 추론된 필드를 근거와 함께 제시, "맞음/수정/모르겠음" 응답 | 가벼움 | `meta.user_confirmed_fields` 등록 |
| **3. 갭 메우기** | 추론 불가 필드(`vision.*`, `scope.must_have`, `team.*` 등)를 greenfield 방식으로 질문 | 중간 | 자유 텍스트 + enum 입력 |
| **4. 코드 grounded 질문** | profile의 발견을 사용자 결정으로 변환 ([§6](#6-코드-grounded-질문-패턴)) | 작지만 가치 높음 | `scope.must_have` / `scope.out_of_scope` / `meta.open_questions` 갱신 |

**확인 단계의 표시 패턴:**

```
✓ constraints.tech_stack.locked_in:
    [Next.js 14, TypeScript, Prisma, Tailwind]
    근거: package.json#dependencies, schema.prisma 존재
    → 맞음 / 수정 / 모르겠음
```

"수정"을 선택하면 사용자 입력으로 덮어쓰고, "모르겠음"은 `inferred_fields`에는 남기되 `user_confirmed_fields`에는 추가하지 않는다.

> **불변식:** `inferred_fields − user_confirmed_fields = 자동 추론만 된 미확인 필드`. Phase 10 Runtime Adaptation은 이 차집합을 "신뢰도 낮음"으로 가중하여 적응 결정 시 우선 사용자 확인을 트리거한다.

### 2-3. 분기 결정 룰

브랜치 결정은 Phase 1의 `project_profile.md#frontmatter.project_type`에서 이미 정해져 있다. Phase 2는 이를 그대로 따르며 자체 판단하지 않는다. 만약 Phase 1이 잘못 분류했다는 신호(예: 사용자가 "이거 처음 만드는 거야"라고 발화했는데 brownfield로 표시됨)가 있으면 Phase 1로 되돌아가 재분류 — 임시방편으로 Phase 2에서 강제 분기하지 않는다.

---

## 3. 자동 추론 매핑 테이블

brownfield 단계 1(자동 추론)에서 `project_profile.md`의 각 필드가 `intent_profile.md`의 어느 필드를 채우는지의 매핑.

### 3-1. 직접 매핑 (high confidence)

매니페스트나 설정 파일에서 명시적으로 측정된 값. 사용자 확인 없이 채워도 안전하지만, 단계 2(확인)에서 사용자에게 보여주긴 한다.

| Project Profile 필드 | → Intent Profile 필드 | 변환 룰 |
|---|---|---|
| `stack.languages[].name` + `stack.frameworks[].name` | `constraints.tech_stack.locked_in` | 매니페스트에 있는 모든 항목을 array로 |
| `stack.frameworks[]`에서 `role: frontend\|backend` 검출 | `architecture.deployment_target` | `next/react/vue` → `web`, `react-native/flutter` → `mobile`, `electron/tauri` → `desktop`, `express/fastapi` 단독 → `server` |
| `convention.formatter.tool != null` | `quality.documentation_level` 보조 신호 | 도구 존재 시 최소 `code_comments` 보정 |
| `maturity.ci_cd.workflows[].stages` | `workflow.ci_cd` | 빈 → `none` / `lint`만 → `lint` / `lint+test` → `test` / `lint+test+deploy` → `full_pipeline` |
| `maturity.test_coverage.line_coverage_percent` | `quality.test_rigor` | `null` 또는 `0` → `none` / `<30%` → `smoke` / `30-70%` → `unit` / `>70%` → `integration` |
| `maturity.documentation.api_docs_present` | `quality.documentation_level` | `true` → 최소 `api`, `inline_comment_density > 0.1` 추가 시 `full` 후보 |

### 3-2. 추정 매핑 (medium / low confidence)

다중 신호를 합성하거나 약한 단일 신호로 추정. 단계 2에서 우선 확인 대상이며, `meta.confidence_low`(project_profile)에 등록된 항목은 여기에 포함된다.

| Project Profile 필드 | → Intent Profile 필드 | 변환 룰 | Confidence |
|---|---|---|---|
| `meta.source_file_count` + git contributors | `constraints.team.size` | contributor 1 → `solo`, 2-5 → `small`, 6-15 → `medium`, 16+ → `large` | Low |
| git commit 빈도 + branch 패턴 | `workflow.collaboration_mode` | 단일 contributor → `solo`, PR 패턴 검출 → `team`, 그 외 → `pair` | Low |
| `maturity.ci_cd.workflows[].triggers` | `workflow.review_style` | `pull_request` 트리거 + branch protection → `peer`, 없음 → `self` | Medium |
| `architecture.structure_pattern` | `architecture.scale_expectation` | `feature-based`/`domain-driven`/`monorepo` → `smb` 이상 후보, `flat` → `toy` 후보 | Low |
| `pain_points.complexity_outliers[]` 존재 | `quality.test_rigor` 상향 압력 | 복잡도 임계 초과 + 테스트 부재 → 사용자 확인 시 강화 권고 | (질문으로 변환) |

**규칙:** medium/low confidence로 추론한 필드는 단계 2 확인 시 시각적으로 구분(예: `~` 또는 `?` 마커)하여 사용자 주의를 끈다.

### 3-3. 매핑하지 않는 필드 (사용자 입력만 가능)

코드만으로는 결정할 수 없는 필드. brownfield라도 단계 3(갭 메우기)에서 사용자에게 직접 묻는다.

| Intent Profile 필드 | 이유 |
|---|---|
| `vision.problem_statement` | 코드는 "어떻게"는 보여주지만 "왜"를 모른다 |
| `vision.target_users` | 운영 데이터 없이 추정 불가 |
| `vision.success_definition` | 비즈니스 KPI는 코드에 없다 |
| `scope.initial_milestone` | 의도된 다음 단계는 코드에 없다 |
| `scope.must_have` | 미래 추가 기능은 코드에 없다 |
| `scope.out_of_scope` | 사용자의 의식적 제외는 코드에 없다 |
| `constraints.tech_stack.preferred` | 이미 있는 것(locked_in)과 다름 — 추가하고 싶은 것 |
| `constraints.tech_stack.forbidden` | 명시적 제외는 코드에 없다 |
| `constraints.team.expertise` | 코드 품질로 간접 추정 가능하나 보수적으로 묻는다 |
| `constraints.timeline.horizon` + `deadline` | 비즈니스 컨텍스트 |
| `architecture.data_sensitivity` | 도메인·법규 컨텍스트 |
| `quality.security_requirements` | 명시적 요구사항은 코드에 없다 |

### 3-4. 신뢰도 결정 룰

추론된 모든 필드는 다음 룰로 confidence를 분류한 뒤 단계 2에 전달:

| Confidence | 조건 | 단계 2 표시 |
|-----------|------|-----------|
| **High** | 직접 측정값 (manifest/config에서 명시) | `✓` 마커, 근거 한 줄 |
| **Medium** | 다중 신호 일치 (예: jest.config + 커버리지 + CI 실행) | `✓` 마커, 근거 2~3줄 |
| **Low** | 단일 약한 신호 또는 추정 | `~` 마커, 근거 + "신뢰도 낮음 — 우선 확인" 문구 |

`project_profile.md#meta.confidence_low`에 등록된 필드는 자동으로 Low로 처리한다.

---

## 4. 질문 생성 룰

### 4-1. 필드 타입별 입력 방식

| 필드 타입 | 입력 방식 | 도구 | 예시 |
|---------|---------|------|------|
| **enum 단일 선택** | multi-choice 제시 | `ask_user_input_v0` 또는 `AskUserQuestion` | `team.size`, `test_rigor`, `horizon` |
| **enum 다중 선택** | multi-select | `AskUserQuestion(multiSelect: true)` | `architecture.deployment_target` |
| **짧은 자유 텍스트 (한 줄)** | 직접 입력 + 짧은 예시 1-2개 | 자연어 프롬프트 | `vision.problem_statement` |
| **긴 자유 텍스트 (서술)** | 직접 입력 + 가이드 문구 + 예시 | 자연어 프롬프트 | `vision.success_definition` |
| **list of strings** | 한 번에 콤마/줄바꿈 구분 | "한 줄에 하나씩 적어주세요" | `scope.must_have`, `forbidden` |
| **bool / 작은 enum** | 두 옵션 제시 | `AskUserQuestion` | "네 / 아니오" |

**예시 제시 룰:** 자유 텍스트 필드에는 반드시 예시 1-2개를 함께 보여준다. 빈 입력 박스만 보여주면 사용자가 "무엇을 적어야 할지 막막함"을 느낀다. 단, 예시는 사용자의 도메인과 멀어 보이는 것을 골라 carrying-over(예시를 그대로 베끼는 현상)를 방지한다.

### 4-2. 진행률 표시 룰

매 섹션 시작 시 한 줄로 표시:

```
**3/7 — Constraints** (기술 스택, 팀, 일정)
```

번호는 `vision(1) → scope(2) → constraints(3) → architecture(4) → quality(5) → workflow(6) → meta(7)` 고정.

### 4-3. 스킵 처리 룰

| 사용자 응답 | 동작 |
|-----------|------|
| "스킵", "건너뛰기", "다음" | 필드를 비우고 `open_questions`에 등록, 다음 필드로 |
| "모르겠음", "미정", "나중에" | 스킵과 동일 처리, 등록 시 응답 표현을 그대로 인용 |
| "상관 없음", "아무거나" | 필수 필드면 기본값 제시 후 확인, 선택 필드면 스킵 |
| (필수 5개) 스킵 시도 | [§7](#7-필수-필드-재질문-룰) 룰 적용 |

### 4-4. 추론 결과 확인 패턴 (brownfield 단계 2)

추론된 필드 한 개를 보여줄 때의 표준 형태:

```
{확신도 마커} {필드 dot-path}: {추론된 값}
    근거: {project_profile의 source 필드 또는 설명}
    → 맞음 / 수정 / 모르겠음
```

**응답별 동작:**

| 응답 | 동작 |
|------|------|
| 맞음 | `user_confirmed_fields`에 추가 |
| 수정 | 새 값을 받아 덮어쓰고, `user_confirmed_fields`에 추가 |
| 모르겠음 | 추론값 유지, `user_confirmed_fields`에는 추가하지 않음 |

**일괄 확인 옵션:** High confidence 항목이 5개 이상이면 "모두 맞음" 단축 응답을 제공하여 사용자 부담을 줄인다.

### 4-5. 자유 텍스트 정규화

자유 텍스트 응답을 frontmatter에 넣을 때:

| 원본 | 정규화 후 |
|------|---------|
| 1줄 답변 | frontmatter의 string 필드에 그대로 |
| 다단락 답변 | 본문 마크다운에 넣고, frontmatter는 1줄 요약 |
| 콤마 구분 list | YAML array로 |
| "그냥 음... 뭐랄까..." 같은 fillers | 제거하고 핵심만 추출 (단, 사용자 의도가 모호하면 그대로 보존하고 확인 요청) |

---

## 5. 섹션별 질문 카탈로그

각 섹션마다 greenfield 버전(전체 질문)과 brownfield 버전(갭 메우기 + 코드 grounded)을 제공.

### 5-1. Vision (1/7)

| 필드 | 입력 방식 | greenfield 프롬프트 | brownfield 프롬프트 |
|------|---------|------------------|-------------------|
| `problem_statement` | 짧은 자유 텍스트 | "이 프로젝트가 해결하려는 문제는 무엇인가요? (1-2문장)" | "기존 시스템에 이 변경을 가하는 이유는 무엇인가요?" |
| `target_users` | list | "주 사용자는 누구인가요? 한 줄에 하나씩." (예: "내부 운영팀 / B2B 고객사") | greenfield와 동일 |
| `success_definition` | 긴 자유 텍스트 | "성공을 어떻게 측정할 건가요? 가능하면 측정 가능한 형태로." (예: "월간 활성 사용자 1,000명, 오류율 < 1%") | greenfield와 동일 |

### 5-2. Scope (2/7)

| 필드 | 입력 방식 | greenfield 프롬프트 | brownfield 프롬프트 |
|------|---------|------------------|-------------------|
| `initial_milestone` | 짧은 자유 텍스트 | "첫 번째 검증할 가설/마일스톤은? (예: '랜딩 페이지에서 가입 전환 5%')" | "이 변경의 첫 번째 검증 지점은? (예: 'A/B 테스트로 CTR +5%')" |
| `must_have` | list | "MVP에 반드시 포함될 기능을 한 줄에 하나씩 나열해주세요." | "이번에 추가할 기능을 한 줄에 하나씩." (코드 grounded 질문에서 churn hotspot 기반 제안 가능) |
| `out_of_scope` | list | "지금은 의도적으로 제외할 기능이 있나요? (scope creep 방지)" | greenfield와 동일 |

### 5-3. Constraints (3/7) — 필수 영역

| 필드 | 입력 방식 | greenfield 프롬프트 | brownfield 프롬프트 |
|------|---------|------------------|-------------------|
| `tech_stack.preferred` | list | "선호하는 기술이 있나요? (예: 'Next.js, PostgreSQL')" | "추가로 도입하고 싶은 기술이 있나요?" |
| `tech_stack.forbidden` | list | "사용 금지 기술이 있나요? (라이선스/조직 정책)" | greenfield와 동일 |
| `tech_stack.locked_in` | list | (greenfield에선 비움) | (자동 추론, 단계 2에서 확인) |
| `team.size` ★ | enum 단일 | "팀 규모는? **solo (1) / small (2-5) / medium (6-15) / large (16+)**" | (Low confidence 추론, 단계 2에서 우선 확인) |
| `team.expertise` | enum 단일 | "팀의 평균 숙련도는? **junior / mid / senior / mixed**" | greenfield와 동일 |
| `timeline.horizon` ★ | enum 단일 | "이 프로젝트의 시간축은? **prototype (검증용) / mvp (실사용자) / production (장기 운영)**" | greenfield와 동일 |
| `timeline.deadline` | 짧은 자유 텍스트 | "데드라인이 있나요? (날짜 또는 'Q3 2026' 같은 형식)" | greenfield와 동일 |

★ 표시는 필수 5개 중 일부.

### 5-4. Architecture (4/7) — 필수 영역

| 필드 | 입력 방식 | greenfield 프롬프트 | brownfield 프롬프트 |
|------|---------|------------------|-------------------|
| `deployment_target` ★ | enum 다중 | "어디서 실행될까요? **web / mobile / desktop / server / embedded** (다중 선택 가능)" | (자동 추론, 단계 2에서 확인) |
| `scale_expectation` | enum 단일 | "예상 규모는? **toy (개인/실험) / smb (중소) / enterprise (대규모)**" | greenfield와 동일, churn hotspot이 많으면 "현재 패턴은 X처럼 보이는데 맞나요?" 보충 |
| `data_sensitivity` | enum 단일 | "취급 데이터의 민감도는? **none / personal / regulated (GDPR·HIPAA 등)**" | greenfield와 동일 |

### 5-5. Quality (5/7) — 필수 일부

| 필드 | 입력 방식 | greenfield 프롬프트 | brownfield 프롬프트 |
|------|---------|------------------|-------------------|
| `test_rigor` ★ | enum 단일 | "테스트 강도는? **none / smoke (스모크) / unit / integration / tdd (test-first)**" | (자동 추론, 단계 2에서 확인. 추론값과 사용자 의도가 다르면 "코드는 X 수준이지만 의도는 Y인가?" 형태로 재질문) |
| `documentation_level` | enum 단일 | "문서화 수준은? **none / code_comments / api / full**" | greenfield와 동일 |
| `security_requirements` | list | "특별한 보안 요구사항이 있나요? (예: 'OAuth2', '암호화 저장')" | profile에서 `data_sensitivity: regulated`가 추론되면 강하게 권고 |

### 5-6. Workflow (6/7)

| 필드 | 입력 방식 | greenfield 프롬프트 | brownfield 프롬프트 |
|------|---------|------------------|-------------------|
| `collaboration_mode` | enum 단일 | "협업 방식은? **solo / pair / team**" | (Low confidence 추론, 우선 확인) |
| `review_style` | enum 단일 | "코드 리뷰 강도는? **none / self / peer / strict (2인 이상 승인)**" | (Medium confidence 추론) |
| `ci_cd` | enum 단일 | "CI/CD 단계는? **none / lint / test / full_pipeline**" | (자동 추론, 단계 2에서 확인) |

### 5-7. Meta (7/7)

`open_questions`, `explicit_assumptions`는 사용자에게 직접 묻지 않는다 — 앞 단계에서 자동 누적되거나 종료 직전 한 번 보여주고 추가 가정이 있는지 묻는다.

```
지금까지 다음 가정을 수집했습니다:
- {assumption 1}
- {assumption 2}
추가하거나 수정할 게 있나요? (없으면 "없음")
```

---

## 6. 코드 grounded 질문 패턴

brownfield 단계 4의 핵심 가치. `project_profile.md`의 발견을 사용자 결정으로 변환하여, 코드만으로는 알 수 없는 "의도"를 추출한다. 사용자 부담은 작지만 다운스트림 품질에 큰 영향을 준다.

### 6-1. Finding → Question 매핑

| Profile Finding | → 생성할 질문 | → 영향 받는 Intent 필드 |
|---|---|---|
| `pain_points.churn_hotspots[]`에 상위 항목 | "`{path}`가 최근 30일간 {count}회 변경됐어요. 이번 작업에 이 영역이 포함되나요? 전담 에이전트가 필요할까요?" | `scope.must_have`, `meta.open_questions` |
| `pain_points.skipped_tests[]` (특히 `reason: "flaky"` 또는 `"WIP"`) | "`{path}`의 스킵된 테스트 '{name}'이(가) 의도된 것인가요? 아니면 이번에 해결할 항목인가요?" | `scope.must_have` 또는 `scope.out_of_scope` |
| `pain_points.deprecated_usages[]` | "`{api}` deprecated 사용이 {n}곳 있어요. 이번 작업에서 마이그레이션을 포함할까요?" | `scope.must_have` 또는 `out_of_scope` |
| `pain_points.todo_markers.by_type.FIXME > 5` | "FIXME가 {n}개 있어요. 그 중 {예시}는 이번 작업과 관련 있나요?" | `scope.must_have`, `meta.explicit_assumptions` |
| `pain_points.complexity_outliers[]` | "`{path}`의 복잡도가 임계({threshold})를 초과했어요({value}). 이번에 리팩토링을 포함할까요?" | `scope.must_have` 또는 `out_of_scope` |
| `maturity.test_coverage.line_coverage_percent < 50` + `timeline.horizon == production` | "현재 라인 커버리지가 {p}%인데 production 목표예요. 테스트 보강이 이번 범위에 포함되나요?" | `quality.test_rigor`, `scope.must_have` |
| `maturity.documentation.adr_count == 0` | "ADR(아키텍처 결정 기록)이 없어요. 이번 작업의 주요 결정을 ADR로 남길 계획인가요?" | `quality.documentation_level`, `meta.explicit_assumptions` |
| `maturity.dependency_health.deprecated_count > 0` | "deprecated 의존성 {n}개 발견. 교체 계획에 포함되나요?" | `scope.must_have` 또는 `out_of_scope` |
| `maturity.dependency_health.known_vulnerabilities > 0` | (강하게 권고) "보안 취약점 {n}개 발견. 즉시 패치가 필요해 보입니다 — 이번 작업에 포함하시겠어요?" | `scope.must_have`, `quality.security_requirements` |
| `meta.confidence_low[]` 항목 | (이미 단계 2에서 처리, 여기서는 생략) | — |
| `architecture.module_boundaries[]`에 명확한 경계 | "`{boundary}` 모듈에 이번 변경이 영향을 주나요? 다른 모듈은 건드리지 않을 건가요?" | `scope.must_have`, `out_of_scope` (모듈 경계 명시) |
| `convention.test_location: mixed` | "테스트가 collocated와 separate가 섞여 있어요. 새 코드는 어느 컨벤션을 따를까요?" | `meta.explicit_assumptions` |
| `convention.file_naming.consistency_score < 0.8` | "파일명 컨벤션 일관성이 {p}예요. 이번에 통일할까요? 아니면 기존 그대로?" | `meta.explicit_assumptions` |

### 6-2. 우선순위 룰

profile에서 finding이 많이 나올 수 있다. 모두 묻지 않고 다음 우선순위로 상위 3~5개만 선택:

1. **보안 취약점** (`known_vulnerabilities > 0`) — 무조건 1순위
2. **deprecated** (마이그레이션 계획)
3. **churn hotspots 상위 1개** — 변경 빈도가 가장 높은 영역
4. **skipped tests** (특히 reason이 명시된 것)
5. **test coverage 갭** (production 목표 시)
6. 그 외 — 사용자가 "다른 것도 알려줘"라 요청할 때만

### 6-3. 질문 형태 룰

| 룰 | 설명 |
|----|------|
| **finding 명시** | "코드에서 X를 발견했어요" 형태로 시작 — 추론이 아니라 측정값임을 알려 신뢰 형성 |
| **의도 묻기, 결정 강요 금지** | "포함할까요?" / "맞나요?" 형태. "포함해야 합니다"는 강압 |
| **YES/NO/MAYBE 3지선다** | "네 / 아니오 / 일단 보류"로 응답 부담 최소화. MAYBE는 `meta.open_questions`로 등록 |
| **한 번에 한 finding** | 멀티-finding 질문은 사용자가 어디에 답하는지 모호해진다 |
| **소요 시간 예고** | "코드 grounded 질문 5개 — 약 2분 소요"로 끝이 보이게 |

### 6-4. 출력 갱신

코드 grounded 질문의 응답은 다음 필드에 누적:

```yaml
scope:
  must_have:
    - "{기존 항목}"
    - "checkout race condition 수정"          # FIXME finding으로부터
  out_of_scope:
    - "{기존 항목}"
    - "request → undici 마이그레이션 (다음 분기)"  # deprecated finding으로부터

meta:
  explicit_assumptions:
    - "checkout 영역 churn 높음 — 추천 시스템과 분리 모듈로 구현"  # churn finding으로부터
  open_questions:
    - "동시 구매 시나리오 테스트 (스킵 중) — POC 후 결정"  # skipped test finding 응답이 MAYBE
```

---

## 7. 필수 필드 재질문 룰

필수 5개 (`tech_stack`, `team.size`, `timeline.horizon`, `deployment_target`, `test_rigor`)는 스킵을 허용하지 않는다. 사용자가 비우려 하면 다음 룰로 재질문.

### 7-1. 1차 재질문 — 기본값 제시

```
'{필드}'는 다운스트림에서 반드시 필요해요 (예: {다운스트림 사용처}).
모르겠으면 다음 기본값으로 진행할까요?
  → {기본값}
```

| 필드 | 다운스트림 사용처 | 기본값 |
|------|----------------|--------|
| `tech_stack` | 스킬 생성 시 프레임워크 관용구 결정 | "프로젝트 디렉토리의 매니페스트로 자동 감지" (brownfield) / "추후 결정 — `meta.open_questions`로" (greenfield, 단 deployment_target에서 추론 시도) |
| `team.size` | 팀 크기 가이드라인 적용 | `solo` (가장 보수적) |
| `timeline.horizon` | QA 강도, 검증 깊이 결정 | `mvp` (중간값) |
| `deployment_target` | 에이전트 분리 축 결정 | `[server]` (가장 일반적) |
| `test_rigor` | QA 에이전트 포함 여부 | `smoke` (최소) |

### 7-2. 2차 재질문 — 짧은 다중 선택

기본값을 거부하면 enum 옵션을 다시 펼쳐 보여준다. 이때는 "모르겠음" 응답을 받아 기본값을 적용하고 `meta.open_questions`에 "(필수 5개 미응답 → 기본값)"으로 등록.

### 7-3. Hard fail 조건

사용자가 명확하게 "이 프로젝트는 진행하지 않을 거야" 같은 응답을 하면 Phase 2를 종료하지 않고 사용자에게 명시적 종료 의사를 확인. 임의로 frontmatter를 비우고 진행하지 않는다.

---

## 8. 검증 룰

Phase 2 종료 직전 `intent_profile.md`가 다음을 통과해야 한다. 검증 실패 시 사용자에게 보고하고 해당 단계로 되돌아간다.

### 8-1. 구조 검증

| 룰 | 검증 |
|----|------|
| frontmatter에 `version: 1`, `project_type` 존재 | YAML 파싱 |
| 본문에 vision/scope/meta 헤딩 존재 | 마크다운 헤딩 매칭 |
| 자유 텍스트 필드는 본문, 구조화 필드는 frontmatter | [§4-5](#4-5-자유-텍스트-정규화) 룰 |

### 8-2. 필수 필드 검증

| 필드 | 검증 |
|------|------|
| `constraints.tech_stack` | `preferred` + `forbidden` + `locked_in` 중 하나라도 비어있지 않거나, `meta.open_questions`에 명시 |
| `constraints.team.size` | enum 값 존재 |
| `constraints.timeline.horizon` | enum 값 존재 |
| `architecture.deployment_target` | array 비어있지 않음 |
| `quality.test_rigor` | enum 값 존재 |

### 8-3. 메타 일관성

| 룰 | 의미 |
|----|------|
| `project_type == greenfield` ⇒ `meta.inferred_fields == []` | greenfield는 추론 대상 없음 |
| `project_type == brownfield` ⇒ `meta.inferred_fields` 1개 이상 | code research가 최소 1개는 추론 가능 |
| `meta.user_confirmed_fields ⊆ meta.inferred_fields` | 확인된 필드는 반드시 추론 후보였어야 함 |
| 스킵된 모든 필드가 `meta.open_questions`에 등록됨 | 침묵 금지 |

### 8-4. Cross-field 룰

`references/intent-profile-schema.md#8-검증-룰`의 cross-field 룰을 그대로 적용한다. 대표:

| 조합 | 룰 |
|------|----|
| `timeline.horizon = production` + `quality.test_rigor = none` | 경고 — 사용자 확인 후 `explicit_assumptions`에 사유 기록 |
| `team.size = solo` + `workflow.review_style = strict` | 경고 — 1인 strict 리뷰 불가능 |
| `data_sensitivity = regulated` + `quality.security_requirements = []` | 경고 — 보안 요구사항 미정의 |
| `project_type = greenfield` + `constraints.tech_stack.locked_in != []` | 모순 — 자동 거부 |

검증 실패 시 사용자에게 "다음 모순이 있어요: ..." 형태로 보고하고, 사용자가 "의도된 것"이라 응답하면 `meta.explicit_assumptions`에 "{룰} 의도적 위반: {사용자 이유}" 형식으로 기록.

### 8-5. 종료 게이트

모든 검증 통과 후 사용자에게 최종 frontmatter 요약을 보여주고 "이대로 저장할까요?" 확인. 승인 시 `_workspace/_baseline/intent_profile.md`로 저장하고 Phase 3으로 진행.
