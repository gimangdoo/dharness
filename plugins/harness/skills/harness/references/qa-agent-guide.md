# QA 에이전트 설계 가이드

> **Read at phase:** Phase 5 (QA 에이전트 정의 시). §1~§5는 host-agnostic doctrine (모든 도메인 적용). §6 도메인 카탈로그(web-app/ML/data/mobile/devops·embedded)는 capability profile signal 매칭 시 발췌.

빌드 하네스에 QA 에이전트를 포함할 때 참고하는 가이드. 다수 derived 프로젝트(web-app·ML·data·mobile·infra) 사이클에서 누적된 경계면 버그 패턴과 근본 원인 분석을 바탕으로, QA가 놓치기 쉬운 결함을 체계적으로 잡는 검증 방법론을 제공한다.

> **Doctrine (2026-05-14 P2-2 환원):** §1~§5는 framework·언어·런타임 가정 없이 *생산자(producer) ↔ 소비자(consumer) 경계면 검증*이라는 추상 doctrine만 박제. 도메인 특화 예시·체크리스트는 §6 카탈로그 (web-app §6-0 / ML §6-1 / data-eng §6-2 / mobile §6-3 / devops·embedded §6-4)에서 발췌. Phase 5 합성 시 capability profile S7~S10 매칭 결과를 보고 §6의 해당 표를 QA 에이전트 정의에 옮긴다.

---

## 목차

1. QA 에이전트가 놓치는 결함의 패턴
2. 통합 정합성 검증 (Integration Coherence Verification)
3. QA 에이전트 설계 원칙
4. 검증 체크리스트 템플릿 (host-agnostic)
5. QA 에이전트 정의 템플릿
6. 도메인별 경계면 카탈로그 (web-app / ML / data / mobile / devops·embedded)

---

## 1. QA 에이전트가 놓치는 결함의 패턴

### 1-1. 경계면 불일치 (Boundary Mismatch)

가장 빈번한 결함. 두 컴포넌트가 각각 "올바르게" 구현되어 있지만, 연결 지점에서 계약(contract)이 어긋남.

| 경계면 (생산자 → 소비자) | 불일치 일반 형태 | 놓치는 이유 |
|--------|-----------|-----------|
| produce-side payload shape → consume-side 타입 가정 | 생산자는 `{ wrapper: [item, ...] }` 반환, 소비자는 `item[]` 기대 | 각각 개별 검증하면 정상, 교차 비교 안 함 |
| 필드 명명 규약 (snake_case ↔ camelCase ↔ kebab-case) | 한 boundary에서만 변환, 다른 곳은 raw 키 노출 | 변환은 한 곳에만 박제, 다른 path 무시 |
| 식별자(path/id/URL/topic) → 호출측 참조 | 정의된 식별자와 호출측 문자열이 typo·prefix 누락으로 mismatch | 식별자 카탈로그와 호출측을 1:1 매핑하지 않음 |
| 상태 전이 정의 → 실제 상태 업데이트 코드 | 전이 맵에 `A→B` 정의, 코드에서 전환 누락 (또는 맵 외 전이 발생) | 맵 존재 확인만 하고, 모든 업데이트 코드를 추적하지 않음 |
| API/이벤트/RPC 엔드포인트 → 소비자 호출 | 엔드포인트 존재하지만 대응 호출 없음 (또는 호출 있는데 엔드포인트 없음) | 양쪽 목록을 1:1 매핑하지 않음 |
| 즉시 응답 ↔ 비동기 결과 | 호출자가 즉시 응답에서 최종 결과 필드 접근 | 동기/비동기 응답 구분 없이 타입만 확인 |

### 1-2. 왜 정적 분석으로 못 잡나

- **타입 시스템 우회 가능성**: 제네릭, 강제 캐스팅, 동적 타입, 스키마 외 추가 필드(`additionalProperties: true`) 등은 컴파일·정적 분석을 통과해도 런타임에서 실패
- **빌드/타입체크 통과 ≠ 정상 동작**: 빌드는 *구조*만 검증, 경계면의 *값* 검증은 안 됨
- **존재 검증 vs 연결 검증의 차이**: "X가 있는가?"와 "X의 출력이 호출측 기대와 일치하는가?"는 전혀 다른 검증 — QA 정의에 후자를 명시적으로 박제하지 않으면 silent fail

