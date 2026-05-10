# Harness — Team-Architecture Factory for Claude Code

> 도메인 한 문장을 **에이전트 팀 + 스킬 세트**로 변환하는 메타 스킬.
> A meta-skill that turns a domain description into an agent team and the skills they use.

---

## 무엇인가

`dharness`는 다음 두 부분으로 구성된 단일 저장소입니다:

1. **`harness` plugin** (`plugins/harness/`) — 도메인을 입력 받아 에이전트 3~5명 + 스킬 세트를 자동 생성하는 메타 스킬 팩토리. **외부 프로젝트에 install 가능.**
2. **Context Manager** (root `.claude/` + `worker/`) — dharness *자체*의 진화를 기록·영속화하는 self-host 런타임. 결정적 hooks 3종 + FastAPI 워커 + `/cm-*` 6 슬래시 커맨드 + `memory-search` 1 스킬. PostToolUse가 dharness 작업 단위(skill/agent/hook/command/manifest 변경)를 자동 분류해 누적하고, SessionEnd가 CLAUDE.md "변경 이력" 표 행 draft를 자동 적재한다. **dharness 본 폴더에서만 동작** (외부 install 미지원).

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

CM(Context Manager)은 dharness 본 폴더에서 자동 동작 — `.claude/settings.local.json`이 hooks 3종을 직접 등록하고 있어 별도 install 없이 다음 Claude Code 세션부터 발화합니다. harness 메타 스킬을 dharness 자체에서 호출하려면 1회 install:

```powershell
claude plugin marketplace add C:\Users\user01\awesome-files\dharness
claude plugin install harness@dharness
```

이후 `/cm-status`, `/harness:harness-audit` 등으로 호출.

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
| **Slash command** | `/harness:harness-new`, `/cm-status` 등 결정적 호출 | 사용자가 Phase 범위 직접 지정 | 비용 회피, 트리거 확률 의존 제거 |

**Slash command 카탈로그 (`harness` 7개 + CM 6개 = 13개):**

```
# harness plugin (메타 스킬 팩토리, 외부 install 가능)
/harness:harness-new <도메인>          # Phase 0~8 전체 (신규 구축)
/harness:harness-add-agent <역할>      # Phase 4·5·7·8 (1·2·3 skip)
/harness:harness-add-skill <스킬>      # Phase 6·7·8 (1~5 skip)
/harness:harness-baseline              # Phase 1·2 재실행 + drift 분석
/harness:harness-audit                 # 정합성 감사 (read-only)
/harness:harness-evolve <피드백>       # Phase 9 수동 진화
/harness:harness-adapt                 # Phase 10 telemetry drift 점검

# CM (dharness self-host, root .claude/commands/)
/cm-status                              # 메모리 통계 + DB 행 수 (dharness_event/pending draft 포함)
/cm-sessions [--limit N]                # 최근 세션 목록
/cm-dashboard                           # worker 상태 + URL 확인
/cm-reset                               # 메모리 전체 삭제 (확인 필수)
/cm-claudemd-apply <sid>                # SessionEnd가 만든 draft를 CLAUDE.md "변경 이력" 표에 삽입
/cm-claudemd-discard [sid]              # draft 폐기 (인자 없으면 모두)
```

명령어 본문(`.md`)은 harness는 `plugins/harness/commands/`, CM은 `.claude/commands/`에 보관.

---

## 프로젝트 구조

