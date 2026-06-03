---
name: harness
description: "전문 에이전트를 정의하고 그 에이전트가 사용할 스킬을 생성하는 메타 스킬. 도메인/프로젝트에 맞는 하네스를 구성·확장·점검한다. 트리거: '하네스 구성/구축/설계/엔지니어링', 도메인/프로젝트 자동화 체계 구축, 기존 하네스 재구성/확장/점검/감사/현황, 에이전트·스킬 동기화 요청."
---

# Harness — Agent Team & Skill Architect

도메인/프로젝트에 맞는 하네스를 구성하고, 각 에이전트의 역할을 정의하며, 에이전트가 사용할 스킬을 생성하는 메타 스킬.

**핵심 원칙:**
1. 에이전트 정의(`.claude/agents/`)와 스킬(`.claude/skills/`)을 생성한다.
2. **에이전트 팀을 기본 실행 모드로 사용한다.**
3. **CLAUDE.md에 하네스 섹션을 등록한다.** — 새 세션에서 오케스트레이터 스킬이 트리거되도록 운영·구조·규칙만 기록한다 (Claude Code CLAUDE.md litmus — 매 세션 로딩, 목표 < 200줄). 변경 이력은 별도 파일.
4. **하네스는 고정물이 아니라 진화하는 시스템이다.** — 매 실행 후 피드백을 반영하고, 에이전트·스킬·CLAUDE.md를 지속 갱신한다.

## 워크플로우

### Phase 0 (Pre-flight): 기존 하네스 감사

> **메타 단계** — 프로젝트 코드가 아니라 **기존 하네스 산출물**(`.claude/agents/`, `.claude/skills/`, `CLAUDE.md`)의 현황을 확인하여 실행 모드를 결정한다. 프로젝트 코드 분석은 Phase 1부터 시작된다. Phase 0는 항상 실행되며 건너뛸 수 없다.

1. `프로젝트/.claude/agents/`, `프로젝트/.claude/skills/`, `프로젝트/CLAUDE.md`를 읽고, `_workspace/_baseline/`·`_workspace/_critique_phase*_*.md` 존재를 확인한다

> **🔄 Entry gate (필수 read):** [`references/phase-entry-gates.md`](./references/phase-entry-gates.md) §"Phase 0 — 중단된 factory run 감지 doctrine" 진입 직전 필수.

2. 현황에 따라 실행 모드를 분기한다:
   - **신규 구축**: 에이전트/스킬 디렉토리가 없거나 비어있음 → Phase 1부터 전체 실행
   - **기존 확장**: 기존 하네스가 있고 새 에이전트/스킬 추가 요청 → 아래 매트릭스에 따라 필요한 Phase만 실행
   - **운영/유지보수**: 기존 하네스의 감사·수정·동기화 요청 → Phase 9-5로 이동

   **기존 확장 시 Phase 선택 매트릭스:**

| 변경 유형 | P1 Code Research | P2 Inquiry | P3 Domain | P4 Team | P5 Agent | P6 Skill | P7 Orch | P8 Valid |
|----------|---|---|---|---|---|---|---|---|
| 에이전트 추가 | – | – | – | 배치 결정만 | 필수 | 전용 스킬 필요 시 | 수정 | 필수 |
| 스킬 추가/수정 | – | – | – | – | – | 필수 | 연결 변경 시 | 필수 |
| 아키텍처 변경 | – | – | – | 필수 | 영향 받는 에이전트만 | 영향 받는 스킬만 | 필수 | 필수 |
| **baseline 갱신** (코드/의도 재분석) | **필수** | **필수** | 영향 시 | 영향 시 | 영향 시 | 영향 시 | 영향 시 | 필수 |

> baseline 갱신 트리거: (1) 사용자가 "프로젝트 다시 분석", "baseline 갱신" 등 명시 요청, (2) Phase 10이 stack/architecture의 큰 변화를 감지, (3) 마지막 분석 후 일정 기간 경과(권장 3개월).

3. 기존 에이전트/스킬 목록과 CLAUDE.md 기록을 대조하여 불일치(drift)를 감지
4. 감사 결과를 사용자에게 요약 보고하고, 실행 계획 확인

### Phase 0.5: Domain Clarification (Pre-flight)

> **사용자 핵심 요구 (2026-05-14)** — `$ARGUMENTS` 모호성 silent 진행 차단. 신규 구축 분기에서만 실행 (기존 확장/유지보수는 skip).

> **🛑 Entry gate (필수 read):** [`references/phase-entry-gates.md`](./references/phase-entry-gates.md) §"Phase 0.5 — 🛑 Anti-premature-judgment doctrine" 진입 직전 필수.

`$ARGUMENTS` (도메인 한 문장)에 대해 4 항목 LLM 검사:

| 항목 | 질문 | empty 시 행동 |
|---|---|---|
| 작업 유형 | 생성 / 분석 / 검증 / 통합 중 1개 이상 명시? | 사용자에게 명시 요청 |
| 입력 source | 어디서 데이터 받는가? (코드/API/문서/사용자 발화/...) | 사용자에게 source 1개 이상 요청 |
| 출력 target | 최종 산출물은? (보고서/코드/배포/리뷰/...) | 사용자에게 target 1개 이상 요청 |
| 사용자 숙련도 | 기술 수준 단서? | skip 가능, Phase 3에서 보강 |

**판정**:
- empty 항목 ≥1 + 사용자가 명시 거부 → "다음 정보 보강 필요: ..." 표 출력 후 진행 (Phase 1 강제 Deep audit + Phase 2 갭 메우기 강도 ↑ doctrine 박제)
- 모든 항목 hit → Phase 1로 진행

산출물: 인라인 (별도 file 0).

### Phase 1: Code Research

프로젝트의 객관적 baseline을 추출. 결과 `_workspace/_baseline/project_profile.md`는 (a) Phase 3의 입력, (b) Phase 10의 t=0 anchor.

> **🚧 Entry gate (필수 read):** [`references/phase-entry-gates.md`](./references/phase-entry-gates.md) §"Phase 1 — 🚧 entry 게이트" 진입 직전 필수.

> **Sub-agent 격리 doctrine (P6-3, 2026-05-14)**: Deep audit 모드에서 5축(Stack/Architecture/Convention/Maturity/Pain Points)을 5 sub-agent 병렬 호출(`Agent` tool, `Explore` 타입). parent는 *합성만* 수행 — 각 sub-agent 회신을 5축 schema로 통합. parent 컨텍스트 부담 ↓, 깊이 ↑. Quick scan은 단일 sub-agent 1회 호출.

**모드 선택:**

| 모드 | 범위 | 자동 적용 조건 |
|------|------|--------------|
| **greenfield** | 최소 형태 (분류 결과 + 디렉토리 트리) | git/manifest/소스 신호 중 2+ 부재 |
| **Quick scan** (brownfield 기본) | Stack + Architecture + Convention 3축 | 소스 파일 ≤100개 |
| **Deep audit** (brownfield) | 5축 전체 + git churn | 소스 파일 >100개, 또는 사용자 명시 요청 |

사용자 키워드가 자동 룰을 오버라이드: "간단히/빠르게" → Quick 강제, "전체 점검/깊이 분석" → Deep 강제.

> 감지 룰, 5축 조사 기법, 폴백 전략은 `references/code-research.md`. 출력 schema는 `references/project-profile-schema.md`.

