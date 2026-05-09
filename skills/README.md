# skills/

Claude Code 플러그인 `harness`가 제공하는 스킬 디렉토리.

이 디렉토리의 각 하위 폴더 = 1개 스킬. Claude Code는 사용자 발화가 스킬의 `description`과 매칭될 때 해당 스킬을 자동으로 트리거한다.

## 수록 스킬

| 스킬 | 진입점 | 역할 |
|------|------|------|
| [`harness/`](./harness/SKILL.md) | `harness/SKILL.md` | 도메인을 입력받아 에이전트 팀과 스킬 세트를 생성하는 메타 스킬 |

> 현재 1개. 도메인별 in-house 스킬을 추가할 때는 본 디렉토리에 새 폴더를 만들어 동일한 구조(`SKILL.md` + 선택적 `references/`, `scripts/`, `assets/`)를 따른다.

## harness 스킬

**한 줄 요약:** 사용자가 도메인/프로젝트를 한 문장으로 설명하면, 해당 도메인에 특화된 에이전트 팀과 그 에이전트들이 사용할 스킬을 `.claude/agents/`·`.claude/skills/`에 자동 생성한다.

**트리거 예시 (description 기반):**
- "하네스 구성해줘", "하네스 구축해줘"
- "하네스 설계", "하네스 엔지니어링"
- "하네스 점검", "하네스 감사", "에이전트/스킬 동기화"

전체 트리거 규칙은 [`harness/SKILL.md`](./harness/SKILL.md) frontmatter 참조.

**또는 Slash command로 명시적 호출:** description 매칭 확률에 의존하지 않고 `/harness-new`, `/harness-add-agent`, `/harness-adapt` 등으로 결정적 호출. 카탈로그는 [`../commands/README.md`](../commands/README.md).

### 워크플로우 11단계

| Phase | 이름 | 역할 |
|-------|------|------|
| 0 | Pre-flight | 기존 하네스 산출물 감사 — 신규/확장/유지보수 분기 |
| 1 | Code Research | 프로젝트 객관 baseline 추출 (greenfield/brownfield 자동 감지) |
| 2 | Project Inquiry | 사용자 의도 7섹션(vision~meta) 수집 |
| 3 | 도메인 분석 | profile + intent 합성, 핵심 작업 유형 식별 |
| 4 | 팀 아키텍처 설계 | 실행 모드 + 패턴 + 분리 기준 결정 |
| 5 | 에이전트 정의 생성 | `.claude/agents/{name}.md` 작성 |
| 6 | 스킬 생성 | `.claude/skills/{name}/SKILL.md` 작성 |
| 7 | 통합 및 오케스트레이션 | 오케스트레이터 스킬 + CLAUDE.md 포인터 |
| 8 | 검증 및 테스트 | 7단계 검증 (구조·실행·트리거·드라이런·반복 개선) |
| 9 | 하네스 진화 | 사용자 피드백 기반 수동 진화 |
| 10 | Runtime Adaptation | 자동 관측 → drift 감지 → 제안+승인 |

상세는 [`harness/SKILL.md`](./harness/SKILL.md).

### references/ 가이드 (11개)

`SKILL.md` 본문은 골격(≤500줄)만 유지하고, 깊이 있는 가이드는 `references/`로 분리(progressive disclosure).

| 파일 | 다루는 주제 | 참조 Phase |
|------|----------|-----------|
| [`code-research.md`](./harness/references/code-research.md) | greenfield/brownfield 감지, 5축 조사, quick scan vs deep audit | Phase 1 |
| [`project-profile-schema.md`](./harness/references/project-profile-schema.md) | Phase 1 산출물 표준 스키마 | Phase 1 |
| [`project-inquiry.md`](./harness/references/project-inquiry.md) | 두 브랜치 채우기 전략, 자동 추론 매핑, 코드 grounded 질문 패턴 | Phase 2 |
| [`intent-profile-schema.md`](./harness/references/intent-profile-schema.md) | Phase 2 산출물 스키마 + greenfield/brownfield 인스턴스 예시 | Phase 2 |
| [`agent-design-patterns.md`](./harness/references/agent-design-patterns.md) | 6 패턴 비교, 실행 모드 결정 트리, 분리 기준 표 | Phase 4 |
| [`team-examples.md`](./harness/references/team-examples.md) | 실제 하네스 산출물 예시 (에이전트 정의 전문 포함) | Phase 4·5 |
| [`qa-agent-guide.md`](./harness/references/qa-agent-guide.md) | QA 에이전트 정의 템플릿, 경계면 버그 패턴 | Phase 5 |
| [`skill-writing-guide.md`](./harness/references/skill-writing-guide.md) | description 작성, 본문 스타일, 출력 형식, 데이터 스키마 | Phase 6 |
| [`orchestrator-template.md`](./harness/references/orchestrator-template.md) | 패턴별 골격, 데이터 흐름, 컨텍스트 확인 단계 템플릿 | Phase 7 |
| [`skill-testing-guide.md`](./harness/references/skill-testing-guide.md) | 테스트 프롬프트, with/without 비교, 트리거 충돌 진단 | Phase 8 |
| [`runtime-adaptation.md`](./harness/references/runtime-adaptation.md) | telemetry schema, 7종 capture 이벤트, drift 룰, 승인 UX | Phase 10 |

## 산출물 위치 (생성된 하네스가 떨어지는 곳)

`harness` 스킬은 본인의 코드를 변경하지 않고 **사용자 프로젝트**에 산출물을 쓴다:

```
{사용자 프로젝트}/
├── .claude/
│   ├── agents/{agent-name}.md         ← Phase 5 산출
│   └── skills/{skill-name}/SKILL.md   ← Phase 6·7 산출
├── _workspace/
│   ├── _baseline/
│   │   ├── project_profile.md         ← Phase 1 산출 (t=0 anchor)
│   │   └── intent_profile.md          ← Phase 2 산출
│   └── _telemetry/{date}.jsonl        ← Phase 10 capture
└── CLAUDE.md                          ← Phase 7-4 하네스 포인터 추가
```

## 새 스킬을 이 디렉토리에 추가할 때

1. **폴더 생성:** `skills/{new-skill-name}/`
2. **SKILL.md 작성:** YAML frontmatter (`name`, `description`) + Markdown 본문, 본문 ≤500줄
3. **description은 적극적으로(pushy):** 트리거 키워드를 5개 이상 명시, 유사하지만 트리거하면 안 되는 경우와 구분
4. **상세는 `references/`로 분리:** SKILL.md 본문은 골격만, 깊이 있는 가이드는 references 파일로
5. **본 README의 "수록 스킬" 표 갱신**

작성 룰 전체는 [`harness/references/skill-writing-guide.md`](./harness/references/skill-writing-guide.md) 참조.

## 라이선스

Apache-2.0 (프로젝트 루트의 `LICENSE` 참조).
