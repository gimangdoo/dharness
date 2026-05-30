# Context Manager (dharness self-host)

> [README](../README.md)로 돌아가기

CM은 dharness *자체*의 진화를 기록·영속화하는 self-host 런타임이다. **LLM 호출 없는 결정적 데이터 파이프라인**으로 동작한다 — 캡처·집계 모두 hooks가 담당하며, 사용자 측 조회는 `/cm-status`·`/cm-sessions` 또는 SQLite 직접 열람으로 한다. 메모리 검색만 LLM이 on-demand로 호출 가능 (`memory-search` 스킬). **dharness 본 폴더에서만 동작** (외부 install 미지원).

---

## 설치 — hooks 등록

CM은 dharness 본 폴더에서 자동 동작 — `.claude/settings.local.json`이 hooks 3종을 직접 등록하면 별도 install 없이 다음 Claude Code 세션부터 발화한다. **본 파일은 `.gitignore` 대상(user-local)이라 clone 직후엔 부재** — OS별 template:

**Windows** (`py` 런처 — Microsoft Store `python` 스텁 회피):

```json
{
  "hooks": {
    "SessionStart": [
      { "matcher": "*", "hooks": [{ "type": "command", "command": "py \"$CLAUDE_PROJECT_DIR/.claude/hooks/session_start.py\"" }] }
    ],
    "PostToolUse": [
      { "matcher": "*", "hooks": [{ "type": "command", "command": "py \"$CLAUDE_PROJECT_DIR/.claude/hooks/post_tool_use.py\"" }] }
    ],
    "SessionEnd": [
      { "matcher": "*", "hooks": [{ "type": "command", "command": "py \"$CLAUDE_PROJECT_DIR/.claude/hooks/session_end.py\"" }] }
    ]
  }
}
```

**Linux/macOS** (`python3` — `py` 런처 미존재):

```json
{
  "hooks": {
    "SessionStart": [
      { "matcher": "*", "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/session_start.py\"" }] }
    ],
    "PostToolUse": [
      { "matcher": "*", "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/post_tool_use.py\"" }] }
    ],
    "SessionEnd": [
      { "matcher": "*", "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/session_end.py\"" }] }
    ]
  }
}
```

> 임계값 변경 시 각 hook 객체에 `"env": { "CM_ADAPT_THRESHOLD_INVOCATIONS": "10", "CM_ADAPT_THRESHOLD_FAILURES": "2" }` 필드 추가. 작성 직후 Claude Code 세션을 한 번 재시작하면 SessionStart 훅이 발화 — `/cm-status` 출력의 `observations: N (dharness_event N)`로 확인 가능. POSIX에선 hook 파일에 `chmod +x` 후 shebang(`#!/usr/bin/env python3`)으로 직접 실행도 가능 (interpreter 명시는 위 template 권장).

---

## 결정적 산출물

| 위치 | 역할 |
|------|------|
| `.claude/hooks/_schema.py` | DDL 단일 진실 원천 (2 테이블 + FTS5 + observations에 category/artifact_kind 컬럼 — R1 2026-05-14 dead schema 정리) + REPO_ROOT 결정적 계산 + `classify_dharness_event()` 도메인 분류기 + `ensure_migrations()` v0→v2 마이그레이션 (ADD COLUMN + DROP COLUMN/TABLE) |
| `.claude/hooks/session_start.py` | SessionStart: ID 발급, dangling 세션 finalize, **4 블록 의미적 inject (session_id + 직전 N=3 세션 dharness_event + 미적용 draft + git status --short, 토큰 budget 2000자)** |
| `.claude/hooks/post_tool_use.py` | PostToolUse: raw.jsonl append + 10KB 초과 시 `_tool_outputs/`에 원본 보존 + **dharness 도메인 분류기 호출 후 매칭 시 `observations.dharness_event`로 자동 INSERT** |
| `.claude/hooks/session_end.py` | SessionEnd: transcript 평탄화, sessions UPDATE + **이번 세션 dharness_event를 모아 CHANGELOG.md "변경 이력" 표 행 draft를 `_workspace/_drafts/{date}_{sid}.md`에 자동 적재** |
| `.claude/hooks/cm_commands.py` | `/cm-*` 결정적 커맨드 핸들러 (status/sessions/reset/claudemd-list/claudemd-apply/claudemd-discard) |
| `.claude/skills/memory-search/SKILL.md` | dharness 진화 이력 자연어 검색 — **4 source(observations_fts + dharness_event 필터 + CHANGELOG.md "변경 이력" 표 + git log) 3-tool progressive disclosure** (R1 2026-05-14: 5번째 clusters/daily_summaries source 제거) |

## 동작 흐름

