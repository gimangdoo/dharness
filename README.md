# Harness — Team-Architecture Factory for Claude Code

> 도메인 한 문장을 **에이전트 팀 + 스킬 세트**로 변환하는 메타 스킬.
> A meta-skill that turns a domain description into an agent team and the skills they use.

---

## 무엇인가

`dharness`는 두 개의 레이어를 한 저장소에 담은 Claude Code 플러그인입니다:

1. **메타 스킬 본체** (`skills/harness/`, `commands/harness-*.md`) — 도메인을 입력 받아 에이전트 3~5명 + 스킬 세트를 자동 생성하는 팩토리.
2. **구축 예시 (Context Manager 하네스)** (`.claude/agents/cm-*.md`, `.claude/skills/`, `_workspace/_hooks/`, `_workspace/_worker/`, `commands/cm-*.md`) — 메타 스킬을 context-management 도메인에 적용해 만든 실제 작동 인스턴스. 세션 간 컨텍스트 손실·도구 출력 비대화·메모리 미영속 문제를 해결합니다.

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
# 적당한 보관 위치에 clone
git clone https://github.com/<your-fork>/dharness.git C:\path\to\dharness
```

### 2. 자기 자신에 대해 사용해 보기

dharness 루트로 이동해 Claude Code를 연 뒤 다음 중 하나를 입력합니다:

| 입력 | 효과 |
|------|------|
| `/cm-status` | 이 레포에 이미 구축된 CM 하네스의 상태 확인 (디렉토리 + DB 행 수) |
| `/cm-init` | CM 메모리 디렉토리·`observations.db` 초기화 (재실행 안전) |
| `/harness-audit` | 본 레포 산출물 정합성 read-only 감사 |

`/cm-init`이 끝나면 [`_workspace/_hooks/INSTALL.md`](./_workspace/_hooks/INSTALL.md)의 절차대로 settings에 훅을 등록하면 세션 캡처가 시작됩니다.

### 3. 새 도메인에 적용해 보기 (선택)

```text
/harness-new 코드 리뷰를 자동화하는 도메인
```

→ `.claude/agents/{name}.md`·`.claude/skills/{name}/SKILL.md`이 그 자리에 생성됩니다.

---

## 호출 방식 두 가지

| 방식 | 발동 | 비용 통제 | 용도 |
|---|---|---|---|
| **자연어 트리거** | "하네스 구성해줘" 등 자연 발화 ↔ skill description 매칭 | LLM이 자동 분기 | 자연스러운 발화, 일반 사용 |
| **Slash command** | `/harness-new`, `/harness-add-agent` 등 결정적 호출 | 사용자가 Phase 범위 직접 지정 | 비용 회피, 트리거 확률 의존 제거 |

**Slash command 카탈로그 (Harness 7 + CM 7 = 14개):**

```
# Harness 메타 스킬 진입점
/harness-new <도메인>          # Phase 0~8 전체 (신규 구축)
/harness-add-agent <역할>      # Phase 4·5·7·8 (1·2·3 skip)
/harness-add-skill <스킬>      # Phase 6·7·8 (1~5 skip)
/harness-baseline              # Phase 1·2 재실행 + drift 분석
/harness-audit                 # 정합성 감사 (read-only)
/harness-evolve <피드백>       # Phase 9 수동 진화
/harness-adapt                 # Phase 10 telemetry drift 점검

