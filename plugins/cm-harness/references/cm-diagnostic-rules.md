# CM Diagnostic Rules — Phase 10 Extension

Context Manager 전용 drift 감지 룰. `references/runtime-adaptation.md`의 Diagnostic 레이어에 추가되는 CM 도메인 특화 규칙 파일.

harness Phase 10이 표준 telemetry (harness_invocation, agent_failure 등)를 분석하는 것과 동일하게, 이 파일은 **CM 전용 telemetry 이벤트** (session_start, tool_output_captured, session_digest_created, memory_clustered, memory_promoted, memory_decayed, memory_query)를 분석하는 룰을 정의한다.

---

## 목차

1. [CM 전용 telemetry 이벤트](#1-cm-전용-telemetry-이벤트)
2. [Baseline drift 룰](#2-baseline-drift-룰)
3. [Usage drift 룰](#3-usage-drift-룰)
4. [Proposed Change 매핑](#4-proposed-change-매핑)
5. [Delta 리포트 CM 섹션 형식](#5-delta-리포트-cm-섹션-형식)
6. [Phase 10 연동 포인터](#6-phase-10-연동-포인터)

---

## 1. CM 전용 telemetry 이벤트

CM 에이전트가 `_workspace/_telemetry/{YYYY-MM-DD}.jsonl`에 append하는 이벤트 타입.
harness의 기존 이벤트 타입(§3 runtime-adaptation.md)에 병합하여 저장한다.

| `type` | 핵심 필드 | 발행 에이전트 |
|--------|----------|-------------|
| `session_start` | `session_id`, `project`, `tokens_injected` | cm-injector |
| `tool_output_captured` | `session_id`, `tool`, `raw_size`, `compressed_size`, `ratio` | cm-compressor |
| `session_digest_created` | `session_id`, `decisions`, `pending`, `size_bytes` | cm-digester |
| `memory_clustered` | `cluster_id`, `members`, `confidence` | cm-curator |
| `memory_promoted` | `cluster_id`, `new_artifact` | cm-curator |
| `memory_decayed` | `memory_id`, `reason`, `confidence_before`, `confidence_after` | cm-curator |
| `memory_query` | `session_id`, `query`, `tokens_returned`, `results` | cm-retriever |

### 집계 쿼리 기준

Diagnostic 레이어가 분석에 사용하는 기준 집계 쿼리 (SQLite로 telemetry JSONL → 임시 DB 적재):

```sql
-- 최근 N일간 압축 비율 이동 평균
SELECT
  date(ts) as day,
  AVG(CAST(json_extract(line, '$.ratio') AS REAL)) as avg_ratio,
  COUNT(*) as compression_count
FROM telemetry
WHERE json_extract(line, '$.type') = 'tool_output_captured'
  AND date(ts) >= date('now', '-30 days')
GROUP BY day
ORDER BY day;

-- 클러스터별 최근 조회 이력
SELECT
  json_extract(line, '$.cluster_id') as cluster_id,
  COUNT(*) as query_count
FROM telemetry
WHERE json_extract(line, '$.type') = 'memory_query'
  AND date(ts) >= date('now', '-30 days')
GROUP BY cluster_id;

-- cm-injector 토큰 이동 평균
SELECT
  date(ts) as day,
  AVG(CAST(json_extract(line, '$.tokens_injected') AS REAL)) as avg_tokens
FROM telemetry
WHERE json_extract(line, '$.type') = 'session_start'
  AND date(ts) >= date('now', '-14 days')
GROUP BY day;
```

---

## 2. Baseline drift 룰

CM 구성요소 자체의 품질이 시간이 지나면서 저하되는 패턴을 감지한다.

### 2-1. Compressor 압축 비율 악화

| 신호 패턴 | 분류 | Confidence |
|----------|------|-----------|
| `tool_output_captured` ratio 7일 이동 평균이 0.1→0.3 이상으로 상승 | cm-compressor 품질 drift | High |
| ratio 이동 평균 > 0.5 (압축 효과 절반 미만) | 심각한 compressor 성능 저하 | High |
| 특정 `tool` 이름의 ratio만 급격히 상승 (다른 도구는 정상) | 해당 도구 압축 전략 미스매치 | Medium |

**baseline 기준값:** 시스템 구축 시점 처음 30회 `tool_output_captured` 이벤트의 ratio 평균 = `_baseline/cm_baseline.json#compressor.initial_avg_ratio`에 기록.

**Proposed Change:** cm-compressor 에이전트 정의의 압축 전략 섹션 보강, 또는 `tool-output-compress` 스킬의 도구별 압축 전략 테이블 업데이트.

---

### 2-2. Injector 토큰 비대화

| 신호 패턴 | 분류 | Confidence |
|----------|------|-----------|
| `session_start` tokens_injected 14일 이동 평균이 50% 이상 증가 | 인젝션 크기 creep | Medium |
| tokens_injected > 1500 (예산 1000의 150%) | 하드 임계 초과 | High |
| tokens_injected가 세션마다 단조 증가 (N=7 세션 연속) | 누적 비대화 패턴 | Medium |

**baseline 기준값:** 초기 10 세션 평균 `tokens_injected` = `_baseline/cm_baseline.json#injector.initial_avg_tokens`.

**Proposed Change:** cm-injector의 `CM_INJECT_N` (읽을 세션 수) 또는 `CM_INJECT_MAX_TOKENS` 파라미터 조정. 또는 세션 선택 로직(최신 N개 → 관련도 기반)으로 전략 변경.

---

### 2-3. Digest 크기 비대화

| 신호 패턴 | 분류 | Confidence |
|----------|------|-----------|
| `session_digest_created` size_bytes 7일 이동 평균이 200% 이상 증가 | digest 상세화 drift | Low-Medium |
| size_bytes > 10,000 (10KB) | digest가 지나치게 상세 | Medium |

**Proposed Change:** `session-digest` 스킬의 추출 규칙(What 최대 항목 수, 상세 기준) 재검토.

---

## 3. Usage drift 룰

CM 에이전트·메모리가 실제로 어떻게 사용되는지를 분석하여 구조적 불일치를 감지한다.

### 3-1. 사문화 메모리 클러스터

| 신호 패턴 | 분류 | Confidence |
|----------|------|-----------|
| 클러스터 X가 생성 이후 10 세션 동안 `memory_query`에서 한 번도 조회되지 않음 | 사문화 cluster | High |
| 클러스터 X가 30일 이상 미조회 (decay 후에도 confidence > 0.1 유지) | 고신뢰 사문화 cluster | High |
| 전체 클러스터 중 미조회 비율 > 70% | 메모리 검색 자체가 활용 안 됨 (cm-retriever 미사용 가능성) | Medium |

**Proposed Change:**
- 미조회 cluster → confidence 즉시 decay (-0.30) + 사용자에게 제거 후보 알림
- 전체 활용률 저하 → cm-orchestrator의 검색 트리거 키워드 확장 검토

---

### 3-2. cm-retriever 검색 품질 저하

| 신호 패턴 | 분류 | Confidence |
|----------|------|-----------|
| `memory_query` results=0 비율 > 50% (최근 20 쿼리) | 검색 히트율 저하 | High |
| `memory_query` tokens_returned 이동 평균 < 100 (쿼리는 되나 정보 희박) | observations.db 빈약 | Medium |
| `memory_query` 이벤트 자체가 7 세션간 없음 | cm-retriever 미사용 | High |

**Proposed Change:**
- 히트율 저하: observations.db FTS5 토큰화 설정 재검토, 또는 `memory-search` 스킬의 fallback LIKE 전략 강화
- cm-retriever 미사용: cm-orchestrator의 검색 키워드 트리거 패턴 점검 (사용자가 다른 표현을 쓰는지 확인)

---

### 3-3. Skill 승격 회로 비활성

| 신호 패턴 | 분류 | Confidence |
|----------|------|-----------|
| `memory_promoted` 이벤트가 60일간 없고, confidence > 0.5 클러스터가 3개 이상 존재 | 승격 회로 정체 | Medium |
| cm-curator가 30 세션간 `memory_clustered` 이벤트를 발행하지 않음 | cm-curator 미실행 | High |

**Proposed Change:**
- 승격 정체: 승격 임계치(0.80) 재검토 또는 cm-curator 주기적 단독 실행 추가
- cm-curator 미실행: SessionEnd 훅 설정 확인, cm-orchestrator 팀 구성 점검

---

### 3-4. cm-compressor 미사용

| 신호 패턴 | 분류 | Confidence |
|----------|------|-----------|
| `tool_output_captured` 이벤트가 14 세션간 없음 | cm-compressor 미트리거 | Medium |
| PostToolUse 훅이 동작하지 않는 패턴 | 훅 설정 문제 | High |

**Proposed Change:** Claude Code 설정의 PostToolUse 훅 등록 상태 확인. cm-orchestrator에서 PostToolUse 라우팅 조건 (>10KB) 임계치 재검토.

---

### 3-5. Dashboard 미접근 (S6 이후)

| 신호 패턴 | 분류 | Confidence |
|----------|------|-----------|
| `/cm-harness:cm-dashboard` 커맨드 30일간 미사용 | dashboard 미활용 | Low |
| dashboard worker 프로세스 미실행 흔적 (session_start 이후 localhost:8765 응답 없음) | worker 비활성 | Medium |

**Proposed Change:** dashboard-render 스킬의 진입 방법 간소화 검토 (자동 실행 옵션), 또는 사용자 워크플로우에서 대시보드 필요성 재평가.

---

## 4. Proposed Change 매핑

CM 도메인 drift → 변경 대상 산출물 매핑. runtime-adaptation.md §6의 Cross-artifact propagation chain과 동일한 atomic 적용 원칙 적용.

| Drift | 1차 변경 대상 | Chain (부수 갱신) |
|-------|-------------|-----------------|
| Compressor 비율 악화 | `plugins/cm-harness/skills/tool-output-compress/SKILL.md` | `plugins/cm-harness/agents/cm-compressor.md` + CLAUDE.md 변경 이력 |
| Injector 토큰 비대화 | `plugins/cm-harness/agents/cm-injector.md` (파라미터) | `_baseline/cm_baseline.json` + CLAUDE.md 변경 이력 |
| Digest 비대화 | `plugins/cm-harness/skills/session-digest/SKILL.md` (추출 규칙) | CLAUDE.md 변경 이력 |
| 사문화 cluster | `_workspace/_memory/clusters/{id}.md` (제거/decay) | observations.db cluster 참조 + CLAUDE.md 변경 이력 |
| Retriever 히트율 저하 | `plugins/cm-harness/skills/memory-search/SKILL.md` (fallback 강화) | CLAUDE.md 변경 이력 |
| cm-curator 미실행 | `plugins/cm-harness/agents/cm-curator.md` + cm-orchestrator 훅 설정 | CLAUDE.md 변경 이력 |
| cm-compressor 미사용 | Claude Code settings.json (PostToolUse 훅) | cm-orchestrator 라우팅 조건 + CLAUDE.md 변경 이력 |
| Skill memory 승격 | `.claude/skills/{name}/SKILL.md` 신규 생성 (사용자 프로젝트의 `.claude/skills/`) | `_workspace/_memory/clusters/{id}.md` `promoted_path` 갱신 + observations.db `clusters.promoted_path` UPDATE + CLAUDE.md 변경 이력 + (선택) `_baseline/cm_baseline.json`에 `user_confirmed_skills` 추가 |

> **범위 외 (영구 제외):** 본 매핑은 의도적으로 `plugins/harness/skills/harness/SKILL.md`, `plugins/harness/skills/harness/references/*`, `plugins/harness/commands/harness-*.md`을 포함하지 **않는다**. 이 영역은 dharness 메타 스킬 본체이며, CM 도메인의 자동 적응(Phase 10 Adapt) 대상이 아니다. dharness 본체 변경이 필요하다고 판단되는 신호가 감지되면, Adapt를 트리거하지 말고 별도 항목 "dharness 일반화 후보"로 delta 리포트에 기록하고 사용자에게 Phase 9 (`/harness:harness-evolve`) 명시 요청을 안내한다.

### Atomic 적용 — Skill memory 승격의 경우

Skill 승격은 단일 원자적 변경이 아니라 4-5개 산출물을 동시에 갱신하는 chain이므로, 표준 Phase 10 rollback 인프라를 그대로 사용한다:

```
1. 사전 스냅샷 (cm-curator):
   _workspace/_telemetry/_rollback/{ts}/
     ├── clusters_{id}.md.bak              # 원본 클러스터 파일
     ├── observations.db.bak               # promoted_path 갱신 전 DB 스냅샷
     ├── CLAUDE.md.bak                     # 변경 이력 추가 전 CLAUDE.md
     └── manifest.json                     # 적용될 변경 chain 기술

2. Chain 적용 (위 §4 표의 "Skill memory 승격" 행 순서대로):
   a. .claude/skills/{name}/SKILL.md 생성 (신규)
   b. _workspace/_memory/clusters/{id}.md의 promoted_path 갱신
   c. observations.db UPDATE clusters SET promoted_path=? WHERE cluster_id=?
   d. CLAUDE.md 변경 이력 행 추가
   e. (선택) cm_baseline.json#user_confirmed_skills append
   f. telemetry: memory_promoted 이벤트 append

3. 검증 실패 시 (a-f 중 하나라도 실패):
   _telemetry/_rollback/{ts}/manifest.json을 읽어 역순으로 복구.
   manifest는 "각 단계가 무엇을 만들고 무엇을 수정했는가"를 기록하므로
   생성된 파일은 삭제하고 수정된 파일은 .bak에서 복원한다.

4. 성공 시:
   _telemetry/_rollback/{ts}/는 30일 후 정리 (다른 rollback 스냅샷과 동일 정책).
```

이는 `references/runtime-adaptation.md` §6의 Cross-artifact propagation chain 메커니즘과 동일하므로 별도 인프라가 필요 없다. cm-curator는 승격 시 표준 rollback API만 호출한다.

---

## 5. Delta 리포트 CM 섹션 형식

표준 delta 리포트 (`_workspace/_telemetry/_delta_{ts}.md`)에 CM 섹션을 추가한다.
기존 "Baseline Drift"와 "Usage Drift" 섹션 뒤에 다음 섹션을 append:

```markdown
## CM System Drift

**분석 범위:** 마지막 Adapt 이후 {N} 세션, CM telemetry 이벤트 {M}건

### CM Baseline Drift ({n}건)

### 🔴 1. Compressor 압축 비율 악화
- **신호:** tool_output_captured ratio 7일 평균 0.05 → 0.31 (6.2배 악화)
- **측정 기간:** 2026-04-15 ~ 2026-05-09
- **baseline 기준:** 초기 30회 평균 ratio 0.05 (_baseline/cm_baseline.json)
- **영향 도구:** WebFetch (ratio 0.41), Read (ratio 0.28), Bash (정상 0.03)
- **신뢰도:** High
- **제안:**
  - `tool-output-compress` 스킬의 WebFetch 압축 전략 보강
  - WebFetch 대상 핵심 섹션 추출 규칙 재검토

### CM Usage Drift ({n}건)

### 🟡 2. 사문화 클러스터 발견: c_a3f (35일 미조회)
- **신호:** memory_query에서 cluster_id=c_a3f 조회 0건 (지난 35 세션)
- **현재 confidence:** 0.18 (decay 적용 후)
- **클러스터 주제:** "Prisma schema 마이그레이션 패턴"
- **신뢰도:** High
- **제안:** 제거 후보 — confidence 즉시 0.05로 decay 또는 수동 삭제 확인 요청
```

---

## 6. Phase 10 연동 포인터

이 파일의 룰을 harness Phase 10 Diagnostic 레이어가 실행하려면:

1. **트리거:** `references/runtime-adaptation.md`의 §5 트리거 조건과 동일 (수동 / 주기 / 임계)
2. **분석 범위:** `_workspace/_telemetry/*.jsonl`에서 CM 이벤트 타입만 필터링
3. **baseline 비교 anchor:** `_workspace/_baseline/cm_baseline.json` (CM 전용 기준값 파일)
4. **delta 리포트:** 표준 `_delta_{ts}.md`의 "CM System Drift" 섹션에 append
5. **적용:** `references/runtime-adaptation.md` §6-7의 Adapt + 승인 UX 그대로 사용

### cm_baseline.json 초기화 (첫 실행 시)

`_workspace/_baseline/cm_baseline.json`:

```json
{
  "created_at": "<ISO8601>",
  "compressor": {
    "initial_avg_ratio": null,
    "initial_sample_count": 0,
    "ratio_alert_threshold": 0.3
  },
  "injector": {
    "initial_avg_tokens": null,
    "initial_sample_count": 0,
    "tokens_alert_threshold": 1500
  },
  "digester": {
    "initial_avg_size_bytes": null,
    "initial_sample_count": 0,
    "size_alert_threshold": 10000
  },
  "notes": "초기값은 처음 30 세션 데이터로 자동 채워진다 (cm-curator 주기 실행 시)"
}
```

초기 30 세션 경과 후 cm-curator가 자동으로 baseline 값을 채운다.
이 파일이 존재하지 않으면 Phase 10 CM Diagnostic을 건너뛰고 경고만 남긴다.
