# PLAN — dharness Evolution

> 본 문서는 **다중 세션 이어가기**용 작업 계획. 모든 세션은 시작 시 §6 "Session Pickup Protocol"을 따른다.

- **상태**: draft / not started
- **마지막 업데이트**: 2026-05-13 (revision 2 — 사용자 의도 반영)
- **감사 baseline**: 본 commit (감사 결과 §2)
- **목표 완료 시점**: 미정 (P0/P1/P6 우선)

---

## §1 목표

프로젝트 전반 harness 설계 + 진행/수정/추가/삭제에 따른 자동 조정 프로그램. **plugin package(`plugins/harness/`)로 외부 프로젝트 배포되어 개별 프로젝트마다 harness setting 실행하는 의도.** CM(`.claude/` + `_workspace/`)은 dharness 본 폴더 dogfooding 영구 한정 — 외부 install·일반화 X (§7 결정 2026-05-13B 박제).

현 dharness 골격은 11 phase로 그 방향을 박제했고 핵심 루프(`PostToolUse → 분류 → draft → apply`) 1건이 라이브로 검증됨 (live `/cm-status`: `observations 7 / draft 1 pending / 변경 이력 4 rows`).

**현재 → 목표**: production-ready ~70% → 90%+. 3대 lever:
1. **최초 setting 품질·정확도 극대화** (Phase 0.5/3.5/5.5/7.5 self-critique + sub-agent 활용 + LLM·deterministic hybrid)
2. **factory 신뢰성** (실 API schema 박제 + 결정적 검증 분리)
3. **Claude Code file read context 효율** (영문 hybrid 마이그레이션 — SKILL.md + references/ + commands/ 본문)

doctrine 박제: **결정·persistence는 deterministic, 추론·합성은 LLM, 검증은 양방향 cross-check** (§7 결정 2026-05-13C).

---

## §2 감사 요약 (2026-05-13)

### 강점

| 영역 | 상태 |
|------|------|
| Phase 0~10 doctrine 일관성 | ✅ |
| `project-profile-schema.md` / `intent-profile-schema.md` | ✅ 결정적 다운스트림 처리 가능 |
| `permission-profiles.md` 12+ cycle empirical 박제 | ✅ |
| QA 가이드 (실제 버그 7건 추출) | ✅ |
| CM "변경 이력 자동 draft" 회로 | ✅ live 검증 |
| test_schema 37/37 pass | ✅ |

### 결손 (우선순위 순)

| ID | 결손 | 차단도 |
|----|------|--------|
| G1 | `TeamCreate`/`SendMessage`/`TaskCreate` 실 API schema 부재 — references 모두 의사코드 | 🔴 High |
| G2 | Phase 10 LLM self-report 의존 (telemetry append, post-adapt 검증, 트리거 20개) — watchdog 0 | 🔴 High |
| G3 | ~~derived 프로젝트 hook 부재 — CM은 dharness 본 폴더 한정 self-host~~ **(폐기)** CM 종속 doctrine 박제됨 (§7 2026-05-13B). plugin 측 결정적 channel(slash command wrapping + plugin scripts)로 대체. | ~~🟡 Mid~~ N/A |
| G4 | `_tool_outputs/` 무제한 증가 — TTL/cap 0 | 🟡 Mid (디스크 부채) |
| G5 | CM dead schema 30% (`daily_summaries`/`clusters`/embedding/digest_path/cluster_id/phase/promoted_path) | 🟡 Mid |
| G6 | `_GIT_RELEVANT` 체인 분류 손실 — `git add X && git commit ...`이 `git_add`로만 분류 | 🟡 Mid |
| G7 | adapt counter wiring 끊김 — `touch_last_adapt()` 호출자 0, monotonic 증가 | 🟡 Mid |
| G8 | 휴리스틱 임계값 근거·튜닝 가이드 부재 (drift ±20%, top-K=3, 트리거 20 등) | 🟢 Low |
| G9 | 도메인 편향 (창작/웹앱) — ML/data/infra/mobile 예시 0 | 🟢 Low |
| G10 | `permission-profiles.md` 873줄 closure summary 부재 | 🟢 Low |
| G11 | `mcp-server-fetch` vs `-typescript` 이름 혼용 (자기 spoofing doctrine 위반) | 🟢 Low |
| G12 | `code-research.md:626` Deep audit "5 subagent 병렬" ↔ Phase 4 "팀 모드 우선" 충돌 | 🟢 Low |
| G13 | session_end race window (자인됨, mitigation 0) | 🟢 Low (bounded) |
| G14 | `cm_commands.py:42` `DRAFT_ROW_RE` brittle | 🟢 Low |
| G15 | `_transcript_utils.py` user/assistant branch dead | 🟢 Low |
| G16 | `settings.local.json` `py ...` Windows-only | 🟢 Low |
| **G17** | **최초 setting multi-pass / self-critique 회로 없음 — Phase 1-7 single-pass LLM 합성, silent error 검출 0** | 🔴 **High** (품질 직결) |
| **G18** | **Phase 1·5·6·8 sub-agent 활용 doctrine 미박제 — parent 컨텍스트 부담 + 깊이 ↓** | 🟡 Mid |
| **G19** | **한국어 doctrine — Claude Code file read context 토큰 비효율 (~1.5-2 tok/char vs 영문 ~0.25). references/ 13 file × ~6000 LOC 누적 부담** | 🟡 Mid (효율) |
| **G20** | **Phase 0 audit은 *기존 산출물*만 점검 — *사용자 입력 도메인 ambiguity* pre-flight 부재. 모호 input silent 진행 가능** | 🟡 Mid |
| **G21** | **trigger 키워드 도메인별 사전 부재 — Phase 6 description "pushy" doctrine은 LLM 자율 채움, 일관성 ↓** | 🟢 Low |
| **G22** | **baseline 5축에 business context · regulatory 누락 — fintech/health/edu 등 도메인 시그널 0** | 🟢 Low |
| **G23** | **PoC 미완 MCP가 합성 default 풀에 섞임 — silent fail 위험 (chrome-devtools/playwright/brave/tavily/exa/firecrawl/slack/postgres)** | 🟡 Mid (정확도) |

