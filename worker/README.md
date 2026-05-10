# CM Dashboard Worker

dharness self-host. SQLite + telemetry JSONL + 디렉토리 스캔 결과를 5개 뷰
(세션·클러스터·압축·pending·인벤토리/로드맵)로 집계하여 localhost로 서빙하는
결정적 워커. LLM 호출 없음.

REPO_ROOT는 본 모듈 위치(`worker/dashboard_server.py`)에서 결정적으로 계산
(`Path(__file__).resolve().parents[1]`). 외부 install / projects.json 레지스트리
없음.

## 의존성

```
fastapi >= 0.110
uvicorn >= 0.27
```

설치:
```powershell
py -3 -m pip install -r worker\requirements.txt
```

## 실행

```powershell
py worker\dashboard_server.py
```

기본 바인딩 `127.0.0.1:8765` — 외부 노출 없음. 종료는 Ctrl+C.

## 엔드포인트

| 경로 | 응답 | 데이터 소스 |
|------|------|-----------|
| `GET /` | landing (정적 UI 있으면 redirect, 없으면 API 인덱스) | — |
| `GET /ui/*` | 정적 프론트엔드 (`worker/static/`에 mount; 디렉토리 없으면 라우트 비활성) | filesystem |
| `GET /api/rollup` | dharness 단일 rollup (sessions/clusters/pending/total_minutes 등) | `sessions`, `clusters`, `observations` |
| `GET /api/sessions` | View 1 (최근 30개) | `sessions` + `observations` |
| `GET /api/clusters` | View 2 (confidence desc) | `clusters` |
| `GET /api/compression` | View 3 (최근 30일) | telemetry JSONL → 임시 테이블 |
| `GET /api/pending` | View 4 | `observations.completed=0` |
| `GET /api/tool-timeline` | 일자별 도구 호출 (스택 차트용) | telemetry JSONL |
| `GET /api/inventory` | View 5 — skills/agents/commands/hooks/mcp | `.claude/`, `plugins/harness/`, `settings*.json` 디렉토리 스캔 |
| `GET /api/roadmap` | View 5 — CLAUDE.md 표 추출 | `CLAUDE.md` markdown 파싱 |

## CORS

`http://127.0.0.1`, `http://localhost`(any port) 허용 — Vite/CRA dev server가
직접 API를 호출할 수 있다. GET only.

## 캐시 정책

- 메모리 내 5분 TTL
- 무효화 anchor: `observations.db` mtime, telemetry `*.jsonl` 최신 mtime, `CLAUDE.md` mtime, `.claude/settings.json` mtime
- 위 4개 mtime 중 하나라도 바뀌면 다음 요청에서 재계산
- 프로세스 재시작 시 전체 캐시 초기화

## 트러블슈팅

| 증상 | 원인 / 해결 |
|------|-----------|
| `ModuleNotFoundError: No module named 'fastapi'` | 의존성 미설치 — 위 "설치" 절 참조 |
| `503 observations.db missing — start a Claude Code session to bootstrap` | 새 Claude Code 세션을 한 번 열면 SessionStart 훅이 자동 생성 |
| 압축 통계가 비어있음 | `_workspace/_telemetry/*.jsonl`에 `tool_output_captured` 이벤트 미발생 — `post_tool_use.py` 훅 등록 확인 |
| Roadmap 빈 배열 | CLAUDE.md에 markdown 표가 없거나 헤더-구분선이 깨짐 (silent fail — 의도된 동작) |
| 포트 8765 충돌 | `dashboard_server.py`의 `port=` 변경 또는 기존 프로세스 종료 |
| 외부 머신에서 접근 안 됨 | **의도된 동작** — 외부 노출 시 `host="0.0.0.0"`으로 변경 (보안 검토 필수) |