### Phase 2: Project Inquiry

사용자의 주관적 의도·제약·우선순위를 7섹션(vision/scope/constraints/architecture/quality/workflow/meta)으로 수집. 결과 `_workspace/_baseline/intent_profile.md`. greenfield/brownfield는 동일 schema를 공유, `project_type` 필드로 분기.

> **🚧 Entry gate (필수 read):** [`references/phase-entry-gates.md`](./references/phase-entry-gates.md) §"Phase 2 — 🚧 entry 게이트" 진입 직전 필수.

**브랜치별 채우기:**
| 브랜치 | 방식 |
|------|-----|
| **greenfield** | 7섹션 순차 질문, 모든 필드 사용자 입력 |
| **brownfield** | 4단계 — 자동 추론 → 확인 → 갭 메우기 → 코드 grounded 질문 |

**필수 5개 (스킵 불가):** `constraints.tech_stack`, `constraints.team.size`, `constraints.timeline.horizon`, `architecture.deployment_target`, `quality.test_rigor`. 그 외는 스킵 가능, 스킵 시 `meta.open_questions`에 등록. **정본:** `plugins/harness/scripts/validate/schema.py:INTENT_REQUIRED` — doc 5곳(SKILL.md / phase-entry-gates.md / intent-profile-schema.md×2 hit / chain.py alias) sync은 `chain.py:check_intent_required_doc_sync` 결정적 검증.

**`meta.dharness_version` 박제 (필수, 2026-05-23 doctrine drift refit 인프라):** `plugins/harness/.claude-plugin/plugin.json` `version` 필드를 read 후 frontmatter `meta.dharness_version: "<현 plugin version>"`로 저장. 합성 시점 plugin doctrine 시점의 anchor. `harness-validate`/`harness-status`가 현 plugin version과 비교해 upgrade 발생 시 doctrine refit 권고 1줄 출력.

**방법론 위임 doctrine (2026-05-24, methodology-advisor v0.3.x handoff + v0.12.1 adapter):** `workflow.methodology` 필드가 사용자에게 모호하거나 (`methodology-advisor` plugin은 ~24 후보 catalog 보유 — dharness 자체 표준 enum 11종: TDD/BDD/DDD/Spec-driven/Trunk-based/Kanban/Scrum/Shape-up/XP/none/unknown은 `chain.py:_METHODOLOGY_ENUM` 정본) 또는 사용자가 명시적으로 "방법론 추천해줘" 발화 시 → `methodology-advisor` plugin sub-skill 호출. advisor 출력 yaml fragment를 dharness 측 단방향 변환 후 intent_profile frontmatter에 merge:
> - `workflow.methodology: ["DDD", "TDD", "Trunk-based"]` (mixed-case list) → primary = list[0] lowercase scalar 박제, secondary = list[1:] lowercase → `meta.advisor_secondary_methodologies`에 보존 (재현성·진화 비교)
> - `workflow.methodology_source: "methodology-advisor v0.3.1"` (free string) → enum `"advisor"`로 정규화, 원본은 `meta.advisor_handoff_version`에 박제
> - `workflow.methodology_matrix_row: "R4" | "matrix-miss"` → 그대로 박제
>
> 사용자 직접 응답 시 `methodology_source: user`, brownfield 자동 추론(jest.config·gherkin·OpenAPI signal) 시 `methodology_source: inferred`, 미수집 시 `none`. 카탈로그 외 방법론은 `methodology: unknown` + secondary에 원본 보존 + `meta.open_questions` 박제. PM 영역(Kanban/Scrum/Shape Up)은 dharness 직접 매핑 없음 — `methodology` 필드만 박제하고 다운스트림 Phase 4·5에서 외부 도구로 위임. 변환 룰 표는 `references/intent-profile-schema.md:§Advisor handoff 수신 시 변환 룰`.

> 채우기 전략 상세, 자동 추론 매핑, 코드 grounded 질문 패턴(13종), 섹션별 질문 카탈로그는 `references/project-inquiry.md`. 풀 schema는 `references/intent-profile-schema.md`, 완성 인스턴스 예시는 `references/intent-profile-examples.md`. Low confidence 추론 또는 필수 5필드 1차 거부 시 1q-at-a-time + LLM 추천 답안 패턴은 `references/grilling-loop.md` (mattpocock grill-me 흡수, 2026-05-19).

### Phase 3: 도메인 분석

1. 사용자 요청에서 도메인/프로젝트 파악
2. **Project Profile + Intent Profile 합성** — 객관 신호와 주관 의도 통합으로 도메인 모델 도출
3. 핵심 작업 유형 식별 (생성, 검증, 편집, 분석 등)
4. Phase 0 감사 결과를 기반으로 기존 에이전트/스킬과의 충돌/중복 분석
5. **사용자 숙련도 감지** — 대화 단서로 기술 수준 파악, 이후 커뮤니케이션 톤 조절. 코딩 경험 적은 사용자에게 "assertion", "JSON schema" 등 용어 무설명 사용 금지.

### Phase 3.5: Self-Critique on Domain Analysis

> **사용자 핵심 요구 (2026-05-14)** — Phase 3 single-pass silent error 검출. Phase 3 산출물에 대한 별도 sub-agent cross-review.

1. **격리된 sub-agent 호출** (Agent tool, `general-purpose` + `model: opus`):
   - 입력: `_workspace/_baseline/{project,intent}_profile.md` + Phase 3 도메인 분석 인라인 결과
   - 지시: "본 도메인 분석을 cross-review. 누락된 작업 유형? 도메인 모델의 오해? 충돌·중복?"
2. **충돌 발견 시**: 사용자 게이트 — Phase 3 결과 vs sub-agent critique 두 견해 출력 + 선택 요청
3. **합의 시**: Phase 4로 진행

산출물: `_workspace/_critique_phase3_{ts}.md` (sub-agent 회신 박제).

### Phase 4: 팀 아키텍처 설계

#### 4-1. 실행 모드

**에이전트 팀이 최우선 기본값.** 2명 이상 협업이면 반드시 팀 먼저 검토.

| 모드 | 언제 사용 | 도구 |
|------|---------|------|
| **에이전트 팀** (기본) | 2+ 협업, 실시간 조율, 중간 산출물 상호 참조 | `TeamCreate` + `SendMessage` + `TaskCreate` |
| **서브 에이전트** (대안) | 단일 작업, 결과만 메인 반환, 팀 통신 오버헤드가 과할 때 | `Agent` + `run_in_background` |
| **하이브리드** | Phase별 특성이 다를 때 (예: 병렬 수집 → 합의 통합) | Phase 단위로 모드 명시 |

#### 4-2. 패턴

작업을 전문 영역으로 분해 → 아래 6개 중 선택:

| 패턴 | 한 줄 설명 |
|------|---------|
| 파이프라인 | 단계별 순차 흐름, 앞 단계 산출물이 다음 단계 입력 |
| 팬아웃·팬인 | 한 작업을 N개 병렬 분기 → 결과 통합 |
| 전문가 풀 | 도메인별 전문가 N명 중 작업에 맞는 1명 동적 선택 |
| 생성-검증 | 생성자와 비판자를 분리, 한 쪽 결과를 다른 쪽이 점검 |
| 감독자 | 메타 에이전트가 작업 분배·진행 모니터·결과 종합 |
| 계층적 위임 | 상위가 하위에 sub-task 위임, 하위 결과를 상위가 통합 |

