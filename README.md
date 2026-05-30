# Harness — Team-Architecture Factory for Claude Code

> 도메인 한 문장을 **에이전트 팀 + 스킬 세트**로 변환하는 메타 스킬.
> A meta-skill that turns a domain description into an agent team and the skills they use.

---

## 무엇인가 · 무엇이 좋은가

`harness`는 도메인 한 문장(예: "코드 리뷰 자동화")을 입력 받아 그 일을 처리할 **에이전트 3~5명 + 스킬 세트 + CLAUDE.md 가이드라인**을 자동 생성하는 메타 스킬 팩토리다.

단일 프롬프트/단일 에이전트 프레임워크와 다른 점:

| 직접 구성 | harness 사용 |
|---|---|
| 에이전트 역할·경계를 손으로 설계 | 도메인 분석 → 6 팀 패턴 중 자동 선택 |
| 스킬 trigger 중복·누락 직접 점검 | 합성 시 self-critique + 결정적 검증 내장 |
| 변경 때마다 수동 편집 | `/harness:harness-evolve` 한 줄로 add/split/merge |
| 진화 이력 수동 기록 | (dharness 본 폴더) hooks가 자동 캡처·draft 적재 |

**효과:** 한 문장 → 곧바로 쓸 수 있는 협업형 에이전트 팀. 구조 일관성·권한 경계·관측 인프라까지 한 번에.

### 6 팀 아키텍처 패턴

| 패턴 | 적합한 작업 |
|------|----------|
| **Pipeline** | 단계별 순차 흐름 (분석 → 설계 → 검증) |
| **Fan-out / Fan-in** | 병렬 분기 → 결과 통합 (멀티 소스 리서치) |
| **Expert Pool** | 도메인별 전문가 풀에서 동적 선택 (티켓 라우팅) |
| **Producer-Reviewer** | 생성-비판 분리 (코드 작성 + 리뷰) |
| **Supervisor** | 메타 에이전트가 분배·모니터·종합 |
| **Hierarchical Delegation** | 상위 → 하위 위임, 결과 상위 통합 |

> dharness 저장소는 ① 외부 install 가능한 **`harness` plugin**(`plugins/harness/`)과 ② dharness 자체 진화를 기록하는 self-host **Context Manager**(`.claude/` + `_workspace/`) 두 부분으로 이뤄진다. CM은 dharness 본 폴더에서만 동작 — 상세는 [docs/context-manager.md](./docs/context-manager.md).

---

## 빠른 시작

### 1. plugin 설치

```powershell
claude plugin marketplace add gimangdoo/dharness
claude plugin install harness@dharness
```

로컬 개발용 (marketplace 미경유):

```powershell
claude --plugin-dir C:\path\to\dharness\plugins\harness
```

### 2. 새 도메인에 적용

```text
/harness:harness-new 코드 리뷰를 자동화하는 도메인
```

→ 사용자 프로젝트의 `.claude/agents/{name}.md`·`.claude/skills/{name}/SKILL.md`·`CLAUDE.md`에 산출물 생성. 이후엔 자연어로 트리거해 그대로 사용.

