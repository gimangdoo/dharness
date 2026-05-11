---
name: harness
description: "하네스를 구성합니다. 전문 에이전트를 정의하며, 해당 에이전트가 사용할 스킬을 생성하는 메타 스킬. (1) '하네스 구성해줘', '하네스 구축해줘' 요청 시, (2) '하네스 설계', '하네스 엔지니어링' 요청 시, (3) 새로운 도메인/프로젝트에 대한 하네스 기반 자동화 체계를 구축할 때, (4) 하네스 구성을 재구성하거나 확장할 때, (5) '하네스 점검', '하네스 감사', '하네스 현황', '에이전트/스킬 동기화' 등 기존 하네스 운영/유지보수 요청 시 사용."
---

# Harness — Agent Team & Skill Architect

도메인/프로젝트에 맞는 하네스를 구성하고, 각 에이전트의 역할을 정의하며, 에이전트가 사용할 스킬을 생성하는 메타 스킬.

**핵심 원칙:**
1. 에이전트 정의(`.claude/agents/`)와 스킬(`.claude/skills/`)을 생성한다.
2. **에이전트 팀을 기본 실행 모드로 사용한다.**
3. **CLAUDE.md에 하네스 포인터를 등록한다.** — 새 세션에서 오케스트레이터 스킬이 트리거되도록 최소한의 포인터(트리거 규칙 + 변경 이력)만 기록한다.
4. **하네스는 고정물이 아니라 진화하는 시스템이다.** — 매 실행 후 피드백을 반영하고, 에이전트·스킬·CLAUDE.md를 지속 갱신한다.

## 워크플로우

### Phase 0 (Pre-flight): 기존 하네스 감사

> **메타 단계** — 프로젝트 코드가 아니라 **기존 하네스 산출물**(`.claude/agents/`, `.claude/skills/`, `CLAUDE.md`)의 현황을 확인하여 실행 모드를 결정한다. 프로젝트 코드 분석은 Phase 1부터 시작된다. Phase 0는 항상 실행되며 건너뛸 수 없다.

1. `프로젝트/.claude/agents/`, `프로젝트/.claude/skills/`, `프로젝트/CLAUDE.md`를 읽는다
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

### Phase 1: Code Research

프로젝트의 객관적 baseline을 추출. 결과 `_workspace/_baseline/project_profile.md`는 (a) Phase 3의 입력, (b) Phase 10의 t=0 anchor.

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

**브랜치별 채우기:**
| 브랜치 | 방식 |
|------|-----|
| **greenfield** | 7섹션 순차 질문, 모든 필드 사용자 입력 |
| **brownfield** | 4단계 — 자동 추론 → 확인 → 갭 메우기 → 코드 grounded 질문 |

**필수 5개 (스킵 불가):** `constraints.tech_stack`, `constraints.team.size`, `constraints.timeline.horizon`, `architecture.deployment_target`, `quality.test_rigor`. 그 외는 스킵 가능, 스킵 시 `meta.open_questions`에 등록.

> 채우기 전략 상세, 자동 추론 매핑, 코드 grounded 질문 패턴(13종), 섹션별 질문 카탈로그는 `references/project-inquiry.md`. 풀 schema와 인스턴스 예시는 `references/intent-profile-schema.md`.

### Phase 3: 도메인 분석

1. 사용자 요청에서 도메인/프로젝트 파악
2. **Project Profile + Intent Profile 합성** — 객관 신호와 주관 의도 통합으로 도메인 모델 도출
3. 핵심 작업 유형 식별 (생성, 검증, 편집, 분석 등)
4. Phase 0 감사 결과를 기반으로 기존 에이전트/스킬과의 충돌/중복 분석
5. **사용자 숙련도 감지** — 대화 단서로 기술 수준 파악, 이후 커뮤니케이션 톤 조절. 코딩 경험 적은 사용자에게 "assertion", "JSON schema" 등 용어 무설명 사용 금지.

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

