---
name: uplift-protocol
description: Q2 workflow uplift baseline — no-harness vs harness 세션 정량 비교 protocol
---

# Q2 Workflow Uplift Baseline Protocol

dharness harness 적용이 작업 품질·효율에 미치는 효과를 정량 측정하는 protocol.
`plugins/harness/scripts/uplift/measure_session.py`가 deterministic 세션 단위 지표를
집계 — 본 문서는 baseline vs harness 세션 페어링 절차와 결정 게이트 박제.

## 측정 지표 (세션 단위)

| 지표 | 정의 | 출처 event |
|------|------|-----------|
| `tool_invocations` | 도구 호출 횟수 (capture 트리거된 것만) | `tool_output_captured` count |
| `total_raw_size_bytes` | 도구 출력 총 byte 합 | `tool_output_captured.raw_size` 합 |
| `agent_invocations` | sub-agent 호출 횟수 | `agent_invocation` count |
| `agent_failures` | sub-agent 실패 횟수 | `agent_failure` count |
| `failure_ratio` | 실패율 (agent 기준) | `agent_failures / agent_invocations` |
| `duration_seconds` | 세션 길이 | `session_capture_finalize.ts - session_capture_init.ts` |

## 측정 protocol

### 옵션 A: 페어링 측정 (권장)

1. **Fixture task 선정** — 재현 가능한 단일 task (예: "Python flask 앱에 healthcheck endpoint 추가")
2. **Baseline 세션 (no-harness):**
   - harness skill 비활성 환경에서 새 세션 시작
   - fixture task 수행
   - `/cm-sessions`로 `<sid_a>` 확보
   - `py plugins/harness/scripts/uplift/measure_session.py --session-id <sid_a> --label baseline`
3. **Harness 세션:**
   - harness skill 활성 환경에서 새 세션 시작 (`/harness:harness-new` 후 생성된 팀 사용)
   - 동일 fixture task 수행
   - `<sid_b>` 확보 → `--label harness`로 측정 적재
4. **비교:** `_workspace/_telemetry/uplift_sessions.jsonl`의 두 label 행을 수기 비교

### 옵션 B: 누적 분포 측정

- 위 페어링을 fixture 3~5건 × baseline/harness 각 1회씩 누적
- `uplift_sessions.jsonl`에서 `label`별 평균·중앙값 추출
- 통계적 유의성은 표본 부족 — 정성 관찰만

## 결정 게이트

| 조건 | 판정 |
|------|------|
| harness `tool_invocations` ≤ baseline AND harness `failure_ratio` ≤ baseline | ✅ uplift 입증 |
| harness `tool_invocations` > baseline + harness `failure_ratio` ≤ baseline × 0.5 | ✅ uplift (도구↑ 허용 — 실패율 절반 이하 회수) |
| harness `failure_ratio` > baseline OR `duration` > baseline × 1.5 | ❌ regression — harness 수정 필요 |
| baseline 측정값 부재 | ⚠️ 측정 보류 — fixture baseline 우선 |

## 한계

- 단일 세션 측정은 모집단 1 — 통계 추론 불가. 누적 fixture 측정으로 신뢰도 확보.
- `tool_output_captured`는 10KB 초과만 캡처 — 작은 호출은 미카운트 (post_tool_use.py THRESHOLD_BYTES=10240).
- 응답 품질 (정확성·완결성) 은 본 회로 미측정 — 사용자 5-Likert 별도 박제.

## 측정 명령 요약

```bash
# 누적 세션 전체 측정
py plugins/harness/scripts/uplift/measure_session.py

# 단일 세션 baseline 박제
py plugins/harness/scripts/uplift/measure_session.py --session-id <sid> --label baseline

# 단일 세션 harness 박제
py plugins/harness/scripts/uplift/measure_session.py --session-id <sid> --label harness

# 누적 결과 조회
cat _workspace/_telemetry/uplift_sessions.jsonl
```