#### 4-3. 분리 기준

전문성·병렬성·컨텍스트·재사용성 4축으로 판단.

> 모드 비교, 패턴별 의사결정 트리, 분리 기준 상세표는 `references/agent-design-patterns.md`.

### Phase 5: 에이전트 정의 생성

> **🚧 Entry gate (필수 read):** [`references/phase-entry-gates.md`](./references/phase-entry-gates.md) §"Phase 5 — 🚧 entry 게이트 — Cardinality justification" 진입 직전 필수.

> **Phase 5-0 — Wiki Feedback pull (self-host opt-in, M4, S18 doctrine, 2026-05-31):** 에이전트·스킬 설계 직전, 로컬 harness wiki `<wiki>/harness/candidates/` 타겟이 존재하면 **promoted candidate를 조회해 재합성 대신 재사용을 우선**한다. pull 대상(`candidates/<name>/eval-results.json`의 `promotion.verdict` + `evals.*.status` + `meta.promoted_to`)·tier 의미(3 tier 전부 PASS + verdict 박제 시만 "검증된 재사용 후보")·재사용 분기는 [`references/wiki-bridge.md`](./references/wiki-bridge.md) §2 단일 출처. **presence gate**: wiki 타겟 부재 시 silent no-op — 정상 합성 진행(외부 install 파생 하네스는 wiki 위치 모르므로 무관). 조회 자체는 `scripts/wiki/bridge.py:pull_promoted`가 수행(read-only glob + `wiki_bridge_pull` telemetry, P5 self-host 전용). 재사용 판단은 *제안 후 사용자 confirm* — 자동 graft 0. M1 Emit(Phase 7-7)과 짝.

**모든 에이전트는 반드시 `프로젝트/.claude/agents/{name}.md` 파일로 정의한다.** 빌트인 타입(`general-purpose`, `Explore`, `Plan`)을 사용하더라도 정의 파일 생성 필수. Agent 도구의 prompt에 역할을 직접 넣는 것은 금지. 이유: 다음 세션 재사용성, 협업 프로토콜 명시, 에이전트(누가)와 스킬(어떻게) 분리.

> **Sub-agent 격리 doctrine (P6-3, 2026-05-14)**: 에이전트 N개 정의 파일 작성을 N sub-agent 병렬 호출(`Agent` tool, `general-purpose` + `model: opus`). 각 sub-agent에 단일 에이전트 정의 책임 위임 — parent는 frontmatter `tools:` allowlist 합성 + 통신 프로토콜 매트릭스 통합만 담당. parent 컨텍스트 격리, N개 동시 작성 시간 단축.

**모델 설정 (Q2 doctrine, 2026-05-16):** frontmatter `model:` 필드는 *agent role 축*으로 결정 — `permission-profiles-synthesis.md` §5-1-c 단일 출처 (P7 분리, 2026-05-23). 기본 `opus` (synthesis/review/write), read-only 탐색·요약 전용 sub-agent는 `sonnet` 가능 (비용 ~7배 ↓). Agent 호출 시 frontmatter `model:` 값과 일치하는 파라미터 명시 필수. 일괄 `opus` 강제는 폐기 — capability profile × role 매트릭스로 합성.

**팀 재구성:** 세션당 한 팀만 활성. Phase 간 팀 해체/재구성 가능. 이전 팀 산출물을 파일로 저장 후 새 팀 생성.

**필수 섹션:** 핵심 역할, 작업 원칙, 입력/출력 프로토콜, 에러 핸들링, 협업, 예시(입출력 사례 ≥ 1). 팀 모드에선 `## 팀 통신 프로토콜` 섹션 추가 (메시지 수신/발신 대상, 작업 요청 범위 명시). frontmatter `tools:`에 외부 입력·부작용 도구(`Bash`/`Write`/`Edit`/`WebFetch`/`WebSearch`/`PowerShell`)를 보유하는 에이전트는 `## 입력 신뢰 경계`(프롬프트 인젝션 방어) 섹션도 필수 — 표준 가드 절은 `references/agent-design-patterns.md` "입력 신뢰 경계" 참조. `harness-validate`가 도구 보유 ↔ 가드 절 정합을 결정적으로 검출한다.

**QA 에이전트 포함 시 필수:**
- 타입은 `general-purpose` (`Explore`는 읽기 전용이라 검증 스크립트 실행 불가)
- 핵심은 "존재 확인"이 아니라 **"경계면 교차 비교"** — API 응답과 프론트 훅을 동시에 읽고 shape 비교
- 전체 완성 후 1회가 아니라 **각 모듈 완성 직후 점진 실행** (incremental QA)

> 정의 템플릿과 실제 파일 전문은 `references/agent-design-patterns.md` + `references/team-examples.md`. QA 상세 가이드는 `references/qa-agent-guide.md`.

**도구·MCP 자동 할당 (Phase 5-2):** 에이전트 `tools:` allowlist + `.claude/settings.json`·`.mcp.json` 합성은 *제안 후 사용자 confirm*. 단일 출처는 `references/permission-profiles*.md` 4 파일 (P7 분리, 2026-05-23):
- `permission-profiles.md` main — §1 3-layer 모델 / §4 결정 트리 / §6 안전 정책 / §9 plugin subagent 제약 (§2/§5/§7/§8/§11은 모두 분리 — profiles·synthesis·empirical)
- `permission-profiles-inventory.md` — §3 MCP 후보 인벤토리 + §3-0 verification_status + §3-1 검증 완료 T0 매트릭스
- `permission-profiles-synthesis.md` — §5-1 에이전트 frontmatter (a/b/c — Layer B / Layer A+B / 모델 by role Q2 doctrine)
- `permission-profiles-dynamic-adoption.md` — §10 dynamic adoption 5-step + 10-4 rollback + 10-7 병렬 세션

운영 함의(mid-session 미전파·uvx 절대경로·자동 install 금지·`tools:` allowlist는 inline 도구 카운트 무력)는 위 4 파일에 분산. 합성 직전 *후보 간 자동 점수화*(3축: 효율성·확장성·정확도) + top-K + R-7 confirm gate + §10 인계는 `references/mcp-recommendation.md`. 자동 install·`allow` 승급은 T0(무키·로컬) 한정. 진단(인벤토리·매트릭스·정합)은 `/harness:harness-status --mcp` (read-only). 도구 API 의사 schema(TeamCreate / SendMessage / TaskCreate / TaskUpdate / TaskGet / TaskOutput 6 도구)는 `references/agent-design-patterns.md` 부록 (PB4 흡수, 2026-05-27).

### Phase 5.5: Self-Critique on Agent Definitions

> **사용자 핵심 요구 (2026-05-14)** — Phase 5 산출물(에이전트 N개) cross-review. 역할 중복·gap·통신 프로토콜 정합성.

1. **격리된 sub-agent N개 병렬 호출** (Agent tool, `general-purpose` + `model: opus`):
   - 각 sub-agent 입력: Phase 5에서 생성한 단일 에이전트 정의 + 다른 N-1개 에이전트 정의의 *프로토콜 헤더만* (핵심 역할 + 통신 프로토콜)
   - 지시: "본 에이전트 정의가 팀 내에서 (a) 책임 중복 없음? (b) gap 메움? (c) 통신 프로토콜 정합? (d) shallow 아님 — 프로토콜이 내부 책임만큼 복잡한 pass-through wrapper 아닌지(deletion test, `references/agent-design-patterns.md` "에이전트 깊이")? cross-check."
