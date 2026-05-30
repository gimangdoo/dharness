> **Read at phase:** Phase 7 (오케스트레이터 합성 — 7-6 Runtime Gate 블록 주입). 런타임 의사결정 게이트 doctrine 단일 출처. dharness가 *빌드*하는 오케스트레이터 본문에 주입되는 런타임 스캐폴드를 정의.

# Runtime Execution — 런타임 게이트 doctrine

## §0. 개요 — 빌드타임 vs 런타임 경계

dharness `harness` 플러그인은 **빌드타임 팩토리** — 도메인 한 문장 → 에이전트 팀·스킬·오케스트레이터 *생성*. 하네스를 *만들* 뿐 프로젝트 작업을 *실행* 하지 않는다.

그러나 합성된 하네스가 런타임에 작업을 받았을 때 따라야 할 의사결정이 있다(작업 규모 판단, plan 분해, 산출물 생성). 이 결정은 dharness가 실행하지 않는다 — **합성 산출물(오케스트레이터)에 *주입*된 스캐폴드**가 런타임에 derived 하네스의 LLM을 인도한다.

| 레이어 | 주체 | 시점 | 산출 |
|---|---|---|---|
| 빌드타임 | dharness `harness` 스킬 | `/harness:harness-new` | 에이전트·스킬·오케스트레이터 |
| **런타임** | **derived 오케스트레이터 (본 게이트 주입됨)** | **derived 하네스가 작업 수령 시** | **작업 산출물** |

본 reference는 런타임 레이어의 단일 출처다. dharness는 본 doctrine을 read해 오케스트레이터에 **Runtime Gate 블록**을 박제한다.

## §1. 게이트 주입 규약 (marker convention)

오케스트레이터 SKILL.md 본문에 다음 마커로 구획된 블록을 박제한다. 마커는 결정적 검증(`chain.py:check_runtime_gate_block`)의 anchor다 — 임의 변경 금지.

```markdown
<!-- RUNTIME-GATE:start -->
## Runtime Gate (런타임 의사결정 게이트)

작업 수령 시 *Phase 1 컨텍스트 확인 직후* 본 게이트를 통과한다. 게이트는 self-contained — 런타임 입력(작업 문장·기존 산출물)만으로 분기를 결정한다.

### G1 규모분류 (선택적 작동)
- **small** (1-file·단일 patch·버그 fix·문구/설정 변경) → 기존 에이전트/도구 **직접 사용**, 합성·plan 분해 생략.
- **medium** (단일 모듈·기존 패턴 확장·2~10 파일) → 기존 팀 충분 판단 → 충분하면 G2, 부족하면 large 승급.
- **large** (새 서브시스템·새 module 50+ files·new_dependency 다수·cross-cutting) → 합성 트리거(에이전트/도구 추가), G2·G3 통과.
- 경계 모호 시 사용자 confirm 1회(권장 분류 + 사유).

### G2 plan 분해
medium/large 작업은 착수 전 plan 먼저(small은 생략).
1. 전체 plan 1문단(목표·표면·완료 조건; 모호하면 confirm 1회).
2. atomic task 분해 — 각 task = 한 파일/함수/테스트 수준, 단독 검증 가능.
3. 각 task에 검증 기준 1줄("make it work" 금지).
4. `TodoWrite`로 todo 박제 — 진행 중 1개만 `in_progress`, 완료 즉시 `completed`. 새 하위작업 발견 시 todo 추가(은폐 금지). 미완 todo 남으면 완료 보고 금지 → 전부 완료 시 G3.

### G3 산출물 생성
`_workspace/_baseline/intent_profile.md`의 `workflow.methodology`로 task당 산출물 형태·순서 분기:
- **tdd**: 실패 테스트→구현→리팩터(테스트 먼저). **bdd**: Given/When/Then→step 구현. **ddd**: 도메인 모델·용어→경계 컨텍스트→구현. **spec-driven**: 스펙(API/schema)→구현→대조. **trunk-based**: 작은 증분+잦은 통합. **xp**: tdd+CI 통과. **kanban/scrum/shape-up**: 프로세스 산출물(보드/백로그/pitch). **none/unknown**: 직접 구현+기본 검증.
- 방법론 산출물 + G2 검증 기준 둘 다 충족해야 task `completed`. 순서 위반(예: tdd인데 구현 먼저) 금지.
- `unknown`이고 large면 완료 보고에 "방법론 미수집 — `/harness:harness-evolve` 재합성 권장" 1줄.
<!-- RUNTIME-GATE:end -->
```