---

## §3 작업 Phase

### P0 — 즉시 (디스크 부채 + 신호 정확도)

| ID | 작업 | 해결 결손 | 파일 | 의존 |
|----|------|----------|------|------|
| P0-1 | `_tool_outputs/` TTL + `/cm-cleanup` 명령 | G4 | `.claude/hooks/cm_commands.py`, `.claude/commands/cm-cleanup.md`, `README.md` §troubleshooting | 없음 |
| P0-2 | `_GIT_RELEVANT` 체인 명령 분류 수정 | G6 | `.claude/hooks/_schema.py`, `.claude/hooks/test_schema.py` | 없음 |
| P0-3 | adapt counter wiring 결정 (옵션 A: `touch_last_adapt()` 호출자 추가 / 옵션 B: counter 제거) | G7 | `.claude/hooks/_schema.py`, (옵션 A) `plugins/harness/commands/harness-adapt.md` | 없음 |
| P0-4 | CM dead schema amputation 결정 + 실행 | G5 | `.claude/hooks/_schema.py`, `.claude/hooks/cm_commands.py`, `.claude/hooks/test_schema.py`, `README.md` §Context Manager 표 | P0-3 (counter 결정과 함께) |

#### P0-1 AC (Acceptance Criteria)
- `py .claude/hooks/cm_commands.py cleanup --older-than 30d` 실 작동
- 환경변수 `CM_TOOL_OUTPUTS_TTL_DAYS` (default 30) 지원
- `/cm-cleanup` 슬래시 커맨드 발화 시 dry-run + 확인 게이트
- `test_schema.py`에 cleanup 단위 테스트 1건 추가
- README §troubleshooting 표에 1행 추가

#### P0-2 AC
- `_GIT_RELEVANT` 정규식이 chain 명령에서 마지막 commit subcommand도 추출
- `git add X && git commit -m "..."` 분류 결과: `git_commit` (또는 `git_add+git_commit` 복합 row 2건)
- `test_schema.py`에 chain test 2건 추가 (단일 add, chain add+commit)
- 기존 37/37 pass 유지

#### P0-3 AC
- **옵션 A 선택 시**: `/harness:harness-adapt` 본문에 `touch_last_adapt()` 호출 hook 추가. adapt counter가 alert 1회 발화 후 reset되어 monotonic 증가 정지.
- **옵션 B 선택 시**: `_schema.py:265-322` counter 로직 제거 + `session_start.py` inject 블록에서 alert 블록 제거 + README §inject 표에서 해당 블록 행 삭제.
- 결정 사유를 본 PLAN.md §7 "결정 로그"에 1줄 박제.

#### P0-4 AC
- `_schema.py` DDL에서 unused 컬럼/테이블 제거: `daily_summaries`, `clusters`, `observations.embedding`, `sessions.digest_path`, `observations.completed`, `observations.cluster_id`, `observations.phase`, `observations.promoted_path`
- 기존 데이터 마이그레이션: `ensure_migrations()`에 ALTER DROP COLUMN (SQLite 3.35+) 또는 신규 테이블 복사 후 swap
- `cm_commands.py`에서 해당 컬럼 참조 제거 (`cmd_sessions` digest indicator 등)
- `test_schema.py` migration test 통과
- README §Context Manager 결정적 산출물 표 갱신 (해당 컬럼/테이블 행 제거)
- CLAUDE.md "변경 이력" 표에 1행 추가 (사유: "CM dead schema 정리")

---

### P1 — high impact (factory 신뢰성)

| ID | 작업 | 해결 결손 | 파일 | 의존 |
|----|------|----------|------|------|
| P1-1 | `TeamCreate`/`SendMessage`/`TaskCreate`/`TaskUpdate`/`TaskGet`/`TaskOutput` API schema reference 신설 | G1 | `plugins/harness/skills/harness/references/team-tools-api.md` (신규), `SKILL.md` Phase 4-1/5/7 cross-link | 없음 |
| P1-2 | `mcp-server-fetch` vs `-typescript` 이름 표준화 | G11 | `plugins/harness/skills/harness/references/permission-profiles.md:76, 313, 775` | 없음 |
| P1-3 | `code-research.md:626` Deep audit 권장 doctrine 정합 | G12 | `plugins/harness/skills/harness/references/code-research.md` | 없음 |

#### P1-1 AC
- 6 도구 (`TeamCreate`, `SendMessage`, `TaskCreate`, `TaskUpdate`, `TaskGet`, `TaskOutput`) 각각:
  - 시그니처 (파라미터명·타입·필수/선택)
  - 반환값 schema
  - 1 호출 예시 (실 호출 검증)
  - 실패 모드 (timeout / 권한 / 미존재 agent 등)
- 출처 박제 (Claude Code 공식 문서 URL 또는 실호출 trial 박제)
- `SKILL.md` Phase 4-1 표, Phase 5, Phase 7 "데이터 전달 프로토콜" 표에 cross-link 추가
- `agent-design-patterns.md`·`orchestrator-template.md`·`team-examples.md` 의사코드 영역에 "실 schema는 `team-tools-api.md` 참조" 박스 추가