2. **충돌 발견 시**: 사용자 게이트
3. **합의 시**: Phase 6로 진행

산출물: `_workspace/_critique_phase5_{ts}.md` (sub-agent N개 회신 통합).

### Phase 6: 스킬 생성

각 에이전트가 사용할 스킬을 `프로젝트/.claude/skills/{name}/SKILL.md`에 생성.

> **Sub-agent 격리 doctrine (P6-3, 2026-05-14)**: 스킬 N개 작성을 N sub-agent 병렬 호출. 각 sub-agent에 단일 스킬 작성 책임 위임. parent는 description 트리거 충돌 cross-check + references/ 분배 통합만 담당.

**구조:**
```
skill-name/
├── SKILL.md (필수: YAML frontmatter + Markdown 본문)
└── (선택) scripts/  references/  assets/
```

> **🚫 빈 스킬 금지 invariant (P0, 2026-05-22):** 스킬 디렉토리를 만들면 *같은 동작에서* `SKILL.md`를 **본문까지 채워** 박제한다. 디렉토리만 만들고 `SKILL.md`를 누락하거나 frontmatter만 남기면, 오케스트레이터·에이전트의 스킬 참조가 dangling이 되어 하네스가 즉시 실행 불가다. 빈 `SKILL.md`·디렉토리만 있는 스킬을 산출물로 남기지 않는다. 최소 본문 골격(트리거 + 워크플로우 + 입출력 + 예시 ≥ 1)은 `references/skill-writing-guide.md` "최소 본문 골격" 참조. `harness-validate`가 빈 스킬 디렉토리·본문 부재를 결정적으로 검출한다.

**핵심 룰:**
- **파일명 `SKILL.md` (대문자 고정)** — 스킬 파일은 정확히 `SKILL.md`. `skill.md`·`Skill.md` 등 대소문자 변종 금지 — Claude Code 스킬 로딩이 대문자 `SKILL.md`를 표준으로 인식하며, 변종은 케이스 민감 파일시스템에서 미로딩된다. CLAUDE.md는 프로젝트 루트(`프로젝트/CLAUDE.md`)에 둔다 — `.claude/CLAUDE.md` 금지.
- **Description은 적극적("pushy")** — description은 유일한 트리거 메커니즘. 스킬이 하는 일 + 구체적 트리거 상황 모두 기술, 유사하지만 트리거하면 안 되는 경우와 구분
- **Why를 설명하라** — "ALWAYS/NEVER" 강압 대신 이유 전달, 엣지 케이스에서도 올바른 판단 가능
- **Lean하게** — SKILL.md 본문 ≤500줄, 초과 시 references/ 분리 + 본문에 "언제 읽으라" 포인터
- **Progressive disclosure** — Metadata(항상 컨텍스트, ~100단어) → SKILL.md 본문(트리거 시) → references/(필요할 때)
- **명령형 어조** — "~한다", "~하라"

**연결:** 에이전트 1개 ↔ 스킬 1~N개 (1:1 또는 1:다). 여러 에이전트 공유 가능. 스킬은 "어떻게", 에이전트는 "누가".

> Description 작성 패턴(좋은 예/나쁜 예), 본문 스타일, 출력 형식 정의, 예시 작성, 스크립트 번들링 기준, 데이터 스키마 표준은 `references/skill-writing-guide.md`.

### Phase 7: 통합 및 오케스트레이션

오케스트레이터는 스킬의 특수 형태로, 개별 에이전트·스킬을 하나의 워크플로우로 엮어 팀 전체를 조율한다. 개별 스킬이 "각 에이전트가 무엇을 어떻게"를 정의한다면, 오케스트레이터는 "누가 언제 어떤 순서로 협업하는가"를 정의.

**기존 확장 시:** 새로 생성하지 않고 기존 오케스트레이터 수정. 에이전트 추가 시 팀 구성·작업 할당·데이터 흐름에 새 에이전트 반영, description에 새 트리거 키워드 추가.

#### 7-0. 오케스트레이터 패턴 (Phase 4-1 모드와 매핑)

| 모드 | 골격 |
|------|------|
| **에이전트 팀** | 오케스트레이터/리더가 `TeamCreate` → `TaskCreate` (의존성 포함) → 팀원이 `SendMessage`로 자체 조율 → 결과 수집·종합 → 팀 정리 |
| **서브 에이전트** | `Agent(run_in_background=true)` 병렬 호출 → 결과 대기·수집 → 통합 산출물 |
| **하이브리드** | Phase마다 다른 모드, 각 Phase 섹션 상단에 `**실행 모드:** 에이전트 팀` 형태 명시 |

#### 7-1. 데이터 전달 프로토콜

| 전략 | 적용 모드 | 적합한 경우 |
|------|---------|-----------|
| 메시지 (`SendMessage`) | 팀 | 실시간 조율, 피드백, 가벼운 상태 |
| 태스크 (`TaskCreate/Update`) | 팀 | 진행 추적, 의존 관계, 작업 자체 요청 |
| 파일 (`_workspace/`) | 팀 + 서브 | 대용량, 구조화 산출물, 감사 추적 |
| 반환값 | 서브 | 결과 수집 |

**파일 기반 규칙:** `_workspace/` 하위에 중간 산출물, 파일명 `{phase}_{agent}_{artifact}.{ext}`, 최종만 사용자 경로에 출력, 중간은 보존(사후 검증·감사용).

#### 7-2. 에러 핸들링

1회 재시도 후 재실패 시 결과 없이 진행(보고서에 누락 명시), 상충 데이터는 삭제하지 않고 출처 병기.

#### 7-3. 팀 크기

소규모(5~10작업) 2~3명, 중규모(10~20) 3~5명, 대규모(20+) 5~7명. **3명 집중 팀이 5명 산만 팀보다 낫다.**

#### 7-4. CLAUDE.md 하네스 섹션

CLAUDE.md는 매 세션 컨텍스트에 로딩된다 — 줄마다 "제거 시 Claude가 실수하나? 아니면 잘라라"를 통과하는 것만 박제. `/init`가 코드베이스에서 명령·구조를 추출하듯, 본 단계는 *합성된 하네스*에서 운영·구조·규칙을 추출한다. 변경 이력(자주 바뀜)·전체 명령 목록(참조 자료)은 CLAUDE.md에서 제외하고 포인터만.

````markdown
# 하네스: {도메인명}

{한 줄 — 이 하네스가 수행/생성하는 것}

## 운영
- {도메인} 작업·후속 요청(수정·재실행·보완) → `{orchestrator-skill}` 스킬. 단순 질문은 직접 응답.
- 검증 `/harness:harness-validate` · 진화 `/harness:harness-evolve` · drift 점검 `/harness:harness-adapt`
- 전체 `/harness:*` 카탈로그 → `{orchestrator-skill}` SKILL.md 헤더

## 구조
실행 모드: {팀 | 서브 | 하이브리드} · 오케스트레이터 `{orchestrator-skill}`

에이전트:
- `{agent-1}` — {역할 ≤ 5단어}
- `{agent-2}` — {역할 ≤ 5단어}

