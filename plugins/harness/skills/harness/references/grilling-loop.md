> **Read at phase:** 0.5 / 2 (필수 5필드 진입 또는 Low confidence 추론 확인 시)

# Grilling Loop — One-Question-at-a-Time Pattern

mattpocock `grill-me` 패턴 흡수 (2026-05-19). batch 표 prompt 대신 *순차 1q + LLM 추천 답* 으로 사용자 부담 ↓, 답변 거부율 ↓.

본 reference는 **모드 분기 가이드** — grilling은 batch의 대안이지 대체 아님. dharness `project-inquiry.md` §4-3 skip 룰, §4-4 batch 확인 패턴, §7 필수 재질문 룰은 그대로 유효.

## 1. 4 패턴

| # | 패턴 | dharness 어휘 매핑 |
|---|---|---|
| 1 | One question at a time | §4-4 batch 표를 *단일 row 순차* 로 분해 |
| 2 | Recommended answer per question | §7-1 "기본값 제시" + Phase 1 자동 추론값을 LLM이 1순위 후보로 제시 |
| 3 | Branch tree walk — 의존성 순서 | §5 섹션 번호 고정(1→7) + cross-field 룰(§8-4) 위반 시 의존 필드 먼저 확정 |
| 4 | Codebase exploration fallback | 사용자가 "코드 보면 알 듯" 응답 시 §3 자동 추론 매핑 재실행 (별도 질문 차감) |

## 2. 언제 grilling vs batch

| 상황 | 모드 | 이유 |
|---|---|---|
| High confidence 추론 ≥5 항목 (§3-4) | **batch** + "모두 맞음" 단축 (§4-4) | 사용자 부담 ↓, 정확도 영향 없음 |
| Low confidence 추론 (§3-2, `meta.confidence_low`) | **grilling** | recommendation + 단일 confirm 필요 |
| 필수 5필드 (§5 ★ 항목) 미답 + 사용자 1차 거부 | **grilling** | doctrine 박제 강도 ↑, hard fail (§7-3) 직전 마지막 시도 |
| greenfield vision/scope 자유 텍스트 | **grilling** | LLM이 답안 후보 1개 먼저 제시 — 빈 박스 막막함 해소 (§4-1 예시 룰 정합) |
| enum 다중 선택 (예: `deployment_target`) | **batch** | multi-select UI 부적합 — grilling으로 분해 시 사용자 부담 ↑ |
| Phase 0.5 4항목 모호성 검사 empty 항목 | **grilling** | 4항목 작은 N — recommendation 비용 < batch 사용자 fatigue |
| Phase 5 cardinality justification (에이전트 N개) | grilling **옵션** | 모호한 후보 1~2개에 한정 — 전체 grilling 시 합성 시간 폭증 |

## 3. Recommended Answer 생성 룰

`grill-me` 핵심: "for each question, provide your recommended answer". dharness anti-premature-judgment doctrine 정합 가드 필수.

### 3-1. 추천 source

| 출처 | 사용 가능 | 사용 금지 (anti-premature-judgment) |
|---|---|---|
| `project_profile.md` signals ≥2 | ✓ | — |
| §3-1 직접 매핑 (High confidence) | ✓ | — |
| §3-2 추정 매핑 (Medium confidence) | ✓ (`recommended:` 표현) | — |
| §3-2 추정 (Low confidence) | ✓ (`recommended (low conf):` 표현) | — |
| 디렉토리 이름 단독 | — | ✗ — Phase 0.5 doctrine 위반 |
| 파일 이름 단독 | — | ✗ |
| README.md 한 줄 | — | ✗ (스캔만 가능) |
| `$ARGUMENTS` 키워드만 | — | ✗ |

### 3-2. 추천 표현 룰

| 표현 | 허용 | 예시 |
|---|---|---|
| `recommended: {value}` (단일 후보) | ✓ | `recommended: solo` |
| `recommended (low conf): {value}` (단일 후보, 약한 신호) | ✓ | `recommended (low conf): smb` |
| `recommended: {v1} / 또는 {v2}` (대안 제시) | ✓ | `recommended: web / 또는 server` |
| `이 프로젝트는 X다` (단정) | ✗ | doctrine 위반 |
| `domain: X로 확정` | ✗ | doctrine 위반 |

### 3-3. 추천 답안 표시 형식

```
{필드 dot-path}: ?
    recommended: {값}
    근거: {project_profile source 또는 §3 매핑 룰}
    → 맞음 / 수정 / 모르겠음 / 코드 봐
```

