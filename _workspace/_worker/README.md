# CM Dashboard Worker

`dashboard-render` 스킬이 정의한 4개 뷰를 SQLite + telemetry JSONL에서 집계하여
localhost로 서빙하는 결정적 워커. LLM 호출 없음.

## 의존성

```
fastapi >= 0.110
uvicorn >= 0.27
```

설치:
```
pip install fastapi uvicorn
```

## 실행

```
python _workspace/_worker/dashboard_server.py
```

기본 바인딩 `127.0.0.1:8765` — 외부 노출 없음. 종료는 Ctrl+C.

## 엔드포인트

| 경로 | 응답 | 데이터 소스 |
|------|------|-----------|
| `GET /` | HTML 대시보드 (4개 뷰) | 모든 SQL + 템플릿 |
| `GET /api/sessions` | View 1 JSON | `sessions` + `observations` |
| `GET /api/clusters` | View 2 JSON | `clusters` |
| `GET /api/compression` | View 3 JSON | telemetry JSONL → 임시 테이블 |
| `GET /api/pending` | View 4 JSON | `observations.completed=0` |

## 캐시 정책

- 메모리 내 5분 TTL
- 프로세스 재시작 시 캐시 초기화
- DB 변경을 즉시 반영하려면 워커 재시작

## 트러블슈팅

| 증상 | 원인 / 해결 |
|------|-----------|
| `503 observations.db not found` | `/cm-init`을 먼저 실행 |
| 압축 통계가 비어있음 | `_workspace/_telemetry/*.jsonl`에 `tool_output_captured` 이벤트 미발생 — cm-compressor 트리거 확인 |
| 포트 8765 충돌 | `dashboard_server.py`의 `port=` 변경 또는 기존 프로세스 종료 |
| 외부 머신에서 접근 안 됨 | **의도된 동작** — 외부 노출 시 `host="0.0.0.0"`으로 변경 (보안 검토 필수) |
