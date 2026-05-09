# Runtime Adaptation 가이드

Phase 10 Runtime Adaptation의 실행 가이드. 하네스가 프로젝트 변화·사용 패턴을 자동으로 관측하고 baseline에서 벗어난 부분을 사용자에게 제안 + 승인 모델로 적용하는 메커니즘.

---

## 목차

1. [개요](#1-개요)
2. [3 레이어 개관](#2-3-레이어-개관)
3. [Telemetry Schema](#3-telemetry-schema)
4. [Capture 레이어](#4-capture-레이어)
5. [Diagnostic 레이어](#5-diagnostic-레이어)
6. [Adapt 레이어](#6-adapt-레이어)
7. [승인 UX](#7-승인-ux)
8. [Baseline 갱신 룰](#8-baseline-갱신-룰)
9. [검증 룰](#9-검증-룰)

---

## 1. 개요

### 목적

Phase 1-2가 한 시점의 baseline(객관 + 주관)을 고정한다면, Phase 10은 **시간이 흐른 뒤의 baseline**을 따라잡는다. 프로젝트는 변하고, 하네스 사용 패턴도 변하므로, 초기 결정을 영원히 유지하면 하네스가 점점 현실과 멀어진다.

### 핵심 설계 원칙

1. **자동 감지, 수동 승인** — Phase 10은 변경을 자동으로 감지하지만 자동으로 적용하지 않는다. 사용자 승인 없는 변경은 신뢰를 깨뜨린다.
2. **Baseline anchor 보존** — Phase 1의 `project_profile.md` 측정값과 `source` 필드는 drift 감지의 기준점. 이 anchor가 흔들리면 무엇이 바뀌었는지 비교할 수 없다.
3. **신뢰도 가중** — Phase 2의 `inferred_fields − user_confirmed_fields` 차집합은 "원래도 추정이었던 필드"를 표시. 이 필드의 drift는 원래 추론이 틀렸을 가능성도 함께 의심한다.
4. **delta 위주 보고** — 사용자에게 baseline 전체를 보여주지 않고, 변한 부분만 골라 보고. 한 번에 처리할 변경 수를 제한 (기본 5건/세션).
5. **append-only telemetry** — 캡처된 이벤트는 절대 삭제·수정하지 않는다. 잘못된 적응 결정을 사후 분석할 수 있어야 한다.

### Phase 9와의 분담

Phase 9는 사용자가 발화한 피드백을, Phase 10은 시스템이 감지한 drift를 처리한다. 같은 변경 이력 테이블을 공유하지만 출처를 명시하여 구분(§8-3 참조).

---

## 2. 3 레이어 개관

### 데이터 흐름

```
[하네스 실행]
     ↓ (매 실행 시)
[Capture 레이어] → _workspace/_telemetry/{date}.jsonl  (append-only)
     ↓ (트리거 시)
[Diagnostic 레이어] → _workspace/_telemetry/_delta_{ts}.md
     ↓ (사용자 승인 시)
[Adapt 레이어] → .claude/agents/, .claude/skills/, CLAUDE.md, _baseline/*.md
```

### 레이어 간 책임 분리

| 레이어 | 입력 | 출력 | 사용자 개입 |
|------|------|------|-----------|
| Capture | 하네스 실행 이벤트 | `{date}.jsonl` 한 줄 추가 | 없음 (백그라운드) |
| Diagnostic | 누적 telemetry + baseline | `_delta_{ts}.md` 보고서 | 없음 (자동 분석) |
| Adapt | delta 보고서 | 변경 제안 + 승인 후 파일 수정 | **있음** (제안 검토·승인) |

이 분리는 다음을 가능케 한다:
- 캡처는 항상 무겁지 않게 (이벤트 한 줄 append)
- 진단은 비동기로 가능 (사용자 차단 없이 분석)
- 적응만 사용자 시간 사용

---

## 3. Telemetry Schema

### 저장 형식

`_workspace/_telemetry/{YYYY-MM-DD}.jsonl` — 날짜별 append-only JSONL. 한 줄에 한 이벤트.

```jsonl
{"ts":"2026-05-09T11:30:00Z","type":"harness_invocation","session_id":"a3f","trigger_keyword":"하네스 실행"}
{"ts":"2026-05-09T11:30:12Z","type":"agent_invocation","session_id":"a3f","agent":"qa","duration_s":45,"outcome":"success"}
{"ts":"2026-05-09T11:31:02Z","type":"skill_invocation","session_id":"a3f","skill":"code-review","outcome":"success"}
{"ts":"2026-05-09T11:32:18Z","type":"agent_failure","session_id":"a3f","agent":"qa","error":"timeout","retry_succeeded":true}
{"ts":"2026-05-09T11:35:00Z","type":"project_signal","signal":"new_dependency","value":"trpc@10.45.0","source":"package.json#dependencies"}
{"ts":"2026-05-09T11:35:02Z","type":"user_bypass","expected_skill":"code-review","actual_action":"manual_edit","note":"사용자가 오케스트레이터 호출 없이 직접 수정"}
```

### 이벤트 타입 표

| `type` | 필드 | 캡처 시점 |
|------|------|----------|
| `harness_invocation` | `session_id`, `trigger_keyword` | 하네스 스킬 트리거 직후 |
| `agent_invocation` | `session_id`, `agent`, `duration_s`, `outcome` | 에이전트 실행 종료 직후 |
| `skill_invocation` | `session_id`, `skill`, `outcome` | 스킬 실행 종료 직후 |
| `agent_failure` | `session_id`, `agent`, `error`, `retry_succeeded` | 에이전트 실행 실패 (재시도 결과 포함) |
| `project_signal` | `signal`, `value`, `source` | Capture 시 프로젝트 스캔에서 baseline과 다른 값 발견 시 |
| `user_bypass` | `expected_skill`, `actual_action`, `note` | 오케스트레이터 우회 감지 시 |
| `user_feedback` | `session_id`, `category`, `text` | Phase 9 피드백 수집 시 (Phase 10에서도 활용) |

`outcome` 값: `success` / `partial` / `failure`.

### 공통 규약

- 모든 이벤트에 `ts` (ISO8601 UTC) 필수
- `session_id`는 한 세션 내 모든 이벤트에 동일 (orchestrator가 발급)
- `value`/`error`는 100자 이내로 truncate (긴 stack trace는 별도 로그)
- 이벤트는 **절대 삭제·수정 금지**. 잘못 캡처된 것도 그대로 두고, 후속 이벤트로 정정

---

## 4. Capture 레이어

### 캡처 대상 — Project Signals (baseline drift 감지용)

매 하네스 실행 시작 시 빠르게 스캔하여 `project_profile.md`(t=0 anchor)와 비교, 차이가 있으면 `project_signal` 이벤트 발행.

| 신호 | 비교 대상 | 임계 |
|------|---------|------|
| 새 의존성 추가 | `stack.frameworks[]` | 즉시 (1개라도 추가 시) |
| 의존성 제거 | `stack.frameworks[]` | 즉시 |
| 새 top-level 디렉토리 | `architecture.key_directories[]` | 즉시 (50 file 이상) |
| 디렉토리 삭제 | `architecture.key_directories[]` | 즉시 |
| LOC 변화 | `meta.total_loc` | ±20% 또는 ±2000 LOC |
| 파일 수 변화 | `meta.source_file_count` | ±20% 또는 ±50 파일 |
| 테스트 커버리지 변화 | `maturity.test_coverage.line_coverage_percent` | ±10pp |
| 새 deprecated 사용 | `pain_points.deprecated_usages[]` | 즉시 |
| 보안 취약점 검출 | `maturity.dependency_health.known_vulnerabilities` | 즉시 (임계 0 → 1+) |
| 구조 패턴 변화 | `architecture.structure_pattern` | 즉시 (예: flat → feature-based) |

### 캡처 대상 — Usage Signals (사용 drift 감지용)

하네스 실행 중 자연스럽게 발생하는 이벤트.

| 신호 | 캡처 시점 | 정밀도 |
|------|---------|------|
| 에이전트 호출 | 매 호출 | 정확 (오케스트레이터가 emit) |
| 스킬 호출 | 매 호출 | 정확 |
| 에이전트 실패 + 재시도 결과 | 실패 직후 | 정확 |
| 사용자 우회 (오케스트레이터 미통과) | 사용자가 수동 작업 후 다시 하네스 호출 시 추정 | 약함 (확실하지 않으면 캡처 생략) |
| Phase 9 피드백 카테고리 | Phase 9 종료 시 | 정확 |

### 캡처 시점

- **세션 시작**: `harness_invocation` + 빠른 project signal 스캔 (≤2초 목표)
- **에이전트/스킬 실행 종료마다**: 해당 이벤트 1줄 append
- **세션 종료**: 별도 이벤트 없음 (`session_id`로 그룹핑 가능하므로)

### 캡처 비용 관리

- **빠른 신호 우선**: 매니페스트 파일 read는 단 한 번. AST 파싱·grep 전수 조사는 Diagnostic에서만.
- **이전 세션 캐시**: 직전 `project_signal` 결과를 비교 anchor로 재사용 가능 (단, 7일 이상 경과 시 baseline에서 다시 비교)
- **필수 신호만 매 실행**: dependency / 디렉토리 / LOC. 커버리지·복잡도는 임계 트리거 시에만 측정

---

## 5. Diagnostic 레이어

### 트리거

| 트리거 | 조건 |
|------|------|
| 수동 | 사용자 키워드 ("점검", "drift", "적응", "baseline 갱신") |
| 주기 | 마지막 Adapt 이후 누적 `harness_invocation` 횟수 ≥ N (기본 10) |
| 임계 | 단일 신호 만으로도 시급한 drift (보안 취약점, 새 프레임워크 도입 등) |

### Drift 감지 룰

#### 5-1. Baseline drift 룰

| 신호 패턴 | 분류 | Confidence |
|---------|------|----------|
| `project_signal: new_dependency` 1개 | minor baseline drift | High (manifest 기반) |
| `project_signal: new_dependency` 3개 이상 (한 세션) | major baseline drift — stack 재평가 권장 | High |
| `project_signal: removed_dependency` | drift (deprecated 가능성) | Medium (의도 확인 필요) |
| `project_signal: new_directory` (50+ files) | architecture drift | High |
| `project_signal: loc_change` ±20% | maturity 재측정 권장 | Medium |
| `project_signal: coverage_change` >+15pp | test_rigor 상향 가능 | Medium |
| `project_signal: coverage_change` >-15pp | test_rigor 하향 또는 회귀 | High (경고) |
| `project_signal: new_vulnerability` | 보안 긴급 | High (즉시) |

#### 5-2. Usage drift 룰

| 신호 패턴 | 분류 | Confidence |
|---------|------|----------|
| 에이전트 X invocation count = 0 in 5+ sessions | 미사용 에이전트 | Medium |
| 에이전트 X invocation count = 0 in 10+ sessions | 사문화 에이전트 | High (제거 후보) |
| 에이전트 X failure rate > 30% in 최근 N invocations | 불안정 에이전트 | High |
| 동일 에러 메시지 반복 (3+) | 구조적 문제 | High |
| `user_bypass` 이벤트 누적 (3+) | 오케스트레이터 미스매치 | Medium |
| Phase 9 피드백에 같은 카테고리 2회 이상 | 반복 피드백 | High |

### 신뢰도 가중치 적용

Phase 2의 `meta` 필드를 참조하여 가중치 조정:

```
final_confidence = base_confidence × inferred_field_weight

inferred_field_weight =
  - 1.0 if 해당 baseline 필드가 user_confirmed_fields에 있음
  - 0.6 if inferred_fields에는 있으나 user_confirmed_fields에는 없음 (Low)
  - 0.7 if confidence_low에 등록된 필드
```

가중치가 0.7 이하인 drift는 Adapt 단계에서 변경안 제시 전 "원래 추론이 맞았는지" 확인 질문을 먼저 표시.

### Delta 리포트 형식

`_workspace/_telemetry/_delta_{ts}.md`:

```markdown
# Drift Report — 2026-05-09T11:30:00Z

**검사 범위:** 마지막 Adapt 이후 12 sessions, 47 events
**Baseline 기준:** _baseline/project_profile.md (2026-04-12 작성)

## Baseline Drift (3)

### 🔴 1. 새 보안 취약점: lodash@4.17.20 (CVE-2026-XXXX)
- **신호:** project_signal (severity: high)
- **출처:** npm audit, package-lock.json
- **영향:** maturity.dependency_health.known_vulnerabilities: 0 → 1
- **신뢰도:** High
- **제안:** 즉시 패치 (lodash 4.17.21+) — 별도 패치 작업 트리거

### 🟡 2. 새 프레임워크 도입: tRPC v10.45
- **신호:** project_signal (3개 새 의존성: trpc, @trpc/client, @trpc/server)
- **출처:** package.json#dependencies
- **영향:** stack.frameworks 미반영, intent_profile.tech_stack.locked_in 미반영
- **신뢰도:** High
- **제안:**
  - project_profile.stack.frameworks에 추가
  - intent_profile.constraints.tech_stack.locked_in에 추가
  - API 영역 에이전트의 스킬에 tRPC 관용구 추가

### 🟡 3. 테스트 커버리지: 67.4% → 82.1%
- **신호:** project_signal (coverage_change +14.7pp)
- **출처:** coverage/coverage-summary.json
- **영향:** quality.test_rigor: "unit" → "integration" 후보
- **신뢰도:** Medium (단일 측정)
- **신뢰도 가중:** test_rigor는 user_confirmed → weight 1.0
- **제안:** intent_profile.quality.test_rigor 갱신 + QA 에이전트 강도 재평가

## Usage Drift (2)

### 🟡 4. 에이전트 "data-modeler" 7 sessions 미사용
- **신호:** agent invocation count = 0
- **마지막 호출:** 2026-04-12
- **신뢰도:** Medium
- **추정 원인:** 오케스트레이터 라우팅 누락 또는 작업 불일치
- **제안:** 제거 후보 또는 다른 에이전트와 머지

### 🟡 5. 에이전트 "qa" 실패율 33% (4/12)
- **신호:** agent_failure 패턴 (모두 timeout)
- **신뢰도:** High
- **제안:** QA 에이전트 프롬프트에 timeout 가이드 추가 또는 작업 분할

## 요약

- 총 5건 drift 감지 (baseline 3, usage 2)
- 1건 즉시 처리 권장 (보안)
- 4건 사용자 검토 후 적용 권장
```

---

## 6. Adapt 레이어

### Drift Signal → Proposed Change 매핑

| Drift Signal | 영향 받는 산출물 | Proposed Change |
|---|---|---|
| 새 의존성 추가 | `_baseline/project_profile.md`, `_baseline/intent_profile.md`, 영향 받는 스킬 | stack.frameworks 추가 / locked_in 추가 / 스킬에 프레임워크 관용구 섹션 추가 |
| 의존성 제거 | 위와 동일 | stack.frameworks 제거 / locked_in 제거 / 스킬의 프레임워크 섹션 제거 (사용자 확인 후) |
| 테스트 커버리지 ±15pp | `_baseline/intent_profile.md`, QA 에이전트 | quality.test_rigor 갱신 + QA 강도 재평가 제안 |
| 새 디렉토리 (50+ files) | `_baseline/project_profile.md` | architecture.key_directories 추가 + module_boundaries 후보 검토 |
| 새 module boundary | 위 + 오케스트레이터 | 새 에이전트 후보 제안 |
| 보안 취약점 | `_baseline/project_profile.md`, scope (must_have) | pain_points 갱신 + scope.must_have에 패치 작업 추가 (즉시) |
| 새 deprecated 사용 | `_baseline/project_profile.md` | pain_points.deprecated_usages 추가 + 마이그레이션 작업 후보 |
| 사문화 에이전트 (10+ sessions 0회) | `.claude/agents/{agent}.md`, 오케스트레이터 | 제거 또는 머지 제안 (변경 이력에 사유 기록) |
| 에이전트 실패율 30%+ | `.claude/agents/{agent}.md` | 프롬프트 강화 또는 분할 제안 |
| 사용자 우회 누적 | 오케스트레이터 | 우회 패턴 분석 + 단순화 또는 공식 경로 추가 제안 |
| Phase 9 반복 피드백 (2+) | 피드백 카테고리에 따라 (Phase 9-2 표 참조) | 동일 |

### Adapt 출력 종류

| 종류 | 적용 대상 | 자동 가능 여부 |
|------|---------|--------------|
| **Schema 갱신** | `_baseline/project_profile.md`, `_baseline/intent_profile.md` | High confidence + user_confirmed 필드는 자동 (변경 이력만 기록) |
| **에이전트 정의 수정** | `.claude/agents/{name}.md` | 항상 사용자 승인 필요 |
| **스킬 본문 수정** | `.claude/skills/{name}/SKILL.md` | 항상 사용자 승인 필요 |
| **에이전트 추가/제거** | `.claude/agents/`, 오케스트레이터 | 항상 사용자 승인 필요 |
| **CLAUDE.md 변경 이력 추가** | `CLAUDE.md` | 자동 (모든 적용 변경 기록) |

### 한 세션 변경 수 상한

기본 5건/세션. 더 많은 drift가 감지돼도 우선순위(보안 > deprecated > baseline > usage > stylistic) 상위 5건만 제시. 사용자가 "다 보고 싶어"라 요청하면 해제.

---

## 7. 승인 UX

### 변경안 제시 형태

drift 1건마다 다음 4개 정보를 함께 제시:

```
[{우선순위 마커}] {drift 제목}

  현재 baseline: {기존 값}
  감지된 변화:   {새 값}
  근거:         {project_signal 또는 usage 신호의 출처}
  제안 변경:     {적용할 변경 한 줄 요약}

  → 승인 / 거부 / 수정 / 나중에
```

### 응답별 동작

| 응답 | 동작 |
|------|------|
| 승인 | 제안된 변경 그대로 적용, 변경 이력에 기록 |
| 거부 | 변경 미적용, telemetry에 `user_decision: rejected` 이벤트 추가 (다음 진단 때 같은 drift를 다시 surface하지 않도록) |
| 수정 | 사용자가 대안 제시, 그 대안을 적용 |
| 나중에 | 이번 Adapt에서 건너뜀, 다음 트리거 때 다시 제시 |

### 일괄 승인 옵션

5건 모두 High confidence + 동일 카테고리(예: 모두 stack 갱신)면 "모두 승인" 단축 응답 제공. 사용자 부담 감소.

### 거부의 학습

거부된 drift 패턴은 telemetry에 누적되어, 같은 패턴이 다시 나오면 자동으로 제안 우선순위를 낮춘다 (3회 이상 거부 시 무시).

### 신뢰도 낮은 필드의 사전 확인

가중치가 0.7 이하인 drift는 변경안 제시 전에 한 단계 더:

```
이 drift는 원래 신뢰도 낮은 추론에 기반해요. 두 가지 가능성이 있습니다:
  (a) 원래 추론이 틀렸음 → baseline 자체를 정정
  (b) 원래 추론은 맞았고 진짜 변화가 일어남 → drift 적용
어느 쪽인가요?
```

응답에 따라 baseline 정정 또는 일반 drift 적용 분기.

---

## 8. Baseline 갱신 룰

### 갱신 대상

| baseline 파일 | 갱신 트리거 |
|------------|----------|
| `_baseline/project_profile.md` | baseline drift 적용 시 항상 |
| `_baseline/intent_profile.md` | locked_in / test_rigor / deployment_target 등 의도 영향 시 |
| `CLAUDE.md` 변경 이력 | 모든 Adapt 적용 시 |

### 갱신 방법

**`project_profile.md`**:
- 측정값 직접 갱신 (예: `coverage_percent: 67.4 → 82.1`)
- `source` 필드도 함께 갱신 (어느 파일/명령에서 새 값을 얻었는지)
- `meta.scanned_at` timestamp 갱신
- 이전 값을 보존하고 싶으면 `meta.history`에 추가 (선택, 기본 비활성)

**`intent_profile.md`**:
- 사용자 승인된 필드만 갱신
- `meta.user_confirmed_fields`에 갱신된 필드 dot-path 추가 (이번 승인을 통해 user-confirmed 됐으므로)
- 자동 추론 갱신은 `meta.inferred_fields` 갱신만 하고 `user_confirmed_fields`에는 추가하지 않음

### 변경 이력 기록 형식

`CLAUDE.md`의 변경 이력 테이블에 다음 형식으로 추가:

```markdown
| 2026-05-09 | tRPC v10.45 도입 — stack.frameworks 갱신, API 에이전트 스킬에 tRPC 관용구 추가 | _baseline + .claude/skills/api/ | Phase 10: drift 감지 (new_dependency) |
```

`사유` 컬럼 형식:
- Phase 9: `Phase 9: 사용자 피드백 — {요약}`
- Phase 10 baseline drift: `Phase 10: drift 감지 ({signal_type})`
- Phase 10 usage drift: `Phase 10: 사용 drift ({pattern})`

이 형식으로 미래의 사후 분석에서 어떤 변경이 어디서 왔는지 추적 가능.

### 다음 Diagnostic의 anchor 갱신

Adapt 적용 후 baseline이 갱신됐으므로, 다음 Diagnostic은 **갱신된 baseline**을 기준으로 비교한다. `meta.scanned_at`이 anchor 시점이며, telemetry 이벤트 중 `ts >= scanned_at`인 것만 새 drift 분석 대상.

---

## 9. 검증 룰

### Capture 검증

| 룰 | 검증 |
|----|------|
| 모든 이벤트에 `ts`, `type` 존재 | JSONL 파싱 시 |
| `outcome` 값이 `success/partial/failure` 중 하나 | enum |
| `session_id`가 한 세션 내 일관 | 같은 세션의 모든 이벤트 동일 ID |
| jsonl 파일 크기 < 10MB | 초과 시 새 파일로 롤오버 (`{date}_2.jsonl`) |

### Diagnostic 검증

| 룰 | 검증 |
|----|------|
| Delta 리포트에 1건 이상 drift 또는 "no drift" 명시 | 침묵 금지 |
| 각 drift에 confidence + 근거 명시 | 표 형식 강제 |
| 신뢰도 가중치 적용 결과 표시 | weight < 1.0인 항목 별도 표시 |
| 보안 취약점은 항상 우선순위 1 | 정렬 룰 |

### Adapt 검증

| 룰 | 검증 |
|----|------|
| 모든 적용 변경이 변경 이력에 기록됨 | 적용 ↔ 이력 1:1 |
| 거부된 drift는 telemetry에 `user_decision: rejected` 기록 | 학습용 |
| baseline 갱신 시 `source` 필드 함께 갱신 | drift 추적성 |
| 한 세션 변경 수 ≤ 5 (또는 사용자 해제) | 부담 관리 |

### Cross-layer 일관성

| 조합 | 룰 |
|------|----|
| Adapt 적용 후 같은 drift가 다음 Diagnostic에 다시 나타남 | 버그 — baseline 갱신 누락 또는 telemetry anchor 미갱신 |
| 거부된 drift가 3회 연속 같은 형태로 surface | 자동으로 우선순위 강등 |
| Phase 10이 Phase 9의 변경을 drift로 다시 감지 | 정상 — 같은 변경 이력 테이블 공유로 출처 구분 |

검증 실패 시 사용자에게 보고하고 telemetry에 `system_warning` 이벤트 추가. 자동 복구 시도는 하지 않는다 (silent automation 금지 원칙).
