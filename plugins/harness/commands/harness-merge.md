---
description: 기존 에이전트 또는 스킬 2개 이상을 1개로 통합. 책임 중복·통신 비용 진단 후 cross-reference 갱신.
argument-hint: <agent|skill> <통합 결과 이름> <원본 이름 2개 이상, 공백 구분>
---

# Harness — Merge Agents or Skills

기존 에이전트/스킬 2개 이상을 1개로 통합한다. Phase 9-2 매핑 표의 "역할 통합" 행에 해당하는 격리된 진입점.

## 컨텍스트

- **인자**: `$ARGUMENTS` (예: `agent unified-dev frontend-dev backend-dev`)
  - 첫 토큰: `agent` | `skill`
  - 두 번째: 통합 결과 이름
  - 세 번째 이후: 원본 이름 2개 이상
- **입력**: 기존 `.claude/agents/{원본i}.md` 또는 `.claude/skills/{원본i}/SKILL.md` N개, 오케스트레이터, baseline
- **출력**: 신규 통합 정의 파일 1개 + 원본 N개 삭제 + cross-reference 갱신 + CLAUDE.md 변경 이력 1행

## 선조건 검증

1. `$ARGUMENTS` 토큰 ≥4 (mode + 결과 + 원본 2개 이상)?
2. 원본 N개 모두 존재?
3. 결과 이름 충돌 0 (단, 결과 이름이 원본 중 하나와 동일 시 *대체* 모드로 처리 — 사용자 confirm 필요)?
4. baseline 존재?
5. 오케스트레이터 식별 가능?

**미충족 시 즉시 중단**.

## 실행 절차

### Step 1: 통합 정당성 cross-check (LLM 추론)

`references/agent-design-patterns.md` §분리 기준 4축의 *역방향* 점검:

1. **전문성 중복**: 원본 N개의 책임이 실제로 중첩되는가? 통합 후 전문성 약화 위험 0?
2. **병렬성 손실**: 원본이 병렬 실행되던 경우 통합으로 직렬화되어 비용 증가?
3. **컨텍스트 폭증**: 통합 후 단일 에이전트가 다루는 컨텍스트가 임계 초과?
4. **재사용성 손실**: 원본 중 하나가 다른 워크플로우에서 재사용 중인가? (재사용 발견 시 통합 차단 권고)

**판정**:
- 4축 모두 PASS → 통합 권장
- 1축 이상 FAIL → 사용자에게 위험 보고 후 진행 confirm 게이트

### Step 2: 영향 분석 + 사용자 confirm 게이트

```
🔀 통합 대상: {agent|skill} {원본1}, {원본2}, ... → {결과}

📋 4축 역방향 cross-check:
  - 전문성 중복: ✓ {중첩 영역 요약}
  - 병렬성 손실: △ {원본이 병렬 실행되었는지 + 비용 추정}
  - 컨텍스트 폭증: ✓ {통합 후 추정 컨텍스트 크기}
  - 재사용성 손실: ✓ {다른 워크플로우 인용 hits}

📋 영향 받는 산출물:
  - 오케스트레이터: 통신 프로토콜 단순화 N → 1
  - 다른 에이전트: SendMessage 대상 갱신 필요 hits
  - 스킬: 트리거 키워드 통합

진행하시겠습니까? [y/N]
```

### Step 3: 통합 정의 파일 작성 (LLM 합성)

**에이전트 통합 시:**

1. 원본 N개 `.claude/agents/{원본i}.md` 본문 LLM 분석 — 책임 union 도출.
2. 신규 `.claude/agents/{결과}.md` 작성:
   - frontmatter: 원본의 최상위 model + 모든 trigger 키워드 union
   - 필수 섹션: 핵심 역할 (union), 작업 원칙 (union — 충돌 시 사용자 confirm), 입력/출력 프로토콜 (union), 에러 핸들링 (union), 협업, 팀 통신 프로토콜 (외부 통신만 유지 — 원본 *간* 통신은 internal로 흡수되어 삭제)
   - **Phase 5-2 (도구·MCP)**: 원본 N개 `tools:` allowlist union. capability profile 재매칭 — 통합으로 새 profile 발화 시 사용자 confirm. allowlist 중복은 1회로 압축.