# Context Manager 도메인 진입점
/cm-status                     # 메모리 통계 + DB 행 수
/cm-sessions [--limit N]       # 최근 세션 목록
/cm-clusters [--min-conf X]    # 클러스터 (confidence desc)
/cm-dashboard                  # worker 상태 + URL 확인
/cm-init                       # 디렉토리 + DB 초기화
/cm-reset                      # 메모리 전체 삭제 (확인 필수)
/cm-curate                     # cm-curator 단독 실행
```

전체 가이드: [`commands/README.md`](./commands/README.md).

---

## 프로젝트 구조

```
.
├── commands/              # Slash command 진입점 14종 (harness-* 7 + cm-* 7)
├── skills/
│   └── harness/           # 메타 스킬 본체 (SKILL.md + references/)
├── .claude/
│   ├── agents/            # context-management 하네스 에이전트 5종 (cm-*)
│   └── skills/            # context-management 하네스 스킬 7종
├── _workspace/
│   ├── _baseline/         # Phase 1-2 산출물 + CM baseline 기준값
│   ├── _telemetry/        # Phase 10 telemetry (append-only JSONL)
│   ├── _memory/           # CM 런타임 메모리 (세션/클러스터/observations)
│   ├── _hooks/            # SessionStart/PostToolUse/SessionEnd 훅 + INSTALL.md
│   ├── _worker/           # FastAPI 대시보드 워커 (+ static/ 프론트엔드)
│   ├── _tool_outputs/     # PostToolUse 원본 보존 (압축 전)
│   ├── projects.json      # 대시보드 멀티 프로젝트 레지스트리
│   └── references/        # CM 전용 Phase 10 진단 룰
└── CLAUDE.md              # 하네스 포인터 + 변경 이력
```

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

상세는 [`skills/harness/SKILL.md`](./skills/harness/SKILL.md).

---

## 다른 프로젝트에 dharness 도입하기

세 가지 형태로 다른 프로젝트에 적용할 수 있습니다:

- **0. (권장) Plugin 설치** — `/plugin install dharness@dharness` 한 줄로 메타 스킬·CM 산출물·훅 모두 자동 등록 (사용자 `settings.json` 무수정).
- **A. 메타 스킬만 사용** — `mklink` 정션으로 메타 스킬만 노출 (plugin 분리 전 임시 — Step 2에서 별도 plugin으로 분리 예정).
- **B. CM 하네스(컨텍스트 매니저) 그대로 적용** — `robocopy`로 cm-* 에이전트/스킬/훅/대시보드를 옮기는 수동 절차 (마찬가지로 Step 2 후 plugin 선택 install 가능).

### 0. (권장) Plugin 설치

본 레포는 `.claude-plugin/plugin.json` 매니페스트를 포함합니다. Claude Code의 plugin 시스템으로 한 줄 설치 가능합니다.

**0-1) marketplace 등록 + 설치**

```powershell
# GitHub 레포에서 직접 marketplace 등록
claude plugin marketplace add gimangdoo/dharness

# plugin 설치 (현재는 메타 스킬 + CM 하네스가 한 패키지)
claude plugin install dharness@dharness
```

**0-2) 로컬 개발용 (마켓플레이스 거치지 않음)**

```powershell
# 다른 프로젝트에서 dharness를 임시 plugin으로 띄움
claude --plugin-dir C:\path\to\dharness
```

설치되면:
- `/dharness:harness-new`, `/dharness:cm-status` 등 14개 슬래시 커맨드 노출
- SessionStart/PostToolUse/SessionEnd 훅이 `${CLAUDE_PLUGIN_ROOT}` 기반으로 자동 등록 (사용자 `.claude/settings.json` 무수정)
- 데이터(`_workspace/_memory/`, `_workspace/_telemetry/`)는 사용자 프로젝트(`${CLAUDE_PROJECT_DIR}`)에 떨어짐 — plugin dir(read-only)는 무손상

**0-3) 검증**

설치 후 그 프로젝트에서 새 세션을 열고:

```
/dharness:cm-status
```

`sessions` 카운트 ≥ 1이면 SessionStart 훅 정상.

> **이중 발화 주의 (dharness 본 폴더 작업 시):** dharness 자체에서 Claude Code를 직접 열 때는 `.claude/settings.local.json`의 기존 `${CLAUDE_PROJECT_DIR}` 기반 훅이 발동합니다. 이 경우 plugin을 disable하거나(`/plugin disable dharness`), 본 폴더의 `settings.local.json`에서 `hooks` 블록을 제거하세요.

> **현재 한계 (Step 1 단계):** 한 plugin에 메타 스킬과 CM 산출물이 모두 묶여 있어 "메타만" 또는 "CM만" 선택 install이 불가. Step 2에서 `harness` plugin과 `cm-harness` plugin으로 분리 예정.

### A. 메타 스킬만 사용 (신규 도메인 구축)

`skills/harness/`와 `commands/harness-*.md`만 대상 프로젝트에 노출시키면 됩니다. Windows에서는 관리자 PowerShell에서 디렉토리 정션을 거는 방식이 안전합니다 (mklink는 OneDrive와 잘 호환됨):

```powershell
# 대상 프로젝트 = C:\path\to\target
$D = "C:\path\to\dharness"
$T = "C:\path\to\target"