> dharness 본 폴더를 clone해 CM까지 쓰려면 hooks 등록이 필요하다 → [docs/context-manager.md "설치"](./docs/context-manager.md#설치--hooks-등록).

---

## 워크플로우 — 언제 무슨 command를 쓰나

프로젝트 진행 흐름과 각 command의 사용 시점.

```
   ┌─ 처음 ─────────────────────────────────────────────────┐
   │  /harness:harness-new <도메인>      팀 신규 구축          │
   │     └ 답이 모호하면 → /harness:harness-grill <step>      │
   └────────────────────────────────────────────────────────┘
                          │  (생성된 에이전트/스킬을 자연어로 사용)
                          ▼
   ┌─ 진행 중 ──────────────────────────────────────────────┐
   │  신규 기능 추가  → /harness:harness-feature <기능>       │
   │  구조 변경 필요  → /harness:harness-evolve <피드백>      │
   │  현황·drift 점검 → /harness:harness-status [--deep --mcp]│
   │  결정적 검증     → /harness:harness-validate            │
   └────────────────────────────────────────────────────────┘
                          │
                          ▼
   ┌─ 장기 운영 ────────────────────────────────────────────┐
   │  telemetry drift  → /harness:harness-adapt              │
   │  plugin upgrade 후 → doctrine refit (status+validate+evolve)│
   └────────────────────────────────────────────────────────┘
```

### harness plugin — 7 command

| 시점 | command | 한다 |
|------|---------|------|
| **처음 구축할 때** | `/harness:harness-new <도메인>` | 도메인 한 문장 → 팀·스킬·CLAUDE.md·관측 인프라 일괄 생성 |
| 구축 중 답이 모호할 때 | `/harness:harness-grill <step>` | 한 문항씩 추천 답 제시 → 사용자 확정 (new가 자동 진입; 수동 재진입도 가능) |
| **진행 중 새 기능이 생겼을 때** | `/harness:harness-feature <기능>` | 기능 의도를 grilling으로 확정 → intent_profile 확장 (구조 재구축 아님) |
| **무언가 바꿔야 할 때** | `/harness:harness-evolve <피드백>` | 피드백 분류 후 add/remove/split/merge/baseline/mcp-adopt 내부 op 적용 |
| 현황·drift가 궁금할 때 | `/harness:harness-status [--verbose --deep --mcp]` | read-only 진단 — 현황·기준선·drift / `--deep` LLM 감사 / `--mcp` MCP 매트릭스 |
| 구조 정합을 확인할 때 | `/harness:harness-validate [--json]` | 결정적 검증 (구조·스키마·체인 + version drift 알림, LLM 0) |
| 오래 써서 패턴이 바뀌었을 때 | `/harness:harness-adapt` | 누적 telemetry vs 기준선 차이 검출 → 변경안 제시 → 승인 후 적용 |

> **변경은 모두 `harness-evolve`가 front door.** 과거 `add-agent`/`add-skill`/`remove`/`split`/`merge`/`baseline`/`mcp-adopt` 명령은 evolve의 내부 op로, `audit`/`mcp-status`/`mcp-recommend`는 status의 플래그(`--deep`/`--mcp`)로 흡수됐다 (2026-05-30 command 병합 doctrine).

### Context Manager — dharness 본 폴더 한정

CM은 hooks가 자동으로 진화를 캡처한다 — 평소엔 사용자 행동 불필요. 아래는 조회·관리용.

| 시점 | command | 한다 |
|------|---------|------|
| 세션 시작 시 현황 보기 | `/cm-status` | 누적 세션·관측 행 수·미적용 draft 통계 |
| 최근 작업 흐름 확인 | `/cm-sessions [--limit N]` | 최근 세션 목록 (ID·날짜·소요·도구) |
| 변경 이력 박제 | `/cm-claudemd-apply <sid> [사유...]` | SessionEnd가 만든 draft 행을 CHANGELOG.md "변경 이력" 표에 삽입 |
| 변경 이력 폐기 | `/cm-claudemd-discard [sid]` | 적용 안 할 draft 폐기 (인자 없으면 모두) |
| 오래된 데이터 정리 | `/cm-prune [--older-than N] [--confirm]` | N일(default 90) 이전 누적 GC (dry-run 우선) |
| 전체 초기화 | `/cm-reset` | 누적 세션·관측 전체 삭제 (확인 필수) |

> CM 동작 원리·CHANGELOG 자동 회로·트러블슈팅 → [docs/context-manager.md](./docs/context-manager.md).

---

## 호출 방식

| 방식 | 발동 | 용도 |
|---|---|---|
| **자연어 트리거** | "하네스 구성해줘" 등 자연 발화 ↔ skill description 매칭 | 자연스러운 발화, 일반 사용 |
| **Slash command** | `/harness:harness-new`, `/cm-status` 등 결정적 호출 | 비용 회피, 트리거 확률 의존 제거 |

명령어 본문(`.md`)은 harness는 `plugins/harness/commands/`, CM은 `.claude/commands/`에 보관.

---

## 프로젝트 구조

```
.
├── .claude-plugin/
│   └── marketplace.json       # harness plugin 단일 카탈로그
├── .claude/                   # CM (dharness self-host)
│   ├── hooks/                 # SessionStart/PostToolUse/SessionEnd + _schema.py + cm_commands.py
│   ├── skills/memory-search/  # on-demand 메모리 검색 (LLM-time)
│   ├── commands/              # cm-* 5개
│   └── settings.local.json    # hooks 등록 (gitignore — 사용자 로컬)
├── plugins/
│   └── harness/               # PLUGIN — 메타 스킬 팩토리 (외부 install 대상)
│       ├── .claude-plugin/plugin.json
│       ├── skills/harness/    # SKILL.md + references/
│       └── commands/          # harness-* 7개
├── _workspace/                # DATA — CM 런타임 산출물 (gitignore)
├── docs/                      # 상세 문서 (CM·MCP·refit·phases)
├── CHANGELOG.md
├── CLAUDE.md
└── README.md
```

**핵심 원칙:** `plugins/harness/` = 외부 install 대상 (read-only when installed). `.claude/` = dharness self-host CM (외부 install 미지원). `_workspace/` = dharness 데이터.

`harness` plugin은 사용자 프로젝트의 `.claude/commands/`에 **아무것도 생성하지 않는다** (read-only invariant). 산출물은 `.claude/agents/`·`.claude/skills/`·`CLAUDE.md`에만 떨어진다.

---

## 문서 인덱스

| 문서 | 용도 |
|------|------|
| [`plugins/harness/skills/harness/SKILL.md`](./plugins/harness/skills/harness/SKILL.md) | 메타 스킬 정의 정본 (15 Phase 워크플로우) |
| [`docs/skill-phases.md`](./docs/skill-phases.md) | harness-new가 거치는 15단계 요약 표 |
| [`docs/context-manager.md`](./docs/context-manager.md) | CM 설치·동작 흐름·CHANGELOG 자동 회로·데이터 조회·트러블슈팅 |
| [`docs/mcp-adoption.md`](./docs/mcp-adoption.md) | 런타임 시점 MCP 신규 채택 (트리거·설치·권한 Tier·probe) |
| [`docs/doctrine-refit.md`](./docs/doctrine-refit.md) | plugin upgrade 후 derived harness 보강 절차 |
| [`plugins/harness/skills/harness/references/permission-profiles.md`](./plugins/harness/skills/harness/references/permission-profiles.md) | MCP·도구 권한 카탈로그 정본 |
| [`CLAUDE.md`](./CLAUDE.md) | 저장소 구성 + In-session 컨텍스트 가드라인 |
| [`CHANGELOG.md`](./CHANGELOG.md) | 변경 이력 정본 |
