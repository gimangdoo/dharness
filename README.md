# Harness — Team-Architecture Factory for Claude Code

> 도메인 한 문장을 **에이전트 팀 + 스킬 세트**로 변환하는 메타 스킬.
> A meta-skill that turns a domain description into an agent team and the skills they use.

---

## 무엇인가

`dharness`는 두 개의 plugin을 한 저장소에 담은 monorepo입니다:

1. **`harness` plugin** (`plugins/harness/`) — 도메인을 입력 받아 에이전트 3~5명 + 스킬 세트를 자동 생성하는 메타 스킬 팩토리.
2. **`cm-harness` plugin** (`plugins/cm-harness/`) — Context Manager 런타임. 세션 간 컨텍스트 손실·도구 출력 비대화·메모리 미영속 문제를 결정적 hooks + FastAPI 워커로 해결합니다 (LLM 호출 없는 데이터 파이프라인).

다른 단일 에이전트/프롬프트 프레임워크와 달리, harness는 **팀 아키텍처 팩토리**입니다 — 6가지 사전 정의된 팀 패턴 중 도메인에 맞는 것을 선택하고 에이전트 협업 프로토콜을 함께 설계합니다.

### 6 팀 아키텍처 패턴

| 패턴 | 적합한 작업 |
|------|----------|
| **Pipeline** | 단계별 순차 흐름 (분석 → 설계 → 검증) |
| **Fan-out / Fan-in** | 병렬 분기 → 결과 통합 (멀티 소스 리서치) |
| **Expert Pool** | 도메인별 전문가 풀에서 동적 선택 (티켓 라우팅) |
| **Producer-Reviewer** | 생성-비판 분리 (코드 작성 + 리뷰) |
| **Supervisor** | 메타 에이전트가 분배·모니터·종합 |
| **Hierarchical Delegation** | 상위 → 하위 위임, 결과 상위 통합 |

---

## 빠른 시작 (5분)

### 1. 저장소 가져오기

```powershell
git clone https://github.com/<your-fork>/dharness.git C:\path\to\dharness
```

### 2. 자기 자신에 대해 사용해 보기

dharness 자체에서 plugin을 사용하려면 우선 두 plugin을 install (1회):

```powershell
claude plugin marketplace add C:\Users\user01\awesome-files\dharness
claude plugin install harness@dharness
claude plugin install cm-harness@dharness
```

이후 `/cm-harness:cm-status`, `/harness:harness-audit` 등으로 호출. self-use 훅은 `.claude/settings.local.json`에서 `${CLAUDE_PROJECT_DIR}/plugins/cm-harness/hooks/...`로 가리키도록 이미 설정 — plugin도 install되어 있으면 이중 발화 가능하므로 둘 중 하나만 활성화.

### 3. 새 도메인에 적용해 보기 (선택)

```text
/harness:harness-new 코드 리뷰를 자동화하는 도메인
```

→ `.claude/agents/{name}.md`·`.claude/skills/{name}/SKILL.md`이 사용자 프로젝트에 생성됩니다.

---

## 호출 방식 두 가지

| 방식 | 발동 | 비용 통제 | 용도 |
|---|---|---|---|
| **자연어 트리거** | "하네스 구성해줘" 등 자연 발화 ↔ skill description 매칭 | LLM이 자동 분기 | 자연스러운 발화, 일반 사용 |
| **Slash command** | `/harness-new`, `/harness-add-agent` 등 결정적 호출 | 사용자가 Phase 범위 직접 지정 | 비용 회피, 트리거 확률 의존 제거 |

**Slash command 카탈로그 (`harness` 7개 + `cm-harness` 4개 = 11개):**

```
# harness plugin (메타 스킬 팩토리)
/harness:harness-new <도메인>          # Phase 0~8 전체 (신규 구축)
/harness:harness-add-agent <역할>      # Phase 4·5·7·8 (1·2·3 skip)
/harness:harness-add-skill <스킬>      # Phase 6·7·8 (1~5 skip)
/harness:harness-baseline              # Phase 1·2 재실행 + drift 분석
/harness:harness-audit                 # 정합성 감사 (read-only)
/harness:harness-evolve <피드백>       # Phase 9 수동 진화
/harness:harness-adapt                 # Phase 10 telemetry drift 점검

# cm-harness plugin (CM 런타임)
/cm-harness:cm-status                  # 메모리 통계 + DB 행 수
/cm-harness:cm-sessions [--limit N]    # 최근 세션 목록
/cm-harness:cm-dashboard               # worker 상태 + URL 확인
/cm-harness:cm-reset                   # 메모리 전체 삭제 (확인 필수)
```