3. **컨텍스트 압박 검증**: 통합 후 단일 에이전트가 모든 책임 처리 시 도구 출력 10KB 초과 빈도 추정. 임계 초과 예상 시 사용자 보고.

**스킬 통합 시:**

1. 원본 N개 `SKILL.md` 본문 LLM 분석 — 워크플로우 단계 정합.
2. 신규 `.claude/skills/{결과}/SKILL.md` 작성:
   - description: 원본 N개 트리거 키워드 union. 중복 키워드는 1회로 압축. 모순 키워드 발견 시 사용자 confirm.
   - 본문: 워크플로우 통합 (LLM이 단계 정합 — 충돌 시 사용자 confirm)
   - references/: 원본 N개의 references union (중복 reference는 1회)
3. **트리거 모순 검증**: 통합 description이 원본 N개 발화 모두 매칭하는가? 누락 발화 발견 시 description 보강.

### Step 4: 원본 N개 삭제 + Cross-reference cleanup

`harness-remove.md` Step 2~3 절차를 원본 N개에 *반복* 적용 — 단, cross-reference cleanup은 *마지막에 1회만* 수행 (N회 중복 cleanup 방지):

1. 원본 N개 파일/디렉토리 삭제
2. 오케스트레이터 본문에서 원본 N개 인용을 모두 *결과 이름*으로 치환 (구조 표·통신 프로토콜·작업 할당). 원본 *간* 통신 프로토콜 행은 제거 (internal로 흡수).
3. 다른 에이전트/스킬에서 원본 N개 인용을 결과 이름으로 치환.

### Step 5: 검증

1. **책임 보존 검증** (LLM 추론): 결과의 책임 = 원본 N개 책임의 union? 누락·중복 0?
2. **Dangling reference grep**: 원본 N개 이름 인용 0건?
3. **트리거 완전성 검증** (스킬 통합 시): 원본 발화 샘플 8개를 description 매칭 cross-check
4. **(가용 시) `/harness:harness-validate` 호출**: deterministic 검증

### Step 6: CLAUDE.md 변경 이력

```
| {YYYY-MM-DD} | {agent|skill} 통합: {원본1}, {원본2}, ... → {결과} | 오케스트레이터 + .claude/{agents|skills}/ | {사유: 4축 역방향 판정 + 통합 동기} |
```

### Step 7: 출력 안내 템플릿

```
🔀 통합 완료
  - 원본 N개 삭제: {원본1}, {원본2}, ...
  - 신규 1개 생성: {결과}
  - 오케스트레이터 통신 프로토콜 단순화: N→1
  - CLAUDE.md 변경 이력 1행 추가

📋 다음 권고:
  - `/harness:harness-audit` — LLM 추론 영역 일관성 검토
  - `/harness:harness-validate` — deterministic 구조·schema·chain 재검증
  - (스킬 통합 시) Phase 8-4 트리거 회귀 8+8 테스트 권고
```

## 범위 외

- **baseline 갱신 X** — 도메인이 단순화되었다면 `/harness:harness-baseline` 별도
- **MCP allowlist 정제 X** — 본 명령은 union만 수행, 정제는 `/harness:harness-mcp-status` + 수동
- **자동 rollback 없음** — git commit 권장

## 사용자 확정 doctrine (2026-05-14)

본 명령은 사용자 의도 "통합" 워크플로우를 격리 명령으로 표면화하는 결정에 따라 신설. evolve 본문 자유 텍스트 포괄은 책임 union 검증·트리거 모순 검증의 결정성 부재로 부적합.
