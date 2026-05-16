---
description: "Context Manager 상태 출력 — _memory/ 디렉토리 통계, observations.db 행 수, 최근 세션 수, draft pending"
---

# /cm-status

Context Manager 시스템의 현재 상태를 출력한다.

## 컨텍스트

- **인자:** 없음
- **입력:** `_workspace/_memory/`, `_workspace/_telemetry/`
- **출력:** 통계 표 (LLM 추론 없음)

## 선조건 검증

`_workspace/_memory/` 미존재 시 → "새 Claude Code 세션을 한 번 열면 SessionStart 훅이 자동 생성합니다" 안내.

## 실행 절차

`py .claude/hooks/cm_commands.py status`를 호출하여 다음을 집계:

1. `observations.db` 2개 테이블의 row 수 (R1 2026-05-14: clusters/daily_summaries 제거)
2. observations 중 `section='dharness_event'` row 수
3. 최근 7일 세션 수
4. 미적용 CLAUDE.md draft 수
5. CLAUDE.md "변경 이력" 표 행 수 + archive 임계 경고

## 범위 외 / 후속 명령

- 세션 상세 — `/cm-sessions`
- 미적용 CLAUDE.md draft 처리 — `/cm-claudemd-apply <sid>` 또는 `/cm-claudemd-discard`