#### P1-2 AC
- 표준 패키지명 선택 후 (권장: `mcp-server-fetch-typescript` — README 현행 사용) 3 hit 모두 정합
- spoofing risk 박스 정합

#### P1-3 AC
- 충돌 해소: 둘 중 하나로 정합 ("팀 모드 우선"으로 통일 또는 "Deep audit은 예외" 박제)
- README §Skill 워크플로우 11단계 정합

---

### P2 — 도메인 보강 + 문서 위생

| ID | 작업 | 해결 결손 | 파일 | 의존 |
|----|------|----------|------|------|
| P2-1 | `team-examples.md` 3 예시 추가 (data pipeline / ML / infra) | G9 | `plugins/harness/skills/harness/references/team-examples.md` | 없음 |
| P2-2 | `qa-agent-guide.md` host-agnostic 환원 (Next.js 가정 제거) | G9 | `plugins/harness/skills/harness/references/qa-agent-guide.md` | 없음 |
| P2-3 | `permission-profiles.md` closure summary 박스 (상단 50줄 이내) | G10 | `plugins/harness/skills/harness/references/permission-profiles.md` | 없음 |
| P2-4 | 휴리스틱 임계값 근거·튜닝 가이드 박스 | G8 | `runtime-adaptation.md`, `mcp-recommendation.md`, `skill-testing-guide.md`, `code-research.md` 각 본문에 근거·튜닝 박스 추가 | 없음 |

#### P2-1 AC
- 3 예시 각각: 풀 frontmatter + 협업 프로토콜 + 1 통신 다이어그램
- 도메인 카탈로그: data pipeline (ETL/Airflow), ML (training/eval/deploy), infra (Terraform/IaC)

#### P2-2 AC
- Next.js·React·`fetchJson<T>` 등 web-specific 표현을 도메인 중립으로 추상화
- 도메인별 경계면 패턴 표 (web / mobile / CLI / data / ML / infra) 1건 추가

#### P2-3 AC
- 873줄 본문 상단에 "현재 상태 closure summary" 박스
- 분류: empirical 검증 / docs 박제 / 미완 3개 컬럼
- 50줄 이내

#### P2-4 AC
- 각 임계값에 근거 1줄 (휴리스틱 / 경험치 / 측정 출처) + 튜닝 가이드 1줄 (도메인별 권장 조정 방향)

---

### P3 — Phase 10 fail-safe + plugin 측 결정적 channel

> **P3-2 폐기** (CM 종속 doctrine — §7 2026-05-13B). derived 프로젝트 hook 합성 X. 대신 plugin scripts/ + slash command wrapping으로 결정적 channel 확보 (P3-4 신규).

| ID | 작업 | 해결 결손 | 파일 | 의존 |
|----|------|----------|------|------|
| P3-1 | Phase 10 telemetry append watchdog (LLM self-report 결손 surface) | G2 | `plugins/harness/skills/harness/references/runtime-adaptation.md`, `orchestrator-template.md` | P0-4 (counter 결정 선결) |
| ~~P3-2~~ | ~~derived 프로젝트용 hook 패키지화~~ **(폐기 — §7 2026-05-13B CM 종속 doctrine)** | ~~G3~~ | — | — |
| P3-3 | post-adapt 회귀 검증 cross-check 자동화 | G2 | `runtime-adaptation.md` §9, `plugins/harness/scripts/validate/post_adapt_check.py` (신규) | P1-1 (API schema 박제 후 호출 가능) |
| **P3-4** | **plugin 측 결정적 channel — `/harness:harness-validate` 신규 slash command (구조·schema·dangling 결정적 검증)** | **G2, G17** | `plugins/harness/commands/harness-validate.md` (신규), `plugins/harness/scripts/validate/{structure,schema,chain}.py` (신규) | P1-1 (API schema 박제 후 LLM 호출 검증부 가능) |

#### P3-1 AC
- derived 프로젝트의 LLM telemetry append 결손율 측정 메커니즘 (예: SessionStart 시 `_telemetry/*.jsonl` 마지막 N 세션 이벤트 수가 SKILL.md 실행 횟수보다 적으면 warning)
- inject 블록에 결손 surface
- 측정 알고리즘 박제 + 검증 룰

#### ~~P3-2 AC~~ **(폐기)**

#### P3-3 AC
- 변경 종류별 (8-1~8-7) 재실행 단계가 LLM grep self-report가 아닌 결정적 스크립트로 cross-check
- 실패 시 자동 rollback 트리거 wiring 검증 (rollback manifest 실 활용)

#### P3-4 AC
- `/harness:harness-validate` 호출 시 3 deterministic 검사 실행:
  - `validate_structure.py` — frontmatter name/description, YAML 파싱, 필수 섹션 grep
  - `validate_schema.py` — `_baseline/*.md` schema 강제 (frontmatter + body + 필수 5 필드)
  - `validate_chain.py` — runtime-adaptation.md §6 chain 표 기준 dangling 참조 grep
- JSON report 출력 (`_workspace/_audit_validate_{ts}.json`)
- LLM 호출 0. plugin 번들 script로 host-agnostic
- `harness-audit` (LLM) ↔ `harness-validate` (deterministic) 분리 — audit이 validate 결과 input으로 받음

---

### P4 — CM 추가 단순화 (선택, 시간 여유 시)

| ID | 작업 | 해결 결손 | 파일 |
|----|------|----------|------|
| P4-1 | session_end race window mitigation (sessionId clear or transactional close) | G13 | `.claude/hooks/session_end.py` |
| P4-2 | `DRAFT_ROW_RE` 강건화 (fence 변형 허용) | G14 | `.claude/hooks/cm_commands.py:42` |
| P4-3 | `_transcript_utils.py` dead branch 제거 | G15 | `.claude/hooks/_transcript_utils.py` |
| P4-4 | `py` 명령 POSIX 호환 (Linux/macOS 대응) | G16 | `README.md` §1 template, `.claude/settings.local.json` 가이드 |