# (없다면) .claude 골격 생성
New-Item -ItemType Directory -Force "$T\.claude\skills" | Out-Null
New-Item -ItemType Directory -Force "$T\.claude\commands" | Out-Null

# 메타 스킬 + 슬래시 커맨드 노출
cmd /c mklink /J "$T\.claude\skills\harness" "$D\skills\harness"
Get-ChildItem "$D\commands\harness-*.md" | ForEach-Object {
  cmd /c mklink "$T\.claude\commands\$($_.Name)" "$_.FullName"
}
```

이후 그 프로젝트에서 Claude Code를 열고:

```
/harness-new <도메인 한 문장>
```

→ Phase 0~8을 거쳐 그 프로젝트의 `.claude/agents/`·`.claude/skills/`·`CLAUDE.md`에 산출물이 생성됩니다. dharness 본체는 read-only 경계가 보호하므로 침범하지 않습니다.

### B. CM 하네스(컨텍스트 매니저) 그대로 적용

본 레포에서 운영 중인 `cm-*` 에이전트/스킬/훅/대시보드를 다른 프로젝트로 옮기는 절차입니다.

**1) 산출물 복사 또는 정션**

```powershell
$D = "C:\path\to\dharness"
$T = "C:\path\to\target"

# 에이전트 5종 + 스킬 7종 + cm-* 슬래시 커맨드 7종
robocopy "$D\.claude\agents"    "$T\.claude\agents"    cm-*.md
robocopy "$D\.claude\skills"    "$T\.claude\skills"    /E /XD harness  # CM 스킬만
robocopy "$D\commands"          "$T\.claude\commands"  cm-*.md

# 훅 + 대시보드 워커 + 레지스트리 — `__pycache__`은 런타임 부산물이므로 제외
robocopy "$D\_workspace\_hooks"  "$T\_workspace\_hooks"  /E /XD __pycache__
robocopy "$D\_workspace\_worker" "$T\_workspace\_worker" /E /XD __pycache__
Copy-Item "$D\_workspace\references\cm-diagnostic-rules.md" `
          "$T\_workspace\references\cm-diagnostic-rules.md" -Force
```

> 변경 사항을 dharness와 동기화하고 싶다면 위 robocopy 대신 `mklink /J` 정션을 쓰세요.

**1-1) 복사 후 검증 — 정의 파일만 옮겨졌는지 확인**

대상 프로젝트가 git 저장소라면 (없다면 `git init` 후) `.gitignore`에 dharness의 런타임 패턴을 미리 병합한 뒤 다음을 실행해 누수가 없는지 확인합니다:

```powershell
# (한 번만) dharness의 .gitignore 룰을 대상 프로젝트에 병합
Copy-Item "$D\.gitignore" "$T\.gitignore.dharness" -Force
# 두 파일을 직접 합치거나, 처음 도입이라면 그대로 .gitignore로 사용

# 검증
cd "$T"
git status --ignored
```

기대 출력:
- 추적 대상에 `_workspace/_memory/`, `_workspace/_telemetry/`, `_workspace/_tool_outputs/`, `_workspace/_baseline/`, `__pycache__/`이 **나타나지 않아야** 함 (이들은 모두 런타임/프로젝트 고유 산출물)
- `Ignored files:` 섹션에는 위 항목들이 등장 가능 — 정상 (실행 후 생성될 것들이 이미 ignore되어 있음)

