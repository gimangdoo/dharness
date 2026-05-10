# Harness — Team-Architecture Factory for Claude Code

> 도메인 한 문장을 **에이전트 팀 + 스킬 세트**로 변환하는 메타 스킬.
> A meta-skill that turns a domain description into an agent team and the skills they use.

---

## 무엇인가

`dharness`는 다음 두 부분으로 구성된 단일 저장소입니다:

1. **`harness` plugin** (`plugins/harness/`) — 도메인을 입력 받아 에이전트 3~5명 + 스킬 세트를 자동 생성하는 메타 스킬 팩토리. **외부 프로젝트에 install 가능.**
2. **Context Manager** (root `.claude/`) — dharness *자체*의 진화를 기록·영속화하는 self-host 런타임. 결정적 hooks 3종 + `/cm-*` 5 슬래시 커맨드 + `memory-search` 1 스킬. PostToolUse가 dharness 작업 단위(skill/agent/hook/command/manifest 변경)를 자동 분류해 누적하고, SessionEnd가 CLAUDE.md "변경 이력" 표 행 draft를 자동 적재한다. **dharness 본 폴더에서만 동작** (외부 install 미지원).

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

이후 `/cm-status`, `/harness:harness-audit` 등으로 호출. 데이터 조회는 `/cm-status`·`/cm-sessions` 또는 `_workspace/_memory/observations/observations.db`를 SQLite 클라이언트로 직접 열람.

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

**Slash command 카탈로그 (`harness` 9개 + CM 5개 = 14개):**

```
# harness plugin (메타 스킬 팩토리, 외부 install 가능)
/harness:harness-new <도메인>          # Phase 0~8 전체 (신규 구축)
/harness:harness-add-agent <역할>      # Phase 4·5·7·8 (1·2·3 skip)
/harness:harness-add-skill <스킬>      # Phase 6·7·8 (1~5 skip)
/harness:harness-baseline              # Phase 1·2 재실행 + drift 분석
/harness:harness-audit                 # 정합성 감사 (read-only)
/harness:harness-evolve <피드백>       # Phase 9 수동 진화
/harness:harness-adapt                 # Phase 10 telemetry drift 점검
/harness:harness-mcp-adopt <사유>      # 런타임 시점 신규 MCP 채택 (§10 dynamic adoption)
/harness:harness-mcp-status            # MCP 상태 진단 — 인벤토리·매트릭스·정합·trigger 자동 감지 (read-only)

# CM (dharness self-host, root .claude/commands/)
/cm-status                              # 메모리 통계 + DB 행 수 (dharness_event/pending draft 포함)
/cm-sessions [--limit N]                # 최근 세션 목록
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
│   ├── commands/             # cm-* 5개
│   └── settings.local.json   # hooks 등록 (gitignore — 사용자 로컬)
├── plugins/
│   └── harness/              # PLUGIN — 메타 스킬 팩토리
│       ├── .claude-plugin/plugin.json
│       ├── skills/harness/   # SKILL.md + references/
│       └── commands/         # harness-* 9개
├── _workspace/               # DATA — CM 런타임 산출물
│   ├── _telemetry/           # 라이프사이클 이벤트 append-only JSONL
│   ├── _memory/              # CM 런타임 메모리 (sessions/clusters/observations.db, dharness_event 포함)
│   ├── _tool_outputs/        # PostToolUse 10KB 초과 원본 보존
│   └── _drafts/              # SessionEnd가 적재한 CLAUDE.md "변경 이력" 표 행 draft (apply/discard 게이트)
└── CLAUDE.md                 # 하네스 포인터 + 변경 이력
```

**핵심 원칙:** `plugins/harness/` = 외부 install 대상 (read-only when installed). `.claude/` = dharness self-host CM (외부 install 미지원). `_workspace/` = dharness 데이터.

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

`harness` plugin만 외부 install 대상입니다. CM은 dharness 본 폴더 한정 self-host로, 외부 프로젝트로 옮기려면 `.claude/`를 수동 복사해야 합니다 (지원 범위 외).

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

CM은 **LLM 호출 없는 결정적 데이터 파이프라인**으로 동작합니다. 캡처·집계 모두 hooks가 담당하며, 사용자 측 조회는 `/cm-status`·`/cm-sessions` 또는 SQLite 직접 열람으로 한다. 메모리 검색만 LLM이 on-demand로 호출 가능 (`memory-search` 스킬).

### 결정적 산출물

