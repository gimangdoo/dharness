---
description: "CM 메모리를 완전히 초기화 — 모든 세션·클러스터·daily_summary 삭제 (사용자 확인 필수)"
---

# /cm-harness:cm-reset

`_workspace/_memory/` 하위 데이터를 모두 삭제하고 빈 상태로 재구축한다.
**파괴적 작업** — 반드시 사용자 명시 확인 후 실행.

## 컨텍스트

- **인자:** 없음
- **입력:** 없음
- **출력:** 삭제 영향 보고

## 선조건 검증

다음을 사용자에게 출력하고 명시적 "yes" 응답을 받기 전까지 진행 금지:

```
⚠️  CM 메모리 전체 삭제

삭제 대상:
- _workspace/_memory/                (sessions, observations.db, clusters, daily_summaries, .current_session)
- _workspace/_tool_outputs/          (raw 도구 출력 보존본)

보존 대상:
- _workspace/_baseline/              (project/intent/cm_baseline)
- _workspace/_telemetry/             (이력)
- _workspace/references/             (진단 룰)

⚠️ 활성 세션은 보존되지 않는다 — 현재 세션의 raw.jsonl도 함께 삭제된다.
   필요하면 SessionEnd 후에 실행하라.

진행하려면 "yes"를 입력하세요.
```

## 실행 절차

`plugins/cm-harness/hooks/cm_commands.py reset --confirm`이 다음을 수행:

1. `_workspace/_memory/` 하위 통째로 삭제 (현재 활성 세션 포함)
2. `_workspace/_tool_outputs/` 하위 삭제
3. `/cm-harness:cm-init` 로직 호출하여 빈 디렉토리 + DB 재생성

## 범위 외 / 후속 명령

- baseline 재생성은 별도 — `/harness:harness-baseline`
- 부분 정리 (사문화 클러스터만) — `/cm-harness:cm-curate`
