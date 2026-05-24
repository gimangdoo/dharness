# 산출물 체크리스트 — must (8) / should (9)

> **Read at phase:** Phase 8 (검증 단계 진입 시) + factory 종료 직전 최종 self-check.
> SKILL.md ≤500 LOC cap 정합 (P2-A 박제, 2026-05-23 review patch). 본 reference 미read 시
> Phase 8-1 구조 검증의 17 항목 catalog 누락.

생성 완료 후 확인. **차단(must)**은 빠지면 하네스 작동 실패, **권장(should)**은 품질 보장.

## 차단 (must) — 8개

- [ ] **Baseline 산출** — `_workspace/_baseline/project_profile.md` (Phase 1) + `intent_profile.md` (Phase 2, schema 준수) + `changelog.md` skeleton (Phase 7-4.1, 후속 `/harness:harness-*` append 대상)
- [ ] **에이전트 정의 파일** — `프로젝트/.claude/agents/{name}.md` 빌트인 타입(`general-purpose`/`Explore`/`Plan`) 포함 필수
- [ ] **스킬 + 오케스트레이터** — `프로젝트/.claude/skills/{name}/SKILL.md` + 오케스트레이터 1개 (데이터 흐름·에러 핸들링·테스트 시나리오 포함). 각 `SKILL.md`는 frontmatter만 있는 빈 파일이 아니라 본문(트리거·워크플로우·입출력·예시)까지 박제 — 빈 파일/디렉토리만 산출 금지 (Phase 6 빈 스킬 금지 invariant)
- [ ] **실행 모드 명시** — 팀 / 서브 / 하이브리드 (하이브리드면 Phase별 모드 기재)
- [ ] **사용자 `.claude/commands/`에 미생성** — harness 플러그인 본체 `commands/`는 L1 진입점으로 별개
- [ ] **CLAUDE.md 하네스 섹션** — 운영·구조·규칙 + 변경 이력 포인터 (Phase 7-4 템플릿, litmus 통과·< 200줄)
- [ ] **오케스트레이터 Phase 1에 컨텍스트 확인 단계** — 초기/후속/부분 재실행 판별
- [ ] **Phase 10 capture 인프라** — `_workspace/_telemetry/` + `_telemetry/_rollback/` 디렉토리 + 오케스트레이터 telemetry capture 훅 + description에 Phase 10 트리거 키워드("점검"·"drift"·"적응"·"baseline 갱신"). 비코드 도메인은 사용 신호 캡처는 박제하고 baseline drift는 CLAUDE.md에 future scope 명시(10-7) — silent 생략 금지

## 권장 (should) — 9개

- [ ] **brownfield baseline 완전성** — 5축(또는 quick scan 3축) 채움 + 필수 5개 필드(`tech_stack`/`team.size`/`timeline.horizon`/`deployment_target`/`test_rigor`) + 스킵 필드 `meta.open_questions` 등록 + `inferred_fields`/`user_confirmed_fields` 둘 다 기록
- [ ] **모든 Agent 호출에 `model: "opus"` 파라미터 명시**
- [ ] **기존 에이전트/스킬과 충돌 없음**
- [ ] **스킬 description 적극적("pushy")** — 후속 작업 키워드 포함
- [ ] **SKILL.md 본문 500줄 이내** — 초과 시 references/ 분리
- [ ] **테스트 프롬프트 2~3개 실행 검증**
- [ ] **트리거 검증** — should-trigger + should-NOT-trigger
- [ ] **변경 이력 갱신** — `_workspace/_baseline/changelog.md`에 에이전트/스킬 추가/삭제/수정 기록
- [ ] **Phase 10 주기 점검** — 오케스트레이터가 telemetry append 직후 마지막 Adapt 후 `harness_invocation` 카운트, ≥ 10이면 최종 보고에 `/harness:harness-adapt` 권장 1줄 (orchestrator-template "Phase 10 주기 점검")