```
.
├── .claude-plugin/
│   └── marketplace.json   # harness plugin 단일 카탈로그
├── .claude/                  # CM (dharness self-host)
│   ├── hooks/                # SessionStart/PostToolUse/SessionEnd + _schema.py + cm_commands.py
│   ├── skills/memory-search/ # on-demand 메모리 검색 (LLM-time)
│   ├── commands/             # cm-* 4개
│   └── settings.local.json   # hooks 등록 (gitignore — 사용자 로컬)
├── plugins/
│   └── harness/              # PLUGIN — 메타 스킬 팩토리
│       ├── .claude-plugin/plugin.json
│       ├── skills/harness/   # SKILL.md + references/
│       └── commands/         # harness-* 7개
├── worker/                   # CM 대시보드 (FastAPI, dharness self-host)
│   ├── dashboard_server.py
│   ├── requirements.txt
│   └── static/               # 정적 프론트엔드 (`/ui/`)
├── _workspace/               # DATA — CM 런타임 산출물
│   ├── _telemetry/           # 라이프사이클 이벤트 append-only JSONL
│   ├── _memory/              # CM 런타임 메모리 (sessions/clusters/observations.db, dharness_event 포함)
│   ├── _tool_outputs/        # PostToolUse 10KB 초과 원본 보존
│   └── _drafts/              # SessionEnd가 적재한 CLAUDE.md "변경 이력" 표 행 draft (apply/discard 게이트)
└── CLAUDE.md                 # 하네스 포인터 + 변경 이력
```

**핵심 원칙:** `plugins/harness/` = 외부 install 대상 (read-only when installed). `.claude/` + `worker/` = dharness self-host CM (외부 install 미지원). `_workspace/` = dharness 데이터.

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

`harness` plugin만 외부 install 대상입니다. CM은 dharness 본 폴더 한정 self-host로, 외부 프로젝트로 옮기려면 `.claude/`와 `worker/`를 수동 복사해야 합니다 (지원 범위 외).

### 1) marketplace 등록 + 설치

```powershell
claude plugin marketplace add gimangdoo/dharness
claude plugin install harness@dharness
```

### 2) 로컬 개발용 (marketplace 거치지 않음)

```powershell
claude --plugin-dir C:\path\to\dharness\plugins\harness
```

### 3) 설치되면

`/harness:harness-new`, `/harness:harness-add-agent` 등 7개 슬래시 커맨드. 사용자 프로젝트의 `.claude/agents/`·`.claude/skills/`·`CLAUDE.md`에 산출물 생성 (Phase 0~8).

### 도입 후 권한 경계

`harness` plugin은 사용자 프로젝트의 `.claude/commands/`에 **아무것도 생성하지 않습니다** (read-only invariant). harness 메타 스킬이 만드는 산출물은 사용자 프로젝트의 `.claude/agents/`·`.claude/skills/`·`CLAUDE.md`에만 떨어집니다.

---

## Context Manager (dharness self-host — 결정적 모델)

CM은 **LLM 호출 없는 결정적 데이터 파이프라인**으로 동작합니다. 캡처는 hooks가, 집계/조회는 워커가 담당합니다. 메모리 검색만 LLM이 on-demand로 호출 가능 (`memory-search` 스킬).

### 결정적 산출물

