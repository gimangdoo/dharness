# CLAUDE.md — dharness

## 이 저장소에 대해

**dharness**는 harness 메타 스킬 플러그인 저장소다.
- `skills/harness/SKILL.md` — harness 메타 스킬 (Phases 0-10)
- `skills/harness/references/` — 설계 가이드 문서
- `commands/` — `/harness-*` 슬래시 커맨드
- `reference-file-for-context-manager/` — CM 시스템 설계 참고 문서

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
- `.claude/skills/tool-output-compress/` — 압축 정책
- `.claude/skills/session-digest/` — digest 구조 + DB 스키마
- `.claude/skills/memory-curate/` — 클러스터링 + decay + 승격
- `.claude/skills/memory-search/` — 3-tool progressive disclosure
- `.claude/skills/dashboard-render/` — 4개 뷰 데이터 집계

**Phase 10 자동 알림:** 세션 시작 시 `_workspace/_telemetry/`의 최신 `.jsonl` 파일을 확인하라.
마지막 `"type":"adapt"` 이벤트 이후 `"type":"harness_invocation"` 이벤트 수가 10회 이상이면,
사용자에게 알린다: "CM 하네스가 {N}회 실행되었습니다. `/harness-adapt`로 drift 점검을 권장합니다."
— telemetry 파일이 없거나 읽기 비용이 클 경우 건너뛴다.

**단계적 구현 현황:**

| 단계 | 산출물 | 상태 |
|------|--------|------|
| S1 | cm-orchestrator + cm-injector + session-digest | ✅ 정의 완료 |
| S2 | cm-digester + observations.db | ✅ 정의 완료 |
| S3 | cm-retriever + memory-search | ✅ 정의 완료 |
| S4 | cm-compressor + tool-output-compress | ✅ 정의 완료 |
| S5 | cm-curator + memory-curate | ✅ 정의 완료 |
| S6 | dashboard-render + worker | ✅ 정의 완료 |
| S7 | cm-diagnostic-rules.md (Phase 10 확장) | ✅ 정의 완료 |

**CM Phase 10 진단 룰 위치:** `_workspace/references/cm-diagnostic-rules.md`
**CM baseline 기준값:** `_workspace/_baseline/cm_baseline.json` (30 세션 후 cm-curator가 자동 채움)

**변경 이력:**

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-05-09 | 초기 구성 | 전체 (S1-S6 정의) | context-management 도메인 harness 신규 구축 |
| 2026-05-09 | S7 완료 — CM 전용 Phase 10 진단 룰 추가 | `_workspace/references/cm-diagnostic-rules.md`, `_workspace/_baseline/cm_baseline.json`, cm-orchestrator 스킬 | Phase 10: CM drift 자체 진화 회로 완성 |