| 위치 | 역할 |
|------|------|
| `.claude/hooks/_schema.py` | DDL 단일 진실 원천 (4 테이블 + FTS5 + observations에 category/artifact_kind/phase 컬럼) + REPO_ROOT 결정적 계산 + `classify_dharness_event()` 도메인 분류기 (단계 B) + `ensure_migrations()` ALTER 마이그레이션 |
| `.claude/hooks/session_start.py` | SessionStart: ID 발급, dangling 세션 finalize, **4 블록 의미적 inject (session_id + 직전 N=3 세션 dharness_event + 미적용 draft + git status --short, 토큰 budget 2000자)** |
| `.claude/hooks/post_tool_use.py` | PostToolUse: raw.jsonl append + 10KB 초과 시 `_tool_outputs/`에 원본 보존 + **dharness 도메인 분류기 호출 후 매칭 시 `observations.dharness_event`로 자동 INSERT** |
| `.claude/hooks/session_end.py` | SessionEnd: transcript 평탄화, sessions UPDATE + **이번 세션 dharness_event를 모아 CLAUDE.md "변경 이력" 표 행 draft를 `_workspace/_drafts/{date}_{sid}.md`에 자동 적재** |
| `.claude/hooks/cm_commands.py` | `/cm-*` 결정적 커맨드 핸들러 (status/sessions/reset/**claudemd-list/claudemd-apply/claudemd-discard**) |
| `.claude/skills/memory-search/SKILL.md` | dharness 진화 이력 자연어 검색 — **5 source(observations_fts + dharness_event 필터 + CLAUDE.md "변경 이력" 표 + git log + clusters/skill 본문) 3-tool progressive disclosure** |

### 동작 흐름

```
SessionStart hook
  → session_id 발급 + DB 부트스트랩 + ensure_migrations (ALTER 안전망)
  → 직전 dangling 세션 finalize
  → 4 블록 deterministic carry-over를 additionalContext로 inject (≤ 2000자)
      ① session_id
      ② 직전 N=3 세션의 dharness_event category 카운트
      ③ 미적용 CLAUDE.md draft 목록 (있으면)
      ④ git status --short (uncommitted/unstaged)

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

> **현재 상태:** PostToolUse → SessionEnd → SessionStart inject → `/cm-claudemd-apply` 게이트의 자기 dogfooding 회로는 단계 D에서 완성됐습니다. `daily_summaries` 테이블은 historic data 보존용으로 schema만 유지하며, SessionStart inject·자동 row 생성은 폐기됐습니다 (단계 A→E 결정적 모델 일관성). 자연어 회고는 `memory-search` 스킬로 `daily_summaries` 기존 행을 여전히 조회 가능합니다.

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

## CM 데이터 직접 조회

대시보드 워커는 폐기됨 — sqlite 클라이언트로 직접 열거나 `/cm-*` 커맨드로 충분합니다.

```powershell
# 통계 한 줄 — pending draft / dharness_event 카운트 포함
py .claude/hooks/cm_commands.py status

# 최근 세션 30개
py .claude/hooks/cm_commands.py sessions --limit 30

# DB 직접 열기 (예: sqlite3 CLI)
sqlite3 _workspace/_memory/observations/observations.db
sqlite> SELECT category, COUNT(*) FROM observations
        WHERE section='dharness_event' GROUP BY category ORDER BY 2 DESC;

# 자연어 회고 — Claude Code 안에서
"이전에 단계 D에서 뭐 했어?"   # → memory-search 스킬이 5 source 조회
```

라이프사이클 telemetry (`tool_output_captured` 등)는 `_workspace/_telemetry/*.jsonl`을 직접 grep:

```powershell
findstr /C:"tool_output_captured" _workspace\_telemetry\*.jsonl
```

---

## 최근 단순화 (2026-05-10) — dashboard 폐기 + 결정적 모델 정합

이 세션에서 CM이 "dharness 자체의 진화 기록자"로 수렴했습니다. 4축으로 정리:

### 1. Dashboard 폐기

| 삭제 | 영향 |
|------|------|
| `worker/` 디렉토리 전체 (dashboard\_server.py / static/ / requirements.txt / README.md) | FastAPI/uvicorn 외부 의존성 0. CM이 **표준 라이브러리만으로 작동** |
| `.claude/commands/cm-dashboard.md` + `cm_commands.py:cmd_dashboard` + `urllib` import | slash 카탈로그 6개 → 5개 (`/cm-dashboard` 폐기) |
| `_schema.py`의 4 분류 룰 (`cm_worker_edit`/`cm_worker_static_edit`/`cm_doc_edit`/`cm_deps_edit`) | 새 dharness\_event 적재 시 worker 경로 매칭 안 됨. 기존 데이터는 historic으로 보존 |

데이터 조회는 `/cm-status`·`/cm-sessions` + sqlite CLI 직접 열람으로 충분. Inventory/Roadmap/Timeline View는 *측정된 사용처 없음*으로 비용 회수 무망 — 단계 A→E의 결정적 모델 정신과 정합.

### 2. In-session 토큰 절약 가이드라인 (CLAUDE.md)

```
CLAUDE.md > "## In-session 컨텍스트 가드라인" 섹션 신설
```

5 행동 룰: (a) cross-cutting 조사 → `Agent` 위임 / (b) 큰 디렉토리 → `Glob`/`Grep` 우선 / (c) commit history → `git log --oneline` + `git show` / (d) diff → `git diff --stat` 우선 / (e) 같은 파일 재read 자제. **LLM 행동 가이드일 뿐 hook이 강제하지 않음** — PostToolUse는 사후 캡처라 in-session 토큰 절약 불가. 진짜 lever는 워크플로우 선택.

### 3. SessionStart inject 5블록 → 4블록

| 변경 | 위치 |
|------|------|
| `fetch_latest_daily_summary` 함수 / `DAILY_SUMMARY_MAX_CHARS` 상수 / ⑤ daily\_summary 블록 제거 | `.claude/hooks/session_start.py` |
| `format_inject` `summary` 파라미터 삭제 | 동상 |
| `daily_summaries` 테이블 schema는 보존 | `_schema.py` (historic data 무손실) |
| memory-search §2c와 source #5에 `clusters` / `daily_summaries` "신규 row 생성 안 됨 — historic data 조회 전용" 인용블럭 | `.claude/skills/memory-search/SKILL.md` |

**Tier 3B(LLM digest job) 정식 무산** — daily\_summary 자동 생성 인프라 완전 폐기. SessionStart inject ⑤ 블록이 stale 1건만 영구 cite하던 dead weight 제거.

### 4. `/cm-claudemd-apply` 사유 인자 추가

```bash
/cm-claudemd-apply <sid>                          # 기존: placeholder 유지 (수동 편집 필요)
/cm-claudemd-apply <sid> Phase 9 e2e 검증 후 적용  # 신규: 사유 즉시 치환
```

| 변경 | 비고 |
|------|------|
| `_schema.py`에 `DRAFT_REASON_PLACEHOLDER` 상수 단일 출처 | session\_end.py / cm\_commands.py가 import — sync drift 방지 |
| `cmd_claudemd_apply(session_id, reason_parts)` + `_sanitize_reason()` 헬퍼 | 공백 join / `\r\n` → 공백 / `\|` escape / 빈 문자열 fallback |
| argparse `reason` 인자 `nargs="*"` (0 또는 N개) | backward compat — 인자 0개는 기존 동작 |
| `cm-claudemd-apply.md` UX 본문 갱신 | `argument-hint: <session_id> [사유...]`, 사용 예시 + 안전 처리 표 |

**Silent failure 해소** — placeholder가 그대로 CLAUDE.md에 들어가고 사용자가 잊으면 표 row가 무의미해지던 문제. 이제 `/cm-claudemd-apply` 한 줄로 끝.

### 5. CLAUDE.md aging banner

```
변경 이력 표 위에 인용블럭 1개 — "현재 아키텍처는 단계 A 이후 단순화된 형태",
폐기 산출물 명시 (cm-harness plugin / Phase 10 baseline / cm-orchestrator /
cm-curator / cm-digester / dashboard worker / daily_summary 자동 생성 /
tool-output-compress), 신규 사용자에게 README/SKILL.md 단일 출처 안내
```

→ 변경 이력 33+ rows의 폐기 DNA 언급이 신규 사용자 onboarding 노이즈가 되는 문제 차단.

### 결과

- **외부 의존성**: FastAPI/uvicorn 사라짐 — CM이 standard library only
- **slash 명령 카탈로그**: 14개 (harness 9 + CM 5)
- **SessionStart inject**: 4 블록 deterministic carry-over (≤ 2000자)
- **draft → CLAUDE.md 회로**: silent failure 해소 (사유 인자 즉시 치환 가능)
- **dharness 본체**: `plugins/harness/` 미변경 — read-only invariant 보존

상세는 [`CLAUDE.md`](./CLAUDE.md) 변경 이력 표의 2026-05-10 마지막 3 rows 참조.

---

## 트러블슈팅 (CM 시스템 전반)

| 증상 | 해결 |
|------|------|
| 훅이 동작하지 않음 | `py --version` 확인 → `.claude/settings.local.json`의 `command`를 `py ...`로 변경 (Microsoft Store 스텁 회피) |
| `/cm-status`가 빈 결과 | 새 Claude Code 세션을 한 번 열어 SessionStart 훅 발동 확인 |
| transcript는 있는데 digest가 없음 | digest 자동 생성은 도입되지 않음 — `memory-search` 스킬이 transcript.md / git log / observations FTS를 직접 fallback 조회 |
| daily_summaries 새 행이 안 생김 | **의도된 동작** — Tier 3B 무산 후 schema만 유지. SessionStart inject 블록도 함께 폐기 |
| `/cm-claudemd-apply`가 "변경 이력 표를 찾지 못함" | CLAUDE.md의 "변경 이력" heading 또는 strong 직후에 markdown 표가 있어야 — 헤더-구분선 깨졌는지 확인 |
| SessionStart inject가 800자에서 잘림 | budget 2000자로 단계 C에서 확장됨 — `.claude/hooks/session_start.py:INJECT_BUDGET` 기본값 |

---

## 문서 인덱스

| 문서 | 용도 |
|------|------|
| [`plugins/harness/skills/harness/SKILL.md`](./plugins/harness/skills/harness/SKILL.md) | 메타 스킬 정의 (11 Phase 워크플로우) |
| [`.claude/skills/memory-search/SKILL.md`](./.claude/skills/memory-search/SKILL.md) | 과거 메모리 LLM 검색 규칙 (3-tool progressive disclosure) |
| [`CLAUDE.md`](./CLAUDE.md) | Context Manager 하네스 포인터 + 변경 이력 + In-session 가드라인 |