명령어 본문(`.md` 파일)은 `plugins/{harness,cm-harness}/commands/`에 보관.

---

## 프로젝트 구조

monorepo subdirs 모델:

```
.
├── .claude-plugin/
│   └── marketplace.json   # 두 plugin git-subdir 카탈로그
├── plugins/
│   ├── harness/           # PLUGIN 1 — 메타 스킬 팩토리
│   │   ├── .claude-plugin/plugin.json
│   │   ├── skills/harness/  # SKILL.md + references/
│   │   └── commands/        # harness-* 7개
│   └── cm-harness/        # PLUGIN 2 — Context Manager 런타임
│       ├── .claude-plugin/plugin.json
│       ├── skills/memory-search/  # on-demand 메모리 검색 (LLM-time)
│       ├── commands/          # cm-* 4개
│       ├── hooks/             # SessionStart/PostToolUse/SessionEnd + _schema.py + cm_commands.py + hooks.json + INSTALL.md
│       └── worker/            # FastAPI 대시보드 (+ static/, requirements.txt)
├── _workspace/             # DATA — 코드 외 런타임 산출물 (사용자 프로젝트별 격리)
│   ├── _telemetry/        # 라이프사이클 이벤트 append-only JSONL
│   ├── _memory/           # CM 런타임 메모리 (sessions/clusters/observations.db)
│   ├── _tool_outputs/     # PostToolUse 10KB 초과 원본 보존
│   └── projects.json      # 대시보드 멀티 프로젝트 레지스트리
└── CLAUDE.md              # 하네스 포인터 + 변경 이력
```

**핵심 원칙:** `plugins/` = 코드(plugin install 시 read-only), `_workspace/` = 데이터(`${CLAUDE_PROJECT_DIR}` 기준 사용자 프로젝트에 생성).

---

## Skill 워크플로우 11단계

`harness` 메타 스킬은 다음 11단계로 동작합니다:

| Phase | 이름 | 출력 |
|-------|------|------|
| 0 | Pre-flight 감사 | 신규/확장/유지보수 분기 |
| 1 | Code Research | `_workspace/_baseline/project_profile.md` |
| 2 | Project Inquiry | `_workspace/_baseline/intent_profile.md` |
| 3 | 도메인 분석 | 작업 유형 + 충돌 분석 |
| 4 | 팀 아키텍처 | 모드 + 패턴 + 분리 기준 |
| 5 | 에이전트 정의 | `.claude/agents/{name}.md` |
| 6 | 스킬 생성 | `.claude/skills/{name}/SKILL.md` |
| 7 | 오케스트레이션 | 통합 스킬 + CLAUDE.md 포인터 |
| 8 | 검증 (7단계) | 구조·실행·트리거·드라이런·반복 개선 |
| 9 | 진화 (수동) | 사용자 피드백 → 에이전트/스킬 갱신 |
| 10 | Runtime Adaptation | telemetry → drift 감지 → 제안+승인 |

상세는 [`plugins/harness/skills/harness/SKILL.md`](./plugins/harness/skills/harness/SKILL.md).

---

## 다른 프로젝트에 dharness 도입하기

`/plugin install` 한 줄로 끝납니다. dharness marketplace는 두 plugin을 제공하므로 필요한 것만 골라 install:

| Plugin | 내용 | 명령 |
|---|---|---|
| `harness` | 메타 스킬 팩토리 (도메인 → 에이전트 팀+스킬 자동 생성) | `/plugin install harness@dharness` |
| `cm-harness` | Context Manager (3 hooks + FastAPI 워커 + 결정적 슬래시 커맨드) | `/plugin install cm-harness@dharness` |

둘 다 install 가능 (네임스페이스 분리: `/harness:*` vs `/cm-harness:*`).

### 1) marketplace 등록 + 설치

