---
name: session-capture
description: |
  세션 ID를 발급하고 세션 동안의 raw 이벤트(사용자 turn, 도구 호출 결과)를
  _workspace/_memory/sessions/{id}/raw.jsonl에 누적 append한다. SessionEnd 직전에
  raw.jsonl을 transcript.md로 평탄화한다. SessionStart 훅 시점의 디렉토리 부트스트랩과
  세션 ID 부여 책임을 가지며, cm-digester / cm-injector / cm-compressor의 입력을 만든다.
  "세션 캡처", "session id 발급", "transcript 생성", "raw.jsonl" 요청 시 이 스킬을 참조하라.
---

# session-capture

CM 시스템이 작동하기 위한 **원본 데이터 캡처** 책임을 가진다. 다른 모든 cm 에이전트는
이 스킬이 만든 산출물(`session_id`, `raw.jsonl`, `transcript.md`)을 입력으로 사용한다.

## 책임 범위

1. **세션 ID 발급** — SessionStart 시 6자 hex (UUIDv4의 첫 6자) 발급
2. **디렉토리 부트스트랩** — `_workspace/_memory/sessions/{session_id}/` 생성
3. **raw.jsonl append** — 사용자 turn / 도구 호출 / 에이전트 응답 이벤트를 한 줄씩 누적
4. **transcript.md 생성** — SessionEnd 직전 raw.jsonl을 평탄화하여 사람이 읽을 수 있는 형태로 저장
5. **세션 메타 upsert** — observations.db `sessions` 테이블에 row 삽입/갱신

## 세션 ID 발급 규칙

```python
import uuid
session_id = uuid.uuid4().hex[:6]   # 예: "a3f9b2"
```

- 1차 충돌 시 8자 hex로 재발급 (sessions 테이블 PK INSERT OR IGNORE rowcount=0 감지)
- 한 Claude Code 프로세스 라이프사이클 동안 동일 ID 유지
- **ID 전달 메커니즘:** `_workspace/_memory/.current_session` 파일에 평문 기록. SessionStart hook이 쓰고, PostToolUse/SessionEnd hook이 읽는다. SessionEnd 종료 시 파일을 제거한다. (Claude Code hook은 별도 프로세스이므로 환경 변수로는 전달되지 않는다.)
- **참조 방식:**
  - **Python 스크립트** (`plugins/cm-harness/hooks/*.py`): `from _schema import read_session_id` 후 `read_session_id()` 호출.
  - **cm-* 에이전트** (Markdown 정의이므로 모듈 import 불가): `Read` 도구로 `_workspace/_memory/.current_session` 파일을 직접 읽거나, `Bash`로 `python -c "from _schema import read_session_id; print(read_session_id())"` 호출. 통상 cm-orchestrator가 prompt 파라미터로 session_id를 직접 전달하므로 에이전트가 직접 읽을 일은 드물다.

## 디렉토리 부트스트랩 (SessionStart 시점)

```
_workspace/_memory/sessions/{session_id}/
  raw.jsonl                  # 빈 파일로 생성
  (digest.md는 SessionEnd에 cm-digester가 생성)
  (transcript.md는 SessionEnd에 본 스킬이 생성)
```

`_workspace/_memory/observations/observations.db`가 없으면 `session-digest` 스킬의
스키마로 초기화한다 (4개 테이블 + FTS5 한 번에).

## raw.jsonl 이벤트 형식

세션 동안 발생하는 모든 이벤트를 한 줄 JSON으로 append한다.

```jsonl
{"ts":"2026-05-10T09:01:23Z","kind":"user_message","content":"..."}
{"ts":"2026-05-10T09:01:45Z","kind":"tool_call","tool":"Read","input_summary":"...","output_size":1240}
{"ts":"2026-05-10T09:02:10Z","kind":"assistant_message","content":"..."}
{"ts":"2026-05-10T09:02:55Z","kind":"tool_result","tool":"Bash","exit_code":0,"output_size":340}
```

**필드 규칙:**
- `kind` ∈ `user_message | assistant_message | tool_call | tool_result | hook_event`
- 도구 결과의 raw 출력은 `_workspace/_tool_outputs/`에 별도 저장하므로 여기엔 `output_size`만 기록
- 컨텍스트 비대화 방지: assistant_message의 `content`는 4KB 초과 시 `content_truncated: true` + 앞 4KB만 저장

## transcript.md 생성 (SessionEnd 직전)

raw.jsonl을 사람이 읽을 수 있는 markdown으로 평탄화한다.

```markdown
# Session {session_id} Transcript

**Date:** 2026-05-10
**Duration:** 47 min
**Tools:** Read, Bash, Edit

## Turn 1 — 09:01:23
**User:** ...

**Assistant:** ...

**Tool calls:**
- Read(file_path=...) → 1240 bytes
- Bash(...) → exit 0, 340 bytes

## Turn 2 — 09:08:11
...
```

transcript.md가 생성되면 cm-digester는 이를 1순위 입력으로 사용한다 (raw.jsonl보다 우선).

## sessions 테이블 upsert

SessionStart 시점:
```sql
INSERT INTO sessions (session_id, date, started_at, project)
VALUES (?, ?, ?, ?)
ON CONFLICT(session_id) DO NOTHING;
```

SessionEnd 시점:
```sql
UPDATE sessions
SET ended_at = ?, duration_min = ?, tools_used = ?, digest_path = ?
WHERE session_id = ?;
```

`digest_path`는 cm-digester가 digest.md를 생성한 후 별도로 UPDATE한다.

## 호출 시점 매트릭스

| 시점 | 호출 주체 | 동작 |
|------|----------|------|
| SessionStart | hook 스크립트 | session_id 발급 + 디렉토리 부트스트랩 + sessions row INSERT |
| 매 turn / tool 호출 | hook 스크립트 (PostToolUse) | raw.jsonl append |
| SessionEnd | hook 스크립트 → cm-orchestrator | transcript.md 생성 + sessions UPDATE → cm-digester 호출 |

본 스킬은 LLM 추론이 필요 없는 결정적 작업이므로 `plugins/cm-harness/hooks/` 하위 Python
스크립트로 구현되며, 에이전트는 별도로 두지 않는다.

## 에러 핸들링

| 상황 | 처리 |
|------|------|
| `_workspace/_memory/sessions/` 생성 실패 | telemetry에 오류 기록, 캡처 스킵 (세션은 정상 진행) |
| raw.jsonl append I/O 오류 | 메모리 버퍼에 임시 누적, 다음 append 시 flush |
| transcript.md 생성 실패 | raw.jsonl만 남기고 cm-digester가 raw.jsonl을 직접 사용 |

## Telemetry

```jsonl
{"ts":"<ISO8601>","type":"session_capture_init","session_id":"<id>","project":"<dir>"}
{"ts":"<ISO8601>","type":"session_capture_finalize","session_id":"<id>","raw_lines":<n>,"transcript_size":<bytes>}
```