만약 추적 대상에 `__pycache__/`이 보이면 위 robocopy의 `/XD __pycache__`가 누락된 것이므로 `Remove-Item -Recurse "$T\_workspace\_hooks\__pycache__", "$T\_workspace\_worker\__pycache__"`로 정리합니다.

**2) `_workspace/projects.json`에 대상 프로젝트 등록 (대시보드용)**

```json
{
  "projects": [
    {"name": "dharness", "path": "C:/Users/user01/awesome-files/dharness"},
    {"name": "target",   "path": "C:/path/to/target"}
  ]
}
```

**권장 — 이 파일은 dharness 쪽에만 둡니다.** 대시보드 워커 한 개가 여러 프로젝트를 한 화면에서 모니터링하는 것이 옵션 A 분산 DB 모델의 의도된 사용 방식입니다(cross-project SQL JOIN 없이 각 DB 독립 조회). 대상 프로젝트의 `_workspace/_worker/`는 정의(코드)만 보유하고 실행은 dharness 워커가 담당합니다 — 따라서 대상 프로젝트에는 워커를 띄우지 않으며, 그쪽 `projects.json`은 빈 채로 두거나 만들지 않습니다.

> **예외:** 사내 보안 정책 등으로 dharness가 대상 프로젝트 디렉토리를 읽을 수 없는 환경이라면 대상에서 워커를 별도로 띄워야 합니다. 그 경우 대상 프로젝트의 `_workspace/projects.json`에 자기 자신만 등록하세요.

**3) CM 메모리 초기화 + 훅 설치**

대상 프로젝트에서 Claude Code를 열고:

```
/cm-init
```

그 다음 [`_workspace/_hooks/INSTALL.md`](./_workspace/_hooks/INSTALL.md)에 따라 `.claude/settings.json`(또는 `.claude/settings.local.json`)에 hooks 섹션을 병합합니다:

```jsonc
{
  "hooks": {
    "SessionStart": [{ "hooks": [
      { "type": "command", "command": "py \"${CLAUDE_PROJECT_DIR}/_workspace/_hooks/session_start.py\"" }
    ]}],
    "PostToolUse": [{ "matcher": "", "hooks": [
      { "type": "command", "command": "py \"${CLAUDE_PROJECT_DIR}/_workspace/_hooks/post_tool_use.py\"" }
    ]}],
    "SessionEnd": [{ "hooks": [
      { "type": "command", "command": "py \"${CLAUDE_PROJECT_DIR}/_workspace/_hooks/session_end.py\"" }
    ]}]
  }
}
```

> Windows에서 bare `python`은 Microsoft Store 스텁으로 매핑되어 exit 9009로 실패할 수 있습니다. 안전한 명령은 `py` 또는 절대경로(`C:\...\python.exe`).

**4) 검증**

새 세션을 연 뒤:

```powershell
py _workspace\_hooks\cm_commands.py status
```

- `sessions` 카운트 ≥ 1 → SessionStart 훅 정상
- 도구 사용 후 세션을 끝내고 다시 열면 `tools_used`가 채워져 있음 → PostToolUse + SessionEnd 정상

### 도입 후 권한 경계

dharness 메타 스킬은 사용자 프로젝트의 `.claude/commands/`에 **아무것도 생성하지 않습니다** (read-only invariant). 위 B 절차의 `cm-*.md` 복사는 사용자 본인이 명시적으로 수행하는 작업이므로 invariant 위반이 아닙니다. CM 자동 적응(Phase 10) 영향 범위는 [`CLAUDE.md`](./CLAUDE.md)의 "CM 적응의 영구 범위 한정" 섹션 참조.

---

## Context Manager 하네스 (구축 예시)

harness 메타 스킬로 구축된 **context-management 도메인 하네스**가 이 레포에 포함되어 있습니다. 세션 간 컨텍스트 손실·도구 출력 비대화·메모리 미영속 문제를 해결하는 실제 구현체입니다.

### 에이전트 5종 (`.claude/agents/`)

