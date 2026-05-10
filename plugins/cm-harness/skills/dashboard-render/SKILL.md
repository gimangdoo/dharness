---
name: dashboard-render
description: |
  Context Manager 대시보드의 4개 뷰를 렌더링하는 스킬. background worker 프로세스가
  직접 호출한다 (에이전트 없음 — LLM 호출 불필요). /cm-harness:cm-dashboard 커맨드로 진입하거나
  "cm 대시보드", "메모리 현황", "세션 통계" 요청 시 참조하라.
---

# dashboard-render

CM 시스템의 4개 뷰 대시보드를 SQLite 데이터에서 집계하여 렌더링한다.
LLM 추론이 필요 없는 결정적(deterministic) 데이터 집계이므로 background worker가 직접 실행한다.

## 설계 원칙

- **LLM 호출 없음** — 모든 렌더링은 SQL 쿼리 + 템플릿으로 처리
- **캐시 정책** — 5분 캐시 (파일 수정 시간 기반)
- **FastAPI 서버** — `localhost:8765`에서 서빙 (background worker)

## 데이터 소스

**옵션 A 분산 DB 모델:** 각 프로젝트는 자기 `_workspace/_memory/observations/observations.db`를
보유한다. dashboard worker는 `_workspace/projects.json`(수동 레지스트리)을 읽어 각 프로젝트의
DB를 독립적으로 열고 결과를 프로젝트별로 묶어 반환한다 — cross-project SQL JOIN은 하지 않는다.
레지스트리 파일이 없거나 비어 있으면 `dharness`(REPO_ROOT) 단일 fallback.

모든 SQL은 4개 테이블(`observations`, `sessions`, `clusters`, `daily_summaries`)을 참조한다.
스키마 정의는 `session-digest` 스킬의 "CM 메모리 DB 스키마 (단일 진실 원천)" 섹션이
권위 있는 정의이며, 본 스킬은 그 스키마를 인용만 한다.

압축 통계(View 3)는 telemetry JSONL을 임시 SQLite DB로 적재한 후 쿼리한다 — 별도
영속 테이블이 아니다 (cm-diagnostic-rules §1과 동일 패턴).

**Inventory(View 5)와 Roadmap(View 5)은 SQL이 아니라** 각 프로젝트의 `.claude/`,
`commands/`, `CLAUDE.md`를 직접 디렉토리 스캔/Markdown 파싱하여 만든다 — 모두 결정적.

## 4개 뷰

### View 1: 세션 타임라인

최근 30개 세션을 날짜 역순으로 표시.

```sql
SELECT
  s.session_id,
  s.date,
  s.duration_min,
  SUM(CASE WHEN o.section = 'do'   AND o.completed = 0 THEN 1 ELSE 0 END) AS pending_count,
  SUM(CASE WHEN o.section = 'warn'                      THEN 1 ELSE 0 END) AS warn_count,
  CASE WHEN s.digest_path IS NOT NULL THEN 1 ELSE 0 END AS has_digest
FROM sessions s
LEFT JOIN observations o ON s.session_id = o.session_id
GROUP BY s.session_id
ORDER BY s.date DESC, s.started_at DESC
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
  promoted_path,
  last_accessed,
  CAST(julianday('now') - julianday(last_accessed) AS INTEGER) AS days_since_access
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

PostToolUse 압축 효율 추적. telemetry JSONL을 임시 SQLite DB로 적재한 후 쿼리한다.

```python
# 적재 단계 (워커가 5분마다 캐시 갱신 시 재실행)
import sqlite3, json, glob
mem = sqlite3.connect(":memory:")
mem.execute("""
  CREATE TABLE telemetry_tool_outputs (
    ts TEXT, tool TEXT, raw_size INTEGER, compressed_size INTEGER, ratio REAL
  )
""")
for path in glob.glob("_workspace/_telemetry/*.jsonl"):
    for line in open(path, encoding="utf-8"):
        evt = json.loads(line)
        if evt.get("type") == "tool_output_captured":
            mem.execute("INSERT INTO telemetry_tool_outputs VALUES (?,?,?,?,?)",
                        (evt["ts"], evt["tool"], evt["raw_size"],
                         evt["compressed_size"], evt["ratio"]))
