---
description: "CM 메모리 디렉토리와 observations.db를 초기화 (재실행 안전 — 기존 데이터 보존)"
---

# /cm-harness:cm-init

CM 시스템의 디렉토리 구조와 SQLite DB를 초기화한다. **재실행에 안전** — 기존 데이터는
보존하고 누락된 디렉토리/테이블만 생성한다 (`CREATE ... IF NOT EXISTS`, `mkdir -p`).

## 컨텍스트

- **인자:** 없음
- **입력:** 없음 (현재 working directory 기준)
- **출력:** 생성/존재 확인된 항목 리스트

## 실행 절차

`plugins/cm-harness/hooks/cm_commands.py init`이 다음을 보장:

1. 디렉토리 생성:
   - `_workspace/_memory/{sessions,observations,clusters}/`
   - `_workspace/_telemetry/_rollback/`
   - `_workspace/_tool_outputs/`
2. `observations.db` 4개 테이블 + FTS5 (스키마는 session-digest 스킬 참조)
3. 출력:
   ```
   ✅ _workspace/_memory/sessions/        (existing)
   ✅ _workspace/_memory/observations/    (created)
   ✅ observations.db                     (4 tables, 1 FTS5 view)
   ...
   ```

> **`_baseline/cm_baseline.json`은 본 커맨드 범위 외:** 파일은 git에 체크인된 템플릿 형태로 이미 존재하며, 초기 30 세션 누적 후 cm-curator가 `initial_avg_*` 필드를 자동으로 채운다. 누락 시 수동 복원 또는 `/harness:harness-baseline` 영역.

## 범위 외 / 후속 명령

- 기존 데이터 삭제 후 재초기화 — `/cm-harness:cm-reset`
- 정상 동작 확인 — `/cm-harness:cm-status`
