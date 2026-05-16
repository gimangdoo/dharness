---
description: 기존 하네스에서 에이전트 또는 스킬 1개를 명시적으로 제거. dangling reference 결정적 cleanup 포함.
argument-hint: <agent|skill> <이름>
---

# Harness — Remove Agent or Skill

기존 하네스에서 에이전트 또는 스킬 1개를 제거한다. Phase 9-2 매핑 표의 "제거" 행에 해당하는 *격리된* 진입점 — `harness-evolve` 자유 텍스트 포괄과 달리 dangling reference cleanup이 결정적으로 수행된다.

## 컨텍스트

- **인자**: `$ARGUMENTS` (예: `agent researcher`, `skill code-review`)
  - 첫 토큰: `agent` | `skill`
  - 두 번째 토큰: 대상 이름 (frontmatter `name:` 기준)
- **입력**: 기존 `.claude/agents/{name}.md` 또는 `.claude/skills/{name}/SKILL.md`, 오케스트레이터 스킬, CLAUDE.md
- **출력**: 대상 파일 삭제 + 오케스트레이터/agents/skills cross-reference 갱신 + CLAUDE.md 변경 이력 1행

## 선조건 검증 (먼저 실행)

1. `$ARGUMENTS` 1·2 토큰 파싱 가능?
2. `agent` 모드: `.claude/agents/{name}.md` 존재?
3. `skill` 모드: `.claude/skills/{name}/SKILL.md` 존재?
4. 기존 오케스트레이터 스킬 식별 가능? (Phase 7-4 CLAUDE.md 포인터 또는 `.claude/skills/`)
5. `_workspace/_baseline/*.md` 존재? (이후 단계 영향 분석 입력)

**미충족 시 즉시 중단**:

| 미충족 | 안내 |
|---|---|
| (1) | "인자 형식 오류 — `agent <이름>` 또는 `skill <이름>` 형식으로 입력하세요." |
| (2)·(3) | "대상 미존재 — `.claude/agents/` 또는 `.claude/skills/` 인벤토리 확인 후 재실행하세요." |
| (4) | "오케스트레이터 식별 실패 — CLAUDE.md 포인터를 수동 확인하세요." |
| (5) | "baseline 미존재 — `/harness:harness-baseline` 먼저 실행 권장 (영향 분석 입력 부재)." |

## 실행 절차

### Step 1: 영향 분석 (사용자 confirm 게이트)

대상 제거가 다른 산출물에 미치는 영향을 *결정적* grep으로 식별:

1. **에이전트 제거 시:**
   - 오케스트레이터 스킬 본문에서 `{name}` 인용 검색 (역할 표, 작업 할당, 통신 프로토콜)
   - 다른 에이전트의 `.md` 본문 `SendMessage` / 통신 프로토콜 표에서 `{name}` 인용
   - 스킬의 description / 본문에서 `{name}` 인용
   - 이 에이전트만 사용하는 스킬이 있는가? (있다면 → orphan 스킬, 사용자 confirm 필요)

2. **스킬 제거 시:**
   - 에이전트 frontmatter `tools:` allowlist의 인용
   - 오케스트레이터 스킬에서의 워크플로우 인용
   - 이 스킬을 발화시키는 description 트리거 키워드

3. **출력 — 사용자 confirm 게이트**:
   ```
   🗑️ 제거 대상: {agent|skill} {name}

   📋 영향 받는 산출물:
     - 오케스트레이터: {orchestrator-name} (N hits)
       - 라인 X: {인용 context}
     - 다른 에이전트: {teammate-a} (M hits), {teammate-b} (K hits)
     - 스킬: {skill-x} (L hits)
   ⚠️ Orphan 산출물 (해당 시): {orphan-list}

   진행하시겠습니까? [y/N]
   ```

   `y` 응답 외 즉시 중단.

### Step 2: 결정적 삭제

1. **에이전트 제거**: `.claude/agents/{name}.md` 삭제
2. **스킬 제거**: `.claude/skills/{name}/` 디렉토리 전체 삭제 (`SKILL.md` + references/ 포함)

### Step 3: Cross-reference 결정적 cleanup

**에이전트 제거 시:**

1. 오케스트레이터 스킬 본문 수정:
   - 에이전트 구성 표에서 `{name}` 행 제거
   - 워크플로우의 작업 할당 표에서 `{name}` 행 제거
   - 통신 프로토콜에서 `{name}` 인용 제거
   - `TeamCreate(members: ...)` 예시 본문이 있다면 `{name}` 항목 제거 (의사코드 영역)
2. 다른 에이전트 `.md` 수정:
   - 통신 프로토콜 표에서 `{name}` 송수신 행 제거
   - 본문 prose 인용은 LLM이 의미 보존하며 재서술 (이 단계만 LLM 추론)

**스킬 제거 시:**

1. 에이전트 frontmatter `tools:` allowlist에서 인용 제거 (해당하는 경우)
2. 오케스트레이터에서 스킬 이름 인용 제거
3. description 트리거 키워드 재검토 (해당 스킬 전용 키워드는 제거 권고)

### Step 4: 검증

1. **Dangling reference grep**: 제거 후 `{name}` 인용이 `.claude/` 트리에 0건임을 확인 (`Grep` 검색).
2. **Orchestrator 구조 검증**: 표 형식 깨짐 없음, YAML frontmatter 파싱 가능.
3. **(가용 시) `/harness:harness-validate` 호출**: 결정적 구조·schema·chain 재검증.

검증 실패 시 사용자에게 보고 + 수동 cleanup 안내 (자동 rollback은 본 명령 범위 외 — git 활용 권장).

### Step 5: CLAUDE.md 변경 이력 갱신

Phase 7-4 템플릿 형식으로 한 행 추가:

```
| {YYYY-MM-DD} | {agent|skill} 제거: {name} | 오케스트레이터 + .claude/{agents|skills}/ | {사유} |
```

### Step 6: 출력 안내 템플릿 (필수)

```
🗑️ 제거 완료
  - .claude/{agents|skills}/{name}{/.md|/} 삭제
  - 오케스트레이터 cross-reference N건 정리
  - 다른 에이전트 cross-reference M건 정리
  - CLAUDE.md 변경 이력 1행 추가

⚠️ Orphan 산출물 (해당 시):
  - {orphan-skill-x}: 이 에이전트만 사용. 별도 `/harness:harness-remove skill {x}` 권고.

📋 다음 권고:
  - `/harness:harness-audit` — LLM 추론 영역 일관성 검토
  - `/harness:harness-validate` — deterministic 구조·schema·chain 재검증
```

## 범위 외

- **baseline 갱신하지 않는다** — 도메인/요구가 축소되었다면 `/harness:harness-baseline` 별도 호출
- **Phase 10 drift 자동 트리거 안 함** — 제거 후 drift 검사는 `/harness:harness-adapt`
- **자동 rollback 없음** — git을 활용한 수동 복원 권장 (제거 작업 *전* commit 권장)
- **MCP 제거 안 함** — `tools:` allowlist 정리만 수행, MCP 자체 uninstall은 사용자 명시 요청 시 별도 진행
- **분할·통합 워크플로우 아님** — 책임 분할은 `/harness:harness-split`, 통합은 `/harness:harness-merge`

## 사용자 확정 doctrine (2026-05-14)

본 명령은 사용자 의도 "삭제" 워크플로우를 격리 명령으로 표면화하는 결정에 따라 신설됨 (감사 plan A1). evolve 본문 자유 텍스트 포괄은 dangling cleanup 결정성 부재로 부적합 판정.