```

```sql
SELECT
  tool,
  COUNT(*)              AS call_count,
  AVG(raw_size)         AS avg_raw,
  AVG(compressed_size)  AS avg_compressed,
  AVG(ratio)            AS avg_ratio
FROM telemetry_tool_outputs
WHERE date(ts) >= date('now', '-30 days')
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

미완성 Do 항목 전체 목록. `observations.completed`는 0=미완료, 1=완료
(스키마는 session-digest의 단일 진실 원천 섹션 참조).

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

### View 5: 프로젝트 인벤토리 + 로드맵

각 프로젝트의 산출물 카탈로그(skills/agents/commands/hooks/mcp)와 CLAUDE.md 표를
파싱한 Roadmap을 반환한다. SQL이 아니라 디렉토리 스캔 + Markdown 파싱 (LLM 없음).

**Inventory 데이터 소스:**
- skills: `<project>/.claude/skills/*/SKILL.md` frontmatter (`name`, `description`)
- agents: `<project>/.claude/agents/*.md` frontmatter (`name`, `description`, `tools`, `model`)
- commands: `<project>/commands/*.md` frontmatter
- hooks: `<project>/.claude/settings.json`의 `hooks` 트리 (이벤트 + matcher + command)
- mcp: `<project>/.claude/settings.json`의 `mcpServers` 트리 (name + command + args)

**Roadmap 데이터 소스:**
- `<project>/CLAUDE.md`에서 `| ... |` + 구분선 패턴으로 표 추출
- 표 직전의 가장 가까운 markdown heading을 `title`로 함께 반환
- 실패 시 silent — 빈 배열 반환

**렌더링:**
```
🧰 dharness 인벤토리
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
skills(7) agents(5) commands(11) hooks(4) mcp(0)

🗺️ Roadmap (CLAUDE.md 표 N개)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[변경 이력] 6 rows
[단계적 구현 현황] 7 rows
```

## FastAPI 서버 설정

실행 가능한 골격 코드는 `plugins/cm-harness/worker/dashboard_server.py`에 있고
실행 가이드는 `plugins/cm-harness/worker/README.md`에 있다.

실행: `python plugins/cm-harness/worker/dashboard_server.py` (기본 포트 8765, 127.0.0.1 바인딩).
정적 프론트엔드는 `plugins/cm-harness/worker/static/`에 mount되며 `/ui/`로 서빙된다 (없으면 fallback HTML).
localhost 출처(예: Vite dev server)에서 API를 호출할 수 있도록 CORS 허용.

엔드포인트 (project별 — 옵션 A 분산 DB):
- `GET /` — landing (정적 UI 있으면 redirect, 없으면 API 인덱스)
- `GET /api/projects` — 레지스트리 + 프로젝트별 rollup 통계
- `GET /api/projects/{name}/sessions` — View 1
- `GET /api/projects/{name}/clusters` — View 2
- `GET /api/projects/{name}/compression` — View 3
- `GET /api/projects/{name}/pending` — View 4
- `GET /api/projects/{name}/tool-timeline` — 일자별 도구 호출 (timeline 차트용)
- `GET /api/projects/{name}/inventory` — View 5 카탈로그
- `GET /api/projects/{name}/roadmap` — View 5 CLAUDE.md 표

Backward-compat (default project = 레지스트리 첫 항목):
- `GET /api/{sessions,clusters,compression,pending}?project=<name>` — `?project=` 미지정 시 default

## 캐시 정책

- 캐시 TTL: 5분 (300초)
- 캐시 무효화: observations.db 수정 시간 변경 감지 시
- 캐시 위치: 메모리 내 (프로세스 재시작 시 초기화)

## /cm-harness:cm-dashboard 커맨드 응답

```
CM 대시보드: http://localhost:8765
(worker 프로세스가 실행 중이어야 합니다)

worker 시작: python plugins/cm-harness/worker/dashboard_server.py
```