```
SessionStart hook
  → session_id 발급 + DB 부트스트랩 + ensure_migrations (ALTER 안전망)
  → 직전 dangling 세션 finalize
  → 4 블록 deterministic carry-over를 additionalContext로 inject (≤ 2000자)
      ① session_id
      ② 직전 N=3 세션의 dharness_event category 카운트
      ③ 미적용 CHANGELOG.md draft 목록 (있으면)
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
  → 이번 세션 dharness_event 집계 → CHANGELOG.md "변경 이력" 표 행 draft를
      _workspace/_drafts/{date}_{sid}.md에 markdown row + 본문으로 자동 적재
      (이벤트 0건이면 skip)

다음 세션에서 사용자 명시 게이트:
  → /cm-claudemd-apply <sid> [사유...]   CHANGELOG.md 표에 draft row 삽입 + applied/로 이동
  → /cm-claudemd-discard [sid]           draft 폐기 → discarded/로 이동
```

---

## CHANGELOG.md 변경 이력 자동 회로

dharness의 진화는 [`CHANGELOG.md`](../CHANGELOG.md) "변경 이력" 표에 사람이 읽는 행으로 기록된다. CM이 이 표 행을 **자동으로 draft 적재하고, 사용자가 명시 게이트로 적용**한다.

### 회로 4 단계

1. **PostToolUse** — Edit/Write/MultiEdit/Bash(git*) 호출마다 file path 또는 git subcommand를 분류해 `observations.dharness_event`에 INSERT
2. **SessionEnd** — 이번 세션의 dharness_event를 집계해 markdown 표 행 draft + 본문(카테고리 카운트 / 변경 대상 / 메타)을 `_workspace/_drafts/{date}_{sid}.md`에 작성 (이벤트 0건이면 skip)
3. **다음 SessionStart** — 미적용 draft가 있으면 `additionalContext`에 한 블록으로 inject:
   ```
   [CM] 미적용 CHANGELOG.md draft 1건 — apply: /cm-claudemd-apply <sid>, discard: /cm-claudemd-discard
     · 2026-05-10 abc123
   ```
4. **사용자 명시 게이트** — `/cm-claudemd-apply <sid> [사유...]` 또는 `/cm-claudemd-discard [sid]`

### 사용 예시

```text
# pending 목록 보기
/cm-status                              # "CHANGELOG.md draft: 1 pending" 표시
py .claude/hooks/cm_commands.py claudemd-list

# draft 본문 미리 보기 (apply 전 권장)
cat _workspace/_drafts/2026-05-10_abc123.md

# CHANGELOG.md "변경 이력" 표 마지막 row 다음에 삽입 (사유 즉시 치환)
/cm-claudemd-apply abc123 Phase 9 e2e 검증 후 적용

# 또는 placeholder 그대로 두고 나중 수동 편집
/cm-claudemd-apply abc123

# 폐기 (discarded/ 보관)
/cm-claudemd-discard abc123             # 단일 sid
/cm-claudemd-discard                    # 모든 pending
```

### 사유 컬럼

draft가 자동 생성하는 행의 "사유" 컬럼은 인자 미제공 시 `(apply 전 작성 — 사유/맥락)` placeholder. apply 시 `<사유...>` 인자로 즉시 치환 가능 (공백 join, `|` escape 자동). *왜 변경했는가*는 deterministic으로 추출 불가능하므로 사람이 보강.

### 적재 디렉토리

| 위치 | 용도 |
|------|------|
| `_workspace/_drafts/{date}_{sid}.md` | pending — 다음 SessionStart가 inject |
| `_workspace/_drafts/applied/` | apply 후 보관 (CHANGELOG.md에 행 추가됨) |
| `_workspace/_drafts/discarded/` | discard 후 보관 (영구 삭제는 수동 또는 `/cm-reset`) |

`.gitignore`에 등록되어 commit에 포함되지 않는다 (사용자 로컬 데이터).

---

## CM 데이터 직접 조회

sqlite 클라이언트로 직접 열거나 `/cm-*` 커맨드로 조회.

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
"이전에 단계 D에서 뭐 했어?"   # → memory-search 스킬이 4 source 조회
```

라이프사이클 telemetry (`tool_output_captured` 등)는 `_workspace/_telemetry/*.jsonl`을 직접 grep:

```powershell
findstr /C:"tool_output_captured" _workspace\_telemetry\*.jsonl
```

---

## 트러블슈팅

| 증상 | 해결 |
|------|------|
| 훅이 동작하지 않음 | `py --version` 확인 → `.claude/settings.local.json`의 `command`를 `py ...`로 변경 (Microsoft Store 스텁 회피) |
| `/cm-status`가 빈 결과 | 새 Claude Code 세션을 한 번 열어 SessionStart 훅 발동 확인 |
| transcript는 있는데 digest가 없음 | digest 자동 생성은 도입되지 않음 — `memory-search` 스킬이 transcript.md / git log / observations FTS를 직접 fallback 조회 |
| `/cm-claudemd-apply`가 "변경 이력 표를 찾지 못함" | CHANGELOG.md의 "변경 이력" heading 또는 strong 직후에 markdown 표가 있어야 — 헤더-구분선 깨졌는지 확인 |
| SessionStart inject가 잘림 | budget 2000 char (token 아님, ~2× 추정) — `.claude/hooks/session_start.py:INJECT_CHAR_BUDGET` 기본값 |
