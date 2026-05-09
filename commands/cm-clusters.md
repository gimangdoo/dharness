---
description: "클러스터 목록 출력 — confidence 순, 멤버 수, 마지막 조회일, 승격 여부"
argument-hint: "[--min-confidence X.XX]"
---

# /cm-clusters

`clusters` 테이블을 confidence 순으로 출력한다.

## 컨텍스트

- **인자:** `--min-confidence X.XX` (선택, 기본 0.0 — 모두 출력)
- **입력:** `_workspace/_memory/observations/observations.db`
- **출력:** 표 형식

## 실행 절차

`_workspace/_hooks/cm_commands.py clusters --min-confidence X.XX`가 다음 SQL 실행:

```sql
SELECT cluster_id, theme, confidence, member_count,
       last_accessed,
       CAST(julianday('now') - julianday(last_accessed) AS INTEGER) AS days_since,
       CASE WHEN promoted_path IS NOT NULL THEN '🏷️' ELSE '·' END AS promoted
FROM clusters
WHERE confidence >= ?
ORDER BY confidence DESC;
```

## 범위 외 / 후속 명령

- 클러스터링 재실행 — `/cm-curate`
- 사문화 클러스터 정리 — `/cm-curate`로 decay 적용 후 사용자 확인