스킬: `{skill-1}`({용도}) · `{skill-2}`({용도})
산출물: `_workspace/` — `00_input/` 입력 · `_baseline/` 프로파일·변경이력 · `_telemetry/` 관측 · 최종 `{경로}`
상세 워크플로우·데이터 흐름 → `{orchestrator-skill}` SKILL.md

## 규칙
- 도메인 작업은 오케스트레이터 경유 — 우회 후 산출물 직접 편집 금지 (drift 추적 끊김)
- `_workspace/_baseline/*`(Phase 1·2 baseline) 수동 편집 금지 — `/harness:harness-evolve "baseline 갱신"`(baseline op) 경유
- {자문성 도메인 한정 — 면책 고지: 본 산출물은 [전문가] 자문을 대체하지 않음}

---
변경 이력 → `_workspace/_baseline/changelog.md`
````

> **CLAUDE.md litmus (Claude Code 공식 — `code.claude.com/docs` memory.md / best-practices.md):** 매 세션 로딩 → 목표 < 200줄, 줄마다 "제거 시 실수 유발? 아니면 컷". **제외**: 자주 바뀌는 정보(변경 이력), 참조 자료(전체 명령 목록 → 포인터), 코드/파일에서 알 수 있는 것. **포함**: 운영 명령, 아키텍처, gotcha·경계. 에이전트 로스터는 ≤ 5단어 역할 태그 — Claude가 팀 역량을 즉시 인식해 작업 라우팅·부분 재실행 정확도가 오른다(file-by-file 설명 아님 = 팀 구성 = 아키텍처). 코드 도메인이면 7-4.5 HOW(스택) 섹션을 `## 규칙` 다음에 추가.

#### 7-4.1. `_workspace/_baseline/changelog.md` 부트스트랩 (필수, bug_002 2026-05-23)

CLAUDE.md 포인터 박제와 동시에 대상 파일 자체를 skeleton 형태로 생성한다. skeleton template + 부트스트랩 절차는 `references/orchestrator-template.md` "changelog.md 부트스트랩 skeleton" 절 단일 출처. 미생성 시 후속 `/harness:harness-*` 9+ 명령이 append 실패 + Phase 8 must 미충족.

#### 7-4.5. CLAUDE.md HOW 본문 draft (Q3 doctrine, 2026-05-16)

포인터만 박제된 CLAUDE.md는 *빈집* — 새 세션마다 stack/build/entry point 재탐색이 토큰 손해. Phase 1 `project_profile.md` 객관 데이터를 HOW 섹션 *draft*로 변환 + 사용자 게이트 후 박제. 코드 프로젝트에서 권장(= `/init` 동급 콘텐츠), 비코드 도메인은 생략.

> 절차(4 단계 — 추출 / draft 생성 / 사용자 게이트 / 재생성 트리거), template, 제약(anti-premature-judgment 정합·사용자 confirm 없이 박제 금지·brownfield skip 가능)은 `references/orchestrator-template.md` "CLAUDE.md HOW 본문 draft" 절 단일 출처.

#### 7-5. 후속 작업 지원

오케스트레이터는 초기 실행뿐 아니라 후속 작업도 처리해야 한다.

1. **description에 후속 키워드 포함** — "다시 실행/재실행/업데이트/수정/보완", "{도메인}의 {부분작업}만 다시", "이전 결과 기반/결과 개선"
2. **오케스트레이터 Phase 1에 컨텍스트 확인 단계** — `_workspace/` 존재 + 부분 수정 → 부분 재실행 / `_workspace/` 존재 + 새 입력 → 새 실행(`_workspace_prev/`로 이동) / 미존재 → 초기 실행
3. **에이전트 정의에 재호출 지침** — 이전 결과 파일 존재 시 읽고 개선점 반영, 사용자 피드백 시 해당 부분만 수정

> 패턴별 골격 상세, 에러 유형별 전략표, 데이터 흐름 다이어그램, Phase 0 컨텍스트 확인 템플릿은 `references/orchestrator-template.md`.

#### 7-6. Runtime Gate 블록 주입 (S17 doctrine, 2026-05-30)

오케스트레이터 `### Phase 1: 준비` *직후*에 **Runtime Gate 블록**을 박제한다 — derived 하네스가 런타임에 작업을 받았을 때 따르는 의사결정 스캐폴드(G1 규모분류·G2 plan분해·G3 산출물생성). 마커 규약·위치·불변식·G1 분기 doctrine·canonical 예시는 `references/runtime-execution.md` 단일 출처. 블록은 `<!-- RUNTIME-GATE:start -->` … `<!-- RUNTIME-GATE:end -->` 1쌍으로 구획하고 식별자 G1·G2·G3를 모두 포함하며, `/harness:harness-validate`(`chain.py:check_runtime_gate_block`)가 derived 오케스트레이터에 마커·스캐폴드 완전성을 결정적 검증한다. **게이트는 self-contained** — derived 하네스는 런타임에 본 plugin reference를 못 읽으므로 분기 규칙을 게이트 본문에 inline 박제한다. G1 규모분류(small→직접 사용/large→합성 트리거, 선택적 작동)·G2 plan분해(medium/large 작업 plan→atomic task→`TodoWrite` todo 박제)·G3 산출물생성(`workflow.methodology`별 task당 deliverable 형태·순서, tdd→테스트 먼저 등)는 모두 inline 채워 박제한다(게이트 self-contained 완성).

#### 7-7. Wiki Bridge Emit (self-host opt-in, S18 doctrine, 2026-05-30)

**dharness self-host 한정** — 외부 install 파생 하네스는 본 단계 건너뛴다. 합성한 skill이 *재사용 가치 있는 범용 패턴*이고 로컬 harness wiki `<wiki>/harness/candidates/` 타겟이 존재하면, 사용자 gate 1회 후 candidate 디렉토리(`SKILL.md` frontmatter 9필드 + `eval-results.json` + `changelog.md`)를 Emit해 wiki 평가 파이프라인(Static/LLM-Judge/MonteCarlo tier)에 태운다(M1). 다음 합성 설계(Phase 5) 시 promoted candidate를 pull해 재합성 대신 재사용을 우선한다(M4). contract·gate·canonical fixture·안전 규약은 `references/wiki-bridge.md` 단일 출처이며 `chain.py:check_wiki_candidate_schema`(M5 schema gate)가 candidate 형태를 결정적 검증한다. **gate 통과 후 실 write·dedup·자가검증·telemetry는 `scripts/wiki/bridge.py:emit_candidate`가 수행**(P5, self-host 전용 — 산문 수기 아님). dedup hit 시 soft_block 반환 → 사용자 재확인. 합성 skill을 *재사용 가치 없음*으로 판단해 Emit 안 하면 `scripts/wiki/bridge.py:note_skip("emit","not-reusable",...)`를 호출해 추적 신호를 남긴다(§0 observability 보장 — "wiki 미설정 vs skip" 구분). **타겟 부재 시 silent no-op** — Emit 생략, 합성 정상 진행. wiki repo 쓰기는 outward-facing이라 사용자 gate 필수.

### Phase 7.5: Orchestrator Dry-Run Simulation

> **사용자 핵심 요구 (2026-05-14)** — Phase 7 오케스트레이터의 *가상 진행*으로 dead link / 데이터 흐름 끊김 사전 검출.