---

## 2. 통합 정합성 검증 (Integration Coherence Verification)

QA 에이전트에 반드시 포함해야 하는 **교차 비교 검증** 영역. 도메인 무관 일반 doctrine이며, 도메인별 구체 grep 패턴은 §6에서 발췌.

### 2-1. 생산자 출력 shape ↔ 소비자 타입 교차 검증

**방법**: 데이터를 생산하는 코드의 직렬화 지점(`encode/serialize/return/emit`)과 소비하는 코드의 역직렬화·타입 가정 지점(`decode/parse/cast`)을 동시에 열어 shape을 비교.

```
검증 단계:
1. 생산자 코드에서 외부로 내보내는 payload shape 추출
2. 소비자 코드에서 가정하는 타입·필드 목록 추출
3. shape 매칭 + 래핑(wrapper) 여부 + 필드 명명 변환 일관성 확인
4. optional/nullable 필드에 대한 양쪽 처리 일관성 확인
```

**주의 패턴 (도메인 공통)**:
- 페이지네이션 / 컬렉션 wrapping (`{ items, total }` vs raw array)
- 명명 규약 변환 누락 (camelCase / snake_case / kebab-case mix)
- 즉시 응답(accepted/queued) vs 최종 결과 shape 차이
- 타임스탬프 직렬화 형식 (ISO8601 / epoch / locale-dependent)

### 2-2. 식별자(path / id / URL / topic) ↔ 참조 매핑

**방법**: 시스템이 정의한 식별자 카탈로그(파일 경로 트리, route table, message topic 목록, DB 키 등)를 추출하고, 코드 내 모든 참조(`link/redirect/publish/subscribe/lookup` 등)와 1:1 대조.

```
검증 단계:
1. 정의된 식별자 카탈로그 추출 (보통 디렉토리 구조·라우터 정의·schema·config)
2. 코드 내 모든 참조 문자열 수집 (link/redirect/router/publish/subscribe/lookup)
3. 각 참조가 카탈로그에 존재하는지 + prefix·동적 세그먼트 채움 일치하는지 확인
4. 카탈로그에 있지만 참조 0인 dead 식별자도 보고 (의도 vs 누락 판별)
```

### 2-3. 상태 전이 완전성 추적

**방법**: 상태 전이 정의(맵·머신·DSL)에서 허용 전이 목록을 추출하고 모든 상태 업데이트 코드와 대조.

```
검증 단계:
1. 상태 전이 정의에서 허용 전이 목록 추출
2. 모든 상태 변이 지점 검색 (status·state 컬럼 update / event emit / actor send)
3. 각 전이가 맵에 정의되어 있는지 (무단 전이 없음)
4. 맵에 정의된 전이 중 실행되지 않는 것 식별 (dead 전이)
5. 특히 중간 상태에서 최종 상태로의 전이 누락 여부 확인 — 미완료 deadlock 원인
```

### 2-4. 엔드포인트 / API / 이벤트 ↔ 호출자 1:1 매핑

**방법**: 시스템이 노출하는 모든 외부 표면(REST endpoint / GraphQL resolver / RPC method / event topic / queue / CLI command 등)과 그것을 호출·구독하는 측을 양쪽 목록으로 만들어 1:1 매핑.

```
검증 단계:
1. 노출 표면 목록 추출 (route 정의 / proto · idl / event registration)
2. 호출자 목록 추출 (client 호출 / subscribe / consumer)
3. 호출되지 않는 표면 → "dead surface" 플래그
4. 정의되지 않은 호출 → "dangling reference" 플래그
5. 의도적 dead (admin only · 단계적 출시) vs 사고는 별도 명시 권고
```

---

## 3. QA 에이전트 설계 원칙

### 3-1. 검증·수정 권한이 필요한 작업은 read-only 에이전트로 분리하지 마라

QA 에이전트가 *읽기 전용*이면 다음이 불가능하다:
- 패턴 grep으로 양쪽 코드 동시 추출
- 검증 스크립트 실행으로 자동 대조
- 발견된 dangling reference의 즉시 수정 요청 wiring