**모든 에이전트는 반드시 `프로젝트/.claude/agents/{name}.md` 파일로 정의한다.** 빌트인 타입(`general-purpose`, `Explore`, `Plan`)을 사용하더라도 정의 파일 생성 필수. Agent 도구의 prompt에 역할을 직접 넣는 것은 금지. 이유: 다음 세션 재사용성, 협업 프로토콜 명시, 에이전트(누가)와 스킬(어떻게) 분리.

**모델 설정:** 모든 에이전트 `model: "opus"`. Agent 호출 시 `model: "opus"` 파라미터 명시 필수 — 하네스 품질은 추론 능력에 직결.

**팀 재구성:** 세션당 한 팀만 활성. Phase 간 팀 해체/재구성 가능. 이전 팀 산출물을 파일로 저장 후 새 팀 생성.

**필수 섹션:** 핵심 역할, 작업 원칙, 입력/출력 프로토콜, 에러 핸들링, 협업. 팀 모드에선 `## 팀 통신 프로토콜` 섹션 추가 (메시지 수신/발신 대상, 작업 요청 범위 명시).

**QA 에이전트 포함 시 필수:**
- 타입은 `general-purpose` (`Explore`는 읽기 전용이라 검증 스크립트 실행 불가)
- 핵심은 "존재 확인"이 아니라 **"경계면 교차 비교"** — API 응답과 프론트 훅을 동시에 읽고 shape 비교
- 전체 완성 후 1회가 아니라 **각 모듈 완성 직후 점진 실행** (incremental QA)

> 정의 템플릿과 실제 파일 전문은 `references/agent-design-patterns.md` + `references/team-examples.md`. QA 상세 가이드는 `references/qa-agent-guide.md`.

**도구·MCP 자동 할당 (Phase 5-2):** 에이전트의 `tools:` allowlist와 프로젝트 `.claude/settings.json`·`.mcp.json` 합성은 *제안 후 사용자 confirm* 절차를 따른다. capability profile 카탈로그(`code-test`/`web-research`/`external-integration`/`reasoning-aux`), 3-layer 권한 모델, 안전 정책, 결정 트리는 `references/permission-profiles.md` 단일 출처. 자동 install·자동 `allow` 승급은 T0(무키·로컬) 한정. **default 합성 패턴은 §5-1 inline `mcpServers:` (parent 미적재 — 공식 docs 기반 권고)** — toolset 지원 MCP는 §5-1-b Layer A+B 결합형(서버 측 advertise 축소까지 동시 적용), 미지원 MCP는 §5-1-a Layer B 단독. `.mcp.json` 등록(§5-2)은 parent 직접 호출 필연성 등 *3 예외 조건* 충족 시에만 anti-pattern으로 한정. **inline `mcpServers:` schema는 *list-of-dicts + `type: stdio`* 필수** (9차 사이클 docs 발췌 확정 — plain dict는 silent skip).

