# CM Dashboard Worker

5개 뷰(세션·클러스터·압축·pending·인벤토리/로드맵)를 SQLite + telemetry JSONL +
디렉토리 스캔에서 집계하여 localhost로 서빙하는 결정적 워커. LLM 호출 없음.

옵션 A 분산 DB 모델: 각 프로젝트는 자기 `_workspace/_memory/observations/observations.db`를
보유. 워커는 `_workspace/projects.json` 레지스트리를 읽어 프로젝트별 DB를 독립 조회한다.

## 의존성

```
fastapi >= 0.110
uvicorn >= 0.27
```

설치 (Windows · 사용자가 사용 중인 Python으로):
```powershell
& C:\Users\user01\AppData\Local\Programs\Python\Python312\python.exe -m pip install -r plugins\cm-harness\worker\requirements.txt
```

또는:
```
py -3 -m pip install -r plugins/cm-harness/worker/requirements.txt
```

## 실행

```
py -3 plugins/cm-harness/worker/dashboard_server.py
```

기본 바인딩 `127.0.0.1:8765` — 외부 노출 없음. 종료는 Ctrl+C.

## 프로젝트 레지스트리

`_workspace/projects.json`에 모니터링할 프로젝트를 수동 등록한다 — 이 파일이 없거나
비어 있으면 dharness(REPO_ROOT) 단일 fallback.

```json
{
  "projects": [
    {"name": "dharness",     "path": "C:/Users/user01/awesome-files/dharness"},
    {"name": "idea-catcher", "path": "C:/Users/user01/awesome-files/my-projects/idea-catcher"}
  ]
}
```

## 엔드포인트

| 경로 | 응답 | 데이터 소스 |
|------|------|-----------|
| `GET /` | landing (정적 UI 있으면 redirect, 없으면 API 인덱스) | — |
| `GET /ui/*` | 정적 프론트엔드 (`plugins/cm-harness/worker/static/`에 mount; 디렉토리 없으면 라우트 비활성) | filesystem |
| `GET /api/projects` | 레지스트리 + 프로젝트별 rollup 통계 | 모든 프로젝트 DB |
| `GET /api/projects/{name}/sessions` | View 1 (최근 30개) | `sessions` + `observations` |
| `GET /api/projects/{name}/clusters` | View 2 (confidence desc) | `clusters` |
| `GET /api/projects/{name}/compression` | View 3 (최근 30일) | telemetry JSONL → 임시 테이블 |
| `GET /api/projects/{name}/pending` | View 4 | `observations.completed=0` |
| `GET /api/projects/{name}/tool-timeline` | 일자별 도구 호출 (스택 차트용) | telemetry JSONL |
| `GET /api/projects/{name}/inventory` | View 5 — skills/agents/commands/hooks/mcp | `.claude/`, `commands/`, `settings.json` 디렉토리 스캔 |
| `GET /api/projects/{name}/roadmap` | View 5 — CLAUDE.md 표 추출 | `<project>/CLAUDE.md` markdown 파싱 |

Backward-compat (default project = 레지스트리 첫 항목):
| 경로 | 비고 |
|------|------|
| `GET /api/{sessions,clusters,compression,pending}?project=<name>` | `?project=` 미지정 시 default project 사용 |

## CORS

`http://127.0.0.1`, `http://localhost`(any port) 허용 — Vite/CRA dev server가
직접 API를 호출할 수 있다. GET only.

## 캐시 정책

- 메모리 내 5분 TTL, 프로젝트별 키 분리
- 무효화 anchor: `observations.db` mtime, telemetry `*.jsonl` 최신 mtime, `CLAUDE.md` mtime, `.claude/settings.json` mtime
- 위 4개 mtime 중 하나라도 바뀌면 다음 요청에서 재계산
- 프로세스 재시작 시 전체 캐시 초기화

## 트러블슈팅

| 증상 | 원인 / 해결 |
|------|-----------|
| `ModuleNotFoundError: No module named 'fastapi'` | 의존성 미설치 — 위 "설치" 절 참조 |
| `503 observations.db missing for project=<name>` | 그 프로젝트에서 새 Claude Code 세션을 한 번 열면 SessionStart 훅이 자동 생성, 또는 `projects.json` 경로 오타 |
| `404 project not found: <name>` | `projects.json`에 해당 name이 없음 |
| 압축 통계가 비어있음 | `<project>/_workspace/_telemetry/*.jsonl`에 `tool_output_captured` 이벤트 미발생 — `post_tool_use.py` 훅 등록 확인 |
| Roadmap 빈 배열 | CLAUDE.md에 markdown 표가 없거나 헤더-구분선이 깨짐 (silent fail — 의도된 동작) |
| 포트 8765 충돌 | `dashboard_server.py`의 `port=` 변경 또는 기존 프로세스 종료 |
| 외부 머신에서 접근 안 됨 | **의도된 동작** — 외부 노출 시 `host="0.0.0.0"`으로 변경 (보안 검토 필수) |