**권장**: QA 에이전트는 검증·수정 양쪽 권한을 갖는 일반 에이전트 타입으로 설정. 단 "검증 → 리포트 → 수정 요청" 프로토콜을 정의에 명시해 *발견*과 *수정*을 분리. 도구 권한은 `permission-profiles.md §2` capability profile 매칭 결과를 따른다.

### 3-2. 체크리스트는 "존재 확인"보다 "교차 비교"를 우선하라

| 약한 체크리스트 (존재 확인) | 강한 체크리스트 (교차 비교) |
|---------------|---------------|
| 외부 표면이 존재하는가? | 외부 표면의 출력 shape과 호출측 타입 가정이 일치하는가? |
| 상태 전이 정의가 있는가? | 모든 상태 업데이트 코드가 정의의 전이와 일치하는가? |
| 정의된 식별자가 존재하는가? | 코드 내 모든 참조가 정의된 식별자를 가리키는가? |
| 정적 분석이 통과하는가? | 정적 분석 우회(any/캐스팅/동적/추가 필드)로 가려진 boundary가 없는가? |

### 3-3. "양쪽을 동시에 읽어라" 원칙

경계면 버그를 잡으려면 한쪽만 읽어선 안 된다. 반드시:
- 생산자 코드 **와** 소비자 코드를 **같이** 읽고
- 상태 전이 정의 **와** 실제 업데이트 코드를 **같이** 읽고
- 식별자 카탈로그 **와** 참조 위치를 **같이** 읽어야 한다

에이전트 정의에 이 원칙을 명시적으로 기재하라. 도메인별 *동시 읽기 페어 카탈로그*는 §6에서 발췌.

### 3-4. QA는 빌드/통합 후가 아니라 각 모듈 완성 직후 실행하라

오케스트레이터에서 QA를 *전체 완성 후*에만 배치하면:
- 버그가 누적되어 수정 비용이 커짐
- 초기 경계면 불일치가 후속 모듈에 전파 (cascade failure)

**권장 패턴**: 각 생산자 모듈 완성 시 즉시 *해당 모듈 + 대응 소비자*의 교차 검증 수행 (incremental QA). orchestrator-template §4 "QA wiring" 참조.

---

## 4. 검증 체크리스트 템플릿 (host-agnostic)

QA 에이전트 정의에 포함할 도메인 무관 통합 정합성 체크리스트. 도메인별 추가 행은 §6에서 발췌.

```markdown
### 통합 정합성 검증 (host-agnostic 공통)

#### 생산자 ↔ 소비자 shape 정합
- [ ] 모든 외부 표면의 출력 shape과 소비자 타입 가정이 일치
- [ ] wrapper / 컬렉션 형태(items/data/results 등)는 소비자에서 명시적으로 unwrap
- [ ] 명명 규약 변환(snake/camel/kebab)이 일관 적용 — 누락 boundary 0
- [ ] 즉시 응답(accepted/queued)과 최종 결과의 shape 구분이 코드에서 명시
- [ ] 타임스탬프 직렬화 형식(ISO8601/epoch/timezone) 양쪽 동일 가정

#### 식별자 / 참조 정합
- [ ] 코드 내 모든 참조(link/redirect/topic/key 등)가 정의된 카탈로그를 가리킴
- [ ] 동적 세그먼트·파라미터가 올바른 값으로 채워짐
- [ ] dead 식별자(참조 0)는 의도(admin·deprecated) vs 사고 구분 박제

#### 상태 머신 정합
- [ ] 정의된 모든 전이가 코드에서 실행됨 (dead 전이 없음)
- [ ] 코드의 모든 상태 변이가 정의에 박제됨 (무단 전이 없음)
- [ ] 중간 상태에서 최종 상태로의 전환 누락 0 (deadlock 방지)
- [ ] 소비자의 상태 기반 분기(`if state == X`)의 X가 실제 도달 가능

#### 데이터 흐름 정합
- [ ] 원천(DB/source) 필드명 ↔ 중간 표현 ↔ 최종 소비자 매핑이 일관
- [ ] 옵셔널·nullable 필드에 대한 양쪽 처리(default/error/skip) 일관
- [ ] 단위·timezone·인코딩이 boundary 전반에서 명시 (silent coercion 0)
```