> **합성 시점 vs 런타임 시점 분리**
> - *합성 시점*(Phase 5-2): `references/permission-profiles.md` §3-§7 — 에이전트 생성 시 1회.
> - *런타임 시점*(프로젝트 진행 중 신규 MCP 채택 필요): `references/permission-profiles.md` §10 dynamic adoption — 트리거 신호 3종 + 5-step 절차 + 프로젝트 유형별 매트릭스(web/data/mobile/research/devops) + rollback. 진입 명령은 `/harness:harness-mcp-adopt <사유>`. 채택 *전후* 진단(인벤토리·매트릭스·정합·trigger 자동 감지)은 `/harness:harness-mcp-status` (read-only).
> - *PoC 진척*: `references/permission-profiles.md` §11 + `references/fixtures/` 4종 reproducer. **§11-1 ✓** (6차) / **§11-3 fixture 본문 갱신** (7차, 3축 메트릭) / **§11-4 e2e ✓** (8차, sqlite 시연으로 §10 5-step 검증) / **§11-2 P0 ✅** (10차, 정정 schema로 양면 empirical 확정 + 🆕 `tools:` allowlist는 inline 서버 도구 통제에 무력 발견) / **§11-3 P1 부분 closure** (13차, `claude -p` mode — project-scope settings.json 토글은 deferred pool 영향 0 부정) / **P2 T0 batch ✅** (filesystem 14 / time 2 / memory 9 — probe-only enum) / **14차 §3-1 매트릭스 박제** (7 T0 MCPs × 4 capability profile 정합 → 합성 시점의 *런타임 가용 default 카탈로그*, web-research 2번째 synthesis_example 동시 박제) / **15차 self-verify ✅** (`harness-mcp-status` self-test로 14차 cycle 산출물 4건 empirical 작동 확인 — 섹션 2 advertise mismatch 감지 / 섹션 3 §3-1 정합 점검 / 섹션 4 fallthrough 룰 / 섹션 6 토큰 임계) / **15차 P3-(b) closure** (`claude -p` mode — user-scope `enabledMcpjsonServers` + `hasTrustDialogAccepted` 양쪽 모두 deferred pool 영향 0 부정 → `claude -p` 모드가 모든 `~/.claude.json` gate 키를 우회한다는 강력 가설 격상, 인터랙티브 비교만 잔존) / **16차 B8 closure** (`disabledMcpjsonServers=["sqlite"]` 명시 차단도 영향 0 — `~/.claude.json` 4-key gate 매트릭스 *전부* falsified, `-p` auto-trust 사실상 확정 / 마지막 분기는 인터랙티브 `verify_11_3_p3c.md` 외부 1회) / **17차 T1+T1+ docs 박제 📜** (WebFetch로 7 MCP 공식 docs enum: playwright 23+caps / chrome-devtools 44 / brave 8 / tavily 4 (도구명 하이픈 첫 케이스) / exa 3+deprecated / firecrawl 10+deprecated / github 19 toolset + npm 패키지 없음 정정 — Docker/Go만; dharness 본 세션 probe 시도는 classifier가 `npx -y` 패턴 차단 → §6 정책 실효성 *T1 패키지에서도 재확인*) / **18차 T1+ probe fixture 5종 박제** (`probe_brave_search`/`tavily`/`exa`/`github`/`firecrawl` — JSON-RPC stdio 핑 패턴 + env 키 placeholder + deprecated 자동 태깅 + `probe_github.js`는 Docker spawn + `GITHUB_TOOLSETS` 3 조합 비교 측정 의도, 본 세션 spawn 0회 → API 키 보유 시점 외부 실행자가 enum 확정; commit 분담 회피: `8322c79`(17차) → `af781a0`(18차) 자연 정렬). 결과는 `fixtures/README.md` 결과 로그에 누적.
>
> **운영 함의 (cycle 11 누적):**
> - mid-session `claude mcp add`는 본 세션·기 spawn된 서브에이전트에 *미전파* (4차 — 양면 검증). Phase 5-2 합성 직후 새 MCP 의존 에이전트 사용 시 **"다음 세션부터 사용 가능"** 명시 필수.
> - **uvx-기반 MCP의 경로 인자(`--db-path`, `--repository` 등)는 절대경로 필수** (8차 sqlite empirical) — 상대경로면 health check `✗ Failed to connect`.
> - **§6 자동 install 금지 정책은 dharness root 외부에서도 동일 enforcement** — derived 프로젝트의 inline `mcpServers:` 작성도 untrusted external code execution으로 차단됨 (8차 self-test 재확인). 사용자 명시 동의 후 통과.
> - plugin-bundled subagent는 `mcpServers`/`permissionMode`/`hooks` 무시(§9) — derived 하네스를 plugin 패키징 시 inline `mcpServers:`는 무력화됨에 주의.
> - **🆕 `tools:` allowlist는 inline 서버 도구를 줄이지 못한다** (10차 P0 새 발견) — Layer B 격리는 *parent isolation*에만 ✅ 작동, 도구 카운트 통제는 ❌. inline 서버의 부수 효과 도구 차단은 (a) Layer A 서버 측 advertise 필터(toolset 지원 MCP) 또는 (b) `permissions.deny` 박제(미지원 MCP) — `ask` 강등은 부족(사용자 confirm으로 통과). 정합 점검은 `/harness:harness-mcp-status` §4 신규 항목 참조.

