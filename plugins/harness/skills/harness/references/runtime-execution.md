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
> P2에서 채움 — atomic task + todo 분해.

### G3 산출물 생성
> P3에서 채움 — methodology별 deliverable 템플릿.
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

## §3. G2 plan 분해 (P2에서 채움)

> **P0 placeholder.** P2 #2 per-task plan + atomic 분해 + todo doctrine을 본 절에 박제. 현재는 G2 골격 표 행만 존재.

## §4. G3 산출물 생성 (P3에서 채움)

> **P0 placeholder.** P3 #3 methodology-advisor 산출물 생성 doctrine(방법론별 deliverable 템플릿 매핑)을 본 절에 박제. 현재는 G3 골격 표 행만 존재.

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
> P2에서 채움 — atomic task + todo 분해.

### G3 산출물 생성
> P3에서 채움 — methodology별 deliverable 템플릿.
<!-- RUNTIME-GATE:end -->

### Phase 2: 팀 구성
...
```

P1에서 G1(규모분류)이 inline 채워져 derived 하네스가 소규모 작업에 합성을 생략하고 대규모에서만 합성을 트리거한다. G2·G3는 P2·P3가 채운다. 주입 메커니즘과 검증 회로는 P0에서 완성됐다.