**주입 위치:** 오케스트레이터 `### Phase 1: 준비` *직후*(컨텍스트 확인으로 실행 모드를 정한 뒤, 본격 작업 전). 모드 무관(팀/서브/하이브리드) 동일 위치.

**불변식:**

1. 마커 쌍 `<!-- RUNTIME-GATE:start -->` … `<!-- RUNTIME-GATE:end -->`가 정확히 1쌍, start가 end보다 앞.
2. 블록 안에 `## Runtime Gate` 헤더 1개. (derived 오케스트레이터의 `## ` 헤더 — plugin SKILL.md `### Phase` 카운트(S16)와 무관.)
3. 게이트 식별자 `G1`·`G2`·`G3` 모두 존재 (`chain.py:check_runtime_gate_block` 결정적 검증). G1 본문은 inline 박제(§2 P1), G2·G3는 P2·P3가 채운다.

## §2. G1 규모분류 — 선택적 작동 (기능 #1)

derived 하네스가 작업을 받으면 **규모를 먼저 분류**해 합성 오버헤드를 조절한다. brownfield의 핵심 요구 — 소규모 작업에 풀 팩토리(에이전트 합성·plan 분해)를 강제하지 않고, 규모가 클 때만 합성을 트리거한다.

### 분류 (small / medium / large)

| 규모 | 정의 | 분기 |
|---|---|---|
| **small** | 1-file 또는 단일 patch — 버그 fix, 함수 수정, 문구·설정 변경 | **직접 사용.** 기존 에이전트/도구로 즉시 처리. 합성·plan 분해 *생략*. |
| **medium** | 단일 모듈·기능 — 2~10 파일, 새 함수/엔드포인트, 기존 패턴 확장 | **판단 게이트.** 기존 팀으로 충분한지 검토 → 충분하면 G2(plan 분해)로, 부족하면 large 승급. |
| **large** | 아키텍처·다중 모듈 — 새 서브시스템, 새 module, cross-cutting 변경 | **합성 트리거.** 에이전트/도구 합성 필요(`/harness:harness-evolve` 또는 신규 에이전트). G2·G3 전체 통과. |

### 규모 신호 (휴리스틱 — `heuristics-baseline.md` 재사용)

- **파일 수:** 1 → small / 2~10 동일 모듈 → medium / 새 module(50+ files 신설, `heuristics-baseline.md §1` "새 디렉토리 신호") 또는 다중 모듈 → large.
- **의존성:** 변경 없음 → small·medium / `new_dependency` major(≥3, `heuristics-baseline.md §3`) → large.
- **아키텍처 영향:** 기존 패턴·경계 내 → small·medium / 새 패턴·새 경계·새 데이터 흐름 → large.

신호가 엇갈리면 *가장 큰* 신호를 따른다(과소분류로 합성을 빠뜨리는 것이 과대분류보다 위험).

### 경계 confirm (anti-premature-judgment 정합)

규모가 경계(small↔medium 또는 medium↔large)에서 모호하면 **사용자 confirm 1회** — 권장 분류 + 사유 1줄 제시 후 진행. 자율 단정 금지(W1 doctrine 정합). 명확하면 confirm 생략.

### worked example

- **small:** "이 함수에 null 체크 추가" → 1-file·패턴 내 → **small** → 기존 코드 에이전트가 직접 수정, 합성 skip.
- **medium:** "리스트 API에 정렬 파라미터 추가" → 1~3 파일·기존 패턴 확장 → **medium** → 기존 팀 충분 판단 → G2 plan 분해 후 진행.
- **large:** "결제 모듈 신설 — PG 연동·정산·웹훅" → 새 서브시스템·새 경계·new_dependency 다수 → **large** → 합성 트리거(결제 에이전트 + 연동 도구), G2·G3 통과.

### 주입 형태 (self-contained)

derived 하네스는 런타임에 본 plugin reference를 읽지 못한다 — 위 분류·신호·분기 규칙을 **게이트 블록 본문에 inline 박제**한다(§1 G1 sub-section). 게이트는 단독으로 derived 오케스트레이터 LLM을 인도해야 한다.

## §3. G2 plan 분해 — per-task plan + atomic 분해 + todo (기능 #2)

G1에서 medium/large로 분류된 작업은 본격 착수 전 **plan을 먼저 세운다**. small은 본 게이트를 건너뛴다(직접 처리). plan 없이 즉시 코드를 쓰면 범위 누락·중간 재작업·미검증 완료가 발생한다 — plan 분해가 이를 차단한다.

### 분해 절차 (plan → atomic task → todo)