```powershell
claude plugin marketplace add gimangdoo/dharness
claude plugin install harness@dharness
claude plugin install cm-harness@dharness
```

### 2) 로컬 개발용 (marketplace 거치지 않음)

```powershell
claude --plugin-dir C:\path\to\dharness\plugins\harness
# 또는
claude --plugin-dir C:\path\to\dharness\plugins\cm-harness
```

### 3) 설치되면

- **harness:** `/harness:harness-new`, `/harness:harness-add-agent` 등 7개 슬래시 커맨드. 사용자 프로젝트의 `.claude/agents/`·`.claude/skills/`·`CLAUDE.md`에 산출물 생성 (Phase 0~8).
- **cm-harness:** `/cm-harness:cm-status`, `/cm-harness:cm-sessions` 등 4개 + SessionStart/PostToolUse/SessionEnd 훅 자동 등록 (사용자 `settings.json` 무수정). 데이터(`_workspace/_memory/`, `_workspace/_telemetry/`)는 사용자 프로젝트의 `${CLAUDE_PROJECT_DIR}`에 떨어짐 — plugin dir는 read-only.

### 4) 검증

설치 후 그 프로젝트에서 새 세션을 열고:

```
/cm-harness:cm-status
```

`sessions` 카운트 ≥ 1이면 SessionStart 훅 정상.

> **이중 발화 주의 (dharness 본 폴더에서 직접 작업 시):** dharness 자체에서 Claude Code를 열면 `.claude/settings.local.json`의 self-use 훅이 발동합니다. 같은 프로젝트에서 `cm-harness` plugin도 enable되어 있으면 훅 2번 발화. plugin을 disable(`/plugin disable cm-harness`)하거나 `settings.local.json` `hooks` 블록을 제거하세요.

### 도입 후 권한 경계

`harness` plugin은 사용자 프로젝트의 `.claude/commands/`에 **아무것도 생성하지 않습니다** (read-only invariant). harness 메타 스킬이 만드는 산출물은 사용자 프로젝트의 `.claude/agents/`·`.claude/skills/`·`CLAUDE.md`에만 떨어집니다.

---

## Context Manager 하네스 (구축 예시 — 결정적 모델)

cm-harness plugin은 **LLM 호출 없는 결정적 데이터 파이프라인**으로 동작합니다. 캡처는 hooks가, 집계/조회는 워커가 담당합니다. 메모리 검색만 LLM이 on-demand로 호출 가능 (`memory-search` 스킬).

### 결정적 산출물

| 위치 | 역할 |
|------|------|
| `plugins/cm-harness/hooks/_schema.py` | DDL 단일 진실 원천 (4 테이블 + FTS5) |
| `plugins/cm-harness/hooks/session_start.py` | SessionStart: ID 발급, dangling 세션 finalize, 최신 daily_summary 1건 inject |
| `plugins/cm-harness/hooks/post_tool_use.py` | PostToolUse: raw.jsonl + 10KB 초과 시 `_tool_outputs/`에 원본 보존 |
| `plugins/cm-harness/hooks/session_end.py` | SessionEnd: transcript 평탄화, sessions UPDATE |
| `plugins/cm-harness/hooks/cm_commands.py` | `/cm-*` 결정적 커맨드 핸들러 (status/sessions/dashboard/reset) |
| `plugins/cm-harness/hooks/hooks.json` | plugin install 시 훅 자동 등록 매니페스트 |
| `plugins/cm-harness/hooks/INSTALL.md` | self-use 시 훅 수동 등록 가이드 |
| `plugins/cm-harness/worker/dashboard_server.py` | FastAPI localhost 워커 (멀티 프로젝트) |
| `plugins/cm-harness/worker/static/` | 정적 프론트엔드 (`/ui/` 마운트) |
| `plugins/cm-harness/skills/memory-search/SKILL.md` | LLM이 자연어 메모리 검색 시 따르는 3-tool progressive disclosure 규칙 |
| `_workspace/projects.json` | 대시보드 멀티 프로젝트 레지스트리 (사용자 데이터) |

### 동작 흐름

