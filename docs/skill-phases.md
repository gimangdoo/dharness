# harness 메타 스킬 — 15단계 워크플로우

> [README](../README.md)로 돌아가기 · 정본 정의: [`plugins/harness/skills/harness/SKILL.md`](../plugins/harness/skills/harness/SKILL.md)

`/harness:harness-new`가 도메인 한 문장을 받아 에이전트 팀·스킬·CLAUDE.md·관측 인프라까지 합성할 때 거치는 단계다 (12 본 phase + 3 critique/sim phase = 15단계).

| Phase | 이름 | 출력 |
|-------|------|------|
| 0 | Pre-flight 감사 | 신규/확장/유지보수 분기 |
| 0.5 | Domain Clarification (Pre-flight) | premature-judgment 차단 게이트 |
| 1 | Code Research | 프로젝트 baseline (코드 인벤토리 + 도메인 sense) |
| 2 | Project Inquiry | 사용자 의도 + 도메인 sense 정합 |
| 3 | 도메인 분석 | 작업 유형 + 충돌 분석 |
| 3.5 | Self-Critique on Domain Analysis | single-pass silent error 검출 |
| 4 | 팀 아키텍처 | 모드 + 패턴 + 분리 기준 |
| 5 | 에이전트 정의 | `.claude/agents/{name}.md` |
| 5.5 | Self-Critique on Agent Definitions | 역할 중복 cross-review |
| 6 | 스킬 생성 | `.claude/skills/{name}/SKILL.md` |
| 7 | 오케스트레이션 | 통합 스킬 + CLAUDE.md 포인터 |
| 7.5 | Orchestrator Dry-Run Simulation | dead link/순환 의존 검출 |
| 8 | 검증 (7단계) | 구조·실행·트리거·드라이런·반복 개선 |
| 9 | 진화 (수동) | 사용자 피드백 → 에이전트/스킬 갱신 |
| 10 | Runtime Adaptation | telemetry → drift 감지 → 제안+승인 |

Phase 9는 `/harness:harness-evolve`, Phase 10은 `/harness:harness-adapt`의 진입점이다.
