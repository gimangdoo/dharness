---
name: memory-search
description: |
  dharness 진화 이력을 자연어로 검색하는 규칙. "이전에 단계 X에서 뭐 했어?",
  "최근 schema 변경 이유는?", "지난번에 hook을 어떻게 단순화했지?", "phase 5 산출물
  관련 메모리" 같은 dharness 개발/유지보수 회고 질문 시 본 스킬의 절차를 따른다.
  검색은 5 source(observations / dharness_event / CLAUDE.md 변경 이력 / git log /
  skill 본문)를 progressive disclosure로 조회하며, 별도 에이전트 호출 없이 LLM이 직접
  SQL·git·Read·Grep을 호출한다.
---

# memory-search

dharness self-host CM의 자연어 검색 규칙. 검색 대상은 **dharness 자체의 진화 이력**으로 한정된다 (외부 프로젝트 메모리 아님).

## 5개 검색 source 우선순위

| 우선순위 | source | 강점 | 도구 |
|----------|--------|------|------|
| 1 | `observations_fts` (FTS5) | 가장 빠른 전문 검색 (모든 section) | SQL |
| 2 | `observations` WHERE `section='dharness_event'` | category/artifact_kind 필터 — "어떤 hook 편집됐어?", "최근 schema 변경" | SQL |
| 3 | `CLAUDE.md` "변경 이력" 표 | 사람이 큐레이션한 narrative + 사유 (가장 신호 좋은 source). 과거 누적(Phase 5-2 24 cycles)은 `archive/full-history` branch에 보존. | Read + grep |
| 4 | `git log` / `git show` | commit message + diff (코드 단위 변경 history) | Bash |
| 5 | `clusters` / `daily_summaries` / skill 본문 | 반복 패턴 + 일자 요약 + 도메인 정의 (clusters·daily\_summaries는 **legacy** — 신규 row 생성 안 됨, historic data만 조회) | SQL + Read |

DB 위치: `_workspace/_memory/observations/observations.db`. 스키마는 `.claude/hooks/_schema.py`의 `DDL` 상수가 단일 진실 원천 (단계 B 이후 `category`/`artifact_kind`/`phase` 컬럼 포함).

---

## 3-Tool Progressive Disclosure

### Tool 1: 검색 (항상 먼저)

쿼리 의도에 따라 source를 선택. 모호하면 1 → 2 → 3 순으로 fallback.

#### 1a. 일반 자연어 → `observations_fts`

```sql
SELECT o.id, o.session_id, o.date, o.section, o.content, o.tags,
       o.category, o.artifact_kind
FROM observations_fts
JOIN observations o ON observations_fts.rowid = o.rowid
WHERE observations_fts MATCH ?
ORDER BY rank
LIMIT 5;
```

#### 1b. 도메인 단어("hook 편집", "schema 변경", "command 추가") → `dharness_event` 필터

```sql
SELECT session_id, date, content, category, artifact_kind
FROM observations
WHERE section = 'dharness_event'
  AND (category LIKE ? OR artifact_kind LIKE ?)
ORDER BY date DESC, rowid DESC
LIMIT 10;
```

category 카탈로그 (현행): `cm_hook_edit`, `cm_schema_edit`, `cm_command_edit`, `cm_skill_edit`, `cm_settings_edit`, `cm_agent_edit`, `harness_skill_edit`, `harness_command_edit`, `harness_reference_edit`, `harness_manifest_edit`, `harness_other_edit`, `claudemd_edit`, `marketplace_edit`, `readme_edit`, `gitignore_edit`, `git_commit`, `git_add`, `git_rm`, `git_mv`, `git_push`, `git_pull`, `git_checkout`, `git_merge`, `git_rebase`, `git_reset`, `git_tag`.

artifact_kind 카탈로그 (현행): `skill`, `agent`, `command`, `hook`, `schema`, `claude_md`, `plugin_manifest`, `reference`, `git`, `harness`, `config`.

> **레거시 카테고리** (DB에는 historic data로 잔존, 신규 적재 없음): `cm_worker_edit`, `cm_worker_static_edit`, `cm_doc_edit`, `cm_deps_edit` — dashboard worker 폐기 후 분류 룰 제거됨. 회고 검색 시에도 매칭됨 (조회 가능).

#### 1c. "단계 X / Phase Y / 사유" → `CLAUDE.md` "변경 이력" 표

CLAUDE.md를 Read하고 grep:

```bash
grep -n "단계 [A-E]" CLAUDE.md
grep -n "Phase [0-9]" CLAUDE.md
```

또는 markdown table 직접 read해 사용자 쿼리와 매칭.

**반환 형식 (1a/1b/1c 통합):**
```markdown
[메모리 검색: "{query}" — {n}개 발견]

| 날짜 | 카테고리 | 내용 | source |
|------|----------|------|--------|
| 2026-05-10 | cm_schema_edit | Edit .claude/hooks/_schema.py | dharness_event |
| 2026-05-10 | (단계 A) | cm-harness plugin 폐지 + dharness self-host로 강등 | CLAUDE.md |

더 보려면 "타임라인 보기" 또는 날짜/세션 ID/단계명을 언급하세요.
```

**토큰 예산:** ≤ 300토큰

### Tool 2: 타임라인 (사용자 요청 시)

**트리거:** "더 보기", "타임라인", "단계 X 자세히", 특정 날짜/세션 언급, Tool 1에서 관련 결과 ≥ 3개

#### 2a. 세션 단위 — `sessions` + `dharness_event`