### Phase 6: 스킬 생성

각 에이전트가 사용할 스킬을 `프로젝트/.claude/skills/{name}/SKILL.md`에 생성.

**구조:**
```
skill-name/
├── SKILL.md (필수: YAML frontmatter + Markdown 본문)
└── (선택) scripts/  references/  assets/
```

**핵심 룰:**
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

#### 7-4. CLAUDE.md 하네스 포인터 등록

새 세션마다 로딩되므로 **포인터(트리거 규칙) + 변경 이력**만 기록. 에이전트/스킬 목록·디렉토리 구조·실행 룰 상세는 넣지 않음(중복).

````markdown
## 하네스: {도메인명}

**목표:** {핵심 목표 한 줄}

**트리거:** {도메인} 관련 작업 요청 시 `{orchestrator-skill-name}` 스킬을 사용하라. 또는 `/harness:harness-*` slash command로 명시적 호출 (`/harness:harness-add-agent`, `/harness:harness-adapt` 등 — 카탈로그는 dharness `README.md`의 "Slash command 카탈로그" 섹션). 단순 질문은 직접 응답 가능.

**Phase 10 자동 알림:** 세션 시작 시 `_workspace/_telemetry/`의 최신 `.jsonl` 파일을 확인하라. 마지막 Adapt 시각(= `_workspace/_telemetry/_delta_*.md` 또는 `_workspace/_telemetry/_rollback/{ts}/` 중 가장 최근 mtime, 둘 다 없으면 telemetry 첫 이벤트의 ts) 이후 `"type":"harness_invocation"` 이벤트 수가 10회 이상이면, 사용자에게 알린다: "하네스가 {N}회 실행되었습니다. `/harness:harness-adapt`로 drift 점검을 권장합니다." — telemetry 파일이 없거나 읽기 비용이 클 경우 건너뛴다.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| {YYYY-MM-DD} | 초기 구성 | 전체 | - |
````

#### 7-5. 후속 작업 지원

오케스트레이터는 초기 실행뿐 아니라 후속 작업도 처리해야 한다.

1. **description에 후속 키워드 포함** — "다시 실행/재실행/업데이트/수정/보완", "{도메인}의 {부분작업}만 다시", "이전 결과 기반/결과 개선"
2. **오케스트레이터 Phase 1에 컨텍스트 확인 단계** — `_workspace/` 존재 + 부분 수정 → 부분 재실행 / `_workspace/` 존재 + 새 입력 → 새 실행(`_workspace_prev/`로 이동) / 미존재 → 초기 실행
3. **에이전트 정의에 재호출 지침** — 이전 결과 파일 존재 시 읽고 개선점 반영, 사용자 피드백 시 해당 부분만 수정

> 패턴별 골격 상세, 에러 유형별 전략표, 데이터 흐름 다이어그램, Phase 0 컨텍스트 확인 템플릿은 `references/orchestrator-template.md`.

### Phase 8: 검증 및 테스트

생성된 하네스를 검증한다.

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

매 하네스 실행 완료 후 사용자에게 피드백 요청 — "결과에서 개선할 부분이 있나요?" / "팀 구성·워크플로우에 바꿀 점이 있나요?". 강요하지 않되 기회는 반드시 제공.

#### 9-2. 피드백 반영 경로

