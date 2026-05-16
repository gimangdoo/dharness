---
description: Phase 10 Runtime Adaptation 수동 트리거 — telemetry drift 자동 감지 진입점. baseline 비교 → 변경안 → 승인 → 적용. 자동 적용 없음.
---

# Harness — Adapt (telemetry drift 진입점)

`plugins/harness/skills/harness/SKILL.md` Phase 10의 **Diagnostic + Adapt 레이어**를 수동으로 실행한다. 누적된 telemetry와 baseline을 비교하여 drift를 감지하고, 변경안을 제시한 뒤 사용자 승인을 받아 적용한다.

> **자동 적용은 없다.** 모든 변경은 명시적 사용자 승인이 필요하다.

## 진화 명령 3분기 doctrine (2026-05-14)

| 명령 | 진입 시점 | 입력 | 특화 워크플로우 |
|---|---|---|---|
| **`/harness:harness-evolve`** | 사용자가 *명시적 피드백* 발화 | 자유 텍스트 | Phase 9 |
| **`/harness:harness-adapt`** | 시스템이 *telemetry drift* 자동 감지 (또는 사용자 명시 점검) | `_workspace/_telemetry/*.jsonl` | 본 명령 |
| **`/harness:harness-remove` / `-split` / `-merge`** | 사용자가 *구조적 변경* 명시 | `agent|skill <이름>` | 격리 워크플로우 |

**언제 본 명령?**:
- 마지막 Adapt 이후 N회 이상 호출 누적 (`harness-status` §3 임계 초과 시)
- 단일 큰 drift (보안 취약점, 새 프레임워크) 감지 또는 의심
- 사용자가 "점검", "drift 확인", "적응" 등 발화

**언제 본 명령 아님?**:
- 사용자가 *구체 피드백* 발화 시 → `evolve`
- *명시적 제거/분할/통합* 요청 → `remove` / `split` / `merge`

## 컨텍스트
- **입력**: `_workspace/_telemetry/*.jsonl` (누적 telemetry, Phase 10 Capture 레이어 산출), `_workspace/_baseline/*.md` (t=0 anchor)
- **출력**: `_workspace/_telemetry/_delta_{ts}.md` (drift 리포트), 승인 시 `.claude/agents/`·`.claude/skills/`·`CLAUDE.md`·`_workspace/_baseline/*.md` 갱신

## 선조건 검증 (먼저 실행)

1. `_workspace/_telemetry/` 디렉토리가 존재하고 1개 이상의 `.jsonl` 파일이 있는가?
2. `_workspace/_baseline/project_profile.md`가 존재하는가?

**미충족 시:**

| 미충족 항목 | 안내 메시지 |
|-----------|----------|
| (1) | "telemetry 데이터가 없습니다. 오케스트레이터에 capture 훅이 설치되어 있는지 확인하세요 — `plugins/harness/skills/harness/references/runtime-adaptation.md` §4 (Capture 레이어) 참조. 신규 하네스라면 최소 몇 회 실행 후 다시 시도하세요." |
| (2) | "baseline이 없습니다. `/harness:harness-new` 또는 `/harness:harness-baseline`을 먼저 실행하세요." |

## 실행 절차

`plugins/harness/skills/harness/references/runtime-adaptation.md`를 참조하여 Phase 10 3 레이어 중 **Diagnostic + Adapt**를 실행한다 (Capture는 오케스트레이터가 매 실행마다 이미 수행 중).

### 1. Diagnostic — drift 감지

누적 telemetry와 baseline을 비교하여 drift를 **두 종류로 분리** 감지:

- **baseline drift**: 프로젝트 자체가 변함 → `project_profile.md` 갱신 필요
  - 새 의존성, 새 디렉토리, 새 프레임워크
  - 보안 취약점 신규 검출
  - 테스트 커버리지·복잡도 큰 변화
- **사용 drift**: 프로젝트는 같지만 하네스 사용 패턴이 변함 → 에이전트/스킬 자체 재구성 필요
  - 특정 에이전트 N회 연속 미사용
  - 특정 에이전트 실패율 임계 초과
  - 사용자가 오케스트레이터 우회하여 수동 작업

### 2. 신뢰도 가중치 적용