§4-4 batch 패턴과 동일 응답 3지 + "코드 봐" 1개 추가 (패턴 4 trigger).

## 3-4. Advisor Delegation Branch (2026-05-24, methodology-advisor v0.3.x + v0.12.1 adapter)

`workflow.methodology` 필드 grilling 시 사용자 응답이 "모르겠음" / "추천해줘" / "방법론 골라줘" 시 별도 분기:

| 사용자 응답 | grilling 동작 |
|---|---|
| 명시적 enum 값 ("TDD", "DDD" 등) | 통상 grilling — `methodology_source: user` 박제 |
| "모르겠음" / "추천" / "골라줘" | **advisor 위임** — `/methodology-advisor` sub-skill 호출, handoff yaml fragment 수신 |
| "스킵" / "건너뛰기" | `methodology: unknown` + `methodology_source: none` + `meta.open_questions`에 등록 |

advisor 위임 시 처리 (5 step):
1. **methodology-advisor sub-skill 호출** (입력: 현 시점 intent_profile 부분 합성 + 사용자 발화, dharness-sub 모드 트리거)
2. **handoff yaml fragment 수신** — advisor v0.3.x `intent_profile_patch:` envelope 보장 (`workflow.methodology` list + `methodology_source` free string + `methodology_matrix_row` 또는 "matrix-miss" sigil)
3. **adapter 변환 step (v0.12.1 신설, dharness 측 단방향)** — `intent-profile-schema.md:§Advisor handoff 수신 시 변환 룰` 표 3 룰 적용:
   - `methodology: ["DDD", "TDD", ...]` → primary scalar(list[0] lowercase) + secondary list(나머지 lowercase) → `meta.advisor_secondary_methodologies`에 보존
   - `methodology_source: "methodology-advisor v0.3.1"` → enum `"advisor"`로 정규화 + 원본 → `meta.advisor_handoff_version` 박제
   - `methodology_matrix_row` → 그대로 (sigil 포함)
   - 카탈로그 외(`[catalog-miss]` sigil) → `methodology: unknown` + secondary에 원본 + `meta.open_questions`에 진화 단계 재합성 사유 박제
4. **intent_profile frontmatter merge** — 변환 후 `workflow` + `meta` 섹션 박제. `meta.user_confirmed_fields`에 `workflow.methodology` 등록 (사용자가 advisor 추천 confirm 게이트 통과한 경우만)
5. **grilling cap 카운트** — advisor 호출 1회 = grilling cap 5 question 중 **1 question** (token 비용 정합)

advisor 호출 미가능(plugin 미설치) 시 — fallback: enum 풀 노출 + 사용자 직접 선택 grilling 1q 진행. adapter step 3 skip.

## 4. Codebase Exploration Fallback (패턴 4)

사용자 응답 "코드 봐" / "모르겠음 — 코드 확인 가능?" 시:

1. 본 필드의 `references/project-inquiry.md §3` 매핑 룰 재조회
2. 매핑 가능 — 추론값으로 추천 갱신 후 재질문 (1회 한정, loop 방지)
3. 매핑 불가 (§3-3 "사용자 입력만 가능" 필드) — 사용자에게 "코드만으로는 결정 불가, 직접 답이 필요해요" 통지 후 재질문
4. loop 카운터 ≥2 도달 시 — §7 필수 재질문 룰 진입 또는 `meta.open_questions` 등록

## 5. Cap 룰 (token bloat 방지)

| 룰 | 값 |
|---|---|
| 단일 grilling 세션 최대 question 수 | **5** |
| 5 초과 시 자동 전환 | batch 표 (`§4-4`) |
| 단일 question 평균 토큰 (LLM 추천 + 응답) | 목표 ≤300 |
| 사용자 무응답 (5분 추정) | session 종료 — `meta.open_questions` 박제 후 batch fallback |

**5 cap 이유**: grilling × 7 섹션 × 평균 3 필드 = 21 질문 → 토큰 bloat. High confidence batch → Low confidence grilling 분리로 grilling 항목을 5 이내로 압축.

## 6. Skip Merge (§4-3 룰과 결합)

grilling 모드에서도 §4-3 스킵 패턴 유효:

| 사용자 응답 | grilling 동작 |
|---|---|
| "스킵" / "건너뛰기" / "다음" | 추천값 박제 + `meta.open_questions`에 "(grilling skip)" 등록 후 다음 question |
| "모르겠음" / "미정" | `user_confirmed_fields` 미등록 + 추천값 유지 (§4-4 룰과 동일) |
| "코드 봐" | 패턴 4 trigger (§4 참조) |
| "상관없음" | 추천값 박제 + `user_confirmed_fields` 등록 (사용자 의사 결정 위임) |
| (필수 5개 ★) 스킵 시도 | §7 필수 재질문 룰 진입 — grilling loop는 1차 재질문 직전 마지막 grilling 1회 후 §7 hard fail |

## 7. Phase별 진입점

| Phase | 진입 조건 | 종료 조건 |
|---|---|---|
| **P0.5** | `$ARGUMENTS` 4항목 검사 empty ≥1 | 모든 empty 항목 채움 또는 사용자 명시 거부 |
| **P2 brownfield 단계 2** | `meta.confidence_low` 항목 존재 | 모든 Low confidence 항목 `user_confirmed_fields` 또는 `open_questions` 등록 |
| **P2 brownfield 단계 3** | 갭 메우기 필드 ≥3 (`§3-3` 사용자 입력만 가능 필드) | 모든 갭 필드 채움 또는 §7 hard fail |
| **P2 §7-1 1차 재질문 직전** | 필수 5필드 미답 + 사용자 1차 거부 | 답변 수령 또는 §7-2 2차 재질문 진입 |
| **P2 workflow.methodology 분기** | 사용자 "모르겠음" / "추천해줘" 응답 (§3-4) | advisor handoff yaml merge 또는 enum 직접 선택 fallback |
| **P5 cardinality (옵션)** | 에이전트 후보 N개 중 `inline-OK` 판정 모호 1~2개 | 모호 후보 inline/agent 결정 |
| **`/harness-grill feedback`·`/harness-evolve` 호출 시 (옵션)** | 사용자가 명시 호출 + 피드백 어휘 모호 ("이상해" 등) | 진화 대상 (§9-2 표 5행) 1개 이상 식별. *자율 진입 없음 — 명시 호출만* (2026-05-30) |

각 Phase grilling 진입 시 본 reference §3 추천 룰 + §5 cap + §6 skip merge 그대로 적용.

## 8. 박제 산출물

grilling 진행 중 누적되는 메타:

```yaml
meta:
  grilling_log:                    # 옵션 필드, grilling 진입 시에만 박제
    - phase: "2"
      field: "constraints.team.size"
      mode: "grilling"
      recommended: "solo"
      user_response: "맞음"
      timestamp: "{ts}"
    - phase: "0.5"
      field: "output_target"
      mode: "grilling"
      recommended: "보고서"
      user_response: "수정 — 코드"
```

`intent-profile-schema.md`의 `meta.*` 확장 — 없으면 schema 검증 silent skip (필수 아님).

## 9. 검증 게이트

| 룰 | 검증 |
|---|---|
| grilling 진입 시 추천값 출처가 §3-1 직접 매핑 또는 `project_profile.md` signals ≥2 | 위반 시 doctrine 위반 (Phase 0.5 anti-premature-judgment) |
| 단일 grilling 세션 question 수 ≤5 | 위반 시 batch fallback 강제 |
| 사용자 응답이 "모르겠음" 연속 ≥3 — grilling 중단 | session 종료 + `open_questions` 박제 |
| 필수 5필드 grilling 중 hard fail (§7-3) 시 grilling 즉시 종료 | Phase 2 종료 게이트 진입 |

## 10. cross-reference

- 본 reference 트리거 조건 및 진입점: `SKILL.md` Phase 0.5 / Phase 2 entry 게이트 박스 + Phase 5 cardinality 게이트 박스 + `/harness:harness-grill`·`/harness:harness-evolve` 명시 호출 (Phase 9-1 자율 진입 제거, 2026-05-30)
- batch 패턴 본체: `project-inquiry.md` §4-4 (추론 결과 확인 패턴)
- skip 룰: `project-inquiry.md` §4-3
- 필수 재질문 룰: `project-inquiry.md` §7
- 검증 룰: `project-inquiry.md` §8 + `intent-profile-schema.md` §8

> **이유**: dharness 표 출력형 batch는 high-confidence 항목에 효율적이지만 low-confidence·자유 텍스트·필수 답안 거부 상황에서 사용자 인지 부담을 흡수하지 못한다. grilling 1q + LLM 추천 + skip merge로 답변 거부율 ↓, doctrine 박제 강도 ↑.
