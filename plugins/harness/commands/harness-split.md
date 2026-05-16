---
description: 기존 에이전트 또는 스킬 1개를 책임별로 2개 이상으로 분할. 분리 기준 4축 cross-check 후 cross-reference 갱신.
argument-hint: <agent|skill> <원본 이름> <분할 결과 이름 2개 이상, 공백 구분>
---

# Harness — Split Agent or Skill

기존 에이전트/스킬 1개를 책임 분할 기준 4축(전문성·병렬성·컨텍스트·재사용성)에 따라 2개 이상으로 분리한다. Phase 9-2 매핑 표의 "역할 분할" 행에 해당하는 격리된 진입점.

## 컨텍스트

- **인자**: `$ARGUMENTS` (예: `agent fullstack-dev frontend-dev backend-dev`)
  - 첫 토큰: `agent` | `skill`
  - 두 번째: 원본 이름
  - 세 번째 이후: 분할 결과 이름 2개 이상
- **입력**: 기존 `.claude/agents/{원본}.md` 또는 `.claude/skills/{원본}/SKILL.md`, 오케스트레이터, baseline
- **출력**: 신규 N개 정의 파일 + 원본 삭제 + cross-reference 갱신 + CLAUDE.md 변경 이력 1행

## 선조건 검증

1. `$ARGUMENTS` 토큰 ≥3 (mode + 원본 + 결과 2개 이상)?
2. 원본 파일 존재?
3. 결과 이름 충돌 0 (`.claude/agents/{결과명}.md` 또는 `.claude/skills/{결과명}/` 미존재)?
4. baseline 존재?
5. 오케스트레이터 식별 가능?

**미충족 시 즉시 중단** — 안내 메시지 형식은 `harness-remove.md` 선조건 표 참조.

## 실행 절차

### Step 1: 분리 기준 4축 자동 cross-check (LLM 추론)

`plugins/harness/skills/harness/references/agent-design-patterns.md` §분리 기준 4축:

1. **전문성 (specialization)**: 분할 결과 각각이 서로 다른 도메인/스택/책임을 가지는가?
2. **병렬성 (parallelism)**: 두 책임이 동시에 진행 가능한가? 아니면 순차적 의존인가?
3. **컨텍스트 (context)**: 분할 후 각자 다루는 컨텍스트가 의미 있게 줄어드는가?
4. **재사용성 (reusability)**: 분할된 책임 중 하나가 다른 에이전트/스킬에서 재사용 가능한가?

**판정**:
- 4축 중 ≥3 PASS → 분할 권장
- ≤2 PASS → 사용자에게 "분할 효과 약함 — 단일 유지 권고" 보고 후 진행 confirm 게이트

### Step 2: 영향 분석 + 사용자 confirm 게이트

`harness-remove.md` Step 1 형식으로 cross-reference 영향 출력:

```
✂️ 분할 대상: {agent|skill} {원본} → {결과1}, {결과2}, ...

📋 4축 cross-check:
  - 전문성: ✓ {각 결과의 도메인}
  - 병렬성: ✓ {병렬/순차 판정}
  - 컨텍스트: ✓ {컨텍스트 감소 추정}
  - 재사용성: △ {판정}

📋 영향 받는 산출물:
  - 오케스트레이터: {hits + 라인}
  - 다른 에이전트/스킬: {hits}

진행하시겠습니까? [y/N]
```

### Step 3: 신규 정의 파일 작성 (LLM 합성)

**에이전트 분할 시:**

