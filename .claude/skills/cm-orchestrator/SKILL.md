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

아래 표에서 "훅 자율"로 표시된 행은 본 스킬이 dispatch에 관여하지 않는다 — Python 훅(`_workspace/_hooks/*.py`)이 별도 프로세스로 자체 실행되어 결정적 작업을 수행하고, 본 스킬은 훅이 끝난 뒤 LLM 작업이 필요한 후속 단계만 라우팅한다.

| 이벤트 | 핸들러 | 본 스킬 관여 | 실행 모드 |
|--------|--------|-------------|-----------|
| SessionStart 훅 (캡처) | `session_start.py` (session_id 발급·DB 부트스트랩·telemetry append) | 훅 자율 | 결정적 (LLM 없음) |
| SessionStart 훅 (인젝션) | cm-injector | dispatch | 서브 에이전트 (Task) |
| PostToolUse 훅 (캡처 + 10KB 분기 결정) | `post_tool_use.py` (raw.jsonl append + ≤10KB 패스스루 + >10KB raw 보존·`tool_output_captured` 이벤트 emit) | 훅 자율 | 결정적 |
| PostToolUse 훅 (출력 >10KB의 압축 단계) | cm-compressor | dispatch | 서브 에이전트 (Task) |
| SessionEnd 훅 (transcript+sessions UPDATE) | `session_end.py` (raw.jsonl 평탄화·sessions UPDATE·`session_capture_finalize` emit) | 훅 자율 | 결정적 |
| SessionEnd 훅 후속 (digest+curation) | cm-digester → cm-curator (순차) | dispatch | 서브 에이전트 2회 (Task) |
| 사용자 메모리 검색 키워드 | cm-retriever | dispatch | 서브 에이전트 |
| /cm-* 슬래시 커맨드 | 스크립트 또는 에이전트 (커맨드별) | dispatch (LLM 커맨드만) | — |
| /cm-curate 또는 자동 N=10 임계 | cm-curator 단독 | dispatch | 서브 에이전트 |

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

각 라우트는 **Task 도구**로 서브 에이전트를 호출한다 (`subagent_type=<cm-*>`, `model="opus"`). hook 스크립트는 결정적 작업(파일 생성·DB upsert·텔레메트리 기록)만 수행하고 LLM 작업은 본 스킬이 Task 호출로 위임한다.

### SessionStart → cm-injector

조건: `_workspace/_hooks/session_start.py`가 SessionStart hook으로 발동되어 `additionalContext`에 `[CM] session_id=...`를 주입한 직후, Claude가 본 스킬에 진입하면 cm-injector를 호출:

```
Task(
  subagent_type="cm-injector",
  description="cm-injector: 직전 세션 daily_summary 주입",
  prompt="현재 세션 시작 시점의 컨텍스트 인젝션을 수행하라. memory-curate의 daily_summaries 1순위, 없으면 직전 세션 digest fallback."
)
```

### PostToolUse → cm-compressor (>10KB)

`post_tool_use.py`가 `_workspace/_telemetry/{date}.jsonl`에 `tool_output_captured` 이벤트를 적은 후, Claude가 raw 출력을 직접 컨텍스트에 받는 대신 본 스킬을 통해 cm-compressor를 호출:

```
Task(
  subagent_type="cm-compressor",
  description="cm-compressor: 대용량 출력 압축",
  prompt="raw_path={raw_path}, tool={tool_name}, raw_size={size}, session_id={session_id} — tool-output-compress 스킬에 따라 압축 요약을 생성하라."
)
```

### SessionEnd → cm-digester → cm-curator (순차)

**실행 모드:** hook 스크립트가 시퀀스를 보장하는 두 번의 Task 호출. Claude Code는 in-process 메시지 버스를 제공하지 않으므로, `digest_complete` 페이로드는 cm-digester의 반환값을 본 스킬이 받아 cm-curator의 prompt에 포함시키는 방식으로 전달한다.

```
1) Task(subagent_type="cm-digester", ...) → 반환: {session_id, observation_ids, digest_path, ...}
2) Task(subagent_type="cm-curator",
        prompt="trigger=digest_complete, payload={1번 반환 JSON}")
```

cm-digester가 transcript missing 등으로 실패하면 cm-curator는 호출하지 않고 telemetry에 `"fallback":"digester_failed"`로 기록한다.

### 메모리 검색 → cm-retriever

```
Task(
  subagent_type="cm-retriever",
  description="cm-retriever: 메모리 검색",
  prompt="query={user_query} — memory-search 스킬의 3-tool progressive disclosure를 따르라."
)
```

### /cm-* 커맨드

| 커맨드 | 동작 | 모드 |
|--------|------|------|
| /cm-status | `_workspace/_memory/` 통계 + DB 행 수 출력 | 결정적 |
| /cm-sessions | 최근 세션 목록 + digest 여부 출력 | 결정적 |
| /cm-clusters | 클러스터 목록 + confidence 출력 | 결정적 |
| /cm-dashboard | localhost worker 상태 + URL 출력 | 결정적 |
| /cm-init | `_workspace/_memory/` 디렉토리 + observations.db 초기화 | 결정적 |
| /cm-reset | 확인 후 `_workspace/_memory/` 초기화 | 결정적 |
| /cm-curate | cm-curator 단독 실행 (decay + daily_summary + 승격 후보 스캔) | 서브 에이전트 (Task 도구) |