1. **전체 plan 1문단** — 작업을 한 문단으로 기술: 목표·건드릴 표면·완료 조건. 모호하면 G1 경계 confirm처럼 사용자 confirm 1회.
2. **atomic task 분해** — plan을 독립 검증 가능한 최소 단위로 쪼갠다. 각 task = 한 파일·한 함수·한 테스트 수준, 다른 task 완료를 기다리지 않고 단독으로 "됐다/안 됐다" 판정 가능.
3. **검증 기준 부착** — 각 atomic task에 검증 1줄(테스트·체크·관찰). "make it work" 같은 약한 기준 금지 — 통과/실패가 결정 가능한 goal(CLAUDE.md §4 goal-driven 정합).
4. **todo 박제** — 분해한 task를 todo list로 고정한다.

### Claude Code todo 도구 활용 규약

derived 하네스는 Claude Code 환경에서 동작하므로 **`TodoWrite` 도구**로 todo를 박제한다.

- 작업 착수 시 atomic task 전부를 `pending`으로 등록.
- 진행 중 **정확히 1개**만 `in_progress`. 한 task 완료 즉시 `completed`로 갱신하고 다음 task를 `in_progress`로.
- task 도중 새 하위작업 발견 시 todo에 추가(은폐 금지) — plan drift를 가시화한다.
- 모든 task `completed` 시 G3(산출물 생성)로. 미완 task가 남으면 완료 보고 금지.

### 규모별 적용

- **small** (G1) → plan 분해 생략, 직접 처리.
- **medium** → 경량 plan(2~5 atomic task) + todo. 과분해 금지(1 task = 1 todo 줄, 표피적 쪼개기 회피).
- **large** → 전체 plan + atomic 분해 + todo 필수. task 수 많으면 단계(milestone)로 묶되 atomic 단위 유지.

### worked example

- **medium:** "리스트 API에 정렬 파라미터 추가" → plan: 쿼리 파라미터 파싱·정렬 로직·테스트. atomic: ① `sort` 파라미터 파싱 + 검증(테스트: 잘못된 키 400) ② 정렬 적용(테스트: asc/desc 결과 순서) ③ 문서 갱신. → 3 todo 박제, 순차 `in_progress`/`completed`.
- **large:** "결제 모듈 신설" → plan 1문단 후 milestone(연동·정산·웹훅)별 atomic 분해, milestone마다 todo 그룹. G3에서 milestone별 산출물 생성.

### 주입 형태 (self-contained)

derived 하네스는 런타임에 본 plugin reference를 읽지 못한다 — plan→atomic→todo 절차와 `TodoWrite` 규약을 **게이트 블록 G2 sub-section에 inline 박제**한다(§1 G2). 게이트 단독으로 derived 오케스트레이터 LLM을 인도한다.

## §4. G3 산출물 생성 — methodology별 deliverable (기능 #3)

빌드타임은 방법론을 *선택*만 한다(W8: advisor handoff/사용자 응답 → `intent_profile.workflow.methodology`). 런타임은 그 선택을 *산출물 생성*으로 확장한다 — G2에서 만든 각 atomic task를 처리할 때, **방법론에 맞는 deliverable 형태·순서로 생성**한다. 같은 task라도 tdd면 테스트가 먼저, ddd면 도메인 모델이 먼저다.

### 출처 (self-contained 입력)

derived 하네스는 자신의 `_workspace/_baseline/intent_profile.md` frontmatter `workflow.methodology`(빌드타임 박제)를 읽어 분기한다. 본 plugin reference는 런타임에 못 읽으므로 아래 매핑을 게이트 G3 sub-section에 inline 박제한다.

### 방법론 → deliverable 매핑

| methodology | task당 산출물 순서 | 핵심 deliverable |
|---|---|---|
| **tdd** | 실패 테스트(red) → 구현(green) → 리팩터 | task마다 테스트 먼저. 미작성 시 완료 금지. |
| **bdd** | Given/When/Then 시나리오 → step 구현 → 통과 | task당 행위 시나리오 1+개. |
| **ddd** | 도메인 모델·유비쿼터스 언어 → 경계 컨텍스트 → 구현 | 모델/언어 산출물 먼저, 그 위에 코드. |
| **spec-driven** | 스펙(API·schema·계약) → 구현 → 스펙 대조 | task당 스펙 문서 먼저 박제. |
| **trunk-based** | 작은 증분 + (필요 시) feature flag → 잦은 통합 | task = 통합 가능한 작은 단위, 큰 분기 금지. |
| **xp** | tdd + pair 시점 표기 + CI 통과 | tdd 산출물 + 통합 신호. |
| **kanban / scrum / shape-up** | 프로세스 산출물(보드 항목·스프린트 백로그·pitch) | 비코드 도메인 — 코드 대신 프로세스 deliverable. |
| **none / unknown** | 직접 구현 + 기본 검증 | 방법론 강제 산출물 없음. G2 검증 기준만 충족. |