```
SessionStart hook
  → session_id 발급 + DB 부트스트랩
  → 직전 dangling 세션 finalize
  → 최신 daily_summary를 additionalContext로 inject (LLM에게 데이터만 전달, 행동 지시 없음)

PostToolUse hook
  → raw.jsonl에 메타 append
  → output > 10KB이면 _tool_outputs/{sid}/에 원본 보존

SessionEnd hook
  → transcript.md 평탄화
  → sessions.ended_at / duration_min / tools_used UPDATE

[Worker 잡 — 별도 프로세스 / 향후 통합 예정]
  → transcript → digest 생성 (Anthropic API)
  → observations 추출 + 저장
  → cluster 생성/갱신 + decay
  → daily_summaries upsert
```

> **알림 (현재 상태):** Worker 측 digest/cluster/daily_summary 자동 생성 잡은 별도 작업으로 분리되어 있습니다. 현재 시점에서 *생성된 데이터*는 조회·검색·대시보드 표시 모두 정상 동작하지만, *새 데이터 자동 생성*은 워커 잡 통합 후 활성화됩니다.

---

## CM Dashboard 사용법

`plugins/cm-harness/worker/dashboard_server.py`(FastAPI + uvicorn 결정적 워커)를 직접 실행해 SQLite + telemetry JSONL + 디렉토리 스캔 결과를 한 화면에서 비교 열람합니다. **LLM 호출 없음**.

### 1. 의존성 설치 (최초 1회)

```powershell
py -3 -m pip install -r plugins\cm-harness\worker\requirements.txt
```

`fastapi >= 0.110`, `uvicorn >= 0.27` 두 개만 필요합니다.

### 2. 멀티 프로젝트 레지스트리 (선택)

`_workspace/projects.json`에 모니터링할 프로젝트들을 수동 등록합니다. 파일이 없거나 비어 있으면 dharness 단일 프로젝트로 fallback.

```json
{
  "projects": [
    {"name": "dharness",     "path": "C:/Users/user01/awesome-files/dharness"},
    {"name": "idea-catcher", "path": "C:/Users/user01/awesome-files/my-projects/idea-catcher"}
  ]
}
```

각 프로젝트는 자기 `_workspace/_memory/observations/observations.db`를 가져야 하며 (없으면 새 Claude Code 세션을 그 프로젝트에서 한 번 열면 SessionStart 훅이 자동 생성), cross-project SQL JOIN은 발생하지 않습니다.

### 3. 실행

```powershell
py -3 plugins\cm-harness\worker\dashboard_server.py
```

기본 바인딩 `127.0.0.1:8765` — 외부 노출 없음. 종료는 Ctrl+C. 백그라운드로 띄우는 가장 간단한 방법은 별도 PowerShell 창에서 위 명령을 그대로 실행해 두는 것입니다.

### 4. 접속

브라우저에서 한 곳만 열면 됩니다:

- **http://127.0.0.1:8765/** — `plugins/cm-harness/worker/static/index.html`이 있으면 자동으로 `/ui/`로 redirect되어 정적 프론트엔드가 뜸. 없으면 minimal HTML 인덱스(레지스트리 표 + 엔드포인트 목록)로 fallback.

`/cm-harness:cm-dashboard` 슬래시 커맨드는 워커 상태와 URL을 출력만 하는 결정적 핸들러이며, 워커 자체는 위 방식으로 직접 띄워야 합니다.

### 5. 5개 View

| View | 엔드포인트 | 데이터 소스 | 의도 |
|------|-----------|-----------|------|
| 1. 세션 | `/api/projects/{name}/sessions` | `sessions` + `observations` | 최근 30 세션, pending/warn count, digest 보유 여부 |
| 2. 클러스터 | `/api/projects/{name}/clusters` | `clusters` | confidence desc, 마지막 접근 후 경과일 |
| 3. 압축 통계 | `/api/projects/{name}/compression` | telemetry JSONL | 도구별 raw/compressed 평균, 비율 (최근 30일) |
| 4. Pending | `/api/projects/{name}/pending` | `observations.completed=0` | 미완료 do 항목 |
| 5. Inventory + Roadmap | `/api/projects/{name}/inventory`, `/roadmap` | `.claude/`·`commands/`·`settings.json`·`CLAUDE.md` | skills/agents/commands/hooks/mcp 산출물 + CLAUDE.md 표 추출 |

