---
description: "Context Manager 상태 출력 — _memory/ 디렉토리 통계, observations.db 행 수, 최근 세션 수, 클러스터 수"
---

# /cm-harness:cm-status

Context Manager 시스템의 현재 상태를 출력한다.

## 컨텍스트

- **인자:** 없음
- **입력:** `_workspace/_memory/`, `_workspace/_telemetry/`
- **출력:** 통계 표 (LLM 추론 없음)

## 선조건 검증

`_workspace/_memory/` 미존재 시 → "새 Claude Code 세션을 한 번 열면 SessionStart 훅이 자동 생성합니다" 안내.

## 실행 절차

`plugins/cm-harness/hooks/cm_commands.py status`를 호출하여 다음을 집계:

1. `observations.db` 4개 테이블의 row 수
2. 최근 7일 세션 수 + digest 보유 비율
3. clusters 중 confidence 임계 구간별 분포
4. 마지막 SessionEnd 시각, 마지막 memory_promoted 시각
5. 미완료 Do 항목 수

## 범위 외 / 후속 명령

- 세션 상세 — `/cm-harness:cm-sessions`
- 클러스터 상세 + 시각화 — `/cm-harness:cm-dashboard` (워커 띄운 후 브라우저)
