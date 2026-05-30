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

derived 하네스가 작업을 수령하면 *Phase 1 컨텍스트 확인 직후* 본 게이트를 통과한다.
각 게이트는 런타임 입력(작업 문장·기존 산출물)을 보고 분기를 결정한다.

| 게이트 | 질문 | 분기 | 단일 출처 |
|---|---|---|---|
| G1 규모분류 | 작업 규모가 small/medium/large 중 무엇인가 | small→직접 사용 / large→합성 트리거 | `runtime-execution.md §2` |
| G2 plan 분해 | 작업을 atomic task + todo로 분해했는가 | 분해 후 진행 | `runtime-execution.md §3` |
| G3 산출물 생성 | methodology에 맞는 deliverable 템플릿을 적용했는가 | 템플릿 적용 후 산출 | `runtime-execution.md §4` |
<!-- RUNTIME-GATE:end -->
```

**주입 위치:** 오케스트레이터 `### Phase 1: 준비` *직후*(컨텍스트 확인으로 실행 모드를 정한 뒤, 본격 작업 전). 모드 무관(팀/서브/하이브리드) 동일 위치.

**불변식 (P0):**

1. 마커 쌍 `<!-- RUNTIME-GATE:start -->` … `<!-- RUNTIME-GATE:end -->`가 정확히 1쌍, start가 end보다 앞.
2. 블록 안에 `## Runtime Gate` 헤더 1개. (derived 오케스트레이터의 `## ` 헤더 — plugin SKILL.md `### Phase` 카운트(S16)와 무관.)
3. 게이트 표 3행(G1/G2/G3) — P0는 골격만, 각 게이트 *본문 doctrine*은 P1-P3가 §2-§4에 채운다.

## §2. G1 규모분류 (P1에서 채움)

> **P0 placeholder.** P1 #1 brownfield 규모 선택적 작동에서 small/medium/large 휴리스틱 + 분기 doctrine을 본 절에 박제. 현재는 G1 골격 표 행만 존재.

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

derived 하네스가 작업을 수령하면 *Phase 1 컨텍스트 확인 직후* 본 게이트를 통과한다.

| 게이트 | 질문 | 분기 | 단일 출처 |
|---|---|---|---|
| G1 규모분류 | 작업 규모가 small/medium/large 중 무엇인가 | small→직접 사용 / large→합성 트리거 | `runtime-execution.md §2` |
| G2 plan 분해 | 작업을 atomic task + todo로 분해했는가 | 분해 후 진행 | `runtime-execution.md §3` |
| G3 산출물 생성 | methodology에 맞는 deliverable 템플릿을 적용했는가 | 템플릿 적용 후 산출 | `runtime-execution.md §4` |
<!-- RUNTIME-GATE:end -->

### Phase 2: 팀 구성
...
```

P0 단계에선 게이트가 *골격*(분기 단서만)이고, P1-P3가 §2-§4 본문을 채우면 derived 하네스가 실제 분기를 수행한다. 주입 메커니즘과 검증 회로는 P0에서 완성된다.