---

### P5 — 최종 검증 + 박제

| ID | 작업 | 파일 |
|----|------|------|
| P5-1 | 전체 audit 재실행 (Agent 2병행) — 본 PLAN의 모든 AC 통과 확인 | (감사 결과만 기록) |
| P5-2 | CLAUDE.md "변경 이력" 표에 본 PLAN 사이클 박제 행 추가 | `CLAUDE.md` |
| P5-3 | README §Skill 워크플로우·§Context Manager 표 최종 정합 확인 | `README.md` |
| P5-4 | 본 PLAN.md를 `_workspace/_baseline/changelog_archive_2026-Qx.md`로 아카이브 (또는 `archive/` 디렉토리) | (이동) |

---

### P6 — 최초 setting 품질·정확도 극대화 (신규, 최상위 우선순위)

> **사용자 핵심 요구.** 가장 처음 harness setting(`/harness:harness-new` 진입점) 산출물 품질·정확도 극대화. **LLM 호출 활용 강화 + multi-pass self-critique + sub-agent 격리 + deterministic·LLM hybrid.**

| ID | 작업 | 해결 결손 | 파일 | 의존 |
|----|------|----------|------|------|
| **P6-1** | **Phase 0.5 (신규) Domain Clarification — `$ARGUMENTS` 모호성 pre-flight 검사** | G20 | `plugins/harness/skills/harness/SKILL.md` (Phase 0.5 신설), `plugins/harness/commands/harness-new.md` | 없음 |
| **P6-2** | **Phase 3.5/5.5/7.5 (신규) Self-Critique 회로 — Phase 3·5·7 산출물 sub-agent cross-review** | G17 | `SKILL.md` (Phase 3.5/5.5/7.5 신설), `agent-design-patterns.md` (cross-review pattern 추가) | P1-1 (sub-agent API schema) |
| **P6-3** | **Sub-agent 활용 doctrine — Phase 1·5·6·8 병렬 sub-agent 격리 박제** | G18 | `SKILL.md` Phase 1·5·6·8 본문 수정 + `code-research.md` 병렬 전략 갱신 | P1-1 |
| **P6-4** | **baseline hybrid — 결정적 매니페스트 추출 + LLM 합성** | G17 | 신규 `plugins/harness/scripts/baseline/extract_manifest.py`, `code-research.md` 시그널 우선순위 1 갱신 | 없음 |
| **P6-5** | **사용자 confirm 게이트 통일 — phase 종료마다 structured summary + enum 응답** | G17 | `SKILL.md` 각 phase 종료 블록 patch, `project-inquiry.md` confirm pattern 일반화 | 없음 |
| **P6-6** | **signal_low 자동 박제 — 확신 낮은 항목 `intent_profile.meta.confidence_low` 강제** | G17 | `intent-profile-schema.md` schema 갱신, `project-inquiry.md` brownfield §3-2 매핑 강화 | 없음 |
| **P6-7** | **도메인별 boundary 카탈로그 — qa-agent-guide.md에 ML/data/embedded/mobile boundary 추가** | G9, G22 | `qa-agent-guide.md` §6-9 신설 | P2-2 (host-agnostic 환원과 동기화) |
| **P6-8** | **trigger 키워드 도메인별 사전 박제** | G21 | 신규 `plugins/harness/skills/harness/references/trigger-keyword-catalog.md`, `skill-writing-guide.md` §1 cross-link | 없음 |
| **P6-9** | **PoC 미완 MCP 합성 default 풀 제외 — verification_status 컬럼 + tier_weight 조정** | G23 | `permission-profiles.md` §3 표 갱신, `mcp-recommendation.md` §2 tier_weight 갱신 | 없음 |
| **P6-10** | **baseline 5축 → 7축 (business_context + compliance)** | G22 | `project-profile-schema.md` §2 schema 확장, `code-research.md` §6·§7축 신설, `intent-profile-schema.md` constraints.compliance 신설 | 없음 |
| **P6-11** | **capability profile 4 → 8 (ml-pipeline / devops-infra / mobile-native / data-eng 추가)** | G9, G22 | `permission-profiles.md` §2-5~§2-8 신설, §3-1 매트릭스 행 4 추가, `mcp-recommendation.md` §1 신호 6→10 | 없음 |

#### P6-1 AC
- Phase 0.5 LLM 검사 룰 박제: 작업 유형(생성/분석/검증/통합) 1개 이상 명시? 입력 source? 출력 target?
- 빈 항목 ≥1이면 사용자 게이트 — "다음 정보 보강 필요: ..." 표 형식
- 모호 유지 시 Phase 1 강제 Deep audit + Phase 2 갭 메우기 강도 ↑ doctrine 박제
- `harness-new.md` 본문에 Phase 0.5 호출 분기 명시

#### P6-2 AC
- Phase 3.5: Phase 3 도메인 분석 직후 별도 sub-agent(`general-purpose`)가 동일 분석 critique. 충돌 시 사용자 게이트
- Phase 5.5: Phase 5 산출물(에이전트 정의 N개) cross-review — 역할 중복·gap·통신 프로토콜 정합성
- Phase 7.5: Phase 7 오케스트레이터 dry-run simulation — 가상 input phase 진행, dead link / 데이터 흐름 끊김 검출
- 각 critique 산출물은 `_workspace/_critique_{phase}_{ts}.md`에 박제