| 피드백 유형 | 수정 대상 | 예시 |
|-----------|----------|------|
| 결과물 품질 | 해당 에이전트의 스킬 | "분석이 너무 피상적" → 스킬에 깊이 기준 추가 |
| 에이전트 역할 | 에이전트 정의 `.md` | "보안 검토도 필요" → 새 에이전트 추가 |
| 워크플로우 순서 | 오케스트레이터 스킬 | "검증을 먼저 해야" → Phase 순서 변경 |
| 팀 구성 | 오케스트레이터 + 에이전트 | "이 둘은 합쳐도 될 듯" → 에이전트 병합 |
| 트리거 누락 | 스킬 description | "이 표현으로 작동 안 함" → description 확장 |

#### 9-3. 변경 이력

모든 변경은 CLAUDE.md 변경 이력 테이블(Phase 7-4 템플릿)에 기록. 출처를 명시하여 Phase 9 변경과 Phase 10 자동 감지를 구분 — `Phase 9: 사용자 피드백 — {요약}` vs `Phase 10: drift 감지 ({drift 이름})`.

#### 9-4. 진화 트리거

명시 요청("하네스 수정해줘", `/harness:harness-evolve <피드백>`)뿐만 아니라:
- 같은 유형의 피드백이 2회 이상 반복 → `/harness:harness-audit`로 구조적 점검 권고
- 에이전트가 반복 실패하는 패턴 → `/harness:harness-adapt`로 telemetry 기반 사용 drift 분석 권고
- 사용자가 오케스트레이터 우회하여 수동 작업 → `/harness:harness-audit`의 변경 이력 누락 검사 권고

#### 9-5. 운영/유지보수 워크플로우

Phase 0에서 "운영/유지보수"로 분기 시 진입. 명시적 진입점은 `/harness:harness-audit` (read-only 정합성 감사).

1. **현황 감사** — `.claude/agents/` ↔ 오케스트레이터 에이전트 구성 비교, `.claude/skills/` ↔ 스킬 구성 비교 → 불일치 보고 (`/harness:harness-audit`이 자동 수행)
2. **점진적 추가/수정** — 한 번에 하나씩, 각 변경 후 즉시 동기화(Step 3)
3. **CLAUDE.md 변경 이력 갱신** — 날짜·내용·대상·사유
4. **변경 검증** — 구조(8-1), 트리거 영향 시 트리거(8-4), 대규모 변경(아키텍처 변경, 에이전트 3+ 추가/삭제) 시 실행 테스트(8-3) + 드라이런(8-5)

### Phase 10: Runtime Adaptation

Phase 9가 사용자 피드백을 **수동**으로 수집한다면, Phase 10은 프로젝트 변화와 하네스 사용 패턴을 **자동 관측**하고 baseline에서 벗어난 부분을 사용자에게 제안한다. 모든 변경은 **제안 + 승인** 모델 — Phase 10이 자동 적용하는 변경은 없다.

#### 10-1. 3 레이어 구조

| 레이어 | 역할 | 출력 위치 |
|------|------|----------|
| **Capture** | 매 실행마다 프로젝트 + 사용 신호 캡처 | `_workspace/_telemetry/{date}.jsonl` |
| **Diagnostic** | 누적 telemetry ↔ baseline 비교, drift 감지 | `_workspace/_telemetry/_delta_{ts}.md` |
| **Adapt** | drift 변경안 제시, 승인 시 적용 | `.claude/agents/`, `.claude/skills/`, `CLAUDE.md`, `_baseline/*.md` |

#### 10-2. 트리거 조건

| 트리거 | 조건 |
|------|------|
| **수동** | "하네스 점검", "drift 확인", "적응", "baseline 갱신" 등 키워드 / `/harness:harness-adapt` 명시 호출 |
| **주기적** | 마지막 Adapt 이후 N회(기본 10) 하네스 실행 누적 |
| **임계** | 단일 큰 drift (새 프레임워크, 보안 취약점 검출 등) |

