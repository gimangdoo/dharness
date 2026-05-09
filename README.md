# Harness — Team-Architecture Factory for Claude Code

> 도메인 한 문장을 **에이전트 팀 + 스킬 세트**로 변환하는 메타 스킬.
> A meta-skill that turns a domain description into an agent team and the skills they use.

---

## 무엇인가

`harness`는 사용자가 도메인/프로젝트를 한 문장으로 설명하면, 해당 도메인에 특화된 **에이전트 3~5명**과 그들이 사용할 **스킬 세트**를 `.claude/agents/`·`.claude/skills/`에 자동 생성하는 메타 스킬입니다.

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

## 호출 방식 두 가지

| 방식 | 발동 | 비용 통제 | 용도 |
|---|---|---|---|
| **자연어 트리거** | "하네스 구성해줘" 등 자연 발화 ↔ skill description 매칭 | LLM이 자동 분기 | 자연스러운 발화, 일반 사용 |
| **Slash command** | `/harness-new`, `/harness-add-agent` 등 결정적 호출 | 사용자가 Phase 범위 직접 지정 | 비용 회피, 트리거 확률 의존 제거 |

**Slash command 카탈로그 (7개):**

```
/harness-new <도메인>          # Phase 0~8 전체 (신규 구축)
/harness-add-agent <역할>      # Phase 4·5·7·8 (1·2·3 skip)
/harness-add-skill <스킬>      # Phase 6·7·8 (1~5 skip)
/harness-baseline              # Phase 1·2 재실행 + drift 분석
/harness-audit                 # 정합성 감사 (read-only)
/harness-evolve <피드백>       # Phase 9 수동 진화
/harness-adapt                 # Phase 10 telemetry drift 점검
```

전체 가이드: [`commands/README.md`](./commands/README.md).

---

## 프로젝트 구조

```
.
├── commands/              # Slash command 진입점 7종 (명시적 호출)
├── skills/
│   └── harness/           # 메타 스킬 본체 (SKILL.md + references/)
├── .claude/
│   ├── agents/            # context-management 하네스 에이전트 5종
│   └── skills/            # context-management 하네스 스킬 6종
├── _workspace/
│   ├── _baseline/         # Phase 1-2 산출물 + CM baseline 기준값
│   ├── _telemetry/        # Phase 10 telemetry (append-only JSONL)
│   ├── _memory/           # CM 런타임 메모리 (세션/클러스터/observations)
│   ├── _tool_outputs/     # PostToolUse 원본 보존 (압축 전)
│   └── references/        # CM 전용 Phase 10 진단 룰
└── CLAUDE.md              # 하네스 포인터 + 변경 이력
```

---

## Skill 워크플로우 한눈에

`harness` 메타 스킬은 11단계로 동작합니다:

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
| `dashboard-render` | 4개 뷰 SQLite 집계 + FastAPI worker (골격 포함) |

### 결정적 부속 산출물

| 위치 | 역할 |
|------|------|
| `_workspace/_hooks/session_start.py` | SessionStart 훅: ID 발급·DB 부트스트랩 |
| `_workspace/_hooks/post_tool_use.py` | PostToolUse 훅: raw.jsonl + 10KB 캡처 |
| `_workspace/_hooks/session_end.py` | SessionEnd 훅: transcript 평탄화 |
| `_workspace/_hooks/cm_commands.py` | `/cm-*` 결정적 커맨드 핸들러 |
| `_workspace/_hooks/INSTALL.md` | 훅 settings.json 등록 가이드 (사용자 수동) |
| `_workspace/_worker/dashboard_server.py` | FastAPI localhost 워커 |
| `commands/cm-*.md` | 7개 슬래시 커맨드 (status·sessions·clusters·dashboard·init·reset·curate) |

### 단계적 구현 현황

| 단계 | 내용 | 상태 |
|------|------|------|
| S1 | cm-orchestrator + cm-injector + **session-capture** | ✅ |
| S2 | cm-digester + session-digest + observations.db (단일 진실 스키마) | ✅ |
| S3 | cm-retriever + memory-search | ✅ |
| S4 | cm-compressor + tool-output-compress | ✅ |
| S5 | cm-curator + memory-curate (decay + daily_summary + 주기 트리거) | ✅ |
| S6 | dashboard-render + FastAPI 워커 골격 | ✅ |
| S7 | Phase 10 CM 진단 룰 (`_workspace/references/cm-diagnostic-rules.md`) | ✅ |

---

## 문서 인덱스

| 문서 | 용도 |
|------|------|
| [`commands/README.md`](./commands/README.md) | Slash command 7종 카탈로그 + 의사결정 트리 |
| [`skills/README.md`](./skills/README.md) | 스킬 디렉토리 인덱스 + references 가이드 |
| [`skills/harness/SKILL.md`](./skills/harness/SKILL.md) | 메타 스킬 정의 (11 Phase 워크플로우) |
| [`CLAUDE.md`](./CLAUDE.md) | Context Manager 하네스 포인터 + 변경 이력 |
| [`_workspace/references/cm-diagnostic-rules.md`](./_workspace/references/cm-diagnostic-rules.md) | Phase 10 CM 전용 drift 진단 룰 |