#### P6-3 AC
- Phase 1: Explore sub-agent 5 병렬 (stack/architecture/convention/maturity/pain_points 각 1) — parent는 합성만
- Phase 5: 에이전트 정의 N개 → N sub-agent 병렬 작성 (each `general-purpose` + `model: opus`)
- Phase 6: 스킬 N개 → N sub-agent 병렬 작성
- Phase 8: 검증 7단계 → 7 sub-agent 병렬 (단 비용 큰 8-3·8-4는 user confirm 후 진행)
- 각 phase 본문에 "sub-agent 격리 패턴" 1줄 doctrine 추가

#### P6-4 AC
- `extract_manifest.py` — `package.json`/`pyproject.toml`/`Cargo.toml`/`go.mod` 등 결정적 추출 → JSON 출력
- Phase 1 입력으로 본 JSON 제공 후 LLM이 5축 합성
- `inferred_fields`의 모든 항목이 `source` 필드 매니페스트 경로 인용 강제 — 인용 0이면 schema 위반 → 재합성 트리거

#### P6-5 AC
- Phase 1~8 각 종료 시 structured summary 4 블록:
  - "이 phase 결정 3-5개 (bullet)"
  - "다음 phase 영향 결정 1-2개"
  - "확신 낮은 항목 (signal_low)"
  - "사용자 응답 enum: OK / 수정 / 더 자세히 / skip"
- 응답 enum 외 입력은 자유 텍스트로 fallback 허용

#### P6-6 AC
- `intent_profile.meta.confidence_low: [string]` 신설 (dot-path 목록)
- brownfield 추론 단계에서 medium/low confidence 매핑 결과 자동 박제
- Phase 10 drift 감지 시 가중치 0.7 이하 룰 active (이미 runtime-adaptation.md §5-3 명세 있음 — 연결 강화)

#### P6-7 AC
- `qa-agent-guide.md` §6: ML pipeline boundary (data schema ↔ 모델 input / 학습 분포 ↔ 추론 분포 / metric 정의 ↔ loss)
- §7: Data eng (스키마 진화 ↔ 다운스트림 쿼리 / 파티션 ↔ retention / null 처리)
- §8: Embedded (memory budget ↔ allocation / 타이밍 ↔ ISR / endianness ↔ wire format)
- §9: Mobile (플랫폼 API ↔ JS bridge / 권한 ↔ 기능 / 회전 상태 보존)
- 각 §에 capability profile 매핑

#### P6-8 AC
- `trigger-keyword-catalog.md` — 도메인 × (공식/캐주얼/명시/암시) × (한국어/영어) 매트릭스
- 8 capability profile별 ≥20 키워드
- Phase 6 합성 시 deterministic input
- Phase 8-4 should/should-NOT 검증 시 사전과 cross-check

#### P6-9 AC
- `permission-profiles.md` §3 표에 `verification_status` 컬럼 추가 (✅ probe ✓ / 📜 docs / 🚫 PoC 미완)
- `mcp-recommendation.md` §2 tier_weight 조정: R0 ×1.0 / R1 (docs only) ×0.5 / R2 (PoC 미완) ×0.2
- Phase 5-2 합성 default 후보 풀에서 "PoC 미완" 자동 제외 — 사용자 명시 요청 시에만 노출 doctrine 박제

#### P6-10 AC
- `project-profile-schema.md` §2: `business_context` 필드 추가 (도메인 enum: fintech/health/edu/ecom/dev-tool/research/...) + `users.persona`
- `intent-profile-schema.md`: `constraints.compliance` (regulatory enum: GDPR/HIPAA/PCI-DSS/SOX/none)
- `code-research.md` §6 (Business Context 축): LICENSE/README/docs deterministic grep + LLM 보강
- `code-research.md` §7 (Compliance 축): 의존성·환경변수·docs grep
- Phase 1 출력에 7축 모두 박제

#### P6-11 AC
- `permission-profiles.md` §2 신설 4 profile:
  - 2-5 ml-pipeline (jupyter/sqlite/memory MCP 후보)
  - 2-6 devops-infra (git/github/sequential-thinking + docker/k8s MCP 후보)
  - 2-7 mobile-native (filesystem + expo/react-native MCP 후보)
  - 2-8 data-eng (sqlite/postgres/memory MCP 후보)
- §3-1 매트릭스 행 4 추가
- `mcp-recommendation.md` §1 신호 추출 6→10 (ML/devops/mobile/data 키워드)

---

### P7 — 영문 hybrid 마이그레이션 (Claude Code file read 효율 + 사고 깊이)

> **사용자 의도.** Claude Code file read context 토큰 효율 + LLM 사고 깊이. 영역별 분리 — **모두 영문 X, 모두 한국어 X.**
> doctrine 박제 (§7 2026-05-13D): SKILL.md·references/·commands 본문 = 영문, trigger·user-facing 메시지 = 양언어 또는 자동 감지, CM(`.claude/`) + 변경 이력 + dharness root README = 한국어 유지.

| ID | 작업 | 파일 | 의존 |
|----|------|------|------|
| **P7-1** | **POC: `plugins/harness/skills/harness/SKILL.md` 영문 마이그레이션 + 1주 dogfooding** | `plugins/harness/skills/harness/SKILL.md` (355 LOC) | 없음 |
| **P7-2** | **trigger 회귀 검증 — 한·영 양언어 발화 40개로 description 매칭 정확도 측정 (Phase 8-4 확장)** | `skill-testing-guide.md` 갱신, 신규 `plugins/harness/scripts/validate/trigger_regression.py` | P7-1 |
| **P7-3** | **references/ 영문 마이그레이션 (P7-1 POC 통과 시)** | `plugins/harness/skills/harness/references/*.md` 13 file (~6000 LOC) | P7-1, P7-2 PASS |
| **P7-4** | **commands/ 영문 본문 + frontmatter 양언어 trigger** | `plugins/harness/commands/harness-*.md` 10 file (~960 LOC) | P7-3 |
| **P7-5** | **plugin README 영문 + `plugins/harness/README.ko.md` 분리** | `plugins/harness/README.md` (130 LOC) | P7-3 |
| **out** | ~~CM(`.claude/`) + dharness root `CLAUDE.md` 변경 이력 + dharness root `README.md`~~ | 한국어 유지 (out-of-scope) | — |

