---
description: "최근 세션 목록 출력 — session_id, 날짜, duration, digest 여부"
argument-hint: "[--limit N] (기본 30)"
---

# /cm-harness:cm-sessions

`sessions` 테이블의 최근 N개를 날짜 역순으로 출력한다.

## 컨텍스트

- **인자:** `--limit N` (선택, 기본 30)
- **입력:** `_workspace/_memory/observations/observations.db`
- **출력:** 표 형식 (LLM 추론 없음)

## 선조건 검증

DB 미존재 시 → "새 Claude Code 세션을 한 번 열면 SessionStart 훅이 자동 생성합니다".

## 실행 절차

`plugins/cm-harness/hooks/cm_commands.py sessions --limit N`이 다음 SQL 실행:

```sql
SELECT session_id, date, duration_min,
       CASE WHEN digest_path IS NOT NULL THEN '✓' ELSE '·' END AS has_digest,
       tools_used
FROM sessions
ORDER BY date DESC, started_at DESC
LIMIT ?;
```

## 범위 외 / 후속 명령

- 특정 세션 디지스트 전문 — 자연어 메모리 검색 ("세션 {id} 전체 보기"). LLM이 `memory-search` 스킬의 3-tool progressive disclosure 규칙을 따라 직접 SQL/파일 조회
- 전체 통계 — `/cm-harness:cm-status`