#### 10-3. drift 두 종류 구분

- **baseline drift**: 프로젝트 자체가 변함 (새 의존성, 새 디렉토리, 커버리지 변화) → `project_profile.md` 갱신 + 영향 받는 에이전트/스킬 점검
- **사용 drift**: 프로젝트는 같지만 하네스 사용 패턴이 변함 (특정 에이전트 미사용, 반복 실패, 사용자 우회) → 에이전트/스킬 자체 재구성

두 종류는 같은 delta 리포트에 분리된 섹션으로 보고된다.

#### 10-4. 신뢰도 가중치 — Phase 2 메타 활용

Phase 2의 `meta.inferred_fields − meta.user_confirmed_fields` 차집합("신뢰도 낮음" 필드)을 가중. 신뢰도 낮은 필드의 baseline drift는 변경안 제시 전 "원래 추론이 맞았는지" 사용자 확인을 먼저 트리거. 신뢰도 높은 필드의 drift는 변경안 직접 제시.

#### 10-5. Phase 9와의 관계

| | Phase 9 (수동 진화) | Phase 10 (Runtime Adaptation) |
|--|---|---|
| 트리거 | 사용자 명시 피드백 | 자동 감지 + 사용자 명시 점검 |
| 입력 | 사용자 발화 | telemetry + baseline |
| 변경 범위 | 사용자가 지목한 부분 | 시스템이 감지한 모든 drift |

두 Phase는 동일한 변경 이력 테이블(Phase 7-4 템플릿)을 공유한다.

#### 10-6. 안전 메커니즘 (적용·검증·복원)

모든 Adapt 적용은 **chain 단위 + 사전 스냅샷 + 사후 검증 + (실패 시) 자동 rollback**으로 처리. 단일 drift라도 부수 갱신이 필요한 산출물이 있으면 atomic하게 묶여 적용된다.

| 메커니즘 | 역할 |
|------|------|
| **Cross-artifact chain** | 1차 변경의 부수 갱신 산출물을 묶어 atomic 적용 (dangling 참조 방지) |
| **패치 미리보기** | 한 줄 요약이 아닌 실제 diff 표시, chain 항목 모든 파일 포함, 민감 정보 마스킹 |
| **사전 스냅샷** | 적용 직전 영향 파일을 `_workspace/_telemetry/_rollback/{ts}/`에 복사 + manifest 기록 |
| **Post-Adapt 회귀 검증** | 변경 종류별 Phase 8의 영향 단계만 자동 재실행 (예: description 변경 → 8-4 트리거 검증) |
| **자동 rollback** | 검증 실패 또는 사용자 명시 요청 시 스냅샷으로 복원, 거부 학습 룰 적용 |

> 상세 telemetry schema, capture 신호 목록(7종 이벤트), diagnostic 룰, adapt 룰, 승인 UX, 안전 메커니즘(chain·diff·rollback·회귀 검증)은 `references/runtime-adaptation.md`.

## 산출물 체크리스트

생성 완료 후 확인:

