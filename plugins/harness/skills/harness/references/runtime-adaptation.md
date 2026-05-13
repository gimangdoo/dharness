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
| 주기 | 마지막 Adapt 이후 누적 `harness_invocation` + `agent_invocation` ≥ N (기본 10) **OR** `agent_failure` ≥ M (기본 2) |
| 임계 | 단일 신호 만으로도 시급한 drift (보안 취약점, 새 프레임워크 도입 등) |

**자동 alert 회로 (host 측 self-host CM 운영 시 한정 — 옵션):** host가 `.claude/hooks/session_start.py` 류의 SessionStart hook을 운영 중이면, 매 SessionStart마다 `_workspace/_telemetry/_last_adapt` 이후 누적 이벤트를 카운트하고 임계값 도달 시 inject에 권장 블록을 추가한다. 임계값은 환경 변수로 오버라이드 가능 — `CM_ADAPT_THRESHOLD_INVOCATIONS`(기본 10) / `CM_ADAPT_THRESHOLD_FAILURES`(기본 2). 둘 다 host의 `.claude/settings.local.json`의 `env` 필드 또는 shell env로 설정. 외부 install 환경(plugin user)은 hook 부재 — alert 발생 안 함, 수동 트리거만 가능.

**derived 프로젝트:** hook 없음. 오케스트레이터-template의 [§Phase 10 Telemetry 강제 블록](orchestrator-template.md#phase-10-telemetry-강제-블록) 따라 LLM이 매 워크플로우 종료 시 telemetry JSONL 직접 append. `/harness:harness-adapt`는 양쪽 모두 동일 명령으로 호출 (harness plugin command).

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

### Cross-artifact propagation chain

위의 §6 매핑 표가 *drift 1개 → 1차 산출물*만 명시한다면, 본 표는 *1차 변경의 부수효과로 함께 갱신해야 하는 산출물 chain*을 명시한다. Adapt는 매 변경마다 본 표를 점검하여 chain의 모든 항목이 함께 갱신되는지 확인한다. chain 누락은 dangling 참조의 근원이며 누적 부채의 가장 큰 원인이다.

| 1차 변경 | 부수 갱신 chain |
|---|---|
| 에이전트 추가 | 오케스트레이터 팀 구성 + 오케스트레이터 description 트리거 키워드 + 다른 에이전트의 협업 프로토콜(`SendMessage` 대상 추가) + Phase 8-6 테스트 시나리오 + CLAUDE.md 변경 이력 |
| 에이전트 제거 | 오케스트레이터 팀 구성에서 제거 + 다른 에이전트의 `SendMessage` 대상에서 제거 + 오케스트레이터 description 트리거 키워드 정리 + `_baseline/intent_profile.md` 도메인 매핑 갱신 + CLAUDE.md 변경 이력 |
| 에이전트 머지 | 위 "추가"와 "제거" chain의 합집합 + 역할 충돌 해소 (협업 프로토콜의 메시지 라우팅 재정의) + 머지 전 두 에이전트의 테스트 시나리오 통합 |
| 에이전트 정의 수정 | (`핵심 역할` 변경) 오케스트레이터 작업 할당 재검토 / (`입출력 프로토콜` 변경) 데이터 흐름에서 영향 받는 다른 에이전트 갱신 / CLAUDE.md 변경 이력 |
| 새 의존성 (프레임워크) | `_baseline/project_profile.md` stack.frameworks + `_baseline/intent_profile.md` constraints.tech_stack.locked_in + 영향 받는 스킬 본문 (관용구 섹션) + 영향 받는 스킬 description 트리거 키워드 + CLAUDE.md 변경 이력 |
| 의존성 제거 | 위 chain의 대칭 + 영향 받는 스킬 본문에서 해당 프레임워크 섹션 제거 (사용자 확인 후) |
| 보안 취약점 | `_baseline/project_profile.md` maturity.dependency_health + `_baseline/project_profile.md` pain_points.deprecated_usages + `_baseline/intent_profile.md` scope.must_have (패치 작업 추가) + CLAUDE.md 변경 이력 (즉시) |
| 새 디렉토리 (50+ files) | `_baseline/project_profile.md` architecture.key_directories + module_boundaries 후보 평가 + (신규 모듈이 새 도메인이면) 새 에이전트 후보 평가 + CLAUDE.md 변경 이력 |
| 디렉토리 삭제 | 위 대칭 + 해당 디렉토리에 묶인 에이전트가 있다면 사문화 후보로 등록 |
| 커버리지 ±15pp | `_baseline/intent_profile.md` quality.test_rigor + QA 에이전트 정의(검증 강도) + Phase 8-3 테스트 강도 + CLAUDE.md 변경 이력 |
| 사문화 에이전트 (10+ session 0회) | "에이전트 제거" chain과 동일 |
| 에이전트 실패율 30%+ | 에이전트 정의 프롬프트 보강 또는 분할 + (분할 시) "에이전트 추가" chain 적용 + 오케스트레이터 폴백 전략 + CLAUDE.md 변경 이력 |
| 사용자 우회 누적 (3+) | 오케스트레이터 단순화 + (필요 시) 신규 스킬 추가 또는 기존 스킬 description 확장 + 트리거 키워드 갱신 + CLAUDE.md 변경 이력 |
| Phase 9 반복 피드백 (2+) | 피드백 카테고리에 매칭되는 위 행의 chain 적용 |

#### Chain 적용 룰

1. **All-or-nothing** — chain의 한 항목만 갱신하고 나머지를 빠뜨리면 dangling 참조가 발생한다. 한 사이클 내에 chain 모두 갱신, 부분 적용 금지.
2. **승인 단위는 chain 단위** — 사용자에게 chain 전체를 한 변경안으로 묶어 제시 (§7 변경안 제시 형태에 chain 항목 명시).
3. **자동 점검** — Adapt 적용 직후 chain 항목별로 grep을 돌려 dangling 참조 잔존 여부 확인. 발견 시 §7 rollback 트리거.
4. **Chain 외 영향 발견 시** — chain 표에 없는 산출물이 영향 받는 것으로 판단되면 적용을 멈추고 사용자 확인 후, chain 표 자체를 보강하는 변경 이력을 기록.

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

drift 1건마다 다음 5개 정보 + 패치 미리보기를 함께 제시. chain 변경이면 chain 항목별 패치를 모두 포함한다.

```
[{우선순위 마커}] {drift 제목}

  현재 baseline: {기존 값}
  감지된 변화:   {새 값}
  근거:         {project_signal 또는 usage 신호의 출처}
  제안 변경:     {적용할 변경 한 줄 요약}
  영향 산출물:   {chain 항목 목록 — §6 Cross-artifact propagation 표 기반}

  ── 패치 미리보기 ────────────────────────────────
  {파일 1 경로} (수정)
  - {제거되는 줄}
  + {추가되는 줄}

  {파일 2 경로} (신규/삭제/수정)
  + {추가 본문 또는 - 삭제 본문}
  …

  → 승인 / 거부 / 수정 / 나중에
```

#### 패치 미리보기 룰

- **diff 형식 강제** — 한 줄 요약이 아니라 실제 패치 라인을 표시. 사용자는 줄 단위로 합리성을 판단할 수 있어야 한다.
- **chain 변경은 모든 파일 패치 포함** — chain 항목이 5개면 패치 블록도 5개. "1차 산출물만 보고 승인" 금지.
- **본문 200줄 초과 시 abbreviation 허용** — `... (n lines unchanged) ...`로 압축, 단 변경 라인 ±5줄 컨텍스트는 항상 표시.
- **신규 파일은 frontmatter + 첫 30줄 + 마지막 5줄 표시** — 전체 표시가 부담일 때 압축. 사용자가 "전체 보기" 요청 시 전체 표시.
- **`수정` 응답 시 사용자가 패치를 직접 편집** — 사용자가 제시된 diff에서 일부 hunk만 승인하거나 라인을 고치면 그 결과를 새 패치로 적용.
- **민감 정보 마스킹** — 패치에 토큰/키/비밀번호로 보이는 패턴이 포함되면 미리보기에서 마스킹하고 사용자에게 경고.

### 응답별 동작

| 응답 | 동작 |
|------|------|
| 승인 | 제안된 변경 그대로 적용, 변경 이력에 기록 |
| 거부 | 변경 미적용, telemetry에 `user_decision: rejected` 이벤트 추가 (다음 진단 때 같은 drift를 다시 surface하지 않도록) |
| 수정 | 사용자가 대안 제시, 그 대안을 적용 |
| 나중에 | 이번 Adapt에서 건너뜀, 다음 트리거 때 다시 제시 |

### 변경 적용 안전 — 스냅샷과 rollback

모든 Adapt 적용은 **사전 스냅샷 → 적용 → 사후 검증 → (실패 시) 자동 rollback** 4단계로 진행한다. 사용자 명시 요청에 의한 rollback도 동일 스냅샷을 사용한다.

#### 사전 스냅샷

적용 직전, chain의 모든 영향 받는 파일을 `_workspace/_telemetry/_rollback/{ts}/`에 복사한다.

```
_workspace/_telemetry/_rollback/2026-05-09T11-30-00Z/
├── manifest.json          # 변경 목록, 사용자 응답, drift 출처
├── .claude/agents/qa.md   # 적용 전 원본
├── .claude/skills/api/SKILL.md
├── _baseline/project_profile.md
└── CLAUDE.md
```

`manifest.json` 형식:

```json
{
  "ts": "2026-05-09T11:30:00Z",
  "session_id": "a3f",
  "drift_id": "delta_2026-05-09_drift_2",
  "applied_files": [".claude/agents/qa.md", ".claude/skills/api/SKILL.md"],
  "user_response": "approved",
  "chain": ["agent_definition", "orchestrator", "claude_md_changelog"],
  "post_adapt_validation": "pending"
}
```

#### Rollback 트리거

| 트리거 | 동작 |
|------|------|
| 사후 검증 실패 (§9 Post-Adapt 회귀 검증 항목 중 하나라도 fail) | 자동 rollback + 사용자에게 실패 단계와 사유 보고 + telemetry에 `system_warning: post_adapt_validation_failed` |
| 사용자 명시 요청 ("되돌려줘", "방금 변경 취소", `/harness:harness-adapt --rollback {ts}`) | 해당 ts 스냅샷으로 복원 |
| Chain 적용 중 일부만 적용된 상태에서 에러 | 즉시 rollback (부분 적용은 dangling 참조 위험) |

#### Rollback 절차

1. `manifest.json`의 `applied_files` 목록을 역순으로 복원
2. CLAUDE.md 변경 이력에 rollback 항목 추가 — `사유` 컬럼은 `Phase 10 rollback: {원인}` 형식
3. telemetry에 `rollback` 이벤트 추가 (다음 Diagnostic이 같은 drift를 다시 surface하지 않도록 거부 학습 룰 적용 — §7 거부의 학습 참조)
4. rollback 자체도 변경의 일종이므로 `manifest.post_adapt_validation` 필드를 `rolled_back`으로 갱신 후 manifest 보존

#### 보존 룰

- 스냅샷은 30일 후 자동 정리. 단, 사용자가 명시 보존 표시한 것은 유지.
- 디스크 부담 관리: 스냅샷 누적 100MB 초과 시 가장 오래된 것부터 압축 (`tar.gz`).
- **스냅샷은 변경 이력에서 누락된 적용을 사후 복구하는 용도로 쓰지 않는다** — 이력 누락 자체가 버그이며, 스냅샷은 "적용된 변경의 안전망"일 뿐 "이력의 대체물"이 아니다.

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

### 변경 이력 아카이브

CLAUDE.md 변경 이력 테이블이 무한 성장하지 않도록 주기적으로 압축한다. 포인터 원칙(§7-4 SKILL.md)을 장기적으로 유지하기 위한 위생 룰.

#### 트리거

| 트리거 | 조건 |
|------|------|
| 분기 경계 | 매 분기 종료 시(3·6·9·12월 말) 직전 분기 항목들을 아카이브 |
| 항목 수 임계 | 변경 이력 행 수 ≥ 50 시 가장 오래된 분기부터 아카이브 |
| 수동 | 사용자 요청 ("CLAUDE.md 변경 이력 정리", `/harness:harness-audit --compact-changelog`) |

#### 아카이브 방법

1. 분기 단위로 항목들을 `_baseline/changelog_archive_{YYYY-Q}.md`로 이동 (예: `changelog_archive_2026-Q1.md`)
2. CLAUDE.md 변경 이력에는 직전 분기 + 현재 분기 행만 유지
3. 아카이브된 분기는 CLAUDE.md에 1줄 요약 행으로 대체:

```markdown
| 2026-01-01 ~ 2026-03-31 | 2026-Q1 변경 16건 압축 | _baseline/changelog_archive_2026-Q1.md | Phase 9: 5건 / Phase 10 baseline: 8건 / Phase 10 usage: 3건 |
```

#### 아카이브 파일 형식

`_baseline/changelog_archive_{YYYY-Q}.md`:

```markdown
# 변경 이력 아카이브 — 2026-Q1

원본: CLAUDE.md (2026-04-01 압축됨)

## 통계

- 총 16건
- Phase 9 (사용자 피드백): 5건
- Phase 10 baseline drift: 8건 (new_dependency 4, coverage_change 2, new_directory 2)
- Phase 10 usage drift: 3건 (사문화 1, 실패율 1, 우회 1)
- rollback: 1건 (Phase 10 적용 후 검증 실패)

## 변경 이력 (날짜 오름차순)

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| ... | ... | ... | ... |
```

#### 보존 룰

- 아카이브 파일은 삭제 금지. 사후 분석에서 "이 변경이 언제 들어왔지?", "이 패턴이 반복되는가?" 추적의 유일한 출처.
- 아카이브 자체는 git에 커밋(`.gitignore` 미적용) — 변경 이력은 프로젝트 자산.
- 압축 시 row 정합성 검증: 압축 전 항목 수 = 아카이브 후 항목 수. 압축 ≠ 삭제.
- 압축 동작도 CLAUDE.md 변경 이력에 메타 항목으로 1줄 기록 (`사유` 컬럼: `meta: 변경 이력 분기 압축`).

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

### Post-Adapt 회귀 검증

변경 적용 직후 자동으로 Phase 8 검증의 *영향 받는 단계만* 재실행한다. 실패 시 §7 rollback 트리거. 성공 시 manifest에 `post_adapt_validation: passed` 기록.

#### 변경 종류별 재실행 단계

| 변경 종류 | 재실행 Phase 8 단계 | 구체 점검 |
|---|---|---|
| 에이전트 정의 frontmatter 수정 | 8-1 구조 검증 | name/description 존재, YAML 파싱 성공, 필수 섹션 5개(핵심 역할/입출력/에러/협업/(팀모드면)통신 프로토콜) 존재 |
| 에이전트 추가 | 8-1 + 8-2 + 8-6 | 구조 + 통신 경로 dead link 없음 + 테스트 시나리오 추가됨 |
| 에이전트 제거 | 8-1 + 8-5 | 다른 에이전트/오케스트레이터에 dangling 참조 grep, 데이터 흐름 dead link 없음 |
| 스킬 description 변경 | 8-4 트리거 검증 | should-trigger 10개 + should-NOT 10개 자동 재실행 (Phase 8-4 표준 20개), 트리거율 회귀 시 fail |
| 스킬 본문 추가 | 줄수 점검 | ≤500줄, 초과 시 references/ 분리 권고 (자동 분리는 안 함, 권고만) |
| 스킬 본문 수정 | 8-3 (가능 시) | with-skill vs without-skill 비교 가능한 테스트 프롬프트 1개 이상 실행, 객관 검증 가능 시 assertion |
| 오케스트레이터 수정 | 8-2 + 8-5 + 8-6 | 실행 모드 명시, 드라이런 dead link 없음, 테스트 시나리오 갱신 |
| `_baseline/project_profile.md` 갱신 | 8-1 (schema) | frontmatter + body 형식, 5축(또는 quick scan 3축) 누락 없음, source 필드 갱신됨 |
| `_baseline/intent_profile.md` 갱신 | 8-1 (schema) | 필수 5필드 보존, meta.user_confirmed_fields 갱신 반영 |
| CLAUDE.md 변경 이력 추가 | 형식 점검 | 4컬럼(날짜/내용/대상/사유), 사유 출처(Phase 9 / Phase 10) 명시, 포인터 섹션 본문이 비대해지지 않았는지 |

#### 검증 실패 처리

1. 즉시 rollback (§7 스냅샷 사용)
2. 사용자에게 실패 단계와 구체 사유 보고 — 어떤 점검 룰이 어떤 파일에서 실패했는지
3. telemetry에 `system_warning: post_adapt_validation_failed` 이벤트 추가 (`details` 필드에 실패 단계명 + 진단 메시지)
4. 같은 drift는 다음 Diagnostic 사이클에 다시 surface하되, "이전 적용이 검증 실패로 rollback됨" 컨텍스트를 함께 표시. LLM이 동일 패치를 재제안하지 않도록 `failed_proposal_hash`로 기록.

#### 부분 성공 처리

Chain 변경에서 일부 산출물 검증은 통과, 일부는 실패한 경우:
- **기본 정책: 전체 rollback** — chain은 atomic. 일관성 보존이 최우선.
- 사용자가 "통과한 것만 적용" 명시 응답 시에만 부분 적용. 단 chain 외 dangling 위험 항목은 telemetry에 `partial_apply_warning`으로 기록하고, 다음 세션 SessionStart 알림에 surface.

#### 검증 비용 관리

- description 변경의 트리거 검증은 LLM 호출 20회(should-trigger 10 + should-NOT 10, Phase 8-4 표준)로 비용이 큼. 변경 묶음에 description 변경이 여러 건이면 한 번에 배치 실행하여 컨텍스트 재사용.
- 본문 수정의 with/without 비교는 *테스트 프롬프트 1개*만 필수. 사용자 명시 요청 시 추가.
- `_baseline/*.md` schema 점검은 정규식·구조 검사만으로 LLM 호출 없이 가능 → 항상 실행해도 무료.

### Cross-layer 일관성

| 조합 | 룰 |
|------|----|
| Adapt 적용 후 같은 drift가 다음 Diagnostic에 다시 나타남 | 버그 — baseline 갱신 누락 또는 telemetry anchor 미갱신 |
| 거부된 drift가 3회 연속 같은 형태로 surface | 자동으로 우선순위 강등 |
| Phase 10이 Phase 9의 변경을 drift로 다시 감지 | 정상 — 같은 변경 이력 테이블 공유로 출처 구분 |

검증 실패 시 사용자에게 보고하고 telemetry에 `system_warning` 이벤트 추가. 자동 복구 시도는 하지 않는다 (silent automation 금지 원칙).