### 적용 규약

1. G2 todo의 각 task를 위 순서대로 생성 — 순서 위반(예: tdd인데 구현 먼저) 금지.
2. 방법론 deliverable과 G2 task 검증 기준은 **둘 다** 충족해야 task `completed`.
3. `methodology: unknown`(advisor 미호출+사용자 미응답)이면 강제 산출물 없이 진행하되, large 작업은 완료 보고에 "방법론 미수집 — `/harness:harness-evolve`로 재합성 권장" 1줄(빌드타임 미결을 런타임이 상속).
4. `meta.advisor_secondary_methodologies`가 있으면 primary 매핑을 따르되 secondary는 보조 참고(강제 아님).

### worked example

- **methodology=tdd, task="sort 파라미터 파싱":** ① 잘못된 키 400 기대 테스트 작성(red) → ② 파싱+검증 구현(green) → ③ 리팩터. 테스트 없이 구현부터 쓰면 순서 위반.
- **methodology=ddd, task="결제 정산 규칙":** ① 정산 도메인 모델·용어 정의 → ② 경계 컨텍스트 배치 → ③ 규칙 구현. 모델 없이 구현 금지.
- **methodology=none, task="null 체크 추가":** 직접 구현 + G2 검증(테스트/관찰)만.

### 주입 형태 (self-contained)

매핑 표·적용 규약을 게이트 블록 **G3 sub-section에 inline 박제**한다(§1 G3). derived 하네스가 자신의 `intent_profile.workflow.methodology`만으로 산출물 형태를 결정한다.

## §5. canonical 주입 예시

derived 오케스트레이터(템플릿 A 팀 모드)에 주입된 모습 — Phase 1과 Phase 2 사이:

```markdown
### Phase 1: 준비
1. 사용자 입력 분석
2. `_workspace/` 생성
3. 입력 데이터를 `_workspace/00_input/`에 저장

<!-- RUNTIME-GATE:start -->
## Runtime Gate (런타임 의사결정 게이트)

작업 수령 시 *Phase 1 컨텍스트 확인 직후* 본 게이트를 통과한다. 게이트는 self-contained.

### G1 규모분류 (선택적 작동)
- **small** (1-file·단일 patch·버그 fix·문구/설정 변경) → 기존 에이전트/도구 **직접 사용**, 합성·plan 분해 생략.
- **medium** (단일 모듈·기존 패턴 확장·2~10 파일) → 기존 팀 충분 판단 → 충분하면 G2, 부족하면 large 승급.
- **large** (새 서브시스템·새 module 50+ files·new_dependency 다수·cross-cutting) → 합성 트리거(에이전트/도구 추가), G2·G3 통과.
- 경계 모호 시 사용자 confirm 1회(권장 분류 + 사유).

### G2 plan 분해
medium/large 작업은 착수 전 plan 먼저(small은 생략).
1. 전체 plan 1문단(목표·표면·완료 조건; 모호하면 confirm 1회).
2. atomic task 분해 — 각 task = 한 파일/함수/테스트 수준, 단독 검증 가능.
3. 각 task에 검증 기준 1줄("make it work" 금지).
4. `TodoWrite`로 todo 박제 — 진행 중 1개만 `in_progress`, 완료 즉시 `completed`. 새 하위작업 발견 시 todo 추가. 미완 todo 남으면 완료 보고 금지 → 전부 완료 시 G3.

### G3 산출물 생성
`intent_profile.workflow.methodology`로 task당 산출물 분기:
- **tdd**: 테스트→구현→리팩터. **bdd**: Given/When/Then→step. **ddd**: 도메인 모델→경계→구현. **spec-driven**: 스펙→구현→대조. **trunk-based**: 작은 증분+잦은 통합. **xp**: tdd+CI. **kanban/scrum/shape-up**: 프로세스 산출물. **none/unknown**: 직접 구현+기본 검증.
- 방법론 산출물 + G2 검증 둘 다 충족 시 `completed`. 순서 위반 금지.
<!-- RUNTIME-GATE:end -->

### Phase 2: 팀 구성
...
```

P1에서 G1(규모분류), P2에서 G2(plan→atomic task→todo), P3에서 G3(methodology→산출물)가 inline 채워져 게이트가 완성됐다 — derived 하네스가 소규모는 직접 처리, medium/large는 plan 분해 후 todo로 진행하며 각 task를 방법론에 맞는 산출물 형태로 생성한다. 주입 메커니즘과 검증 회로는 P0에서 완성됐다.