#### P7-1 AC
- SKILL.md 전체 영문 (355 LOC)
- frontmatter `description`은 영문 본문 + 한국어 trigger 키워드 병기 (예: `description: "Meta-skill that defines agents and creates skills. Triggers: '하네스 구성/구축/설계', agent team architecture, harness setup..."`)
- 1주 dogfooding 후 한국어 사용자 발화 ↔ 영문 description trigger 매칭 측정 (≥10 실 호출)

#### P7-2 AC
- `trigger_regression.py` — should-trigger 20 + should-NOT 20 (한국어 + 영어 각 절반)
- 정확도 ≥85% PASS 기준
- 회귀 발견 시 description에 한국어 키워드 보강 → 재검증 cycle
- 본 검증 결과를 PLAN.md §7 결정 로그에 박제

#### P7-3 AC
- 13 file 영문 마이그레이션 (총 ~6000 LOC)
- 토큰 절감 측정 — 마이그레이션 전후 (`tiktoken` 또는 동급) 비교, 기대 절감 ≥60%
- 사고 깊이 측정 — 마이그레이션 후 sample Phase 1·5·8 산출물 품질 사용자 평가
- 한국어 ↔ 영문 cross-reference table 생성 (legacy 한국어 발화 grep 시 fallback)

#### P7-4 AC
- 10 command 본문 영문
- frontmatter `description`은 양언어 trigger (P7-1 패턴)
- `argument-hint`는 영문 + 한국어 예시 병기

#### P7-5 AC
- `plugins/harness/README.md` = 영문 (글로벌 marketplace)
- `plugins/harness/README.ko.md` = 한국어 (사용자 진입점)
- 두 README cross-link

---

---

## §4 작업 트래커

각 task는 작업 시작 시 `status: in_progress`, 완료 시 `status: done` + commit hash 박제.

| ID | Title | Status | Session | Commit | Notes |
|----|-------|--------|---------|--------|-------|
| P0-1 | `_tool_outputs/` TTL + `/cm-cleanup` | todo | - | - | - |
| P0-2 | `_GIT_RELEVANT` chain 분류 | todo | - | - | - |
| P0-3 | adapt counter wiring 결정 | todo | - | - | 옵션 A/B 결정 필요 |
| P0-4 | CM dead schema amputation | todo | - | - | P0-3 결정 후 진행 |
| P1-1 | `TeamCreate` 군 API schema reference | todo | - | - | 최대 영향도 |
| P1-2 | `mcp-server-fetch` 이름 표준화 | todo | - | - | - |
| P1-3 | `code-research.md:626` doctrine 정합 | todo | - | - | - |
| P2-1 | team-examples 3 예시 추가 | todo | - | - | - |
| P2-2 | qa-agent-guide host-agnostic 환원 | todo | - | - | - |
| P2-3 | `permission-profiles.md` closure summary | todo | - | - | - |
| P2-4 | 휴리스틱 임계값 근거 박스 | todo | - | - | - |
| P3-1 | Phase 10 telemetry watchdog | todo | - | - | P0-4 선결 |
| ~~P3-2~~ | ~~derived 프로젝트 hook 패키지화~~ | **skipped** | - | - | **폐기 — §7 2026-05-13B CM 종속 doctrine** |
| P3-3 | post-adapt 회귀 검증 자동화 | todo | - | - | P1-1 선결 |
| P3-4 | `/harness:harness-validate` slash command + plugin scripts/validate | todo | - | - | P1-1 선결 |
| P4-1 | session_end race mitigation | todo | - | - | optional |
| P4-2 | `DRAFT_ROW_RE` 강건화 | todo | - | - | optional |
| P4-3 | `_transcript_utils.py` 정리 | todo | - | - | optional |
| P4-4 | `py` POSIX 호환 | todo | - | - | optional |
| P5-1 | 최종 audit 재실행 | todo | - | - | 모든 P0-P3 선결 |
| P5-2 | CLAUDE.md 변경 이력 박제 | todo | - | - | - |
| P5-3 | README 정합 확인 | todo | - | - | - |
| P5-4 | PLAN.md 아카이브 | todo | - | - | 모든 P5 후 |
| **P6-1** | **Phase 0.5 Domain Clarification pre-flight** | todo | - | - | 사용자 핵심 요구 |
| **P6-2** | **Phase 3.5/5.5/7.5 Self-Critique 회로** | todo | - | - | P1-1 선결 (sub-agent API) |
| **P6-3** | **Sub-agent 활용 doctrine (Phase 1·5·6·8)** | todo | - | - | P1-1 선결 |
| **P6-4** | **baseline hybrid — 결정적 매니페스트 추출 + LLM 합성** | todo | - | - | - |
| **P6-5** | **사용자 confirm 게이트 통일 (structured summary + enum)** | todo | - | - | - |
| **P6-6** | **signal_low 자동 박제** | todo | - | - | - |
| **P6-7** | **도메인별 boundary 카탈로그 (ML/data/embedded/mobile)** | todo | - | - | P2-2 동기화 |
| **P6-8** | **trigger 키워드 도메인별 사전** | todo | - | - | - |
| **P6-9** | **PoC 미완 MCP 합성 풀 제외** | todo | - | - | - |
| **P6-10** | **baseline 5축 → 7축 (business + compliance)** | todo | - | - | - |
| **P6-11** | **capability profile 4 → 8** | todo | - | - | - |
| **P7-1** | **SKILL.md 영문 POC + dogfooding** | todo | - | - | 사용자 핵심 요구 |
| **P7-2** | **trigger 한·영 회귀 검증** | todo | - | - | P7-1 |
| **P7-3** | **references/ 13 file 영문 마이그레이션** | todo | - | - | P7-1, P7-2 PASS |
| **P7-4** | **commands/ 영문 + 양언어 trigger** | todo | - | - | P7-3 |
| **P7-5** | **plugin README 영문 + README.ko.md 분리** | todo | - | - | P7-3 |

