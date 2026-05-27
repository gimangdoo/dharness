---
description: "Phase 10 adapt 권장 alert 카운터 reset — `_last_adapt` 파일 mtime 갱신"
---

# /cm-reset-adapt-counter

Phase 10 자동 adapt 권장 알림 누적을 0에서 다시 시작한다. `_workspace/_telemetry/_last_adapt`
파일 mtime을 현재 시각으로 박제 — 이후 SessionStart의 `count_events_since_last_adapt()`가
이 시점 이후의 `harness_invocation`/`agent_invocation`/`agent_failure`만 카운트한다.

## 컨텍스트

- **인자:** 없음
- **입력:** 없음
- **출력:** 새 mtime 박제 보고

## 실행 절차

`py .claude/hooks/cm_commands.py reset-adapt-counter`가 다음을 수행:

1. `touch_last_adapt()` 호출 — `_last_adapt` 파일 mtime을 현재 epoch로 갱신 (없으면 생성)
2. 갱신된 mtime을 stdout에 표시
3. 다음 SessionStart부터 alert 카운터가 새로 누적됨을 안내

## 사용 시점

- `/harness:harness-adapt`를 외부 실행 후 카운터를 수동 reset할 때
- 임계값 도달 alert가 떴지만 적용 의지 없이 dismiss하고 누적을 끊을 때
- (PO5 (2026-05-27) 이전) manual shell touch doctrine — 폐기됨

## 범위 외

- 임계값 자체 조정은 `plugins/harness/skills/harness/references/runtime-adaptation.md` 참조
- 알림 끄기(suppress)는 미지원 — reset만 노출