1. **격리된 sub-agent 호출** (Agent tool, `general-purpose` + `model: opus`):
   - 입력: Phase 7 오케스트레이터 스킬 본문 + 모든 에이전트 정의 + baseline profile 2종
   - 지시: "본 오케스트레이터를 가상 input 1개로 dry-run. 각 Phase에서 (a) input 가용성 (b) 산출물 다음 Phase 전달 가능 (c) dead link 0 (d) 에러 시나리오 폴백 가용 — cross-check 후 1줄 보고."
2. **dead link / 끊김 발견 시**: 사용자 게이트 — Phase 7 수정 또는 강행 confirm
3. **합의 시**: Phase 8로 진행

산출물: `_workspace/_critique_phase7_{ts}.md` (sub-agent dry-run 보고 박제).

### Phase 8: 검증 및 테스트

생성된 하네스를 검증한다.

> **Sub-agent 격리 doctrine (P6-3, 2026-05-14)**: 검증 7단계(8-1~8-7)를 sub-agent 병렬 호출. 단 *비용 큰* 8-3 (실행 테스트)과 8-4 (트리거 회귀 검증 — 쿼리 카운트 정본은 [`references/skill-testing-guide.md` §7](./references/skill-testing-guide.md))는 사용자 confirm 후 진행. 8-1·8-2·8-5·8-6·8-7은 sub-agent 5 병렬. parent는 결과 통합 + 보고만 담당.
>
> **결정적 검증 위임 (2026-05-14)**: 8-1 구조 검증은 `/harness:harness-validate` (LLM 0, plugin scripts 번들)로 위임 가능 — sub-agent 호출 비용 절감.

**검증 7단계 (Phase 9-5 / runtime-adaptation §6 회귀 검증이 8-N으로 참조하는 번호와 일치):**
1. **8-1 구조 검증** — 파일 위치, frontmatter(name/description), 참조 일관성, **사용자 프로젝트의** `.claude/commands/` 미생성 확인 (harness 플러그인 본체의 `commands/`는 L1 진입점으로 별개)
2. **8-2 실행 모드별 검증** — 팀: 통신 경로·작업 의존성·팀 크기 / 서브: 입출력 연결·`run_in_background`·반환값 수집 / 하이브리드: Phase별 모드 명시 + 경계 데이터 전달 끊김 없음
3. **8-3 스킬 실행 테스트** — 각 스킬에 2~3개 현실적 테스트 프롬프트, 가능하면 with-skill vs without-skill(baseline) 병렬 비교, 객관 검증 가능 시 assertion + 주관은 사용자 피드백
4. **8-4 트리거 검증** — should-trigger 10개 + should-NOT-trigger 10개(총 20개). 둘 다 공식·캐주얼·명시·암시 표현을 섞고, 특히 **경계가 모호한 near-miss**를 should-NOT 쪽에 다수 배치. (8개는 절대 floor — 미만은 트리거 정확도 보장 불가)
5. **8-5 드라이런** — Phase 순서 논리, 데이터 전달 dead link, 입출력 매칭, 에러 시나리오별 폴백
6. **8-6 테스트 시나리오 작성** — 오케스트레이터에 `## 테스트 시나리오` 섹션, 정상 1개 + 에러 1개 이상
7. **8-7 반복 개선** — 피드백을 일반화하여 스킬 수정(좁은 수정 금지). 사용자 만족 또는 의미 있는 개선이 더 없을 때까지. 공통 코드는 `scripts/`에 번들링

> 테스트 프롬프트 작성, with/without 비교, near-miss 작성, 트리거 충돌 진단은 `references/skill-testing-guide.md`.

### Phase 9: 하네스 진화

하네스는 한 번 만들고 끝나는 정적 산출물이 아니다. 사용자 피드백에 따라 계속 진화한다.

#### 9-1. 실행 후 피드백 수집

매 하네스 실행 완료 후 사용자에게 피드백 기회를 제공할 수 있다 — "결과에서 개선할 부분이 있나요?". 단 **다음 액션을 자동 제안하지 않는다**: 진화·점검·적응은 사용자가 해당 슬래시 커맨드(`/harness:harness-evolve` 등)를 명시 호출할 때만 시작된다 (autonomous trigger 제거 doctrine, 2026-05-30).

> **Grilling 분기 (command-only, 2026-05-30 개정)**: 피드백 어휘가 모호해도 *자동으로* grilling에 진입하지 않는다. 사용자가 `/harness:harness-grill feedback` 또는 `/harness:harness-evolve`를 명시 호출할 때만 `references/grilling-loop.md` 1q + recommended answer 패턴으로 §9-2 표 5행 중 진화 대상을 분기한다. recommendation 출처는 직전 실행 telemetry signal — 디렉토리·파일 이름 단독 추천 doctrine 위반. cap 5 question.

#### 9-2. 피드백 반영 경로

| 피드백 유형 | 수정 대상 | 예시 |
|-----------|----------|------|
| 결과물 품질 | 해당 에이전트의 스킬 | "분석이 너무 피상적" → 스킬에 깊이 기준 추가 |
| 에이전트 역할 | 에이전트 정의 `.md` | "보안 검토도 필요" → 새 에이전트 추가 |
| 워크플로우 순서 | 오케스트레이터 스킬 | "검증을 먼저 해야" → Phase 순서 변경 |
| 팀 구성 | 오케스트레이터 + 에이전트 | "이 둘은 합쳐도 될 듯" → 에이전트 병합 |
| 트리거 누락 | 스킬 description | "이 표현으로 작동 안 함" → description 확장 |

#### 9-3. 변경 이력

모든 변경은 `_workspace/_baseline/changelog.md` 변경 이력 테이블에 기록 (CLAUDE.md엔 포인터만 — 변경 이력은 자주 바뀌어 매 세션 로딩되는 CLAUDE.md에서 제외). 출처를 명시하여 Phase 9 변경과 Phase 10 자동 감지를 구분 — `Phase 9: 사용자 피드백 — {요약}` vs `Phase 10: drift 감지 ({drift 이름})`.

#### 9-4. 진화 트리거 (command-only)

진화는 **사용자의 명시 슬래시 커맨드 호출로만** 시작된다 — `/harness:harness-evolve <피드백>` (통합 변경 front door). harness는 "피드백 2회 반복", "반복 실패", "우회 감지" 같은 신호를 *자동 판단해 다음 액션을 제안하지 않는다* (autonomous trigger 제거 doctrine, 2026-05-30). telemetry는 계속 캡처되며(§10-1 Capture), 사용자가 `/harness:harness-status` 또는 `/harness:harness-adapt`를 호출하면 그때 누적 신호를 근거로 진단·변경안을 제시한다.

#### 9-5. 운영/유지보수 워크플로우

Phase 0에서 "운영/유지보수"로 분기 시 진입. 명시적 진입점은 `/harness:harness-status --deep` (read-only LLM 정합 감사).

1. **현황 감사** — `.claude/agents/` ↔ 오케스트레이터 에이전트 구성 비교, `.claude/skills/` ↔ 스킬 구성 비교 → 불일치 보고 (`/harness:harness-status --deep`이 수행)
2. **점진적 추가/수정** — 한 번에 하나씩, 각 변경 후 즉시 동기화(Step 3)
3. **변경 이력 갱신** — `_workspace/_baseline/changelog.md`에 날짜·내용·대상·사유
4. **변경 검증** — 구조(8-1), 트리거 영향 시 트리거(8-4), 대규모 변경(아키텍처 변경, 에이전트 3+ 추가/삭제) 시 실행 테스트(8-3) + 드라이런(8-5)

