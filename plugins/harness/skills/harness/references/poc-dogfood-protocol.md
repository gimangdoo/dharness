---
name: poc-dogfood-protocol
description: P7-2 옵션 B 영문 POC dogfood — 실 세션 토큰·품질·시간 측정 protocol
---

# P7-2 옵션 B Dogfood Protocol

EN POC (`*.en.md`) 4건의 실제 효과를 정량 측정하는 사용자 측 protocol. 정적 token cost는
`plugins/harness/scripts/poc/measure_dogfood.py`가 deterministic 측정 — 본 문서는 실 세션
응답 품질/시간/오류 측정 절차를 박제한다.

## 측정 목표

| 차원 | 측정 방법 | 단위 |
|------|----------|------|
| 정적 token cost | `measure_dogfood.py` cl100k_base | tokens |
| 세션 토큰 누계 | `_workspace/_telemetry/<date>.jsonl` `tool_output_captured.raw_size` 합 | bytes (→ token 환산) |
| 응답 품질 | 사용자 평가 (5-Likert: 1=오답/5=완벽) | score |
| 도구 호출 횟수 | telemetry `tool_*` 이벤트 count | int |
| 세션 시간 | SessionStart→SessionEnd 차 | seconds |
| 실패율 | `agent_failure` event / `agent_invocation` event | ratio |

## 옵션 B-a: KO baseline 측정

1. `.claude/agents/*.md` + `plugins/harness/skills/harness/SKILL.md`가 KO references만 참조하는 상태 확인 (default)
2. 신규 세션 시작 → `/cm-status`로 session_id 박제
3. fixture task 실행 (예: "harness-add-agent로 reviewer 에이전트 1개 생성")
4. SessionEnd 후 telemetry 측정값 jsonl 1행에 박제

## 옵션 B-b: EN swap 측정

1. SKILL.md/references 본문의 `references/<stem>.md` 링크를 `references/<stem>.en.md`로 swap (4건)
   - 또는 `<stem>.md`를 `<stem>.ko.md`로 백업 + `<stem>.en.md`를 `<stem>.md`로 복사
2. 신규 세션 시작 → 동일 fixture task 실행
3. 측정값 jsonl 박제
4. 측정 후 원본 복원 (swap 역행)

## 옵션 B-c: 폐기

- B-a/b 둘 다 사용자 시간 비용이 회수 가치 초과 시
- 정적 token cost (`measure_dogfood.py` 결과)만 doctrine evidence로 채택
- README/SKILL.md에 "EN POC는 정적 token 56% 감소까지 검증, runtime dogfood는 미실시" 박제

## 결과 박제 위치

| 산출물 | 경로 |
|--------|------|
| 정적 측정 누적 | `_workspace/_telemetry/poc_dogfood_static.jsonl` |
| 세션 dogfood 비교 | `_workspace/_telemetry/poc_dogfood_runtime.jsonl` (사용자 수기 박제) |
| 최종 결정 doctrine | `plugins/harness/skills/harness/SKILL.md` P7-2 옵션 B 박스 갱신 |

## 결정 임계

- ratio < 0.60 + 품질 ≥ 4.0 → EN POC 채택 (KO refs `.ko.md`로 백업, EN을 정본)
- ratio < 0.60 + 품질 < 4.0 → 품질 저하 → KO 정본 유지 + EN POC 폐기 (옵션 B-c)
- ratio ≥ 0.60 → 절감 효과 미미 → KO 정본 유지

## 측정 명령 요약

```bash
# 정적 cost (지금 즉시 가능)
py plugins/harness/scripts/poc/measure_dogfood.py
py plugins/harness/scripts/poc/measure_dogfood.py --strip-poc-note

# 세션 telemetry (실 세션 후)
py .claude/hooks/cm_commands.py sessions  # session_id 확보
# _workspace/_telemetry/<date>.jsonl에서 raw_size 합산, agent_failure 카운트
```