상태 값: `todo` / `in_progress` / `blocked` / `done` / `skipped`

---

## §5 작업 순서 + 의존성

```
P0-1 ─┐
P0-2 ─┤
P0-3 ─┴─→ P0-4 ─→ P3-1   (P3-2 폐기)

P1-1 ─┬─→ P3-3
      ├─→ P3-4
      ├─→ P6-2 (sub-agent API 의존)
      └─→ P6-3
P1-2  (독립)
P1-3  (독립)

P2-2 ←→ P6-7 (qa-agent-guide 동기화)
P2-* (독립, 병행 가능)
P4-* (독립, 선택)

P6-1, P6-4~P6-11 (독립, 병행 가능)

P7-1 ─→ P7-2 ─(PASS)→ P7-3 ─┬─→ P7-4
                              └─→ P7-5

(모든 P0/P1/P2/P3/P6 완료 + P7 진척) → P5-1 → P5-2 → P5-3 → P5-4
```

**권장 실행 순서 (revision 2)**:
1. **P6-1** (Phase 0.5 pre-flight — 최초 setting 품질 lever, LLM 호출 즉시 활용)
2. P0-1, P0-2 (병행 — 디스크 + 신호 즉시 개선)
3. P0-3 결정 → P0-4 (CM 정리)
4. **P7-1** (SKILL.md 영문 POC) — dogfooding 1주 동시 진행
5. P1-1 (factory 신뢰성 + sub-agent API — P6-2/P6-3 unblock)
6. **P6-2, P6-3** (self-critique + sub-agent 활용 — 품질 lever)
7. **P6-4, P6-5, P6-6** (baseline 정확도)
8. **P7-2** (trigger 회귀 검증) — PASS 시 P7-3 진입
9. P1-2, P1-3, P2-* (병행 doctrine 위생) — P2-2 ↔ P6-7 동기화
10. **P6-7, P6-8, P6-9, P6-10, P6-11** (도메인 폭 + 정확도)
11. P3-1, P3-3, P3-4 (fail-safe)
12. **P7-3, P7-4, P7-5** (영문 마이그레이션 본격)
13. P4-* (선택)
14. P5-* (마무리)

---

## §6 Session Pickup Protocol

**다른 세션이 본 작업을 이어갈 때 따르는 절차**:

1. `Read PLAN.md` — 본 문서 읽기
2. §2 감사 baseline ↔ 현 코드 차이 확인 (`git log --since="2026-05-13"` + audit 영역 변경 추적)
3. §4 트래커에서 `status: in_progress` task 확인 — 진행 중 task 있으면 인계 메모 검토
4. `todo` task 중 §5 의존성 위반 없는 첫 task 선택
5. 작업 시작 시:
   - 본 PLAN.md §4 트래커 해당 행 `status: in_progress`, `session` 컬럼에 session_id 기입
   - 본 PLAN.md `마지막 업데이트` 날짜 갱신
6. 작업 중간 결정 사항은 §7 "결정 로그"에 1줄 박제
7. 완료 시:
   - §4 트래커 `status: done`, `commit` 컬럼에 commit hash 기입
   - AC 항목 모두 만족했는지 self-check 후 박제
   - 작업 commit message 형식: `feat/fix/refactor/docs(scope): {요약} — PLAN P{X-Y}`
8. blocking 발견 시: `status: blocked`, `notes` 컬럼에 blocking 사유 박제, 다음 task로 이동

**중요 규칙**:
- PLAN.md는 단일 진실 원천. 트래커가 git 상태와 차이 나면 PLAN.md를 갱신 (역방향 금지)
- AC 미충족 task를 `done`으로 표기 금지
- 의존성 위반 작업 금지 (위반 발견 시 즉시 revert 권장)

---

## §7 결정 로그

작업 중 발생한 비-자명한 결정·trade-off를 시간순 박제. 다른 세션이 의사결정 맥락 추적 가능.

