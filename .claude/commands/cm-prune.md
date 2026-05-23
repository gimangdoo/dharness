---
description: "메모리 부분 GC — N일 이전 누적 데이터(세션·관측·tool 출력·telemetry·applied/discarded draft) 삭제 (default 90일, dry-run 우선)"
---

# /cm-prune

`_workspace/_memory/` + `_workspace/_telemetry/` + `_workspace/_tool_outputs/` +
`_workspace/_drafts/{applied,discarded}/` 누적분을 **N일 이전**만 부분 삭제한다.
누적 무한 증가로 인한 디스크 압박·memory-search 검색 속도 저하 해소가 목적.

`/cm-reset`이 전체 wipe라면 `/cm-prune`은 age 기준 부분 GC.

## 컨텍스트

- **인자:** `--older-than DAYS` (default: 90), `--confirm` (생략 시 dry-run)
- **입력:** 없음
- **출력:** 영향 미리보기 또는 실제 삭제 결과

## 선조건 검증

1. `_workspace/_memory/observations.db` 존재 (없으면 SessionStart 미실행 — 안내 후 종료).
2. `--older-than` 값이 1 이상 (1 미만이면 거부).

## 실행 절차

### Step 1 — dry-run 영향 미리보기 (default)

```
py .claude/hooks/cm_commands.py prune --older-than 90
```

출력 예:

```
🔍 [dry-run] prune (cutoff: 2026-02-22 *이전* 데이터)
  sessions:             12 rows
  observations:        184 rows
  session 디렉토리:      12 개
  tool_output 디렉토리:   8 개
  telemetry 파일:         3 개
  applied 드래프트:      10 개
  discarded 드래프트:     2 개

--confirm 플래그 없이는 *삭제하지 않습니다* (dry-run). 실제 삭제: prune --older-than 90 --confirm
```

### Step 2 — 사용자 확인 후 실제 삭제

사용자가 영향 범위 보고 OK 시:

```
py .claude/hooks/cm_commands.py prune --older-than 90 --confirm
```

## 보존 / 삭제 규칙

| 항목 | 보존 | 삭제 |
|------|------|------|
| `_workspace/_memory/sessions/{sid}/` | cutoff 이후 sid | cutoff 이전 sid 디렉토리 통째 |
| `_workspace/_tool_outputs/{sid}/` | cutoff 이후 sid | cutoff 이전 sid 디렉토리 통째 |
| `observations` rows | cutoff 이후 session_id | cutoff 이전 session_id 모두 |
| `sessions` rows | cutoff 이후 | cutoff 이전 |
| `_workspace/_telemetry/{date}.jsonl` | cutoff 이후 date | cutoff 이전 date 파일 |
| `_workspace/_drafts/applied/` | cutoff 이후 date | cutoff 이전 date 파일 |
| `_workspace/_drafts/discarded/` | cutoff 이후 date | cutoff 이전 date 파일 |
| `_workspace/_drafts/*.md` (pending) | **항상 보존** | — (사용자 명시 게이트 대기 중) |
| `.current_session` | **항상 보존** | — |
| `_workspace/_telemetry/_last_adapt` | **항상 보존** | — |
| `CHANGELOG.md` | **항상 보존** | — |

`/cm-reset`과 차이:
- `reset`: 전부 wipe + 빈 상태로 재부트스트랩
- `prune`: cutoff 기준 부분 삭제, 활성 세션·pending draft·CHANGELOG는 무조건 보존

## 범위 외 / 후속 명령

- 활성 세션의 `raw.jsonl`도 cutoff 이후라면 prune 대상 아님 (sessions.date가 today 기준).
- prune 후 `_workspace/_memory/observations_fts`는 자동 정합 — FTS 인덱스는 트리거로 sync.
- 더 공격적인 wipe가 필요하면 `/cm-reset` 사용.
