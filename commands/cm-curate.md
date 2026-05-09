---
description: "cm-curator 단독 실행 — decay 적용, daily_summary 갱신, 승격 후보 스캔, baseline 자동 채움"
---

# /cm-curate

cm-curator를 SessionEnd 외 시점에 단독 실행한다. 주기적 정리 작업의 명시적 진입점.

## 컨텍스트

- **인자:** 없음
- **입력:** observations.db, `_workspace/_baseline/cm_baseline.json`
- **출력:** 큐레이션 결과 보고 (decay된 클러스터 수, 승격 후보, baseline 갱신 여부)

## 실행 절차

cm-orchestrator가 cm-curator를 서브 에이전트로 호출:

```
Agent(
  description="cm-curator: 주기 큐레이션",
  subagent_type="cm-curator",
  model="opus",
  prompt="trigger: manual_curate. memory-curate 스킬에 따라 다음 작업을 수행하라:
    1. 30일 이상 미조회 클러스터 decay 적용
    2. confidence ≥ 0.80 클러스터 승격 후보 사용자 알림
    3. 오늘 날짜 daily_summary upsert
    4. (30 세션 누적 시) cm_baseline.json initial_avg_* 자동 채움"
)
```

## 자동 트리거와의 관계

`/cm-curate`는 명시적 호출. 자동 호출은 cm-orchestrator가 다음 조건에서 수행:

- 마지막 `memory_decayed` 이벤트 이후 `session_digest_created` 10건 누적
- 마지막 `memory_promoted` 이후 60일 + confidence > 0.5 클러스터 3개 이상

## 범위 외 / 후속 명령

- 클러스터 강제 삭제 — 사용자가 `_workspace/_memory/clusters/{id}.md` 직접 삭제
- 승격 후 회귀 검증 — `/harness-adapt`의 Phase 8 회귀 검증 활용
