---
name: session-digest
description: |
  cm-digester 에이전트가 세션 transcript를 구조화된 digest로 변환할 때 사용하는 스킬.
  what/when/do/warn 4섹션 구조, observations.db 스키마, 결정·펜딩 추출 규칙을 정의한다.
  세션이 끝난 후 digest를 생성하거나 기존 digest 형식을 확인할 때 이 스킬을 참조하라.
---

# session-digest

세션 transcript를 what/when/do/warn 4섹션 구조의 digest로 변환하는 규칙을 정의한다.

## Digest 구조 (4섹션)

```markdown
---
session_id: <6자 hex>
date: <YYYY-MM-DD>
duration_min: <n>
tools_used: [<tool_name>, ...]
tags: [<topic>, ...]
---

## What (무엇을 했나)
- {완료된 작업 항목들 — 동사로 시작하는 bullet}

## When (언제 / 어떤 맥락에서)
- {작업의 배경과 동기 — 왜 이 작업이 필요했는지}

## Do (결정 및 다음 실행 항목)
- [ ] {다음에 해야 할 일 — 체크박스 형식}

## Warn (실패·주의·미완성)
- ⚠️ {실패한 시도, 주의사항, 미완성 작업}
```

## 추출 규칙

### What 섹션
- 완료된 행동만 포함 (시도 실패는 Warn으로)
- 동사 원형으로 시작: "구현", "수정", "확인", "생성" 등
- 너무 세부적인 구현 단계는 하나로 묶는다
- 최대 10개 bullet (초과 시 상위 10개)

### When 섹션
- 이 작업이 왜 시작되었는지 맥락 기술
- 사용자가 명시한 목표 또는 문제
- 이전 세션과의 연속성이 있으면 언급

### Do 섹션
- 사용자나 Claude가 명시적으로 "다음에 ~하자"고 한 항목
- 미완성 작업 중 재개 예정인 것
- 체크박스 형식 `[ ]` 필수

### Warn 섹션
- 시도했지만 실패한 접근법 (같은 실수 반복 방지)
- 주의해야 할 제약사항 (도구 한계, 환경 특이사항)
- 의도적으로 미완성으로 둔 항목

## CM 메모리 DB 스키마 (사양 진실 원천)

`_workspace/_memory/observations/observations.db` (SQLite + FTS5)는 CM 시스템의 모든 영속 메모리를 담는다.

**진실 원천 두 계층:**
- **사양:** 본 섹션의 SQL 정의가 사람이 읽는 단일 진실 원천이다. 다른 스킬(`memory-curate`, `memory-search`, `dashboard-render`)은 이 섹션을 인용하기만 하고 자체 정의를 갖지 않는다.
- **코드:** `plugins/cm-harness/hooks/_schema.py`의 `DDL` 상수가 본 섹션을 그대로 미러링한다. `session_start.py`, `cm_commands.py`가 `from _schema import DDL`로 import한다. 본 섹션을 변경할 때는 `_schema.py`도 함께 갱신한다 (Phase 10 진단룰의 chain 적용 대상).

```sql
-- ========== 1. observations: 세션 디지스트 bullet 단위 ==========
CREATE TABLE IF NOT EXISTS observations (
  id           TEXT PRIMARY KEY,    -- obs_{session_id}_{n}
  session_id   TEXT NOT NULL,
  date         TEXT NOT NULL,       -- YYYY-MM-DD
  section      TEXT NOT NULL,       -- what | when | do | warn
  content      TEXT NOT NULL,       -- 원문 bullet 내용
  tags         TEXT,                -- JSON 배열 ["python", "sqlite"]
  embedding    BLOB,                -- sqlite-vec 벡터 (S4 이후)
  completed    INTEGER DEFAULT 0,   -- do 항목 완료 여부 (0/1)
  cluster_id   TEXT,                -- 병합된 cluster (없으면 NULL)
  created_at   TEXT NOT NULL        -- ISO8601
);

CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
  content, session_id, tags,
  content="observations", content_rowid="rowid"
);

-- ========== 2. sessions: 세션 메타 (cm-digester가 SessionEnd에 upsert) ==========
CREATE TABLE IF NOT EXISTS sessions (
  session_id    TEXT PRIMARY KEY,   -- 6자 hex
  date          TEXT NOT NULL,      -- YYYY-MM-DD
  started_at    TEXT NOT NULL,      -- ISO8601
  ended_at      TEXT,
  duration_min  INTEGER,
  tools_used    TEXT,               -- JSON 배열
  digest_path   TEXT,               -- _workspace/_memory/sessions/{id}/digest.md (NULL=미생성)
  project       TEXT                -- working dir 이름
);

-- ========== 3. clusters: cm-curator가 관리 ==========
CREATE TABLE IF NOT EXISTS clusters (
  cluster_id     TEXT PRIMARY KEY,  -- c_{6자 hex}
  theme          TEXT NOT NULL,
  confidence     REAL NOT NULL,     -- 0.0 ~ 1.0
  member_count   INTEGER NOT NULL DEFAULT 0,
  tags           TEXT,              -- JSON 배열
  embedding      BLOB,              -- sqlite-vec (S4 이후)
  promoted_path  TEXT,              -- 승격된 .claude/skills/.../SKILL.md (없으면 NULL)
  created_at     TEXT NOT NULL,
  last_updated   TEXT NOT NULL,
  last_accessed  TEXT               -- memory_query 마지막 시각
);

-- ========== 4. daily_summaries: cm-curator가 SessionEnd 이후 생성/갱신 ==========
CREATE TABLE IF NOT EXISTS daily_summaries (
  date          TEXT PRIMARY KEY,   -- YYYY-MM-DD
  summary       TEXT NOT NULL,      -- 그날 세션들의 통합 요약 (~300토큰)
  session_ids   TEXT NOT NULL,      -- JSON 배열
  generated_at  TEXT NOT NULL
);
```

`telemetry_tool_outputs`는 별도 테이블이 아니라 `_workspace/_telemetry/*.jsonl`에서 `type='tool_output_captured'` 이벤트를 적재한 임시 뷰다. `dashboard-render`가 필요할 때 JSONL을 SQLite 임시 DB로 로드한 후 SELECT한다 (cm-diagnostic-rules §1과 동일 패턴).

각 digest bullet이 하나의 observation row가 된다. `sessions`는 cm-digester가 SessionEnd에 upsert하고, `clusters`/`daily_summaries`는 cm-curator가 관리한다.

## 품질 기준

| 지표 | 기준 |
|------|------|
| digest 크기 | transcript의 5-15% |
| What 항목 수 | 3-10개 |
| Do 항목 수 | 0-5개 |
| 추출 소요 시간 | < 30초 (Opus 기준) |

## DB 초기화

`observations.db`가 없을 때 cm-digester(또는 session-capture 스킬)가 위 4개 테이블 + FTS5 가상 테이블을 모두 한 번에 생성한다. 각 테이블 정의는 `IF NOT EXISTS`이므로 재실행에 안전하다.

sqlite-vec 설치 시 `observations.embedding`, `clusters.embedding` 컬럼이 활용된다 (S4 이후). sqlite-vec이 없어도 스키마는 그대로 두고, `memory-curate`의 키워드 기반 fallback 알고리즘이 동작한다.
