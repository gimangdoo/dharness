---
name: cm-orchestrator
description: |
  Context Manager의 라이프사이클 이벤트 라우터. Claude Code의 SessionStart, PostToolUse,
  SessionEnd 훅을 수신하여 적절한 CM 에이전트로 라우팅한다. 사용자가 메모리를 검색하거나
  /cm-* 슬래시 커맨드를 실행할 때도 진입점이 된다. 또한 "cm 상태", "cm 대시보드",
  "cm 초기화", "메모리 정리", "세션 기록" 요청 시 이 스킬을 사용하라.
  재실행/업데이트/부분 실행 포함: "cm 다시 실행", "cm 설정 변경" 시에도 사용.
---

# cm-orchestrator

Context Manager 시스템의 진입점이자 이벤트 라우터.
어떤 이벤트인지 판별하고 적절한 에이전트 또는 스크립트로 디스패치한다.

## 컨텍스트 확인 (재실행 시)

```
1. _workspace/_memory/ 존재 + 세션 데이터 있음 → 후속 실행 (기존 데이터 보존)
2. _workspace/_memory/ 존재 + 비어있음 → 초기화 재실행
3. _workspace/ 없음 → 첫 실행 (디렉토리 구조 생성)
```

## 이벤트 라우팅

| 이벤트 | 핸들러 | 실행 모드 |
|--------|--------|-----------|
| SessionStart 훅 | cm-injector | 서브 에이전트 |
| PostToolUse 훅 (출력 >10KB) | cm-compressor | 서브 에이전트 |
| PostToolUse 훅 (출력 ≤10KB) | 패스스루 (처리 없음) | — |
| SessionEnd 훅 | cm-digester + cm-curator | 팀 (TeamCreate) |
| 사용자 메모리 검색 키워드 | cm-retriever | 서브 에이전트 |
| /cm-* 슬래시 커맨드 | 스크립트 (결정적, LLM 없음) | — |
| 주기적 클러스터링 | cm-curator 단독 | 서브 에이전트 |

## Phase 1: 이벤트 판별

진입 시 다음 순서로 이벤트 유형을 판별한다:

1. Hook 이벤트 여부 확인 (SessionStart / PostToolUse / SessionEnd)
2. /cm-* 커맨드 패턴 여부
3. 메모리 검색 키워드 패턴:
   - "기억", "이전 세션", "과거에", "지난번에", "~했던 거", "메모리 검색"
4. 관리 명령 패턴:
   - "cm 상태", "cm 대시보드", "cm 초기화"

판별 실패 시: 사용자에게 "어떤 CM 기능을 사용하시겠습니까?" 안내.

## Phase 2: 디스패치

### SessionStart → cm-injector

```
Agent(
  description="cm-injector: 직전 세션 digest 주입",
  subagent_type="cm-injector",
  model="opus"
)
```

### PostToolUse → cm-compressor (>10KB)

```
Agent(
  description="cm-compressor: 대용량 출력 압축",
  subagent_type="cm-compressor",
  model="opus",
  prompt="도구: {tool_name}, 출력 크기: {size}bytes, 세션: {session_id}"
)
```

### SessionEnd → cm-digester + cm-curator 팀

**실행 모드:** 에이전트 팀 (TeamCreate)

```
팀 구성:
- cm-digester: digest 생성 담당 (먼저 실행)
- cm-curator: digest_complete 메시지 수신 후 클러스터링 수행

팀 통신:
- cm-digester → SendMessage(to: cm-curator) → digest_complete 메시지
- cm-curator → 클러스터링 완료 후 팀 종료
```

### 메모리 검색 → cm-retriever

```
Agent(
  description="cm-retriever: 메모리 검색",
  subagent_type="cm-retriever",
  model="opus",
  prompt="쿼리: {user_query}"
)
```

### /cm-* 커맨드 → 스크립트 (결정적)

| 커맨드 | 동작 |
|--------|------|
| /cm-status | `_workspace/_memory/` 통계 출력 |
| /cm-sessions | 세션 목록 + digest 여부 출력 |
| /cm-clusters | 클러스터 목록 + confidence 출력 |
| /cm-dashboard | localhost dashboard URL 출력 |
| /cm-init | `_workspace/_memory/` 디렉토리 구조 초기화 |
| /cm-reset | 확인 후 `_workspace/_memory/` 초기화 |

## Phase 3: Telemetry

모든 핸들러 완료 후 `_workspace/_telemetry/{YYYY-MM-DD}.jsonl`에 이벤트 append.
각 에이전트가 자체 telemetry를 기록하므로 오케스트레이터는 라우팅 이벤트만 기록:

```jsonl
{"ts":"<ISO8601>","type":"harness_invocation","event":"<event_type>","handler":"<handler_name>"}
```

## Phase 10 Runtime Adaptation 연동

Phase 10 telemetry 카운터 확인:
- 마지막 `"type":"adapt"` 이후 `"type":"harness_invocation"` 수가 10회 이상이면:
  → "CM 하네스가 {N}회 실행되었습니다. `/harness-adapt`로 drift 점검을 권장합니다."

**CM 전용 진단 룰:** `_workspace/references/cm-diagnostic-rules.md`
- harness Phase 10 Diagnostic 실행 시 이 파일의 룰을 함께 적용한다
- CM baseline 기준값: `_workspace/_baseline/cm_baseline.json` (30 세션 누적 후 채워짐)
- CM drift delta: 표준 `_delta_{ts}.md`의 "CM System Drift" 섹션에 append

## 에러 핸들링

| 상황 | 처리 |
|------|------|
| 이벤트 판별 실패 | 사용자에게 이벤트 유형 확인 요청 |
| 에이전트 실패 | telemetry에 실패 기록, 보고서에 누락 명시 |
| 팀 통신 실패 | 1회 재시도 후 각자 독립 실행으로 fallback |

## 테스트 시나리오

**정상 — SessionEnd 팀 흐름:**
1. SessionEnd 이벤트 수신
2. cm-digester + cm-curator 팀 생성
3. cm-digester: digest.md 생성 + observation_ids 발신
4. cm-curator: 수신 + 클러스터링 실행
5. telemetry 이벤트 2개 기록 확인

**에러 — cm-digester 실패:**
1. SessionEnd 수신
2. cm-digester 실행 중 transcript 없음 오류
3. 현재 세션 메시지로 fallback
4. digest 생성 완료
5. telemetry에 `"fallback":"transcript_missing"` 기록