> **도메인 보강 권고**: 위 체크리스트는 host-agnostic 골격. 합성 시 §6의 해당 도메인 표(예: ML이면 §6-1, data-eng이면 §6-2)에서 검증 행을 추가로 발췌해 QA 에이전트 정의 체크리스트에 박는다.

---

## 5. QA 에이전트 정의 템플릿 (host-agnostic)

빌드 하네스의 QA 에이전트에 포함할 핵심 섹션 — 도메인 무관 골격.

```markdown
---
name: qa-inspector
description: "QA 검증 전문가. 스펙 준수, 통합 정합성, 도메인 품질 기준을 검증."
---

# QA Inspector

## 핵심 역할
스펙 대비 구현 품질과 **모듈 간 통합 정합성**을 검증한다.

## 검증 우선순위

1. **통합 정합성** (가장 높음) — 경계면 불일치가 런타임 실패의 주요 원인
2. **기능 스펙 준수** — 외부 표면 / 상태 머신 / 데이터 모델
3. **도메인 품질 기준** — (도메인별 §6 카탈로그에서 발췌: web→a11y/perf, ML→분포/드리프트, data→무결성, mobile→플랫폼 가이드, infra→drift/SLO)
4. **코드 품질** — 미사용 코드, 명명 규칙

## 검증 방법: "양쪽 동시 읽기"

경계면 검증은 반드시 **양쪽 코드를 동시에 열어** 비교한다:

| 검증 대상 (도메인 공통 추상) | 왼쪽 (생산자) | 오른쪽 (소비자) |
|----------|-------------|---------------|
| 외부 표면 출력 shape | 생산자 직렬화 지점 | 소비자 타입 가정 지점 |
| 식별자·참조 | 카탈로그 (디렉토리/route/topic) | 참조 사용 위치 |
| 상태 전이 | 정의 (맵/머신/DSL) | 변이 지점 (update/emit) |
| 데이터 흐름 | 원천 schema (DB/source) | 최종 소비자 타입 |

> 도메인별 동시 읽기 페어는 §6의 해당 도메인 표에서 발췌해 본 표에 추가하라.

## 팀 통신 프로토콜

- 발견 즉시 해당 에이전트에게 구체적 수정 요청 (파일:라인 + 수정 방법)
- 경계면 이슈는 양쪽 에이전트 **모두**에게 알림
- 리더에게: 검증 리포트 (통과/실패/미검증 항목 구분)
```

---

## 6. 도메인별 경계면 카탈로그 (2026-05-14 P6-7 + P2-2 신설)

§1~§5는 host-agnostic doctrine. 본 §6은 capability profile signal (mcp-recommendation.md §1-2 S6~S10) 매칭 시 *QA 에이전트가 추가로 점검해야 할 경계면 카탈로그*. 합성 시 매칭 도메인 표를 QA 에이전트 정의 체크리스트에 *발췌* 권고.

> **doctrine:** 본 카탈로그는 *닫힌 spec*이 아니라 *반복 발견되는 패턴 catalog*. derived 프로젝트에서 새 버그 패턴 발견 시 본 §6에 행 추가 (cycle 누적 doctrine).

### 6-0. Web application (S6 매칭 — `web-app` 일반 / Next.js·React·Vue·Svelte 등)

§1~§5 doctrine을 web-app 도메인에 인스턴스화한 카탈로그. 본 절은 §1~§5 host-agnostic 환원 이전(2026-05-14 P2-2)의 web-app 기원 예시를 박제.

