---
description: "Context Manager 대시보드 worker 상태와 접속 URL 출력"
---

# /cm-harness:cm-dashboard

localhost 대시보드 worker 상태를 점검하고 URL을 안내한다.

## 컨텍스트

- **인자:** 없음
- **입력:** `plugins/cm-harness/worker/dashboard_server.py`
- **출력:** worker 상태 메시지 + URL

## 실행 절차

`plugins/cm-harness/hooks/cm_commands.py dashboard`가 다음을 수행:

1. localhost:8765에 GET / 시도 (1초 timeout)
2. 응답 200 → "✅ Worker 실행 중: http://localhost:8765"
3. 연결 실패 → 다음 안내 출력:
   ```
   Worker 미실행. 다음 명령으로 시작:
       python plugins/cm-harness/worker/dashboard_server.py
   기본 포트 8765, 127.0.0.1만 바인딩 (외부 노출 없음).
   ```

## 범위 외 / 후속 명령

- worker 자동 시작/종료 — 의도적으로 미지원 (사용자가 명시적으로 시작)
- 4개 뷰 데이터 직접 조회 — `/cm-harness:cm-status`, `/cm-harness:cm-sessions`, `/cm-harness:cm-clusters`