```sql
SELECT s.session_id, s.date, s.duration_min, s.tools_used,
       COUNT(o.id) AS event_count,
       GROUP_CONCAT(DISTINCT o.category) AS categories
FROM sessions s
LEFT JOIN observations o ON s.session_id = o.session_id AND o.section = 'dharness_event'
WHERE s.session_id IN (?)
GROUP BY s.session_id;
```

#### 2b. 단계/커밋 단위 — `git log` + CLAUDE.md cross-reference

```bash
git log --oneline --grep="단계 [A-E]"
git show <commit-sha> --stat
```

CLAUDE.md "변경 이력" 표의 row와 git commit을 매핑해서 코드 변화 범위까지 포함 응답.

#### 2c. 클러스터/요약 단위 — `clusters` + `daily_summaries` (legacy)

> **Legacy 노트:** `clusters`(7 historic rows)와 `daily_summaries`(1 historic row)는 단계 A→E 이후 **신규 row가 생성되지 않습니다**. cm-curator/Tier 3B 폐기로 자동 승격·자동 요약 엔진이 모두 사라졌습니다. SQL 조회는 historic data 회고 용도로만 유효합니다.

```sql
SELECT cluster_id, theme, confidence, tags, promoted_path
FROM clusters
WHERE tags LIKE '%' || ? || '%' AND confidence > 0.3
ORDER BY confidence DESC LIMIT 3;

SELECT date, summary FROM daily_summaries
WHERE date BETWEEN ? AND ? ORDER BY date DESC;
```

조회된 cluster의 `last_accessed`를 현재 시각으로 UPDATE한다.

```sql
UPDATE clusters SET last_accessed = ? WHERE cluster_id IN (...);
```

**반환 형식:**
```markdown
[타임라인 — "{query}" 관련 {n}개 단위]

**2026-05-10 · 단계 A (commit d14d2e7)**
- 변경: cm-harness plugin 폐지 + dharness self-host로 강등
- 산출물: .claude/{hooks,commands,skills}, marketplace.json 단일화
- 사유: 외부 install 가치보다 self-host 단순함 우선 (project memory 결정)

**2026-05-10 · 단계 B (commit 201e21c)**
- 변경: observations 컬럼 추가 + dharness 도메인 분류기
- 카테고리: cm_hook_edit:5, cm_schema_edit:1
- 사유: dharness 작업 단위를 결정적으로 적재 가능하게

전체 보기: "단계 A 전체 보기" 또는 "commit d14d2e7 보기"
```

**토큰 예산:** ≤ 800토큰

### Tool 3: 전체 읽기 (사용자 명시 요청 시)

**트리거:** "전체 보기", "단계 X 전체", "commit Y diff", "skill 본문"

| 명시 | 대상 |
|------|------|
| "단계 X 전체" | CLAUDE.md "변경 이력" 표의 해당 row + 관련 git log/show |
| "commit X" | `git show X` (full diff) |
| "session X 전체" | `_workspace/_memory/sessions/{X}/digest.md` 또는 `transcript.md` |
| "skill X 본문" | `.claude/skills/{X}/SKILL.md` 또는 `plugins/harness/skills/harness/SKILL.md` |
| "cluster X 전문" | `clusters` 테이블 row 또는 `_workspace/_memory/clusters/{X}.md` |

**토큰 예산:** 없음 (사용자가 명시 요청)

---

## 쿼리 패턴 → source 매핑

| 사용자 쿼리 패턴 | 우선 source | 비고 |
|----------------|------------|------|
| "이전에 {X}했던 거" | observations_fts | X 키워드 추출 |
| "최근 {category} 변경" | dharness_event 필터 | category LIKE 매칭 |
| "단계 X / Phase Y" | CLAUDE.md + git log | "단계 [A-E]" / "Phase [0-9]" grep |
| "사유 / 왜 / 이유" | CLAUDE.md 변경 이력 | 사유 컬럼 + commit message |
| "어떤 파일 / 무엇이 바뀜" | dharness_event content + git diff | artifact_kind 그룹화 |
| "{날짜} 작업" | daily_summaries + dharness_event | date 필터 |
| "skill / agent / command 정의" | skill 본문 Read | `.claude/skills/`, `plugins/harness/` |

---

## Fallback 전략

| 상황 | 처리 |
|------|------|
| FTS5 결과 없음 | LIKE 기반 fallback (`content LIKE '%' \|\| ? \|\| '%'`) |
| dharness_event 결과 없음 | observations_fts로 확대 검색 |
| CLAUDE.md 표 매칭 없음 | git log --grep으로 fallback |
| observations.db 없음 | "메모리 DB 없음 — 새 Claude Code 세션을 한 번 열면 SessionStart 훅이 자동 생성" 안내 |
| 모든 source 결과 없음 | "관련 메모리 없음. 이 주제의 첫 작업일 수 있습니다." |

---

## 토큰 예산 관리

| Tool | 소프트 한도 | 하드 한도 |
|------|-----------|---------|
| Tool 1 | 200토큰 | 300토큰 |
| Tool 2 | 500토큰 | 800토큰 |
| Tool 3 | 없음 | 없음 |

소프트 한도 초과 시 결과 수 줄이고 "더 있음 ({n}개 더)" 안내.

---

## 적용 범위

- ✅ **dharness 본 폴더 작업** (이 저장소 자체의 진화 이력)
- ❌ 외부 프로젝트 메모리 검색 (cm-harness plugin은 단계 A 이후 폐지)

dharness 자체의 자기 dogfooding 회로이므로, 검색 결과는 항상 *이 저장소의 변화*를 가리킨다. 사용자 프로젝트의 임의 도메인 메모리는 본 스킬 범위 밖이다 (필요하면 사용자 측에서 별도 CM을 구축).
