# CLAUDE.md — dharness

## 이 저장소에 대해

**dharness**는 두 Claude Code plugin을 호스트하는 monorepo다 (Step 2 이후).
- `plugins/harness/` — `harness` plugin: 메타 스킬 팩토리 (Phases 0-10)
  - `skills/harness/SKILL.md` — 메타 스킬 본체
  - `skills/harness/references/` — 설계 가이드 문서
  - `commands/harness-*.md` — `/harness:harness-*` 슬래시 커맨드 7종
- `plugins/cm-harness/` — `cm-harness` plugin: Context Manager 런타임
  - `agents/cm-*.md` — 에이전트 5종, `skills/<7>/SKILL.md` — 스킬 7종
  - `commands/cm-*.md` — `/cm-harness:cm-*` 슬래시 커맨드 7종
  - `hooks/` — 3종 lifecycle 훅 + `hooks.json` 자동 등록 매니페스트
  - `worker/` — FastAPI 멀티 프로젝트 dashboard
  - `references/cm-diagnostic-rules.md` — Phase 10 진단 룰
- `.claude-plugin/marketplace.json` — 두 plugin git-subdir 카탈로그
- `_workspace/` — DATA (사용자 프로젝트별 격리, plugin install 시 `${CLAUDE_PROJECT_DIR}` 기준)

---

## 하네스: context-management

**목표:** Claude Code 세션 간 컨텍스트 손실 해소, 도구 출력 압축, 메모리 영속화

**트리거:** context-management 관련 작업 요청 시 `cm-orchestrator` 스킬을 사용하라.
또는 `/harness:harness-*` slash command로 명시적 호출 (카탈로그는 [`README.md`](./README.md) "Slash command 카탈로그" 섹션).
단순 질문은 직접 응답 가능.

