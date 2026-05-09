# commands/

Harness 플러그인의 명시적 진입점 — slash command. `description` 매칭 확률에 의존하지 않고 사용자가 직접 호출하는 결정론적 호출 방식.

## 호출 방식 두 가지

| 방식 | 발동 | 비용 통제 | 용도 |
|---|---|---|---|
| **자연어 트리거** (`skills/harness/SKILL.md` description) | 발화 ↔ description 매칭 (확률) | LLM이 Phase 0 매트릭스로 판단 | "하네스 구성해줘" 등 자연스러운 발화 |
| **Slash command** (이 디렉토리) | `/명령어` (결정) | 사용자가 명령어 선택으로 직접 통제 | Phase 범위 명시, 비용 회피, CI 자동화 |

두 방식은 **양립**한다. 명령어 본문은 얇은 진입점이며 실제 로직은 모두 `skills/harness/SKILL.md`를 따른다.

## 명령어 카탈로그 (Phase 0 매트릭스 매핑)

| 명령어 | 인자 | 실행 Phase 범위 | Phase 0 매트릭스 행 |
|---|---|---|---|
| [`/harness-new`](./harness-new.md) | `<도메인 한 문장>` | 0~8 전체 | 신규 구축 |
| [`/harness-add-agent`](./harness-add-agent.md) | `<역할 한 줄>` | 4·5·7·8 (1·2·3 SKIP) | 에이전트 추가 |
| [`/harness-add-skill`](./harness-add-skill.md) | `<스킬 이름/의도>` | 6·7·8 (1·2·3·4·5 SKIP) | 스킬 추가/수정 |
| [`/harness-baseline`](./harness-baseline.md) | – | 1·2 재실행 + 영향 분석 | baseline 갱신 |
| [`/harness-audit`](./harness-audit.md) | – | 9-5 §1 (read-only 정합성 감사) | 운영/유지보수 |
| [`/harness-evolve`](./harness-evolve.md) | `<피드백>` | 9 수동 진화 (피드백 → 9-2 매핑) | (Phase 9) |
| [`/harness-adapt`](./harness-adapt.md) | – | 10 Diagnostic + Adapt | (Phase 10) |

## 의사결정 트리

```
하네스 만들고 싶다 → /harness-new <도메인>

하네스 이미 있다
├── 에이전트 1명 추가 → /harness-add-agent <역할>
├── 스킬 1개 추가/수정 → /harness-add-skill <스킬>
├── 사용자 피드백 반영 → /harness-evolve <피드백>
├── 코드 많이 변함 → /harness-baseline
├── 정합성 의심 (파일 ↔ 오케스트레이터) → /harness-audit
└── telemetry 기반 자동 점검 → /harness-adapt
```

## 공통 설계 원칙

모든 명령어는 다음 4섹션을 가진다:

1. **컨텍스트** — 인자 / 입력 / 출력 명시
2. **선조건 검증** — 호출 전 만족해야 할 조건 + 미충족 시 다른 명령으로 안내
3. **실행 절차** — 어느 Phase를 어떤 순서로 (SKILL.md 본체 참조, 로직 복제 없음)
4. **범위 외 / 후속 명령** — 이 명령이 다루지 않는 작업 + 적절한 다음 명령

**자동 적용 금지 원칙** — `/harness-adapt`은 변경안을 사용자 승인 후에만 적용. `/harness-audit`은 read-only.

## 두 레벨 구분 (L1 vs L2)

| 레벨 | 위치 | 정책 |
|---|---|---|
| **L1: 본 디렉토리** (`dharness/commands/`) | harness 플러그인 진입점 | **추가 가능** — 본 README가 카탈로그 |
| **L2: 사용자 프로젝트** (`{사용자 프로젝트}/.claude/commands/`) | harness가 생성한 산출물 일부 | **금지** — `skills/harness/SKILL.md` 산출물 체크리스트 |

이 구분은 SKILL.md 산출물 체크리스트 항목 "사용자 프로젝트의 `.claude/commands/`에는 아무것도 생성하지 않음"의 범위를 명확히 한다.

## 명령어 추가/수정 가이드

새 명령어 추가 시:

1. `commands/{name}.md` 생성 — frontmatter(`description`, `argument-hint` if any) + 본문
2. **본문은 얇게 유지** — 로직은 `skills/harness/SKILL.md` 또는 `references/`를 가리킴
3. 위 4섹션 패턴 준수 (컨텍스트 / 선조건 / 실행 / 범위 외)
4. 본 README의 카탈로그 표 + 의사결정 트리 갱신
5. 관련 다른 명령어의 "후속 명령" 섹션에서 새 명령 언급 (cross-link)