| 경계면 | 불일치 예시 | 놓치는 이유 | QA 검증 방법 |
|--------|----------|-----------|------------|
| HTTP API 응답 ↔ 클라이언트 훅 타입 | API가 `{ projects: [...] }` 반환, 훅이 `Project[]` 기대 | TS 제네릭(`fetchJson<Project[]>()`)으로 캐스팅 시 컴파일 통과 | API route의 `Response.json()`·`NextResponse.json()` ↔ 훅의 `fetchJson<T>` shape 교차 grep |
| API 응답 필드명 ↔ 타입 정의 | API는 `thumbnailUrl`, 타입은 `thumbnail_url` | 명명 규약 변환 누락 — TS 제네릭이 못 잡음 | API serializer ↔ 타입 정의 ↔ 컴포넌트 사용처 3 출처 grep |
| 파일 경로 ↔ 링크 href | 페이지가 `/dashboard/create`, 링크가 `/create` | 파일 구조와 href 교차 비교 안 함 (route group `(group)` URL 제거 잊음) | `src/app/` page 파일 → URL 패턴 추출 ↔ `href=`·`router.push(`·`redirect(` 값 매핑 |
| 상태 전이 맵 ↔ status 업데이트 | 맵에 `generating_template → template_approved` 정의, 코드 전환 누락 | 맵 존재 확인만, 모든 `.update({ status })` 추적 안 함 | `STATE_TRANSITIONS` 맵 ↔ 모든 `.update({ status: "..." })` grep 매트릭스 |
| API 엔드포인트 ↔ 프론트 훅 | API 존재하지만 호출 훅 없음 (또는 그 반대) | route 목록과 hook 목록 1:1 매핑 안 함 | `src/app/api/**/route.ts` ↔ `src/hooks/use*.ts`·`fetch(` 매트릭스 |
| 즉시 응답 (202 Accepted) ↔ 비동기 결과 | 프론트가 `data.failedIndices` 접근, 실제는 백그라운드 작업 결과 | 동기·비동기 응답 구분 없이 타입만 확인 | API 응답 status code · payload 분류 + 폴링/구독 wiring 검증 |
| accessibility 가정 ↔ 실제 마크업 | 디자인은 a11y 통과 가정, 실제 마크업은 aria 누락 | 빌드 통과 ≠ a11y 검증 | axe-core / lighthouse a11y 자동화 + 핵심 페이지 manual audit |
| performance budget ↔ 번들 크기 | 4G 모바일 budget 200KB, 실제 1.2MB | bundle analyzer 미실행 — silent | `next-bundle-analyzer` / `vite-bundle-visualizer` CI gate + LCP/INP 측정 |

> **실제 사례 (SatangSlide cycle empirical)**: `projects?.filter is not a function` (API↔훅), 대시보드 모든 링크 404 (`/dashboard/` 접두사 누락), 테마 이미지 안 보임 (`thumbnailUrl` vs `thumbnail_url`), 테마 선택 저장 안 됨 (select-theme API 존재 / 훅 없음), 생성 페이지 영원히 대기 (`template_approved` 전이 코드 누락), `data.failedIndices` 크래시 (즉시 응답 ↔ 비동기 결과), 슬라이드 보기 404 (`/projects/` → `/dashboard/projects/`).

### 6-1. ML pipeline (S7 매칭 — `ml-pipeline` profile)

| 경계면 | 불일치 예시 | 놓치는 이유 | QA 검증 방법 |
|--------|----------|-----------|------------|
| dataset schema → training feature columns | dataset에 `user_id` 컬럼 추가됐는데 feature pipeline에서 누락 | 컬럼 추가는 silent — 학습은 진행되나 신호 손실 | 학습 코드의 `df.columns` 추출 ↔ dataset schema diff |
| label 분포 → 평가 지표 선택 | binary classification에 accuracy만 사용 (label imbalance 9:1) | sklearn default가 accuracy — imbalance 시 부적절 | label 분포 추출 ↔ 지표 코드 매칭 (imbalance >3:1이면 F1/PR-AUC 강제) |
| training preprocessing ↔ inference preprocessing (train-serve skew) | training은 fit_transform, inference는 별도 fit (재학습) | code path가 분리되어 두 곳을 동시에 본 적이 없음 | preprocessing 함수 단일 출처 강제 — train/serve 양쪽에서 *동일 함수* 호출 grep |
| 모델 input shape ↔ inference API request shape | 모델은 (224,224,3), API는 (256,256,3) PIL resize | API 코드는 mock 통과, 실 모델 호출 시 shape mismatch | model `input_shape` ↔ API preprocessing transform 교차 비교 |
| 학습 데이터 분포 ↔ production 데이터 분포 (data drift) | 학습은 2024 데이터, production은 2026 — feature 분포 이동 | drift 자동 감지 인프라 없으면 silent degradation | training data summary 통계 ↔ production sample 통계 KS test (또는 PSI) |
| experiment log ↔ deployed model artifact | MLflow run에 다른 hyperparam 기록, 실제 배포 모델은 다른 파일 | run ID와 artifact ID가 다른 store에 — 수동 link | run_id ↔ deployed model meta cross-grep |
| eval metric (offline) ↔ business metric (online) | offline AUC 0.9 vs production CTR 변화 0 | offline-online gap은 model 외 요인 — 양쪽 측정 미박제 시 false claim | A/B test 결과 ↔ offline metric 동시 리포트 강제 |

