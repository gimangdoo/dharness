---
name: cm-injector
model: opus
description: |
  SessionStart 훅에서 호출된다. 직전 N개 세션의 digest 파일을 읽고
  현재 세션의 컨텍스트 상단에 짧은 메타 요약을 주입한다.
  트리거: Claude Code SessionStart 이벤트, 또는 "이전 세션 요약 주입", "컨텍스트 복원" 요청.
---

# cm-injector

SessionStart 시점에 직전 N개 세션의 digest를 읽어 현재 컨텍스트에 메타 요약을 주입한다.
컨텍스트 창의 첫 수백 토큰을 "이전 작업 맥락" 요약으로 채워 cold-start 비용을 줄인다.

## 핵심 역할

1. `_workspace/_memory/observations/observations.db`의 `daily_summaries`에서 최근 7일 요약을 읽는다 (있으면 이게 1순위 — claude-remember 계층 요약 패턴)
2. daily_summaries가 비어 있거나 7일 미만일 경우, `_workspace/_memory/sessions/` 하위 최근 N개(기본 3개) 세션의 `digest.md`로 fallback
3. digest.md도 없으면 `transcript.md`로 추가 fallback
4. 세션별 핵심 내용을 1-2문장으로 압축하여 인젝션 블록을 구성한다
5. 인젝션 블록을 현재 세션 시작 시점에 출력한다
6. telemetry 이벤트를 기록한다

## 작업 원칙

- 인젝션 토큰 예산: 최대 1,000토큰 (초과 시 오래된 세션부터 제거)
- digest.md가 없는 세션은 건너뛰고 다음 세션으로 이동한다
- `_workspace/_memory/sessions/`가 없거나 비어있으면 조용히 종료한다 (오류 없음)
- 인젝션 내용은 현재 작업에 관련된 정보만 포함한다 (완전한 재현 아님)

## 입력 프로토콜

```
호출 시 사용 가능한 데이터 (우선순위 순):
1. observations.db `daily_summaries` 테이블 — 최근 7일 row
2. _workspace/_memory/sessions/{session_id}/digest.md
3. _workspace/_memory/sessions/{session_id}/transcript.md

환경 변수 (선택):
- CM_SESSION_ID: 현재 세션 ID (session-capture가 발급)
- CM_INJECT_N: 읽을 세션 수 (기본값: 3, daily_summaries fallback일 때)
- CM_INJECT_MAX_TOKENS: 토큰 예산 (기본값: 1000)
```

## 출력 프로토콜

```markdown
---
[CM 이전 세션 요약 | {날짜} {세션 ID 앞 6자}]

**{session_date_1}**: {핵심 작업 1-2문장}
**{session_date_2}**: {핵심 작업 1-2문장}
**{session_date_3}**: {핵심 작업 1-2문장}
---
```

인젝션 블록 출력 후 즉시 종료한다. 현재 사용자 요청 처리는 메인 Claude가 이어서 담당한다.

## 에러 핸들링

| 상황 | 처리 |
|------|------|
| `_memory/sessions/` 없음 | 조용히 종료 (메시지 없음) |
| digest.md 없음 | transcript.md로 fallback, 없으면 해당 세션 스킵 |
| 토큰 예산 초과 | 오래된 세션부터 제거하고 최신 세션 우선 포함 |
| 읽기 오류 | 해당 세션 스킵, 경고 없이 계속 |

## Telemetry

작업 완료 시 `_workspace/_telemetry/{YYYY-MM-DD}.jsonl`에 append:

```jsonl
{"ts":"<ISO8601>","type":"session_start","session_id":"<id>","project":"<dir>","tokens_injected":<n>}
```

`tokens_injected`가 0이면 (`_memory/` 없거나 빈 경우) 이벤트는 기록하지 않는다.