Phase 2 메타에서 `meta.inferred_fields − meta.user_confirmed_fields` 차집합("신뢰도 낮음" 필드)을 가중. **신뢰도 낮은 필드의 baseline drift는 변경안 제시 전 "원래 추론이 맞았는지" 사용자 확인을 먼저 트리거.** 신뢰도 높은 필드의 drift는 변경안 직접 제시.

### 3. Delta 리포트 생성

`_workspace/_telemetry/_delta_{timestamp}.md` 작성:
- §Baseline Drift (심각도 🔴/🟡 표시)
- §Usage Drift (심각도 🔴/🟡 표시)
- §요약 (총 drift 수, 권장 우선순위)

### 4. Adapt — 변경안 제시

drift 신호별로 매핑된 변경안을 사용자에게 제시. **한 세션 변경 수 상한 준수** (기본 5건).

### 5. 승인 UX

각 변경안에 대해 4개 옵션 제공:
- **a) 즉시 적용** — 해당 변경 바로 반영
- **b) 보류** — 다음 점검까지 대기
- **c) 거부** — 학습됨(같은 패턴이 다시 감지되어도 우선순위 낮춤)
- **d) 일괄 승인** — 남은 모든 변경 일괄 적용

### 6. 승인된 변경 적용

해당하는 위치에 반영:
- `.claude/agents/{name}.md` — 에이전트 역할/프로토콜 갱신
- `.claude/skills/{name}/` — 스킬 description/본문 갱신
- `CLAUDE.md` — 트리거 규칙 갱신, 변경 이력 추가
- `_workspace/_baseline/*.md` — baseline 갱신 (다음 Diagnostic의 anchor)

### 7. 변경 이력 기록

CLAUDE.md 변경 이력 테이블(Phase 7-4 템플릿)에 출처 명시:

```
| {YYYY-MM-DD} | Phase 10: drift 감지 ({drift 이름}) — {요약} | {대상} | {사유} |
```

Phase 9(사용자 수동 피드백)와 출처를 분리 기록하여 추적 가능성 보장.

### 8. Adapt counter reset (필수, 마지막 단계)

현 호출 context의 `_workspace/_telemetry/_last_adapt` 파일을 현재 timestamp로 갱신. host repo가 SessionStart alert 통합을 운영 중이면 본 reset이 다음 사이클부터 alert 카운팅을 새로 시작시킨다. 사용자 승인 변경 적용 후, 또는 거부만 있어도 reset(drift 점검 자체는 수행됨).

```powershell
# Windows PowerShell
$ts = (Get-Date -AsUTC).ToString("yyyy-MM-ddTHH:mm:ssZ")
Set-Content -Path "_workspace\_telemetry\_last_adapt" -Value $ts -Encoding utf8
```

```bash
# bash / POSIX
date -u +"%Y-%m-%dT%H:%M:%SZ" > _workspace/_telemetry/_last_adapt
```

`pwd` 기준 현 context의 `_workspace/_telemetry/_last_adapt` *1개만* 갱신 — host repo와 derived 동시 갱신 금지.

> **Optional integration — dharness self-host CM 환경:** dharness 본 저장소에서 호출된 경우, SessionStart hook(`.claude/hooks/session_start.py` + `_schema.py`의 `count_events_since_last_adapt`)이 누적 invocation/failure 카운트로 alert를 띄운다. 본 reset으로 alert가 새 사이클부터 카운팅된다. 임계값 변경은 `.claude/hooks/_schema.py`의 `HARNESS_ADAPT_THRESHOLD_INVOCATIONS` / `HARNESS_ADAPT_THRESHOLD_FAILURES` 상수. **derived 프로젝트 등 일반 install 환경**에는 본 hook이 없으므로 alert 자체가 발생하지 않으며, reset은 단순히 카운터 anchor를 갱신할 뿐. 본 reset을 생략하면 다음 Diagnostic이 같은 telemetry 윈도우를 다시 평가한다.

## 트리거 빈도 권고

- **수동**: 큰 변경 직후, 또는 매주~격주
- **주기적**: 마지막 Adapt 이후 N회(기본 10) 하네스 실행 누적 시 자동 제안
- **임계**: 단일 큰 drift (보안 취약점, 새 프레임워크 도입 등) 즉시
