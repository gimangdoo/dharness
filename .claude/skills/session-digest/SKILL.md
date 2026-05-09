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

## Observations DB 스키마

`_workspace/_memory/observations/observations.db` (SQLite + FTS5):

```sql
CREATE TABLE observations (
  id TEXT PRIMARY KEY,          -- obs_{session_id}_{n}
  session_id TEXT NOT NULL,
  date TEXT NOT NULL,           -- YYYY-MM-DD
  section TEXT NOT NULL,        -- what | when | do | warn
  content TEXT NOT NULL,        -- 원문 bullet 내용
  tags TEXT,                    -- JSON 배열 ["python", "sqlite"]
  embedding BLOB,               -- sqlite-vec: 벡터 (S4 이후)
  created_at TEXT NOT NULL      -- ISO8601
);

CREATE VIRTUAL TABLE observations_fts USING fts5(
  content,
  session_id,
  tags,
  content="observations",
  content_rowid="rowid"
);
```

각 digest bullet이 하나의 observation row가 된다.

## 품질 기준

| 지표 | 기준 |
|------|------|
| digest 크기 | transcript의 5-15% |
| What 항목 수 | 3-10개 |
| Do 항목 수 | 0-5개 |
| 추출 소요 시간 | < 30초 (Opus 기준) |

## DB 초기화

`observations.db`가 없을 때 cm-digester가 다음 스크립트로 초기화:

```python
import sqlite3

conn = sqlite3.connect("_workspace/_memory/observations/observations.db")
conn.executescript("""
  CREATE TABLE IF NOT EXISTS observations (...);
  CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts ...;
""")
conn.close()
```

sqlite-vec 설치 시 벡터 컬럼 활성화 (S4에서 추가).