추가:
- `/api/projects` — 등록 프로젝트 + rollup 통계 (sessions/clusters/pending/total_minutes)
- `/api/projects/{name}/tool-timeline` — 일자별 도구 호출 (스택 차트용)

Backward-compat (default project = 레지스트리 첫 항목):
| 경로 | 비고 |
|------|------|
| `GET /api/{sessions,clusters,compression,pending}?project=<name>` | `?project=` 미지정 시 default project |

### 6. CORS / 캐시 / 보안

- **CORS:** `http://127.0.0.1` / `http://localhost`(any port) GET only — Vite 등 별도 dev server가 직접 API를 호출 가능
- **캐시:** 메모리 내 5분 TTL, 프로젝트별 키 분리. 무효화 anchor = `observations.db` mtime + telemetry `*.jsonl` 최신 mtime + `CLAUDE.md` mtime + `.claude/settings.json` mtime. 4개 중 하나라도 바뀌면 다음 요청에서 재계산
- **보안:** 외부 노출 없음 (`host="127.0.0.1"`). 외부 접근이 필요하면 코드의 `host="0.0.0.0"`으로 변경 + 자체 보안 검토 필수

### 7. 트러블슈팅

| 증상 | 원인 / 해결 |
|------|-----------|
| `ModuleNotFoundError: No module named 'fastapi'` | 의존성 미설치 — §1 다시 실행 |
| `503 observations.db missing for project=<name>` | 그 프로젝트에서 새 Claude Code 세션을 한 번 열면 SessionStart 훅이 자동 생성, 또는 `projects.json` 경로 오타 점검 |
| `404 project not found: <name>` | `projects.json`에 해당 name이 없음 |
| 압축 통계가 비어있음 | `<project>/_workspace/_telemetry/*.jsonl`에 `tool_output_captured` 이벤트 미발생 — `post_tool_use.py` 훅 등록 확인 |
| Roadmap 빈 배열 | `CLAUDE.md`에 markdown 표가 없거나 헤더-구분선이 깨짐 (silent fail — 의도된 동작) |
| 포트 8765 충돌 | `dashboard_server.py`의 `port=` 변경 또는 기존 프로세스 종료 |
| 외부 머신에서 접근 안 됨 | **의도된 동작** — `host="0.0.0.0"`로 변경 후 직접 보안 검토 |

### 8. 종료 / 재시작

- 종료: 워커 콘솔에서 `Ctrl+C`
- 재시작 시 캐시 전체 초기화. 코드를 수정했다면 그냥 재시작하면 됨 (auto-reload 미사용)

워커 자체 README: [`plugins/cm-harness/worker/README.md`](./plugins/cm-harness/worker/README.md).

---

## 트러블슈팅 (CM 시스템 전반)

| 증상 | 해결 |
|------|------|
| 훅이 동작하지 않음 | `py --version` 확인 → settings의 `command`를 `py ...`로 변경 (Microsoft Store 스텁 회피) |
| `/cm-harness:cm-status`가 빈 결과 | 새 Claude Code 세션을 한 번 열어 SessionStart 훅 발동 확인 |
| transcript는 있는데 digest.md가 없음 | Worker 측 digest 잡이 미통합 상태 — 현재 알려진 한계 (이번 surgery 후속 작업) |
| daily_summaries 비어있음 | 동상 |

---

## 문서 인덱스

| 문서 | 용도 |
|------|------|
| [`plugins/harness/skills/harness/SKILL.md`](./plugins/harness/skills/harness/SKILL.md) | 메타 스킬 정의 (11 Phase 워크플로우) |
| [`plugins/cm-harness/hooks/INSTALL.md`](./plugins/cm-harness/hooks/INSTALL.md) | self-use 시 훅 수동 등록 절차 (plugin install 시 자동) |
| [`plugins/cm-harness/worker/README.md`](./plugins/cm-harness/worker/README.md) | 대시보드 워커 명세 (엔드포인트·CORS·캐시) |
| [`plugins/cm-harness/skills/memory-search/SKILL.md`](./plugins/cm-harness/skills/memory-search/SKILL.md) | 과거 메모리 LLM 검색 규칙 (3-tool progressive disclosure) |
| [`CLAUDE.md`](./CLAUDE.md) | Context Manager 하네스 포인터 + 변경 이력 |