| 날짜 | 결정 | 사유 | 영향 task |
|------|------|------|----------|
| 2026-05-13 | 본 PLAN.md 신설 — 루트 위치 | 다른 세션이 CLAUDE.md auto-load 후 발견 가능, `_workspace/`는 gitignored이라 부적합 | 전체 |
| 2026-05-13A | revision 2 — 사용자 의도 반영 (CM 종속 + LLM 활용 + 최초 setting 품질 + 영문 hybrid) | 사용자 명시 ("CM은 외부 호출 X, dharness 종속" + "LLM 호출 0 의문" + "최초 setting 품질 극대화" + "영문 교체로 file read 효율 + 사고 깊이"). plugin은 외부 프로젝트별 harness setting 실행 의도 — derived hook 합성과 충돌 X (P3-2 폐기로 정합) | 전체 |
| 2026-05-13B | **CM 종속 doctrine 확정** — `.claude/` + `_workspace/`는 dharness 본 폴더 dogfooding 영구 한정. 외부 install·일반화 X. plugin(`plugins/harness/`)과 CM은 영구 분리 — plugin은 host-agnostic, CM은 host-specific | 사용자 명시. derived 프로젝트 강제성은 plugin scripts/ + slash command wrapping(P3-4)로 대체 — hook 합성(P3-2) 불필요 | G3 폐기, P3-2 폐기, P3-4 신규 |
| 2026-05-13C | **LLM·deterministic hybrid doctrine** — "결정·persistence는 deterministic, 추론·합성은 LLM, 검증은 양방향 cross-check". LLM 호출 0 doctrine은 *capture·classify·persistence*에만 적용. Phase 1-7 합성은 LLM 호출 적극 활용 + multi-pass self-critique 권장 | LLM 호출 0이 항상 최상 X. capture는 결정성 필요하나 합성은 LLM 추론 깊이 필요 | P6 전체 |
| 2026-05-13D | **영문 hybrid 마이그레이션 doctrine** — SKILL.md·references/·commands 본문 = 영문 / frontmatter trigger·user-facing 메시지 = 양언어 또는 자동 감지 / CM(`.claude/`) + dharness root CLAUDE.md 변경 이력 + dharness root README = 한국어 유지. POC(SKILL.md 1 file) → 회귀 검증 PASS → 본격 마이그레이션 단계적 진행 | Claude Code file read context 토큰 효율(영문 ~0.25 tok/char vs 한국어 ~1.5-2) + LLM 학습 데이터 영문 우세 → 사고 깊이 ↑. 단 trigger 매칭 회귀 위험 — POC + 회귀 검증으로 게이트 | P7 전체 |

---

## §8 위험·전제

| 위험 | 영향 | 대응 |
|------|------|------|
| `TeamCreate` 군 실 API schema가 공식 문서에 미공개 | P1-1 진행 불가 | 실호출 trial-and-error 박제로 대체. fail 시 P1-1 보류 + 의사코드 유지 |
| CM dead schema amputation 후 미발견 dependency | P0-4 후 회귀 | `grep -r {column_name}` 사전 점검 + 단계적 제거 (테이블 → 컬럼) |
| derived 프로젝트 hook 패키지화 시 `claude plugin install` API 변경 | P3-2 차단 | claude-code-guide agent 또는 공식 문서 확인 |
| Phase 10 watchdog가 LLM 응답에 surface되어 트리거 노이즈 | P3-1 UX 저하 | 결손율 임계값 sane default (예: 10%+) |
| 본 PLAN 크기 > 500줄 (SKILL.md 정신과 톤 차이) | 가독성 저하 | P5-4 아카이브 시 압축 — done task는 별도 archive |

---

## §9 측정 — 완료 기준 (revision 2)

본 PLAN의 "production-ready 90%+" 도달 측정:

**P0/P1 기존 기준:**
- [ ] G1~G16 결손 중 G1, G2 해결 (G3 폐기). 3 lever 중 2개 — 나머지 1개는 P6/P7 lever로 대체
- [ ] `/cm-status` 출력에 dead column 0
- [ ] `test_schema.py` 100% pass (count 증감 무관, 신규 test 포함)
- [ ] `permission-profiles.md` 상단 closure summary 박스 존재
- [ ] team-examples 도메인 8개 이상 (현 5 + 신규 3)
- [ ] CLAUDE.md "변경 이력" 표에 본 PLAN 사이클 박제 행 1건 이상

**P6 신규 기준 (최초 setting 품질):**
- [ ] G17, G18, G20 해결 (multi-pass / sub-agent / pre-flight)
- [ ] Phase 0.5 pre-flight 호출 검증 (≥3 derived 프로젝트 실 setting)
- [ ] Phase 3.5/5.5/7.5 self-critique 산출물 박제 (`_workspace/_critique_*.md`) ≥3
- [ ] baseline `inferred_fields`의 `source` 인용율 100% (P6-4 hybrid)
- [ ] capability profile 8종 박제 (4 신규 + §3-1 매트릭스 행 4 추가)
- [ ] baseline 7축 박제 (business_context + compliance 추가)

**P7 신규 기준 (영문 hybrid):**
- [ ] G19 부분 해결 — P7-1 POC + P7-2 회귀 검증 PASS (≥85%)
- [ ] SKILL.md 영문 마이그레이션 완료 (P7-1)
- [ ] references/ 13 file 영문 마이그레이션 토큰 절감 ≥60% 측정 박제

**완료 비율:**
- [ ] 본 PLAN.md `status: done` 비율 ≥ P0/P1/P5/**P6/P7** 전체, P2/P3는 ≥ 75%, P4는 선택

위 모든 항목 체크 시 본 PLAN을 archive하고 후속 PLAN 사이클 신설.

---

## 참고

- 감사 보고서 원본: 본 세션 (`session_id=1f0cd2`) 대화 직전 turn
- 현 dharness commit: `a4a3509` (2026-05-13 archive doctrine 정합)
- 본 PLAN 박제: dharness PostToolUse 분류기가 자동 감지 → SessionEnd draft 적재 예상
- **revision 2 (2026-05-13)**: 사용자 의도 반영 — CM 종속 doctrine 확정(2026-05-13B), LLM·deterministic hybrid doctrine(2026-05-13C), 영문 hybrid 마이그레이션 doctrine(2026-05-13D). G17-G23 7 결손 추가, P6(최초 setting 품질) + P7(영문 마이그레이션) phase 신설, P3-2(derived hook 합성) 폐기, P3-4(`/harness:harness-validate`) 신규.