| 위치 | 역할 |
|------|------|
| `.claude/hooks/_schema.py` | DDL 단일 진실 원천 (4 테이블 + FTS5 + observations에 category/artifact_kind/phase 컬럼) + REPO_ROOT 결정적 계산 + `classify_dharness_event()` 도메인 분류기 (단계 B) + `ensure_migrations()` ALTER 마이그레이션 |
| `.claude/hooks/session_start.py` | SessionStart: ID 발급, dangling 세션 finalize, **5 블록 의미적 inject (직전 N=3 세션 dharness_event + 미적용 draft + git status --short + daily_summary, 토큰 budget 2000자)** |
| `.claude/hooks/post_tool_use.py` | PostToolUse: raw.jsonl append + 10KB 초과 시 `_tool_outputs/`에 원본 보존 + **dharness 도메인 분류기 호출 후 매칭 시 `observations.dharness_event`로 자동 INSERT** |
| `.claude/hooks/session_end.py` | SessionEnd: transcript 평탄화, sessions UPDATE + **이번 세션 dharness_event를 모아 CLAUDE.md "변경 이력" 표 행 draft를 `_workspace/_drafts/{date}_{sid}.md`에 자동 적재** |
| `.claude/hooks/cm_commands.py` | `/cm-*` 결정적 커맨드 핸들러 (status/sessions/dashboard/reset/**claudemd-list/claudemd-apply/claudemd-discard**) |
| `worker/dashboard_server.py` | FastAPI localhost 워커 (단일 프로젝트) |
| `worker/static/` | 정적 프론트엔드 (`/ui/` 마운트) |
| `.claude/skills/memory-search/SKILL.md` | dharness 진화 이력 자연어 검색 — **5 source(observations_fts + dharness_event 필터 + CLAUDE.md "변경 이력" 표 + git log + clusters/skill 본문) 3-tool progressive disclosure** |

### 동작 흐름

```
SessionStart hook
  → session_id 발급 + DB 부트스트랩 + ensure_migrations (ALTER 안전망)
  → 직전 dangling 세션 finalize
  → 5 블록 deterministic carry-over를 additionalContext로 inject (≤ 2000자)
      ① session_id
      ② 직전 N=3 세션의 dharness_event category 카운트
      ③ 미적용 CLAUDE.md draft 목록 (있으면)
      ④ git status --short (uncommitted/unstaged)
      ⑤ 최신 daily_summary 600자 cap (있으면)

PostToolUse hook
  → raw.jsonl에 메타 append
  → output > 10KB이면 _tool_outputs/{sid}/에 원본 보존
  → tool_input 분류 (Edit/Write/MultiEdit/Bash git) → 매칭 시
      observations 테이블에 section='dharness_event' INSERT
      (category/artifact_kind/content/tags) — LLM 호출 없음

SessionEnd hook
  → transcript.md 평탄화
  → sessions.ended_at / duration_min / tools_used UPDATE
  → 이번 세션 dharness_event 집계 → CLAUDE.md "변경 이력" 표 행 draft를
      _workspace/_drafts/{date}_{sid}.md에 markdown row + 본문으로 자동 적재
      (이벤트 0건이면 skip)

다음 세션에서 사용자 명시 게이트:
  → /cm-claudemd-apply <sid>     CLAUDE.md 표에 draft row 삽입 + applied/로 이동
  → /cm-claudemd-discard [sid]   draft 폐기 → discarded/로 이동
```

> **현재 상태:** PostToolUse → SessionEnd → SessionStart inject → `/cm-claudemd-apply` 게이트의 자기 dogfooding 회로는 단계 D에서 완성됐습니다. *transcript → digest LLM 요약 → daily_summary 자동 upsert* 잡은 여전히 후속 작업(Tier 3B, manual LLM trigger only)으로 미통합 — 기존 daily_summary 데이터는 조회·검색·인젝트 모두 정상이나 새 daily_summary 자동 생성은 사용자 결정 대기 중입니다.

---

## CLAUDE.md 변경 이력 자동 회로

dharness의 진화는 [`CLAUDE.md`](./CLAUDE.md) "변경 이력" 표에 사람이 읽는 행으로 기록됩니다. 단계 D 이후 이 표 행은 **자동으로 draft 적재되고, 사용자가 명시 게이트로 적용**합니다.

### 회로 4 단계

1. **PostToolUse** — Edit/Write/MultiEdit/Bash(git*) 호출마다 file path 또는 git subcommand를 분류해 `observations.dharness_event`에 INSERT (단계 B)
2. **SessionEnd** — 이번 세션의 dharness_event를 집계해 markdown 표 행 draft + 본문(카테고리 카운트 / 변경 대상 / 메타)을 `_workspace/_drafts/{date}_{sid}.md`에 작성 (이벤트 0건이면 skip)
3. **다음 SessionStart** — 미적용 draft가 있으면 `additionalContext`에 한 블록으로 inject:
   ```
   [CM] 미적용 CLAUDE.md draft 1건 — apply: /cm-claudemd-apply <sid>, discard: /cm-claudemd-discard
     · 2026-05-10 abc123
   ```
4. **사용자 명시 게이트** — `/cm-claudemd-apply <sid>` 또는 `/cm-claudemd-discard [sid]`

### 사용 예시

```text
# pending 목록 보기
/cm-status                              # "CLAUDE.md draft: 1 pending" 표시
py .claude/hooks/cm_commands.py claudemd-list

# draft 본문 미리 보기 (apply 전 권장)
cat _workspace/_drafts/2026-05-10_abc123.md

# CLAUDE.md "변경 이력" 표 마지막 row 다음에 삽입
/cm-claudemd-apply abc123

# 또는 폐기 (discarded/ 보관)
/cm-claudemd-discard abc123             # 단일 sid
/cm-claudemd-discard                    # 모든 pending
```

### 사유 컬럼은 placeholder

draft가 자동 생성하는 행의 "사유" 컬럼은 `(apply 전 작성 — 사유/맥락)` placeholder로 채워집니다. apply 후 CLAUDE.md를 직접 편집해 사유를 채우는 것이 의도된 manual gate — *왜 변경했는가*는 deterministic으로 추출 불가능하므로 사람이 보강해야 합니다.

### 적재 디렉토리

| 위치 | 용도 |
|------|------|
| `_workspace/_drafts/{date}_{sid}.md` | pending — 다음 SessionStart가 inject |
| `_workspace/_drafts/applied/` | apply 후 보관 (CLAUDE.md에 행 추가됨) |
| `_workspace/_drafts/discarded/` | discard 후 보관 (영구 삭제는 수동 또는 `/cm-reset`) |

`.gitignore`에 등록되어 commit에 포함되지 않습니다 (사용자 로컬 데이터).

---

## CM Dashboard 사용법

`worker/dashboard_server.py`(FastAPI + uvicorn 결정적 워커)를 직접 실행해 SQLite + telemetry JSONL + 디렉토리 스캔 결과를 한 화면에서 열람합니다. **LLM 호출 없음 · dharness 단일 프로젝트.**

### 1. 의존성 설치 (최초 1회)

```powershell
py -3 -m pip install -r worker\requirements.txt
```

`fastapi >= 0.110`, `uvicorn >= 0.27` 두 개만 필요합니다.

### 2. 실행

```powershell
py -3 worker\dashboard_server.py
```

기본 바인딩 `127.0.0.1:8765` — 외부 노출 없음. 종료는 Ctrl+C. 백그라운드로 띄우는 가장 간단한 방법은 별도 PowerShell 창에서 위 명령을 그대로 실행해 두는 것입니다.

### 3. 접속

브라우저에서 한 곳만 열면 됩니다:

- **http://127.0.0.1:8765/** — `worker/static/index.html`이 있으면 자동으로 `/ui/`로 redirect되어 정적 프론트엔드가 뜸. 없으면 minimal HTML 인덱스(엔드포인트 목록)로 fallback.

`/cm-dashboard` 슬래시 커맨드는 워커 상태와 URL을 출력만 하는 결정적 핸들러이며, 워커 자체는 위 방식으로 직접 띄워야 합니다.

### 4. 5개 View

| View | 엔드포인트 | 데이터 소스 | 의도 |
|------|-----------|-----------|------|
| 1. 세션 | `/api/sessions` | `sessions` + `observations` | 최근 30 세션, pending/warn count, digest 보유 여부 |
| 2. 클러스터 | `/api/clusters` | `clusters` | confidence desc, 마지막 접근 후 경과일 |
| 3. 압축 통계 | `/api/compression` | telemetry JSONL | 도구별 raw/compressed 평균, 비율 (최근 30일) |
| 4. Pending | `/api/pending` | `observations.completed=0` | 미완료 do 항목 |
| 5. Inventory + Roadmap | `/api/inventory`, `/api/roadmap` | `.claude/`·`plugins/harness/`·`settings*.json`·`CLAUDE.md` | skills/agents/commands/hooks/mcp 산출물 + CLAUDE.md 표 추출 |

추가:
- `/api/rollup` — dharness rollup 통계 (sessions/clusters/pending/total_minutes)
- `/api/tool-timeline` — 일자별 도구 호출 (스택 차트용)

### 5. CORS / 캐시 / 보안

- **CORS:** `http://127.0.0.1` / `http://localhost`(any port) GET only — Vite 등 별도 dev server가 직접 API를 호출 가능
- **캐시:** 메모리 내 5분 TTL. 무효화 anchor = `observations.db` mtime + telemetry `*.jsonl` 최신 mtime + `CLAUDE.md` mtime + `.claude/settings.json` mtime. 4개 중 하나라도 바뀌면 다음 요청에서 재계산
- **보안:** 외부 노출 없음 (`host="127.0.0.1"`). 외부 접근이 필요하면 코드의 `host="0.0.0.0"`으로 변경 + 자체 보안 검토 필수

### 6. 트러블슈팅

| 증상 | 원인 / 해결 |
|------|-----------|
| `ModuleNotFoundError: No module named 'fastapi'` | 의존성 미설치 — §1 다시 실행 |
| `503 observations.db missing — start a Claude Code session to bootstrap` | 새 Claude Code 세션을 한 번 열면 SessionStart 훅이 자동 생성 |
| 압축 통계가 비어있음 | `_workspace/_telemetry/*.jsonl`에 `tool_output_captured` 이벤트 미발생 — `post_tool_use.py` 훅 등록 확인 |
| Roadmap 빈 배열 | `CLAUDE.md`에 markdown 표가 없거나 헤더-구분선이 깨짐 (silent fail — 의도된 동작) |
| 포트 8765 충돌 | `dashboard_server.py`의 `port=` 변경 또는 기존 프로세스 종료 |
| 외부 머신에서 접근 안 됨 | **의도된 동작** — `host="0.0.0.0"`로 변경 후 직접 보안 검토 |

### 7. 종료 / 재시작

- 종료: 워커 콘솔에서 `Ctrl+C`
- 재시작 시 캐시 전체 초기화. 코드를 수정했다면 그냥 재시작하면 됨 (auto-reload 미사용)

워커 자체 README: [`worker/README.md`](./worker/README.md).

---

## 트러블슈팅 (CM 시스템 전반)

| 증상 | 해결 |
|------|------|
| 훅이 동작하지 않음 | `py --version` 확인 → `.claude/settings.local.json`의 `command`를 `py ...`로 변경 (Microsoft Store 스텁 회피) |
| `/cm-status`가 빈 결과 | 새 Claude Code 세션을 한 번 열어 SessionStart 훅 발동 확인 |
| transcript는 있는데 digest.md가 없음 | transcript → digest LLM 잡은 Tier 3B 미통합 (manual trigger only) |
| daily_summaries 새 행이 안 생김 | 동상 — 기존 행 조회/인젝트는 정상 |
| `/cm-claudemd-apply`가 "변경 이력 표를 찾지 못함" | CLAUDE.md의 "변경 이력" heading 또는 strong 직후에 markdown 표가 있어야 — 헤더-구분선 깨졌는지 확인 |
| SessionStart inject가 800자에서 잘림 | budget 2000자로 단계 C에서 확장됨 — `.claude/hooks/session_start.py:INJECT_BUDGET` 기본값 |

---

## 문서 인덱스

| 문서 | 용도 |
|------|------|
| [`plugins/harness/skills/harness/SKILL.md`](./plugins/harness/skills/harness/SKILL.md) | 메타 스킬 정의 (11 Phase 워크플로우) |
| [`worker/README.md`](./worker/README.md) | 대시보드 워커 명세 (엔드포인트·CORS·캐시) |
| [`.claude/skills/memory-search/SKILL.md`](./.claude/skills/memory-search/SKILL.md) | 과거 메모리 LLM 검색 규칙 (3-tool progressive disclosure) |
| [`CLAUDE.md`](./CLAUDE.md) | Context Manager 하네스 포인터 + 변경 이력 |