### 6-2. Data engineering (S10 매칭 — `data-eng` profile)

| 경계면 | 불일치 예시 | 놓치는 이유 | QA 검증 방법 |
|--------|----------|-----------|------------|
| source schema → target schema (ETL) | source `created_at` TIMESTAMP, target는 DATE — 시간 정보 손실 | DDL은 통과, 데이터 의미 손실은 silent | source/target schema diff + 타입 호환성 매트릭스 |
| pipeline step output ↔ next step input | step A가 `{user_id, ts}` 출력, step B가 `{uid, timestamp}` 기대 | 각 step 단위 테스트 통과, 연결 시점 실패 | DAG 모든 edge의 schema contract 박제 강제 (dbt sources/exposures, Airflow XCom) |
| dimension table → fact table FK | dim.user 새로 추가된 user_id가 fact.event 적재 시 누락 (race) | dim refresh와 fact load timing 가정 fragile | FK 무결성 daily check + dim-first 적재 순서 강제 |
| timezone handling 양 끝 | source는 UTC, sink는 local time — daylight saving 시 24h gap | timezone은 사람이 자주 잊음, library default가 분산 | 모든 datetime 필드에 timezone 명시 강제 (naive datetime ban) |
| 스키마 진화 (schema evolution) | source에 새 컬럼 추가 → ingestion script 미수정 → 신컬럼 silent drop | "추가는 안전"이라는 가정, 실제로는 의도 손실 | source schema watcher + Slack alert + downstream impact 분석 |
| 데이터 quality 가정 ↔ 실제 | `email` 컬럼 NOT NULL 가정, 실제로 5% NULL | 단위 테스트는 합성 데이터, production NULL률 미측정 | great_expectations 같은 expectation suite + production 샘플 quality dashboard |
| backfill ↔ incremental load 일관성 | backfill은 dedupe, incremental은 dedupe 누락 → duplicate row | 두 path가 code 분리 — backfill은 rare event라 실 검증 적음 | backfill·incremental 양 path에 동일 dedupe key 박제 ↔ test 양쪽 |
| PII data ↔ compliance boundary | PII 컬럼 (email, ssn, phone)이 analytics warehouse로 평문 적재 | DDL은 통과, hash/redact 정책은 doc 외부 | PII 필드 카탈로그 ↔ ingestion path grep — 평문 적재 시 alert (compliance signal GDPR/HIPAA/PCI-DSS 매칭 강제) |

### 6-3. Mobile native (S9 매칭 — `mobile-native` profile)

| 경계면 | 불일치 예시 | 놓치는 이유 | QA 검증 방법 |
|--------|----------|-----------|------------|
| API response (server) ↔ JSON decode (client) | server `created_at` ISO8601, iOS `Codable` `JSONDecoder.dateDecodingStrategy` mismatch | iOS는 silent fail → optional `nil`, UI는 빈 칸으로 표시 | API spec ↔ Decodable struct 교차 grep + `.iso8601` strategy 강제 |
| iOS Info.plist permission ↔ Android Manifest permission | iOS는 `NSCameraUsageDescription` 박제, Android는 `<uses-permission CAMERA>` 누락 | 두 manifest 분리 — 한쪽만 PR에 박힘 | feature flag 단일 출처 ↔ 양 platform manifest 동시 확인 |
| Deep link URL scheme ↔ 라우터 매핑 | iOS `myapp://product/42` Universal Link 등록, Android intent-filter는 path만 등록 | URL 형태가 미묘하게 다름 (host vs path) | manifest URL scheme · iOS Associated Domains · Android intent-filter 3 출처 cross-check |
| native bridge method signature ↔ JS side call | React Native bridge `getPhoto(callback)`, JS 호출 `getPhoto(opts, callback)` | TS 타입은 별도 d.ts — native와 desync silent | bridge method extractor + d.ts diff |
| API version contract ↔ app store rollout | server v3 API 배포, 구버전 app은 v2 contract — backward break | server 변경 후 rollout 진행되며 구버전 user 트래픽 분포 미측정 | API version별 client 분포 dashboard + breaking change matrix |
| code signing identity ↔ entitlements | entitlements file 갱신, provisioning profile 미재발급 | Xcode error는 빌드 후 → CI 실패 후 디버그 비용 큼 | pre-build script — entitlement diff ↔ profile capabilities 비교 |
| native crash log ↔ source map | dSYM (iOS) 또는 Proguard mapping (Android) 누락 → crash log unreadable | release build flag 분산 — debug에선 동작, release만 실패 | release build 후 symbol upload step 강제 + crash log readability smoke test |

