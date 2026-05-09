---
name: dashboard-render
description: |
  Context Manager 대시보드의 4개 뷰를 렌더링하는 스킬. background worker 프로세스가
  직접 호출한다 (에이전트 없음 — LLM 호출 불필요). /cm-dashboard 커맨드로 진입하거나
  "cm 대시보드", "메모리 현황", "세션 통계" 요청 시 참조하라.
---

# dashboard-render

CM 시스템의 4개 뷰 대시보드를 SQLite 데이터에서 집계하여 렌더링한다.
LLM 추론이 필요 없는 결정적(deterministic) 데이터 집계이므로 background worker가 직접 실행한다.

## 설계 원칙

- **LLM 호출 없음** — 모든 렌더링은 SQL 쿼리 + 템플릿으로 처리
- **캐시 정책** — 5분 캐시 (파일 수정 시간 기반)
- **FastAPI 서버** — `localhost:8765`에서 서빙 (background worker)

## 4개 뷰

### View 1: 세션 타임라인

최근 30개 세션을 날짜 역순으로 표시.

```sql
SELECT
  s.session_id,
  s.date,
  s.duration_min,
  COUNT(CASE WHEN o.section = 'do' THEN 1 END) as pending_count,
  COUNT(CASE WHEN o.section = 'warn' THEN 1 END) as warn_count,
  s.digest_path IS NOT NULL as has_digest
FROM sessions s
LEFT JOIN observations o ON s.session_id = o.session_id
GROUP BY s.session_id
ORDER BY s.date DESC
LIMIT 30;
```

**렌더링:**
```
📅 세션 타임라인 (최근 30개)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2026-05-09 | a3f | 45분 | ✅ digest | ⚠️ 2 | 📋 3
2026-05-08 | b7e | 30분 | ✅ digest | ⚠️ 0 | 📋 1
...
```

### View 2: 메모리 클러스터 맵

현재 클러스터를 confidence 순으로 표시.

```sql
SELECT
  cluster_id,
  theme,
  confidence,
  member_count,
  promoted,
  last_accessed,
  julianday('now') - julianday(last_accessed) as days_since_access
FROM clusters
ORDER BY confidence DESC;
```

**렌더링:**
```
🧠 메모리 클러스터 (총 {n}개)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[■■■■■■■■░░] 0.82 | SQLite FTS5 패턴 | 7세션 | 마지막: 2일 전
[■■■■■░░░░░] 0.51 | Python async 설정 | 3세션 | 마지막: 15일 전
[■░░░░░░░░░] 0.15 | FastAPI 라우팅 | 1세션 | 마지막: 25일 전 ⚠️ decay
```

### View 3: 도구 출력 압축 통계

PostToolUse 압축 효율 추적.

```sql
SELECT
  tool,
  COUNT(*) as call_count,
  AVG(raw_size) as avg_raw,
  AVG(compressed_size) as avg_compressed,
  AVG(ratio) as avg_ratio
FROM telemetry_tool_outputs
WHERE date >= date('now', '-30 days')
GROUP BY tool
ORDER BY call_count DESC;
```

**렌더링:**
```
📦 압축 통계 (최근 30일)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
도구       | 횟수 | 평균 raw | 평균 압축 | 비율
WebFetch   |   45 |    52KB  |    1.2KB  | 2.3%
Read       |   23 |    34KB  |    0.8KB  | 2.4%
Bash       |   12 |    18KB  |    0.5KB  | 2.8%
```

### View 4: Pending 작업 목록

미완성 Do 항목 전체 목록.

```sql
SELECT
  o.content,
  o.session_id,
  o.date,
  o.tags
FROM observations o
WHERE o.section = 'do'
  AND o.completed = 0
ORDER BY o.date DESC;
```

**렌더링:**
```
📋 미완성 작업 (총 {n}개)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] sqlite-vec 연동 테스트 (2026-05-09, 세션 a3f)
[ ] cm-compressor 10KB 임계치 조정 (2026-05-08, 세션 b7e)
...
```

## FastAPI 서버 설정

`_workspace/_worker/dashboard_server.py`:

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    # 4개 뷰 데이터 집계 + 템플릿 렌더링
    ...

@app.get("/api/sessions")
async def sessions():
    # View 1 데이터 JSON 반환
    ...
```

실행: `uvicorn dashboard_server:app --host 127.0.0.1 --port 8765`

## 캐시 정책

- 캐시 TTL: 5분 (300초)
- 캐시 무효화: observations.db 수정 시간 변경 감지 시
- 캐시 위치: 메모리 내 (프로세스 재시작 시 초기화)

## /cm-dashboard 커맨드 응답

```
CM 대시보드: http://localhost:8765
(worker 프로세스가 실행 중이어야 합니다)

worker 시작: python _workspace/_worker/dashboard_server.py
```
