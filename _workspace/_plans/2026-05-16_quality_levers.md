# Quality Lever Plan — 2026-05-16

dharness 산출물 품질 향상 계획. 외부 검토 2건(`referencefilesfordharness/1.md` 구조 변경안 + `referencefilesfordharness/2.md` 품질·철학 분석) + 자체 review 합성.

## 0. 전제 — 기능 무결성 한계

dharness 작동 무결을 *증명 불가*. 단 실측 박제 영역(58 tests / cycle 13~24차 empirical / dharness self-host 운영)은 신뢰 가능. 본 plan은 *합성 derived 산출물 품질 향상* — 내부 버그 fix와 분리.

## 1. 필수성 판정 — 16 lever 중 *진짜* 필수 = 0건

dharness 현 상태로 미션 충족(에이전트 팀 + 스킬 합성·진화). 16건 전부 *품질·선택* 영역. 미적용 시 합성 실패·진화 정지·데이터 손실 empirical evidence 0. CLAUDE.md "변경 이력" 표 2026-05-16 행 "잔여 사용자 결정 0건 → 완전 closure" 박제.

→ 사용자 의도(산출물 품질) 정합 lever 9건(Q1~Q9) + 자체 추가 5건(Q10~Q14) = 14 levers 검토.

## 2. Lever 분류 (산출물 품질 직접 영향)

| # | lever | 영향 산출물 | 출처 |
|---|---|---|---|
| Q1 | derived hook 합성 | hooks | 2.md #1 |
| Q2 | 모델 다단화 | agents | 2.md #2 |
| Q3 | CLAUDE.md HOW 본문 draft | CLAUDE.md | 2.md #3 |
| Q4 | Parts catalog YAML | agents/skills | 1.md #2 |
| Q5 | chain.py description overlap | skills | 자체 |
| Q6 | Composition trace | agents/CLAUDE.md | 1.md #3 |
| Q7 | 팀 fallback | orchestrator | 2.md #4 |
| Q8 | Slot 라이브러리 | 전체 | 1.md #1 |
| Q9 | Phase 0.5 결정적 검증 | 전체 | 자체 |
| Q10 | 에이전트 필수 섹션 검사 | agents | 자체 |
| Q11 | description signal coverage | skills | 자체 |
| Q12 | `tools:` ↔ `mcpServers:` 정합 | agents | 자체 |
| Q13 | derived 부트 가능성 검증 | 전체 | 자체 |
| Q14 | 트리거 매트릭스 자동 초안 | skills | 자체 |

내부 cleanup 6건(I1~I6: lock file / Phase 8 matrix / 임계값 자가 튜닝 / test count drift / `.harness-host` 결정적 차단 / README sync)는 *별도 cycle* — 산출물 영향 0.

## 3. 우선순위 Tier

### Tier A — 단일 사이클 (즉시 진행)

| 순위 | lever | 노력 | 변경 위치 |
|---|---|---|---|
| 1 | Q2 모델 다단화 | XS | `references/permission-profiles.md` §5-1 `recommended_model:` 컬럼 |
| 2 | Q3 CLAUDE.md HOW draft | S | `SKILL.md` Phase 7-4 + 신규 Phase 7-4.5, CM `_drafts/` 게이트 재사용 |
| 3 | Q10 에이전트 필수 섹션 검사 | XS | `validate/structure.py` `check_agent_required_sections()` |
| 4 | Q12 tools ↔ mcp 정합 | S | `validate/chain.py` `check_agent_tools_mcp_consistency()` |
| 5 | Q5 description overlap | S | `validate/chain.py` `check_skill_description_overlap()` |
| 6 | Q11 signal coverage | S | `validate/chain.py` `check_skill_signal_coverage()` |
| +  | tests | XS | `test_schema.py` 신규 case 4-6개 |
| +  | doctrine 박제 | XS | `CLAUDE.md` "변경 이력" 표 행 추가 |

의존: Q2/Q3/Q10 독립. Q12/Q5/Q11 chain.py 동시 patch.

### Tier B — 후속 사이클

| lever | 비고 |
|---|---|
| Q14 트리거 매트릭스 자동 초안 | scripts/gen_trigger_matrix.py 신규 |
| Q1 derived hook 합성 | parts-catalog hook-templates 포함 |
| Q4 Parts catalog YAML | references 추출 |
| Q7 팀 fallback | TeamCreate env empirical 1회 측정 후 확정 |

### Tier C — 장기/보류

| lever | 보류 사유 |
|---|---|
| Q6 Composition trace | Phase 5/6 sub-agent 회로 patch 동반 — 큰 변경 |
| Q9 Phase 0.5 결정적 검증 | LLM-trust doctrine 위반 empirical 0 |
| Q8 Slot 라이브러리 | 유지보수 부담 — derived 합성 분산이 실제 손해라는 evidence 누적 후 |
| Q13 derived 부트 가능성 검증 | 외부 binary 의존 |

## 4. Tier A 실행 절차

### 단계 1 — Q2 모델 다단화

`references/permission-profiles.md` §5-1 capability profile 표에 `recommended_model:` 컬럼 추가. mapping:
- `code-test` / `external-integration` / `review` → opus
- `read-only` / `explore` / `validation` → sonnet
- QA boundary check / synthesis / domain analysis → opus