### Phase 10: Runtime Adaptation

Phase 9가 사용자 피드백을 수집한다면, Phase 10은 프로젝트 변화와 하네스 사용 패턴을 **수동 관측(Capture)**하되, drift 진단·변경안 제시는 사용자가 `/harness:harness-adapt`를 명시 호출할 때만 수행한다. Capture 레이어(telemetry 기록)는 매 실행 자동으로 누적되지만, **harness가 스스로 "이제 적응할 때"라고 판단해 제안하지 않는다** (autonomous trigger 제거 doctrine, 2026-05-30). 모든 변경은 **제안 + 승인** 모델 — Phase 10이 자동 적용하는 변경은 없다.

#### 10-1. 3 레이어 구조

| 레이어 | 역할 | 출력 위치 |
|------|------|----------|
| **Capture** | 매 실행마다 프로젝트 + 사용 신호 캡처 | `_workspace/_telemetry/{date}.jsonl` |
| **Diagnostic** | 누적 telemetry ↔ baseline 비교, drift 감지 | `_workspace/_telemetry/_delta_{ts}.md` |
| **Adapt** | drift 변경안 제시, 승인 시 적용 | `.claude/agents/`, `.claude/skills/`, `CLAUDE.md`, `_baseline/*.md` |

#### 10-2. 트리거 조건 (command-only)

| 트리거 | 조건 |
|------|------|
| **수동 (유일)** | `/harness:harness-adapt` 명시 호출. 호출 시점에 누적 telemetry를 baseline과 비교해 drift 진단 + 변경안 제시 |

> **주기적·임계 자동 트리거 제거 (2026-05-30):** "N회 누적", "단일 큰 drift" 같은 신호로 harness가 *스스로 Adapt를 발화·제안하던* 트리거는 폐기됐다. Capture는 계속 누적되지만, drift 분석은 사용자가 `/harness:harness-adapt`를 호출한 순간에만 일어난다.

#### 10-3. drift 두 종류 구분

- **baseline drift**: 프로젝트 자체가 변함 (새 의존성, 새 디렉토리, 커버리지 변화) → `project_profile.md` 갱신 + 영향 받는 에이전트/스킬 점검
- **사용 drift**: 프로젝트는 같지만 하네스 사용 패턴이 변함 (특정 에이전트 미사용, 반복 실패, 사용자 우회) → 에이전트/스킬 자체 재구성

두 종류는 같은 delta 리포트에 분리된 섹션으로 보고된다.

#### 10-4. 신뢰도 가중치 — Phase 2 메타 활용

Phase 2의 `meta.inferred_fields − meta.user_confirmed_fields` 차집합("신뢰도 낮음" 필드)을 가중. 신뢰도 낮은 필드의 baseline drift는 변경안 제시 전 "원래 추론이 맞았는지" 사용자 확인을 먼저 트리거. 신뢰도 높은 필드의 drift는 변경안 직접 제시.

#### 10-5. Phase 9와의 관계

| | Phase 9 (수동 진화) | Phase 10 (Runtime Adaptation) |
|--|---|---|
| 트리거 | `/harness-evolve` 명시 호출 | `/harness-adapt` 명시 호출 |
| 입력 | 사용자 발화 | telemetry + baseline |
| 변경 범위 | 사용자가 지목한 부분 | 시스템이 감지한 모든 drift |

두 Phase는 동일한 변경 이력 테이블(`_workspace/_baseline/changelog.md`)을 공유한다.

#### 10-6. 안전 메커니즘 (적용·검증·복원)

모든 Adapt 적용은 **chain 단위 + 사전 스냅샷 + 사후 검증 + (실패 시) 자동 rollback**으로 atomic 처리.

> 5종 메커니즘(Cross-artifact chain·패치 미리보기·사전 스냅샷·Post-Adapt 회귀 검증·자동 rollback) 상세, telemetry schema, capture 신호 7종, diagnostic·adapt 룰, 승인 UX는 `references/runtime-adaptation.md` §6 단일 출처.

#### 10-7. 비코드 도메인 telemetry 적응

`_workspace/_telemetry/` 인프라와 **사용 신호**(`harness_invocation`·`agent_invocation`·`agent_failure`) 캡처는 도메인 무관 — 모든 하네스가 박제한다. 미사용 에이전트 감지 등 drift 진단은 `/harness:harness-adapt` 호출 시점에 코드 여부와 무관하게 작동한다 (자동 발화 없음, §10-2). 반면 **baseline drift 신호**(`project_signal` — 새 의존성·커버리지·LOC 변화)는 코드 프로젝트 전제다.

비코드 도메인(재무·교육·생활·문서·기획 등)은:
- 사용 신호 캡처 + `_telemetry/` 인프라는 **그대로 박제** — 차단 항목이다.
- `project_signal`은 도메인 신호로 치환(예: 입력 데이터 스키마 변경, 산출물 카테고리 추가)하거나, 도메인상 의미가 없으면 CLAUDE.md에 "Phase 10: 사용 신호만 캡처, baseline drift는 향후 범위" 한 줄로 **명시**한다.
- silent 생략 금지 — 합성 회귀 평가에서 telemetry 인프라 미박제가 반복 결함으로 누적됐다. 명시적 future scope 선언은 graceful, 침묵은 결함이다.

## 산출물 체크리스트

> **🚧 Read at phase:** Phase 8 검증 진입 직전 + factory 종료 전 최종 self-check.
> 18 항목 (must 9 / should 9) 단일 출처는 [`references/output-checklist.md`](./references/output-checklist.md) — 본 reference 미read 시 Phase 8-1 구조 검증의 항목 catalog 누락. `harness-validate`가 must 항목 일부를 결정적으로 검증.

## 참고