- [ ] **`_workspace/_baseline/project_profile.md`** — Phase 1 산출물 (greenfield/brownfield 무관 항상 생성)
- [ ] **`_workspace/_baseline/intent_profile.md`** — Phase 2 산출물, schema 준수 (frontmatter + body)
- [ ] **brownfield의 경우**: project_profile.md의 5축 (또는 quick scan의 3축) 모두 채워짐
- [ ] Intent profile의 필수 5개 필드 채워짐 (`tech_stack`, `team.size`, `timeline.horizon`, `deployment_target`, `test_rigor`)
- [ ] 스킵된 필드는 `meta.open_questions`에 등록됨
- [ ] (brownfield) `meta.inferred_fields`와 `meta.user_confirmed_fields` 둘 다 기록됨
- [ ] `프로젝트/.claude/agents/` — **에이전트 정의 파일 필수 생성** (빌트인 타입이라도 파일 생성 필수)
- [ ] `프로젝트/.claude/skills/` — 스킬 파일들 (SKILL.md + references/)
- [ ] 오케스트레이터 스킬 1개 (데이터 흐름 + 에러 핸들링 + 테스트 시나리오 포함)
- [ ] 실행 모드 명시 (에이전트 팀 / 서브 에이전트 / 하이브리드 중 선택, 하이브리드면 Phase별 모드 기재)
- [ ] 모든 Agent 호출에 `model: "opus"` 파라미터 명시
- [ ] **사용자 프로젝트의 `.claude/commands/`에는 아무것도 생성하지 않음** (harness 플러그인 본체의 `commands/`는 별개 — L1 진입점이며 본 체크리스트 범위 외)
- [ ] 기존 에이전트/스킬과 충돌 없음
- [ ] 스킬 description이 적극적("pushy")으로 작성됨 — **후속 작업 키워드 포함**
- [ ] SKILL.md 본문이 500줄 이내, 초과 시 references/ 분리
- [ ] 테스트 프롬프트 2~3개로 실행 검증 완료
- [ ] 트리거 검증 (should-trigger + should-NOT-trigger) 완료
- [ ] **CLAUDE.md에 하네스 포인터 등록** (트리거 규칙 + 변경 이력)
- [ ] **CLAUDE.md 변경 이력에 에이전트/스킬 추가/삭제/수정 기록**
- [ ] **오케스트레이터 Phase 1에 컨텍스트 확인 단계** (초기/후속/부분 재실행 판별)
- [ ] **`_workspace/_telemetry/` 디렉토리 생성** (Phase 10 capture 출력 위치 사전 확보)
- [ ] **`_workspace/_telemetry/_rollback/` 디렉토리 사전 생성** (Adapt 적용 시 스냅샷 저장 위치)
- [ ] **오케스트레이터에 telemetry capture 훅 삽입** (매 실행 시 `_telemetry/{date}.jsonl`에 이벤트 append)
- [ ] **Phase 10 트리거 키워드를 오케스트레이터 description에 포함** ("점검", "drift", "적응", "baseline 갱신")
- [ ] **CLAUDE.md에 Phase 10 자동 알림 지침 포함** (세션 시작 시 telemetry 카운터 확인, 10회 누적 시 `/harness:harness-adapt` 알림 — Phase 7-4 템플릿 준수)

## 참고

- 하네스 패턴: `references/agent-design-patterns.md`
- 기존 하네스 예시 (실제 파일 전문 포함): `references/team-examples.md`
- 오케스트레이터 템플릿: `references/orchestrator-template.md`
- **스킬 작성 가이드**: `references/skill-writing-guide.md` — 작성 패턴, 예시, 데이터 스키마 표준
- **스킬 테스트 가이드**: `references/skill-testing-guide.md` — 테스트/평가/반복 개선 방법론
- **QA 에이전트 가이드**: `references/qa-agent-guide.md` — 통합 정합성 검증, 경계면 버그 패턴, QA 정의 템플릿
- **Code Research 방법론**: `references/code-research.md` — greenfield/brownfield 감지, 5축 조사, quick scan vs deep audit
- **Project Profile 스키마**: `references/project-profile-schema.md` — Phase 1 출력 표준 형식
- **Project Inquiry 가이드**: `references/project-inquiry.md` — 두 브랜치별 채우기 전략, profile-finding → question 매핑 룰
- **Intent Profile 스키마**: `references/intent-profile-schema.md` — Phase 2 출력 표준 형식 + greenfield/brownfield 인스턴스 예시
- **Runtime Adaptation 가이드**: `references/runtime-adaptation.md` — Phase 10 telemetry schema, capture 신호, diagnostic 룰, adapt 룰, 승인 UX
