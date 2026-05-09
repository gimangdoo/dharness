---
description: "CM 메모리를 완전히 초기화 — 모든 세션·클러스터·daily_summary 삭제 (사용자 확인 필수)"
---

# /cm-reset

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
- _workspace/_memory/sessions/        (X개 세션)
- _workspace/_memory/observations/    (observations.db, X행)
- _workspace/_memory/clusters/        (X개 클러스터)
- _workspace/_memory/daily_summaries/ (X일 요약)
- _workspace/_tool_outputs/           (X개 raw 파일)

보존 대상:
- _workspace/_baseline/               (project/intent/cm_baseline)
- _workspace/_telemetry/              (이력)
- _workspace/references/              (진단 룰)
- _workspace/_memory/sessions/{현재 활성 세션}/  (있을 경우 보존)

진행하려면 "yes"를 입력하세요.
```

## 실행 절차

`_workspace/_hooks/cm_commands.py reset --confirm`이 다음을 수행:

1. 활성 세션 ID(`CM_SESSION_ID`) 백업
2. `_workspace/_memory/` 하위 통째로 삭제
3. `_workspace/_tool_outputs/` 하위 삭제
4. `/cm-init` 로직 호출하여 빈 디렉토리 + DB 재생성
5. 활성 세션 디렉토리 복원

## 범위 외 / 후속 명령

- baseline 재생성은 별도 — `/harness-baseline`
- 부분 정리 (사문화 클러스터만) — `/cm-curate`