`SKILL.md` Phase 5 모델 박제(L192) 갱신: "capability profile 매핑 따라 opus/sonnet 결정 — `permission-profiles.md` §5-1 참조".

### 단계 2 — Q3 CLAUDE.md HOW draft

`SKILL.md` Phase 7-4에 신규 sub-step 추가: Phase 1 `project_profile.md`에서 `stack`/`build_tools`/`key_directories`/`entry_points` 추출 → CLAUDE.md HOW 섹션 *draft* → `_workspace/_drafts/claudemd_how_{ts}.md`에 적재. 사용자 `/cm-claudemd-apply` 패턴 재사용(또는 별도 게이트).

`orchestrator-template.md`에 HOW draft 적용 예시 박제.

### 단계 3 — Q10 에이전트 필수 섹션 검사

`validate/structure.py`에 `check_agent_required_sections()` 추가. 검사 항목:
- 핵심 역할 / 작업 원칙 / 입력·출력 프로토콜 / 에러 핸들링 / 협업 5섹션
- 팀 모드 frontmatter `team_role:` 또는 본문 `## 팀 통신 프로토콜` 섹션

### 단계 4 — Q12 tools ↔ mcpServers 정합

`validate/chain.py`에 `check_agent_tools_mcp_consistency()` 추가. frontmatter `tools:` 리스트의 `mcp__<server>__<tool>` 패턴 항목 → `mcpServers:` 정의에 `<server>` 존재 검증.

### 단계 5 — Q5 description overlap

`validate/chain.py`에 `check_skill_description_overlap()` 추가. 모든 skill description trigger keyword 추출 → 쌍별 Jaccard 유사도 > 임계 시 보고.

### 단계 6 — Q11 signal coverage

`validate/chain.py`에 `check_skill_signal_coverage()` 추가. `trigger-keyword-catalog.md` 10 signal × Korean/English 매핑 load → skill description이 *최소 1 signal* hit하는지 검증.

### 단계 7 — tests

`test_schema.py` 또는 `plugins/harness/scripts/validate/test_*.py` 신규 case:
- Q10: 필수 섹션 누락 정의 → 오류 1건
- Q12: `tools:` 항목이 `mcpServers:` 미정의 → 오류 1건
- Q5: 중복 description → 오류 1건
- Q11: 모든 signal miss → 오류 1건

### 단계 8 — doctrine 박제

`CLAUDE.md` 변경 이력 표 행 추가: "2026-05-16 Tier A 6 lever 적용 — 산출물 품질 향상". 사유 자유.

## 5. 결정 기록

- 사용자 선택: **Tier A** (2026-05-16)
- empirical 트리거 발생 전 Tier B/C 미진입.
- Tier A 적용 후 derived 합성 1회 실행 → 신규 검증 회로 동작 박제 → Tier B 진입 판정.

### 5-1. Tier A 실행 결과 (2026-05-16)

- **Q10 drop** — structure.py L32-39 `AGENT_REQUIRED_SECTIONS` 6패턴 기 박제 (`핵심 역할` / `작업 원칙` / `입력·출력` / `에러 핸들링` / `협업` / `팀 통신`) + L81-83 enforcement. redundant → Tier A에서 제외.
- **Q2 적용** — `references/permission-profiles.md` §5-1-c 신규 (model selection by agent role 매트릭스 + profile × role 매트릭스). `SKILL.md` Phase 5 model 박제 갱신 — `opus` 일괄 강제 폐기, role 축 매핑으로.
- **Q12 적용** — `chain.py:check_agent_tools_mcp_consistency()` — frontmatter `tools:` mcp__ 참조 ↔ `mcpServers:` 정의 정합 검사.
- **Q5 적용** — `chain.py:check_skill_description_overlap()` — pairwise Jaccard ≥ 0.5 트리거 충돌 검출.
- **Q11 적용** — `chain.py:check_skill_signal_coverage()` — trigger-keyword-catalog 10 signal 중 최소 1 hit 강제. `_TRIGGER_SIGNAL_KEYWORDS` dict 박제 (catalog ↔ 코드 sync 필요).
- **Q3 적용** — `SKILL.md` Phase 7-4.5 신규 — `project_profile.md`에서 stack/build/key_directories/commands/entry_points 추출 → `_workspace/_drafts/claudemd_how_{ts}.md` draft → 사용자 게이트.
- **추가 (Q2 보강)** — `chain.py:check_agent_model_field()` — frontmatter `model:` 필드 누락 검출.
- **테스트** — `scripts/validate/test_chain.py` 신규 (15 tests, 외부 의존 0, 임시 dir + module monkey-patch).
- **회귀** — self-host chain.py PASS (memory-search description signal hit 검증), test_schema 58/58 유지.
- **부수 fix** — `_schema.py` migration ALTER TABLE DROP COLUMN silent swallow 2건 → stderr 로그 (별도 task, 본 plan 외).

## 6. 출처 박제

- `referencefilesfordharness/1.md` — 외부 검토자 의견 (구조 변경안 5종)
- `referencefilesfordharness/2.md` — 외부 검토자 의견 (품질·철학 분석 + 우선 보완 5종)
- 본 conversation — 필수성 판정 + Tier 분류 + 사용자 결정