> **Progressive disclosure doctrine (2026-05-14 M8 박제):** references/ 파일은 *Phase별 lazy load* — 본 SKILL.md 본문 진입 시 자동 read 0건. 각 reference 상단에 `> **Read at phase:** N` 헤더 박제 — LLM은 해당 phase 진입 시에만 read. 무차별 prefetch 시 토큰 부담 ~6000 LOC × 13 file. 본 표는 phase → reference 매핑 단일 출처.
>
> | 진입 phase | reference 파일 | 사용 시점 |
> |---|---|---|
> | Phase 0 | `phase-entry-gates.md` ("Phase 0 — 중단된 factory run 감지 doctrine" 절) | 감사 진입 |
> | Phase 0.5 | `phase-entry-gates.md` ("Phase 0.5 — 🛑 Anti-premature-judgment doctrine" 절) | Domain Clarification 진입 |
> | Phase 1 | `phase-entry-gates.md` ("Phase 1 — 🚧 entry 게이트" 절), `code-research.md`, `project-profile-schema.md` | Code Research 진입 |
> | Phase 2 | `phase-entry-gates.md` ("Phase 2 — 🚧 entry 게이트" 절), `project-inquiry.md`, `intent-profile-schema.md`, `grilling-loop.md` (Low confidence 또는 필수 5필드 1차 거부 시) | Project Inquiry 진입 |
> | Phase 3 | (없음 — Phase 1+2 합성) | 도메인 분석 |
> | Phase 4 | `agent-design-patterns.md`, `team-examples.md` | 팀 패턴 선택 |
> | Phase 5 | `phase-entry-gates.md` ("Phase 5 — 🚧 entry 게이트 — Cardinality justification" 절), `agent-design-patterns.md`, `team-examples.md`, `qa-agent-guide.md` (QA 에이전트 정의 시), `wiki-bridge.md` §2 (self-host — Phase 5-0 Wiki Feedback pull) | 에이전트 정의 |
> | Phase 5-2 | `permission-profiles.md` + 3 sibling (`-inventory.md` / `-synthesis.md` / `-dynamic-adoption.md`, P7 분리, 2026-05-23), `mcp-recommendation.md`, `trigger-keyword-catalog.md` | MCP·도구 할당 |
> | Phase 6 | `skill-writing-guide.md`, `skill-testing-guide.md` | 스킬 생성 |
> | Phase 7 | `orchestrator-template.md` | CLAUDE.md 통합 |
> | Phase 8 | `output-checklist.md` (must 9 / should 9 catalog), `skill-testing-guide.md` (트리거 회귀) | 검증 |
> | Phase 9 | (사용자 발화 종속 — case-by-case) | 진화 |
> | Phase 10 | `runtime-adaptation.md` | telemetry drift 적응 |
> | Sub-agent 활용 | `agent-design-patterns.md` (부록 §Team Tools API) | Phase 1/5/6/8 sub-agent 격리 시 |
> | Doctrine 박제·갱신·refit | `doctrine-registry.md` | 신규 doctrine 박제, 기존 doctrine 갱신, plugin upgrade 후 refit 진단 |
>
> **trigger:** LLM은 phase 진입 시점에 위 매핑 표를 보고 *해당 phase에 대응하는 reference만* read. cross-phase 참조 필요 시 (예: Phase 5에서 Phase 2 intent profile 다시 read) 명시적으로 *재read* — silent prefetch 금지.
>
> **검증:** 각 reference 상단 헤더와 본 표 일치 — `harness-validate`가 향후 chain 검증에 포함 가능 (P0-2 doctrine 정합).

- **Phase Entry Gates** (Phase 0/0.5/1/2/5 entry 게이트 doctrine 박스 모음, 2026-05-23 P2-A 분리): `references/phase-entry-gates.md`
- **Output Checklist** (must 9 / should 9 항목 catalog, 2026-05-23 P2-A 분리): `references/output-checklist.md`
- **Doctrine Registry** (전 영역 doctrine 단일 색인 — id·박제 위치·근거 commit·정합 점검, 2026-05-23 P9): `references/doctrine-registry.md`
- 하네스 패턴: `references/agent-design-patterns.md`
- 기존 하네스 예시 (실제 파일 전문 포함): `references/team-examples.md`
- 오케스트레이터 템플릿: `references/orchestrator-template.md`
- **스킬 작성 가이드**: `references/skill-writing-guide.md` — 작성 패턴, 예시, 데이터 스키마 표준
- **스킬 테스트 가이드**: `references/skill-testing-guide.md` — 테스트/평가/반복 개선 방법론
- **QA 에이전트 가이드**: `references/qa-agent-guide.md` — 통합 정합성 검증, 경계면 버그 패턴, QA 정의 템플릿 (`qa-agent-guide.md §6` ML/data/mobile/devops 도메인 경계 카탈로그)
- **Code Research 방법론**: `references/code-research.md` — greenfield/brownfield 감지, 5축 조사, quick scan vs deep audit
- **Code Research Deep 축** (분할 #2, 2026-05-31): `references/code-research-deep.md` — deep audit 전용 Maturity·Pain Points 2축 상세 조사 기법
- **Project Profile 스키마**: `references/project-profile-schema.md` — Phase 1 출력 표준 형식
- **Project Inquiry 가이드**: `references/project-inquiry.md` — 두 브랜치별 채우기 전략, profile-finding → question 매핑 룰
- **Intent Profile 스키마**: `references/intent-profile-schema.md` — Phase 2 출력 표준 형식 + meta 필드 의미 + 검증 룰
- **Intent Profile 예시** (분할 #1, 2026-05-31): `references/intent-profile-examples.md` — greenfield/brownfield 완성 인스턴스 예시 2종
- **Intent Profile Advisory** (PB5 분리, 2026-05-27): `references/intent-profile-advisory.md` — LLM-only 권장 룰 + cross-field 경고 3종 (Phase 2 합성 직전 final review)
- **Advisor Integration** (PB6 분리, 2026-05-27): `references/advisor-integration.md` — methodology-advisor v0.3.x handoff 변환 룰 + cross-field invariant (advisor 위임 분기 시점만 read)
- **Runtime Adaptation 가이드**: `references/runtime-adaptation.md` — Phase 10 capture 신호, diagnostic 룰, adapt 룰, 승인 UX
- **Runtime Telemetry Schema** (분할 #3, 2026-05-31): `references/runtime-telemetry.md` — telemetry 저장 형식·이벤트 타입 7종·공통 규약
- **Permission Profiles (main)**: `references/permission-profiles.md` — §0 진입 매트릭스 + §1 3-layer / §4 결정 트리 / §6 안전 정책 / §9 plugin subagent 제약 (분리 본문은 profiles/inventory/synthesis/dynamic-adoption/empirical)
- **Permission Profiles Profiles** (PA5 분리, 2026-05-28): `references/permission-profiles-profiles.md` — §2 8 capability profile 본문 (code-test / web-research / external-integration / reasoning-aux + ml-pipeline / devops-infra / mobile-native / data-eng)
- **Permission Profiles Empirical** (PA5 분리, 2026-05-28): `references/permission-profiles-empirical.md` — §8 검증 상태 (공식 docs ✓ + empirical ✓✓ + 외부 의제) + §8-3 stdio probe 기법 + §11-1~§11-4 실증 reproducer fixture
- **Permission Profiles Inventory** (P7 분리): `references/permission-profiles-inventory.md` — §3 MCP 후보 인벤토리 + §3-0 verification_status + §3-1 T0 매트릭스
- **Permission Profiles Synthesis** (P7 분리): `references/permission-profiles-synthesis.md` — §5-1 에이전트 frontmatter 합성 (a/b/c — Layer B / Layer A+B / 모델 by role Q2 doctrine)
- **Permission Profiles Dynamic Adoption** (P7 분리): `references/permission-profiles-dynamic-adoption.md` — §10 5-step + §10-D rollback + §10-G multi-writer (P4)
- **MCP Recommendation 엔진**: `references/mcp-recommendation.md` — Phase 5-2 합성 시 자동 추천 (신호 추출·후보 풀·3축 점수·캐시·거부 학습, 10 신호 S1~S10)
- **Heuristics Baseline** (PB2 통합, 2026-05-27): `references/heuristics-baseline.md` — Phase 1·5-2·6·8·10 휴리스틱 임계값 통합 catalog (4 doc 표 → 1 단일 출처). 원 doc 본문은 1줄 pointer만 보유
- **Trigger Keyword Catalog**: `references/trigger-keyword-catalog.md` — 10 signal × Korean·English 키워드 단일 출처 (P6-8, 2026-05-14). Phase 5 description 작성 + Phase 5-2 signal 추출 시 should/NOT 예시 catalog