### 6-4. DevOps · embedded (S8 매칭 — `devops-infra` profile + embedded 부분)

| 경계면 | 불일치 예시 | 놓치는 이유 | QA 검증 방법 |
|--------|----------|-----------|------------|
| IaC (Terraform) ↔ 실제 cloud state | tf apply 후 console에서 수동 변경 — drift 누적 | drift는 silent — 다음 apply에서 부작용 | `terraform plan` daily run + drift alert |
| Kubernetes ConfigMap ↔ pod env reference | ConfigMap key rename, deployment env reference 미갱신 → pod CrashLoopBackOff | helm template 분리 — values 갱신 시 한쪽 누락 | template render 후 grep diff + readiness probe 강제 |
| secret rotation ↔ 배포 cycle | DB password rotate, application은 90일간 캐시 — rotate 시점 mass failure | rotate 자동화는 인프라 책임, 앱은 graceful reload 가정 | rotate event ↔ application restart 자동 trigger + secret expiration alert (만료 7일 전) |
| feature flag ↔ deploy stage | flag on/off가 staging/prod 분리, 코드는 단일 — 한 environment에서만 발화 | flag service config는 environment별 — code review로 안 보임 | flag matrix (env × flag) ↔ code reference grep |
| 모니터링 metric name ↔ alert rule | metric name `request_count`로 변경, alert rule은 `requests_total` 참조 | alert는 silent — fire 안 되어 incident detection 손실 | metric emit ↔ alert rule grep — 매칭 안 되는 alert 발견 시 fail |
| firmware version ↔ host driver | embedded firmware 신 protocol 박제, host driver는 구버전 — handshake 실패 | firmware는 OTA, driver는 별도 패키지 — version compatibility matrix 부재 | compatibility matrix 강제 + handshake smoke test |
| hardware register layout ↔ HAL 코드 | datasheet에 register address 0x1A, HAL은 0x1B (off-by-one typo) | datasheet 읽기는 사람이 검증, code review에 datasheet 미첨부 | register table 자동 생성 (vendor SDK header에서) ↔ HAL grep |
| RTOS task priority ↔ deadline 가정 | high-priority task 추가 후 기존 task starvation — deadline miss silent | scheduling 분석은 별도 도구 — code review에서 안 보임 | priority assignment diff ↔ schedulability analysis (RMA/EDF) 강제 |

### 6-5. 도메인 카탈로그 사용 흐름

```
Phase 5 합성 시:
  ↓
도메인 신호 매칭 (mcp-recommendation.md §1-2 S6~S10)
  ↓
S6 web 매칭 → §6-0 발췌 → QA 에이전트 체크리스트에 박제
S7 ml-aux 매칭 → §6-1 발췌
S8 infra 매칭 → §6-4 발췌
S9 mobile 매칭 → §6-3 발췌
S10 data-eng 매칭 → §6-2 발췌
  ↓
복합 매칭 (예: S7+S10 = ML data eng) → 양 표 union, 책임 과대 의심 시 Phase 5.5 split 권고
```

> **본 §6는 living catalog** — derived 프로젝트에서 새 경계면 버그 패턴 발견 시 본 표에 행 추가 (Phase 9 evolve / Phase 10 adapt 둘 다 가능). 발견 시점·empirical 출처 박제 권장 (예: "발견: 2026-MM-DD derived/<project> 사이클 N차").
