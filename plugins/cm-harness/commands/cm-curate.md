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

본 커맨드는 LLM 작업이므로 결정적 핸들러(`_workspace/_hooks/cm_commands.py`)에서 처리하지 **않는다**. Claude는 다음 절차로 cm-curator 에이전트를 직접 호출한다:

1. `Task` 도구를 `subagent_type="cm-curator"`로 호출.
2. 프롬프트에 `trigger: manual_curate`를 명시하고 `memory-curate` 스킬을 따라 다음 작업을 지시:
   - 30일 이상 미조회 클러스터 decay 적용
   - confidence ≥ 0.80 클러스터 승격 후보 사용자 알림
   - 오늘 날짜 daily_summary upsert
   - (30 세션 누적 시) `cm_baseline.json` `initial_avg_*` 자동 채움
3. 승격 후보 발견 시 사용자 확인을 받기 전까지 자동 적용하지 않는다.
4. 결과를 `_workspace/_telemetry/{date}.jsonl`에 `memory_clustered`/`memory_decayed`/`memory_promoted` 이벤트로 append.

## 자동 트리거와의 관계

`/cm-curate`는 명시적 호출. 자동 호출은 cm-orchestrator가 다음 조건에서 동일한 에이전트를 호출한다:

- 마지막 `memory_decayed` 이벤트 이후 `session_digest_created` 10건 누적
- 마지막 `memory_promoted` 이후 60일 + confidence > 0.5 클러스터 3개 이상

## 범위 외 / 후속 명령

- 클러스터 강제 삭제 — 사용자가 `_workspace/_memory/clusters/{id}.md` 직접 삭제
- 승격 후 회귀 검증 — `/harness-adapt`의 Phase 8 회귀 검증 활용
