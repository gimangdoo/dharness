---
name: memory-search
description: |
  cm-retriever 에이전트가 과거 세션 메모리를 검색할 때 사용하는 스킬.
  3-tool progressive disclosure 패턴, 검색 대상 우선순위, 토큰 예산 관리를 정의한다.
  "이전에 ~했던 거", "과거 세션에서", "메모리 검색", "지난번에 ~를 어떻게" 등
  과거 기억 참조 요청 시 이 스킬을 참조하라.
---

# memory-search

과거 세션 memories를 효율적으로 검색하여 progressive disclosure로 반환하는 규칙을 정의한다.

## 3-Tool Progressive Disclosure

### Tool 1: 검색 (항상 먼저)

**대상:** observations_fts (FTS5 전문 검색)

**쿼리:**
```sql
SELECT o.id, o.session_id, o.date, o.section, o.content, o.tags
FROM observations_fts
JOIN observations o ON observations_fts.rowid = o.rowid
WHERE observations_fts MATCH ?
ORDER BY rank
LIMIT 5;
```

**반환 형식:**
```markdown
[메모리 검색: "{query}" — {n}개 발견]

| 날짜 | 섹션 | 핵심 |
|------|------|------|
| 2026-05-01 | what | SQLite FTS5 설정 중 encoding 이슈 해결 |
| 2026-04-28 | do | cm-digester 초안 작성 예정 |

더 보려면 "타임라인 보기" 또는 날짜를 언급하세요.
```

**토큰 예산:** ≤ 300토큰

### Tool 2: 타임라인 (사용자 요청 시)

**트리거:**
- "더 보기", "타임라인 보여줘", 특정 날짜 언급
- Tool 1 결과에서 관련성 높은 세션이 여러 개일 때

**대상:** 관련 session_ids의 `digest.md`

**반환 형식:**
```markdown
[타임라인 — {n}개 관련 세션]

**2026-05-01 (세션 a3f)**
- What: SQLite FTS5 설정, encoding 이슈 해결
- Do: sqlite-vec 연동 테스트 예정

**2026-04-28 (세션 b7e)**
- What: cm-digester 초안 작성
- Warn: async 처리 미완성

특정 세션 전체 보기: "세션 a3f 전체 보기"
```

**토큰 예산:** ≤ 800토큰

### Tool 3: 전체 읽기 (사용자 명시 요청 시)

**트리거:**
- "전체 보기", "세션 {id} 전체", "전체 내용"

**대상:** `sessions/{id}/digest.md` 또는 `clusters/{id}.md` 전문

**반환 형식:** 파일 전문 (토큰 예산 없음)

## 검색 대상 우선순위

| 우선순위 | 대상 | 이유 |
|----------|------|------|
| 1 | `observations_fts` (FTS5) | 가장 빠른 전문 검색 |
| 2 | `clusters` 테이블 | 승격된 패턴 — 고품질 정보 |
| 3 | `daily_summaries` 테이블 | 날짜 범위 쿼리에 최적 (`WHERE date BETWEEN ? AND ?`) |
| 4 | `sessions/*/digest.md` 파일 | DB가 비어 있을 때 fallback |

`daily_summaries`는 cm-curator가 SessionEnd 이후 그날의 모든 세션을 집계하여 생성한다
(memory-curate 스킬의 "Daily summary 생성" 섹션 참조).

## 쿼리 파싱 규칙

자연어 쿼리에서 검색 키워드 추출:

| 패턴 | 키워드 추출 |
|------|-----------|
| "이전에 {X}했던 거" | X |
| "~에 대한 메모리" | ~ |
| "지난번에 {X}를 어떻게" | X |
| "과거 세션에서 {X}" | X |
| 날짜 포함 ("5월 1일") | date=2026-05-01 필터 추가 |

## Fallback 전략

| 상황 | 처리 |
|------|------|
| FTS5 검색 결과 없음 | LIKE 기반 fallback 검색 |
| observations.db 없음 | "메모리 DB 없음. S2 단계가 완료되어야 합니다." 안내 |
| LIKE도 결과 없음 | "관련 메모리 없음. 이 주제의 첫 세션일 수 있습니다." |

## 클러스터 검색 통합

observations 검색과 동시에 clusters도 확인. `clusters` 테이블 스키마는
`session-digest` 스킬의 "CM 메모리 DB 스키마 (단일 진실 원천)" 섹션이 권위 있는 정의다.

```sql
SELECT cluster_id, theme, confidence, tags, promoted_path
FROM clusters
WHERE tags LIKE '%' || ? || '%'
  AND confidence > 0.3
ORDER BY confidence DESC
LIMIT 3;
```

조회된 cluster의 `last_accessed`를 현재 시각으로 UPDATE한다 (memory-curate의
confidence 갱신 룰에서 +0.03 적용 트리거).

```sql
UPDATE clusters SET last_accessed = ? WHERE cluster_id IN (...);
```

클러스터 결과가 있으면 Tool 1 결과 상단에 "관련 패턴" 섹션으로 표시. 승격된
클러스터(`promoted_path` IS NOT NULL)는 별도 마커로 강조한다.

## 토큰 예산 관리

| Tool | 소프트 한도 | 하드 한도 |
|------|-----------|---------|
| Tool 1 | 200토큰 | 300토큰 |
| Tool 2 | 500토큰 | 800토큰 |
| Tool 3 | 없음 | 없음 |

소프트 한도 초과 시 결과 수 줄이고 "더 있음 ({n}개 더)" 안내.