| 에이전트 | 실행 시점 | 모드 |
|--------|----------|------|
| `cm-injector` | SessionStart 훅 | 서브 에이전트 |
| `cm-compressor` | PostToolUse 훅 (>10KB) | 서브 에이전트 |
| `cm-digester` | SessionEnd 훅 | 팀 (curator와) |
| `cm-curator` | SessionEnd + 주기 | 팀 (digester와) |
| `cm-retriever` | 메모리 검색 on-demand | 서브 에이전트 |

### 스킬 7종 (`.claude/skills/`)

| 스킬 | 역할 |
|------|------|
| `cm-orchestrator` | 라이프사이클 이벤트 → 에이전트 라우터 |
| `session-capture` | session_id 발급 + raw.jsonl/transcript.md 캡처 (S1) |
| `tool-output-compress` | 도구별 압축 전략 + raw 보존 경로 |
| `session-digest` | what/when/do/warn 구조 + **단일 DB 스키마 진실 원천** |
| `memory-curate` | 클러스터링 + decay + 승격 + daily_summary + 주기 트리거 |
| `memory-search` | 3-tool progressive disclosure |
| `dashboard-render` | 5개 뷰 SQLite 집계 + FastAPI worker 명세 |

### 결정적 부속 산출물

| 위치 | 역할 |
|------|------|
| `_workspace/_hooks/session_start.py` | SessionStart 훅: ID 발급·DB 부트스트랩 |
| `_workspace/_hooks/post_tool_use.py` | PostToolUse 훅: raw.jsonl + 10KB 캡처 |
| `_workspace/_hooks/session_end.py` | SessionEnd 훅: transcript 평탄화 |
| `_workspace/_hooks/cm_commands.py` | `/cm-*` 결정적 커맨드 핸들러 |
| `_workspace/_hooks/INSTALL.md` | 훅 settings.json 등록 가이드 (사용자 수동) |
| `_workspace/_worker/dashboard_server.py` | FastAPI localhost 워커 |
| `_workspace/_worker/static/` | 정적 프론트엔드 (`/ui/` 마운트) |
| `_workspace/projects.json` | 대시보드 멀티 프로젝트 레지스트리 |
| `commands/cm-*.md` | 7개 슬래시 커맨드 |

### 단계적 구현 현황

| 단계 | 내용 | 상태 |
|------|------|------|
| S1 | cm-orchestrator + cm-injector + **session-capture** | 완료 |
| S2 | cm-digester + session-digest + observations.db (단일 진실 스키마) | 완료 |
| S3 | cm-retriever + memory-search | 완료 |
| S4 | cm-compressor + tool-output-compress | 완료 |
| S5 | cm-curator + memory-curate (decay + daily_summary + 주기 트리거) | 완료 |
| S6 | dashboard-render + FastAPI 워커 (멀티 프로젝트 옵션 A) | 완료 |
| S7 | Phase 10 CM 진단 룰 (`_workspace/references/cm-diagnostic-rules.md`) | 완료 |

---

## CM Dashboard 사용법

`_workspace/_worker/dashboard_server.py`(FastAPI + uvicorn 결정적 워커)를 직접 실행해 SQLite + telemetry JSONL + 디렉토리 스캔 결과를 한 화면에서 비교 열람합니다. **LLM 호출 없음**.

### 1. 의존성 설치 (최초 1회)