**구성 산출물 카탈로그(에이전트 5종 / 스킬 7종 / 훅 3종 + 워커 1종 / `/cm-harness:cm-*` 7종):** 본 파일은 포인터만 유지한다 — 상세 카탈로그·역할 표는 [`README.md` "Context Manager 하네스"](./README.md#context-manager-하네스-구축-예시) 섹션을 단일 출처로 본다. plugin install 시 hooks.json이 자동 등록 — self-use(dharness 본 폴더 직접 작업) 시는 `plugins/cm-harness/hooks/INSTALL.md` 참조.

**Phase 10 자동 알림:** 세션 시작 시 `_workspace/_telemetry/`의 최신 `.jsonl` 파일을 확인하라.
마지막 Adapt 시각(= `_workspace/_telemetry/_delta_*.md` 또는 `_workspace/_telemetry/_rollback/{ts}/` 중 가장 최근 mtime,
둘 다 없으면 telemetry 첫 이벤트의 ts) 이후 `"type":"harness_invocation"` 이벤트 수가 10회 이상이면,
사용자에게 알린다: "CM 하네스가 {N}회 실행되었습니다. `/harness-adapt`로 drift 점검을 권장합니다."
— telemetry 파일이 없거나 읽기 비용이 클 경우 건너뛴다.

**단계적 구현 현황(S1~S7) / Phase 10 진단 룰·baseline 위치:** README.md의 "Context Manager 하네스" 섹션 + `plugins/cm-harness/references/cm-diagnostic-rules.md`를 단일 출처로 본다 (본 파일에서 중복 보유 금지 — Phase 7-4 포인터 룰).

**변경 이력:**

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-05-09 | 초기 구성 | 전체 (S1-S6 정의) | context-management 도메인 harness 신규 구축 |
| 2026-05-09 | S7 완료 — CM 전용 Phase 10 진단 룰 추가 | `_workspace/references/cm-diagnostic-rules.md`, `_workspace/_baseline/cm_baseline.json`, cm-orchestrator 스킬 | Phase 10: CM drift 자체 진화 회로 완성 |
| 2026-05-10 | 갭 9건 해소 (점검 결과 반영) | session-capture 스킬 신설, session-digest를 단일 DB 스키마 진실 원천으로 통합, dashboard-render/memory-search SQL 정합화, memory-curate에 daily_summary + 주기 트리거 추가, cm-injector daily_summaries 우선 입력, cm-curator 책임 확장, /cm-* 7종 커맨드 + 핸들러 스크립트 신설, FastAPI 워커 골격 작성, 훅 INSTALL.md 가이드 | 레퍼런스 line 168-176 정합 + 실행 가능성 확보 |
| 2026-05-10 | Skill memory 승격을 Phase 10 rollback chain에 명시적으로 통합 | `_workspace/references/cm-diagnostic-rules.md` §4 표에 "Skill memory 승격" 행 + Atomic 적용 절차 추가, `.claude/skills/memory-curate/SKILL.md` 승격 프로세스를 표준 `_telemetry/_rollback/{ts}/` 인프라 사용으로 구체화 | 승격 시 다중 산출물(skill 파일/cluster md/DB/CLAUDE.md) chain의 dangling rollback 위험 제거 |
| 2026-05-10 | dharness 본체 read-only 경계 invariant 3곳 추가 | `.claude/agents/cm-curator.md` 작업 원칙, `_workspace/references/cm-diagnostic-rules.md` §4 범위 외 각주, `.claude/skills/cm-orchestrator/SKILL.md` Phase 10 연동 영구 범위 한정 섹션 | CM 자동 적응(Phase 10)이 dharness 메타 스킬 본체(`skills/harness/`, `commands/harness-*`)를 침범할 경로를 명시적으로 차단. dharness 일반화 가치가 있는 신호는 Phase 9(`/harness-evolve`)로만 진입 |
| 2026-05-10 | 전체 review 결과 BLOCKER 8 + MAJOR 11 정합성 픽스 (Phase 9: 사용자 피드백 — 전체 파일 리뷰) | `_workspace/_hooks/_schema.py` 신설(DDL+session_id 헬퍼), `_hooks/{session_start,post_tool_use,session_end,cm_commands}.py` 재작성(파일 기반 sid + stdout 컨트랙트 정합 + TZ + dict 직렬화 + DDL import), `_hooks/INSTALL.md` matcher/`${CLAUDE_PROJECT_DIR}` 보강, `commands/cm-curate.md` Task 도구 호출로 정정, `commands/cm-reset.md` 약속 단순화, `commands/harness-new.md` Phase 0-8+10 명시, `cm-orchestrator/SKILL.md` 가상 API→Task 도구로 교체, `session-capture/SKILL.md` 환경변수→파일 기반 명시, `session-digest/SKILL.md` 진실 원천 2계층 명시, `tool-output-compress/SKILL.md` margin 룰 정리, `memory-curate/SKILL.md` member_observations 권위 출처 명시, `cm-injector.md` description 정정 + 5 cm-* 에이전트에 `tools:` allowlist, `_baseline/cm_baseline.json` notes/user_confirmed_skills 정렬, `_baseline/project_profile.md` detection_signals 갱신, `_worker/dashboard_server.py` XSS escape + mtime 캐시 무효화, `harness/SKILL.md` Phase 8 단계 8-1~8-7 명시 + should-trigger 10+10 통일, `runtime-adaptation.md` 8 → 10+10 정렬 | 4-그룹 병렬 리뷰에서 발견한 hook 컨트랙트 위반·DDL 진실원천 우회·가상 API·schema drift·XSS 등 정합성 버그 일괄 해소. dharness 본체 read-only invariant는 보존 (skills/harness/SKILL.md의 Phase 8 단계 번호 정합화는 사용자 직접 수정 영역) |
| 2026-05-10 | 정합성 11건 일괄 정정 (Phase 9: 사용자 피드백 — 전체 폴더 review) | `CLAUDE.md`(Phase 7-4 포인터화 — 카탈로그·구현 현황·진단 룰 위치 README/skills 단일 출처로 위임) + `harness/SKILL.md` Phase 7-4 템플릿 + `cm-orchestrator/SKILL.md`(Phase 10 mtime-anchor 도입 + 라우팅 표 "훅 자율" 컬럼 분리) + `cm-digester.md` `cm-curator.md`(SendMessage→Task 반환값/prompt payload 정정 + obs_id 형식 통일 + SessionEnd 호출 타이밍 명시) + `session-capture/SKILL.md`(에이전트는 파일 직접 read, 스크립트만 `_schema.read_session_id()`) + `commands/cm-init.md`(baseline json 자동 생성 항목 제거) + `cm_commands.py`(미사용 `daily_summaries/` 디렉토리 생성 제거) + `intent_profile.md`(S6 dashboard 워커 open_question을 Resolved로 이전) + `session_start.py`(session_id 충돌 시 orphan 디렉토리 cleanup) | (1) Phase 10 카운터가 발행되지 않는 `type:adapt`에 의존하던 spec drift 해소 — `_delta_*.md`/`_rollback/{ts}/` mtime을 anchor로 사용. (2) 메시지 버스 부재 환경에서 SendMessage 잔재 정정. (3) CLAUDE.md가 자체 Phase 7-4 룰 위반(전체 카탈로그 중복 보유)을 자기 시연으로 해소. (4) 코드와 spec의 micro-drift 6건 동기화. dharness 본체(`skills/harness/SKILL.md` Phase 7-4 템플릿)는 사용자 명시 요청 — Phase 9 영역. |
| 2026-05-10 | 멀티 프로젝트 dashboard (옵션 A — 분산 DB) + Inventory/Roadmap View 5 | `_workspace/_hooks/_schema.py`(REPO_ROOT를 `CLAUDE_PROJECT_DIR` 우선으로) + `_workspace/projects.json` 신설(수동 프로젝트 레지스트리) + `_worker/dashboard_server.py` 재작성(프로젝트별 routes + inventory 스캐너 + CLAUDE.md 표 파서 + StaticFiles `/ui/` mount + localhost CORS) + `dashboard-render/SKILL.md`에 옵션 A 모델 + View 5 + 신규 엔드포인트 명세 추가 | dharness 하네스가 적용된 여러 프로젝트의 세션·tools·축적 정보를 한 화면에서 비교 열람. 프론트엔드는 Claude design 산출물을 `_workspace/_worker/static/`에 mount하여 `/ui/`로 서빙. cross-project SQL JOIN 없음 — 각 프로젝트 DB 독립 조회. dharness 본체 read-only invariant 보존 |
| 2026-05-10 | LLM 단계 사슬 끊김 픽스 (영속성/압축 점검 결과 반영) | `_workspace/_hooks/session_start.py`(dangling 세션 자동 finalize + `digest_path IS NULL` 후보를 `[CM Backfill]` 신호로 additionalContext에 포함) + `_workspace/_hooks/session_end.py`(`clear_session_id()` 제거 — `unknown` 누수 방지) + `cm-orchestrator/SKILL.md`(라우팅 표에 SessionStart digest backfill 행 추가 + cm-digester 다회→cm-curator 1회→cm-injector 순차 dispatch 절차 명시, SessionEnd 후속은 다음 SessionStart로 이월) | 점검 결과 cm-digester/cm-curator/cm-compressor가 0회 실행되어 observations·clusters·daily_summaries 모두 0행. 원인은 SessionEnd 훅이 LLM 단계를 트리거할 창구가 없는 구조적 결함. SessionStart의 `additionalContext` 채널을 통해 직전 세션 digest 미생성을 자동 backfill하도록 사슬 복구. dharness 본체 read-only invariant 보존 |
| 2026-05-10 | Plugin 매니페스트 도입 — `/plugin install` 가능한 형태로 전환 (Step 1+1.6) | `.claude-plugin/plugin.json` 신설 (skills 2종/commands/agents/hooks 경로 선언) + `.claude-plugin/marketplace.json` 신설 (github source 단일 plugin 카탈로그) + `_workspace/_hooks/hooks.json` 신설 (`${CLAUDE_PLUGIN_ROOT}` 기반 3종 훅 등록) + `README.md` "다른 프로젝트에 dharness 도입하기"에 §0 (권장) Plugin 설치 섹션 추가 (A/B 절차는 보존) | 디렉토리 구조 변경 0, 코드 수정 0줄. 기존 `_schema.py`가 이미 `CLAUDE_PROJECT_DIR` env var로 데이터 경로를 잡고 있어서 plugin model과 자연 호환. 사용자가 `settings.json` 직접 편집 없이 `/plugin install dharness@dharness` 한 줄로 도입 가능. 메타 스킬과 CM 산출물이 한 plugin에 묶여 선택 install이 안 되는 한계는 Step 2(plugin 분리)에서 해소 예정 |
| 2026-05-10 | Step 2 — monorepo subdirs 모델로 두 plugin 분리 (Step 2.1~2.5) | `plugins/harness/` 신설 (메타 스킬 + harness-* commands 이동) + `plugins/cm-harness/` 신설 (cm-* agents/skills/commands + hooks/ + worker/ + references/ 이동) + 각자 `.claude-plugin/plugin.json` + `plugins/cm-harness/hooks/hooks.json` 경로를 plugin-relative(`${CLAUDE_PLUGIN_ROOT}/hooks/...`)로 정정 + `_schema.py`에 `_walk_up_for_workspace()` fallback 추가 (manual self-use에서 `_workspace/` 디렉토리를 가진 가장 가까운 조상 탐색) + 기존 root `.claude-plugin/plugin.json` 삭제 + `marketplace.json`을 두 plugin git-subdir 카탈로그로 확장 + `.claude/settings.local.json` 훅 경로 갱신 (gitignore이라 commit에 미포함) + 기존 `commands/README.md`, `skills/README.md` 삭제 + `README.md` 전면 갱신 + `CLAUDE.md` 최상단 산출물 카탈로그 갱신 | 사용자가 "메타만" 또는 "CM만" 또는 "둘 다" 선택 install 가능. `harness:harness-*` vs `cm-harness:cm-*` 네임스페이스 분리. `plugins/`(코드, install 시 read-only) ↔ `_workspace/`(데이터, 사용자 프로젝트별 격리) invariant가 디렉토리 경계로 자연 강제됨. plugin 내부 SKILL.md/agent.md 파일들이 옛 경로(`_workspace/_hooks/...`)를 가리키는 잔존 참조는 다음 단계(Step 2.6)에서 일괄 갱신 |