1. 원본 `.claude/agents/{원본}.md` 본문을 LLM이 분석 — 각 책임 단위로 절(섹션)을 그루핑.
2. N개 신규 파일 `.claude/agents/{결과명}.md` 작성:
   - frontmatter `name:` 갱신
   - `model:` 원본 유지 (기본 `opus`)
   - 필수 섹션: 핵심 역할, 작업 원칙, 입력/출력 프로토콜, 에러 핸들링, 협업, 팀 통신 프로토콜
   - **Phase 5-2 (도구·MCP)**: 원본 `tools:` allowlist를 책임별로 분할. capability profile 재매칭 — `references/permission-profiles.md` §3-1 매트릭스. 결과 에이전트 중 일부가 신규 profile에 해당하면 사용자 confirm 후 MCP 추가 install 검토 (단 본 명령 범위 외 — `/harness:harness-mcp-adopt`로 안내).
3. **결과 에이전트 간 통신 프로토콜**: 원본이 단독 처리하던 데이터 흐름을 결과 에이전트 N개의 `SendMessage` 프로토콜로 분산. orchestrator-template.md "팀원 간 통신 규칙" 패턴 적용.

**스킬 분할 시:**

1. 원본 `SKILL.md` 본문을 LLM이 분석 — 워크플로우 단계를 책임별로 그루핑.
2. N개 신규 디렉토리 `.claude/skills/{결과명}/SKILL.md` 작성:
   - description: 원본의 트리거 키워드를 책임별로 분할 (한 키워드가 두 결과 스킬에 동시 매칭되지 않도록 boundary 박제)
   - 본문: 분할된 워크플로우 + references/ 분배 (공유 reference는 양쪽에서 link)
3. **트리거 충돌 검증**: 결과 스킬 N개의 description이 동일 발화에 모두 매칭되면 우선순위 doctrine 박제 또는 description 재서술.

### Step 4: 원본 삭제 + Cross-reference cleanup

`harness-remove.md` Step 2~3 절차 그대로 적용 — 원본 파일 삭제 후 orchestrator/agents/skills 인용을 결과 N개로 분배.

**중요**: 분할은 *책임 보존* 원칙 — 원본의 모든 책임이 결과 N개에 1:1 매핑되어야 함. LLM이 책임 누락/중복 검출 시 사용자에게 보고.

### Step 5: 검증

1. **책임 보존 검증** (LLM 추론): 결과 N개의 책임 합집합 = 원본 책임?
2. **Dangling reference grep**: 원본 이름 인용 0건?
3. **트리거 충돌 검증** (스킬 분할 시): 결과 스킬 description 매칭 발화 cross-check
4. **(가용 시) `/harness:harness-validate` 호출**: deterministic 검증

### Step 6: CLAUDE.md 변경 이력

```
| {YYYY-MM-DD} | {agent|skill} 분할: {원본} → {결과1}, {결과2}, ... | 오케스트레이터 + .claude/{agents|skills}/ | {사유: 4축 판정 + 분할 동기} |
```

### Step 7: 출력 안내 템플릿

```
✂️ 분할 완료
  - 원본 .claude/{agents|skills}/{원본} 삭제
  - 신규 N개 생성: {결과1}, {결과2}, ...
  - 오케스트레이터 cross-reference 분산: N→M
  - CLAUDE.md 변경 이력 1행 추가

📋 다음 권고:
  - `/harness:harness-audit` — LLM 추론 영역 일관성 검토
  - `/harness:harness-validate` — deterministic 구조·schema·chain 재검증
  - (스킬 분할 시) Phase 8-4 트리거 회귀 8+8 테스트 권고
```

## 범위 외

- **baseline 갱신 X** — 도메인 자체가 분기되었다면 `/harness:harness-baseline` 별도
- **MCP 추가 install X** — 결과 에이전트가 신규 profile 매칭 시 `/harness:harness-mcp-adopt`로 안내만
- **자동 rollback 없음** — git commit 권장

## 사용자 확정 doctrine (2026-05-14)

본 명령은 사용자 의도 "분할" 워크플로우를 격리 명령으로 표면화하는 결정에 따라 신설. evolve 본문 자유 텍스트 포괄은 책임 보존 검증·트리거 충돌 검증의 결정성 부재로 부적합 판정.
