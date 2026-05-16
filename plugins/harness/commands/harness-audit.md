---
description: 하네스 LLM 추론 영역 정합성 감사 — 책임 중복·트리거 정합·통신 프로토콜 의미·workflow 일관성. 결정적 검증은 별도(`/harness:harness-validate`). 자동 수정 없음.
---

# Harness — Audit (LLM 추론 영역)

하네스 산출물 간 **LLM 추론 영역의 정합성**을 점검한다. `plugins/harness/skills/harness/SKILL.md` Phase 9-5 운영/유지보수 워크플로우의 Phase 9-5-1 현황 감사 단계를 수동으로 트리거하는 명령이다.

> **3개 명령 분리 doctrine (2026-05-14, LLM·deterministic hybrid)**:
> - `/harness:harness-audit` — **LLM 추론 영역** (책임 중복·트리거 의미·workflow 일관성). 본 명령.
> - `/harness:harness-validate` — **deterministic 영역** (구조·schema·chain). LLM 0, plugin scripts 번들.
> - `/harness:harness-adapt` — **telemetry 기반 행동 drift**. Phase 10.
>
> doctrine 2026-05-13C: 결정·persistence는 deterministic, 추론·합성은 LLM, 검증은 양방향 cross-check.

## audit이 validate 결과를 input으로 받는 패턴 (권장 호출 순서)

1. 먼저 `/harness:harness-validate --json` 호출 — deterministic 결과 `_workspace/_audit_validate_{ts}.json` 생성
2. 본 명령 호출 — validate JSON 파일을 input으로 받아:
   - validate **PASS** 시 → LLM 추론 영역에만 집중
   - validate **FAIL** 시 → 구조 실패 우선 보고 + LLM 추론 영역 skip 권고

본 명령이 단독 호출되어도 작동하지만, validate 결과가 있을 때 *추론 영역에 자원 집중*되어 품질 ↑.

## 컨텍스트
- **입력**: `.claude/agents/`, `.claude/skills/`, `CLAUDE.md` 하네스 포인터, `_workspace/_baseline/*.md`
- **출력**: `_workspace/_audit_{ts}.md` 정합성 리포트. **자동 수정 없음** — 발견된 불일치를 사용자에게 보고 후 후속 명령(`/harness:harness-add-agent`, `/harness:harness-evolve` 등)으로 안내.

## 선조건 검증

1. `.claude/agents/` 또는 `.claude/skills/`에 1개 이상 파일이 있는가?

**미충족 시:** "감사할 하네스가 없습니다. `/harness:harness-new`를 먼저 실행하세요."

## 검사 항목 (LLM 추론 영역)

> **참고**: 결정적 검증(파일 존재·frontmatter 파싱·dangling reference·필수 필드 존재)은 본 명령 **범위 외** — `/harness:harness-validate`로 위임. 본 섹션은 *의미·일관성·표현 quality*에 집중.

### 1. 에이전트 책임 중복·gap LLM 분석
- 에이전트 N명의 핵심 역할 본문을 *추론* — 책임 영역이 명확히 분리되는가? overlap 있는가? gap 있는가?
- `model: "opus"` 명시 누락 시 *권고* (validate가 결정적 검출하지만 audit이 *권고 사유* 박제)
- 팀 통신 프로토콜의 의미 정합 — N명의 SendMessage 송수신 매트릭스가 *실제로* 워크플로우 진행에 충분한가?

### 2. 스킬 description 트리거 quality 추론
- 트리거 키워드 빈약도 (구체 키워드 < 3개면 flag)
- **트리거 충돌 추론**: N개 스킬 description이 동일 발화에 동시 매칭될 위험 분석 (Phase 8-4 should/should-NOT 보완)
- description의 *적극성* ("pushy") 평가 — 너무 수동적이면 발화 시 미트리거 위험
- Orphan skill 추론 (validate가 결정적 검출하지만 audit이 *제거 vs 유지* 권고)

### 3. CLAUDE.md 변경 이력 의미 정합
- 변경 이력 표 row의 *사유 열*이 LLM 추론에 충분한 맥락 제공하는가? (1행 추가 시 다른 세션이 의사결정 추적 가능?)
- 최근 `.claude/agents/`·`.claude/skills/` 파일 mtime이 변경 이력 마지막 날짜보다 새로움 → *미기록 변경 회상 요청*
- Phase 9/10 출처 박제 정합 (`Phase 9: 사용자 피드백` vs `Phase 10: drift 감지`)

### 4. baseline 추론 영역 정합
- intent profile 필수 5개 필드의 *내용* quality — 필드 존재는 validate가, 내용 quality는 audit이
- `inferred_fields` vs `user_confirmed_fields` 분리 정합 — `source` 인용 0이면 validate가 결정적 검출, 본 명령은 *낮은 confidence 항목의 영향* 추론
- 마지막 갱신 후 3개월 초과 시 *flag + adapt 권고*

### 5. Phase 10 인프라 의미 정합
- 오케스트레이터에 capture 훅 *흔적* 존재 (lines 박제는 validate가) — 본 명령은 *capture 신호 충분도* 추론
- description의 Phase 10 트리거 키워드 ("점검", "drift", "적응", "baseline 갱신") 의미 정합
- *런타임 시그널 부족* 추론 — 누적 이벤트 패턴이 빈약하면 drift 검출 정확도 저하 위험

## 실행 절차

1. 위 5개 항목을 순차 검사
2. 각 발견 사항을 심각도(🔴 차단 / 🟡 경고 / 🟢 OK)로 분류
3. `_workspace/_audit_{timestamp}.md` 작성 — 항목별 발견 사항 + 권장 조치
4. 사용자에게 요약 보고

## 발견된 불일치 처리

| 패턴 | 권장 후속 명령 |
|---|---|
| Orphan agent | `/harness:harness-evolve "에이전트 X 사용 안 됨 — 제거 또는 재배치"` |
| Phantom agent/skill | 수동 — 오케스트레이터 또는 정의 파일 직접 수정 |
| 변경 이력 누락 | 사용자에게 최근 변경 회상 요청 → 수동 기록 |
| baseline stale | `/harness:harness-baseline` |
| Phase 10 인프라 누락 | 수동 — 오케스트레이터에 capture 훅 추가 + description 갱신 |

**자동 수정 절대 금지** — audit은 read-only.