```powershell
py -3 -m pip install -r _workspace\_worker\requirements.txt
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

각 프로젝트는 자기 `_workspace/_memory/observations/observations.db`를 가져야 하며 (없으면 `/cm-init`로 생성), cross-project SQL JOIN은 발생하지 않습니다.

### 3. 실행

```powershell
py -3 _workspace\_worker\dashboard_server.py
```

기본 바인딩 `127.0.0.1:8765` — 외부 노출 없음. 종료는 Ctrl+C. 백그라운드로 띄우는 가장 간단한 방법은 별도 PowerShell 창에서 위 명령을 그대로 실행해 두는 것입니다.

### 4. 접속

브라우저에서 한 곳만 열면 됩니다:

- **http://127.0.0.1:8765/** — `_workspace/_worker/static/index.html`이 있으면 자동으로 `/ui/`로 redirect되어 정적 프론트엔드가 뜸. 없으면 minimal HTML 인덱스(레지스트리 표 + 엔드포인트 목록)로 fallback.

`/cm-dashboard` 슬래시 커맨드는 워커 상태와 URL을 출력만 하는 결정적 핸들러이며, 워커 자체는 위 방식으로 직접 띄워야 합니다.

### 5. 5개 View

대시보드 워커는 dashboard-render 스킬이 정의한 5개 뷰를 제공합니다:

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
| `503 observations.db missing for project=<name>` | 그 프로젝트에서 `/cm-init` 미실행 또는 `projects.json` 경로 오타 |
| `404 project not found: <name>` | `projects.json`에 해당 name이 없음 |
| 압축 통계가 비어있음 | `<project>/_workspace/_telemetry/*.jsonl`에 `tool_output_captured` 이벤트 미발생 — cm-compressor 트리거 확인 |
| Roadmap 빈 배열 | `CLAUDE.md`에 markdown 표가 없거나 헤더-구분선이 깨짐 (silent fail — 의도된 동작) |
| 포트 8765 충돌 | `dashboard_server.py`의 `port=` 변경 또는 기존 프로세스 종료 |
| 외부 머신에서 접근 안 됨 | **의도된 동작** — `host="0.0.0.0"`로 변경 후 직접 보안 검토 |

### 8. 종료 / 재시작

- 종료: 워커 콘솔에서 `Ctrl+C`
- 재시작 시 캐시 전체 초기화. 코드를 수정했다면 그냥 재시작하면 됨 (auto-reload 미사용)

워커 자체 README: [`_workspace/_worker/README.md`](./_workspace/_worker/README.md).

---

## 트러블슈팅 (CM 시스템 전반)

| 증상 | 해결 |
|------|------|
| 훅이 동작하지 않음 | `py --version` 확인 → settings의 `command`를 `py ...`로 변경 (Microsoft Store 스텁 회피) |
| `/cm-status`가 빈 결과 | `/cm-init` 실행 → 새 세션을 한 번 열어 SessionStart 훅 발동 확인 |
| transcript는 있는데 digest.md가 없음 | SessionEnd 훅이 끝난 후 cm-digester 호출이 실패한 것 — `_workspace/_telemetry/{date}.jsonl`에서 `"fallback":"digester_failed"` 검색 |
| daily_summaries 비어있음 | memory-curate 주기 트리거 미실행 — `/cm-curate`로 강제 실행 |
| Phase 10 자동 알림 누락 | 마지막 `_delta_*.md`/`_rollback/{ts}/` mtime 이후 `harness_invocation` 이벤트 10회 미만 — 정상 |

CM 전용 진단 룰 전체: [`_workspace/references/cm-diagnostic-rules.md`](./_workspace/references/cm-diagnostic-rules.md).

---

## 문서 인덱스

| 문서 | 용도 |
|------|------|
| [`commands/README.md`](./commands/README.md) | Slash command 14종 카탈로그 + 의사결정 트리 |
| [`skills/README.md`](./skills/README.md) | 스킬 디렉토리 인덱스 + references 가이드 |
| [`skills/harness/SKILL.md`](./skills/harness/SKILL.md) | 메타 스킬 정의 (11 Phase 워크플로우) |
| [`_workspace/_hooks/INSTALL.md`](./_workspace/_hooks/INSTALL.md) | 훅 등록 절차 + matcher 주의사항 |
| [`_workspace/_worker/README.md`](./_workspace/_worker/README.md) | 대시보드 워커 명세 (엔드포인트·CORS·캐시) |
| [`CLAUDE.md`](./CLAUDE.md) | Context Manager 하네스 포인터 + 변경 이력 |
| [`_workspace/references/cm-diagnostic-rules.md`](./_workspace/references/cm-diagnostic-rules.md) | Phase 10 CM 전용 drift 진단 룰 |
