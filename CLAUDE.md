# CLAUDE.md — dharness

## 이 저장소에 대해

**dharness**는 harness 메타 스킬 플러그인 저장소다.
- `skills/harness/SKILL.md` — harness 메타 스킬 (Phases 0-10)
- `skills/harness/references/` — 설계 가이드 문서
- `commands/` — `/harness-*` 슬래시 커맨드

---

## 하네스: context-management

**목표:** Claude Code 세션 간 컨텍스트 손실 해소, 도구 출력 압축, 메모리 영속화

**트리거:** context-management 관련 작업 요청 시 `cm-orchestrator` 스킬을 사용하라.
또는 `/harness-*` slash command로 명시적 호출 (`/harness-add-agent`, `/harness-adapt` 등 — 카탈로그는 `commands/README.md`).
단순 질문은 직접 응답 가능.

**에이전트 목록:**
- `.claude/agents/cm-injector.md` — SessionStart 컨텍스트 주입
- `.claude/agents/cm-compressor.md` — PostToolUse 출력 압축
- `.claude/agents/cm-digester.md` — SessionEnd digest 생성 (팀)
- `.claude/agents/cm-curator.md` — 클러스터링 + skill 승격 (팀)
- `.claude/agents/cm-retriever.md` — 메모리 검색

**스킬 목록:**
- `.claude/skills/cm-orchestrator/` — 이벤트 라우터 (진입점)
- `.claude/skills/session-capture/` — session_id 발급 + raw.jsonl/transcript.md 캡처
- `.claude/skills/tool-output-compress/` — 압축 정책
- `.claude/skills/session-digest/` — digest 구조 + **단일 DB 스키마 진실 원천**
- `.claude/skills/memory-curate/` — 클러스터링 + decay + 승격 + daily_summary 생성
- `.claude/skills/memory-search/` — 3-tool progressive disclosure
- `.claude/skills/dashboard-render/` — 4개 뷰 데이터 집계

**훅 + 워커:**
- `_workspace/_hooks/{session_start,post_tool_use,session_end,cm_commands}.py` — 결정적 캡처/커맨드 핸들러
- `_workspace/_hooks/INSTALL.md` — **사용자 직접 설치 필요** — `.claude/settings.json` 훅 등록 가이드. 자동 모드의 권한 정책상 에이전트는 hook 등록 파일을 쓸 수 없으므로 본 가이드대로 사용자가 직접 적용한다.
- `_workspace/_worker/dashboard_server.py` — FastAPI 대시보드 (localhost:8765)

**/cm-* 슬래시 커맨드:** `commands/cm-{status,sessions,clusters,dashboard,init,reset,curate}.md`

**Phase 10 자동 알림:** 세션 시작 시 `_workspace/_telemetry/`의 최신 `.jsonl` 파일을 확인하라.
마지막 `"type":"adapt"` 이벤트 이후 `"type":"harness_invocation"` 이벤트 수가 10회 이상이면,
사용자에게 알린다: "CM 하네스가 {N}회 실행되었습니다. `/harness-adapt`로 drift 점검을 권장합니다."
— telemetry 파일이 없거나 읽기 비용이 클 경우 건너뛴다.

**단계적 구현 현황 (레퍼런스 line 168-176과 일치):**

| 단계 | 산출물 | 상태 |
|------|--------|------|
| S1 | cm-orchestrator + cm-injector + **session-capture** 스킬 | ✅ 정의 완료 |
| S2 | cm-digester + session-digest 스킬 + observations.db (단일 진실 스키마) | ✅ 정의 완료 |
| S3 | cm-retriever + memory-search | ✅ 정의 완료 |
| S4 | cm-compressor + tool-output-compress | ✅ 정의 완료 |
| S5 | cm-curator + memory-curate (decay + daily_summary + 승격 + 주기 트리거) | ✅ 정의 완료 |
| S6 | dashboard-render + worker (FastAPI 골격 코드 + README) | ✅ 정의 완료 |
| S7 | cm-diagnostic-rules.md (Phase 10 확장) | ✅ 정의 완료 |

**CM Phase 10 진단 룰 위치:** `_workspace/references/cm-diagnostic-rules.md`
**CM baseline 기준값:** `_workspace/_baseline/cm_baseline.json` (30 세션 후 cm-curator가 자동 채움)

**변경 이력:**

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-05-09 | 초기 구성 | 전체 (S1-S6 정의) | context-management 도메인 harness 신규 구축 |
| 2026-05-09 | S7 완료 — CM 전용 Phase 10 진단 룰 추가 | `_workspace/references/cm-diagnostic-rules.md`, `_workspace/_baseline/cm_baseline.json`, cm-orchestrator 스킬 | Phase 10: CM drift 자체 진화 회로 완성 |
| 2026-05-10 | 갭 9건 해소 (점검 결과 반영) | session-capture 스킬 신설, session-digest를 단일 DB 스키마 진실 원천으로 통합, dashboard-render/memory-search SQL 정합화, memory-curate에 daily_summary + 주기 트리거 추가, cm-injector daily_summaries 우선 입력, cm-curator 책임 확장, /cm-* 7종 커맨드 + 핸들러 스크립트 신설, FastAPI 워커 골격 작성, 훅 INSTALL.md 가이드 | 레퍼런스 line 168-176 정합 + 실행 가능성 확보 |
| 2026-05-10 | Skill memory 승격을 Phase 10 rollback chain에 명시적으로 통합 | `_workspace/references/cm-diagnostic-rules.md` §4 표에 "Skill memory 승격" 행 + Atomic 적용 절차 추가, `.claude/skills/memory-curate/SKILL.md` 승격 프로세스를 표준 `_telemetry/_rollback/{ts}/` 인프라 사용으로 구체화 | 승격 시 다중 산출물(skill 파일/cluster md/DB/CLAUDE.md) chain의 dangling rollback 위험 제거 |