각 커맨드 정의는 `commands/cm-*.md`에 있다. 결정적 커맨드 6종(status/sessions/clusters/dashboard/init/reset)은 `_workspace/_hooks/cm_commands.py` 스크립트가 처리한다. `/cm-curate`는 LLM 작업이므로 `commands/cm-curate.md`가 cm-curator 에이전트를 Task 도구로 직접 호출한다 (cm_commands.py에 핸들러 없음).

## Phase 3: Telemetry

각 에이전트가 자체 telemetry(`session_start`, `tool_output_captured`, `session_digest_created`, `memory_*`, `memory_query`)를 기록한다.

`harness_invocation` 이벤트는 **`session_start.py` hook이 SessionStart 시점에 1회 발행**한다. 이는 Phase 10 자동 알림(마지막 `adapt` 이후 10회 누적 시 `/harness-adapt` 권장)의 카운터 입력이다. 이 외 시점에는 본 스킬이 추가로 발행하지 않는다 (이중 카운트 방지).

```jsonl
{"ts":"<ISO8601>","type":"harness_invocation","event":"SessionStart","handler":"session_start.py","session_id":"<id>"}
```

## Phase 10 Runtime Adaptation 연동

Phase 10 telemetry 카운터 확인:
- 마지막 Adapt 시각(= `_workspace/_telemetry/_delta_*.md` 또는 `_workspace/_telemetry/_rollback/{ts}/` 중 가장 최근 mtime,
  둘 다 없으면 telemetry 첫 이벤트의 ts) 이후 `"type":"harness_invocation"` 수가 10회 이상이면:
  → "CM 하네스가 {N}회 실행되었습니다. `/harness-adapt`로 drift 점검을 권장합니다."

이 mtime-based anchor는 별도의 `"type":"adapt"` 이벤트 발행 없이 작동하도록 설계되었다 — `/harness-adapt`는 이미 delta 리포트와 rollback 스냅샷을 만드므로, 그 산출물의 mtime이 자연스러운 anchor 역할을 한다.

**CM 전용 진단 룰:** `_workspace/references/cm-diagnostic-rules.md`
- harness Phase 10 Diagnostic 실행 시 이 파일의 룰을 함께 적용한다
- CM baseline 기준값: `_workspace/_baseline/cm_baseline.json` (30 세션 누적 후 채워짐)
- CM drift delta: 표준 `_delta_{ts}.md`의 "CM System Drift" 섹션에 append

### CM 적응의 영구 범위 한정 (dharness 본체 보호)

CM drift 적응은 **다음 경로로만 영향이 한정된다.** chain 정의·rollback manifest·승격 어떤 단계에서도 dharness 본체를 변경 대상에 포함시키지 않는다:

**적응 가능 대상 (CM 도메인):**
- `.claude/agents/cm-*.md`
- `.claude/skills/cm-orchestrator/`, `session-capture/`, `session-digest/`, `tool-output-compress/`, `memory-curate/`, `memory-search/`, `dashboard-render/`
- `.claude/skills/{승격 신규}/SKILL.md` (memory-curate 승격 산출물)
- `_workspace/_memory/`, `_workspace/_baseline/cm_baseline.json`, `_workspace/_tool_outputs/`
- `_workspace/references/cm-diagnostic-rules.md`
- `CLAUDE.md` (변경 이력 행 추가만)

**영구 제외 대상 (dharness 메타 스킬 본체):**
- `skills/harness/SKILL.md`
- `skills/harness/references/*`
- `commands/harness-*.md`
- `skills/README.md`

dharness 본체에 대한 일반화 가치가 있는 신호가 발견되면, Adapt chain에 포함시키지 말고 delta 리포트의 별도 섹션 "dharness 일반화 후보"로 기록한 뒤 사용자에게 `/harness-evolve <피드백>`(Phase 9) 명시 요청을 안내한다.

## 에러 핸들링

| 상황 | 처리 |
|------|------|
| 이벤트 판별 실패 | 사용자에게 이벤트 유형 확인 요청 |
| 에이전트 실패 | telemetry에 실패 기록, 보고서에 누락 명시 |
| cm-digester 실패 → cm-curator 의존 끊김 | cm-curator는 호출하지 않고 다음 SessionEnd로 이월, telemetry에 `"fallback":"digester_failed"` 기록 |

## 테스트 시나리오

**정상 — SessionEnd 순차 흐름:**
1. SessionEnd hook(`session_end.py`)이 transcript.md 생성 + sessions UPDATE + telemetry append
2. 본 스킬이 cm-digester를 Task 도구로 호출 → digest.md 생성 + observation_ids 반환
3. 본 스킬이 cm-digester 반환값을 `payload=...`로 cm-curator prompt에 포함시켜 Task 호출
4. cm-curator: 클러스터링 + daily_summary upsert + (조건 충족 시) 승격 후보 알림
5. telemetry: `session_capture_finalize` + `session_digest_created` + `memory_clustered` 이벤트 기록 확인

**에러 — cm-digester 실패:**
1. SessionEnd hook 정상 종료 (transcript.md 생성됨)
2. cm-digester 호출 시 transcript missing/parsing 오류
3. cm-digester가 현재 세션 메시지로 fallback 시도
4. fallback도 실패 시: cm-curator 호출 스킵, telemetry에 `"fallback":"digester_failed"` 기록
5. 다음 SessionEnd에서 누락 세션 포함 재시도 (cm-curator 자동 N=10 임계 도달 시)
