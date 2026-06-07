> **Read at phase:** Phase 6/7 (reusable skill 합성 — wiki Emit 판단 시) + Phase 5 설계 진입(promoted candidate 재사용 판단 시). self-host opt-in — 평시·외부 install 시 read 불요.

# Wiki Bridge — harness ↔ wiki 양방향 다리 doctrine

dharness가 합성한 reusable skill을 로컬 "harness" wiki의 평가 파이프라인에 태워 검증·승격하고(Emit), wiki의 승격 결과를 다음 합성에 재사용하는(Feedback) 양방향 다리. **dharness self-host 한정 인프라** — Context Manager처럼 dharness 본 폴더 + 사용자 로컬 wiki monorepo 사이에서만 작동. 외부 install 파생 하네스는 wiki 위치를 모르므로 본 다리 미적용.

## §0. 경계 — presence-gated, self-host only

| 레이어 | 주체 | 시점 | 산출 |
|---|---|---|---|
| dharness (빌드타임 팩토리) | `harness` 스킬 | reusable skill 합성 시 | candidate 디렉토리 (M1 Emit) |
| wiki (평가 파이프라인) | `wiki-harness` 오케스트레이터 | `candidates/` ingest | Static/LLM-Judge/MonteCarlo tier + promotion (별도 wiki repo, Phase A/B 완료) |
| dharness (재사용) | `harness` 스킬 | 다음 합성 설계 시 | promoted candidate 재사용 (M4 Feedback) |

**presence gate:** 로컬 wiki `<wiki>/harness/candidates/` 타겟이 **존재할 때만** 다리 작동. 부재 시 silent no-op — Emit/Feedback 생략, 합성 정상 진행. wiki 측 contract는 `<wiki>/harness/candidates/README.md` 단일 출처이며 본 doctrine은 dharness 측 단방향 정합(wiki 출력 형식 변경 0).

**observability (P5 강제):** silent no-op은 추적 신호가 0이라 "wiki 미설정" vs "설정됐으나 skip"을 운영자가 구분 못 한다. self-host 실행 경로(`bridge.py`)는 게이트 미작동·dedup·성공/실패 시 telemetry(`_workspace/_telemetry/`)를 **자동 박제**한다 — `wiki_bridge_skipped {milestone: emit|pull, reason: target-absent|not-reusable|dedup-hit}` · `wiki_bridge_emit {slug, outcome}` · `wiki_bridge_pull {n_promoted}` (runtime-telemetry.md §2 정본). M1 Emit·M4 Feedback skip 사유는 `milestone`으로 분리. 권장→강제 격상(2026-06-03). derived 하네스는 telemetry 채널 보유 시 동형 로깅 권장.

**Layering invariant:** M1 Emit(SKILL Phase 7-7 trigger)·M5 gate(fixture-anchored)는 doctrine+fixture template의 *결정적 정합 검증*일 뿐 실제 wiki `candidates/` write가 아니다. 실 candidate 박제는 derived 런타임 post-synthesis + 사용자 gate 1회. wiki-bridge는 active dharness phase가 아니라 doctrine+fixture 정의 — runtime-execution.md의 marker 위치·게이트 구조가 바뀌어도 본 contract는 Phase 7 공유 컨텍스트만 참조하며 서로의 내부 구조에 의존하지 않는다.

## §1. M1 Emit — dharness → wiki `candidates/`

reusable skill을 합성했고 wiki candidates/ 타겟이 존재하면, `candidates/<kebab-slug>-v<N>/` 디렉토리에 3 파일을 박제한다. **canonical 예시: `fixtures/wiki_candidate_example/`** (M5 gate가 검증하는 정본 형태).

**(a) `SKILL.md`** — Anthropic skill convention frontmatter + 본문. 필수 frontmatter:

```yaml
name: <kebab-case slug>
description: <50-200자, 트리거 ≥3, 부정 예시 ≥1>
meta:
  skill_kind: user-facing          # candidate 기본 (internal-capability 금지 — wiki rule 3-a)
  candidate_version: <N>           # 정수
  gap_source: gap-detection | pattern-synthesis | external-adoption
  static_tier: PASS | WARN | FAIL | not-run
  llm_judge_tier: PASS | FAIL | not-run
  mc_tier: PASS | FAIL | not-run
  promoted_to: null | ".claude/skills/<name>/"
```

**(b) `eval-results.json`** — tier 누적 결과. shape: `candidate_slug`(str) · `candidate_version`(int) · `gap_source`(str) · `emit_at`(ISO8601, 권장) · `evals.{static,llm_judge,monte_carlo}`(각 `status`/`last_run` 보유) · `promotion.{verdict,promoted_to,promoted_at}`. Emit 시점은 전 tier `status: not-run`(또는 dharness 측 Static 선검증분 PASS) + `promotion.verdict: null`. `emit_at`은 M4 Feedback이 tier staleness(예: Static `last_run` > 90일)를 진단하는 기준 — M5 gate는 미강제(권장 필드).

**(c) `changelog.md`** — append-only 표(일자/event/본문), 첫 행 `emit` event.

**Emit trigger (self-host):** dharness가 *재사용 가치 있는* skill을 합성했을 때(특정 프로젝트 전용이 아닌 범용 패턴) + wiki candidates/ 존재 + 사용자 gate 1회. 특정 프로젝트 1회용 skill은 Emit 금지(wiki rule 2-a 75% 중복·inflation guard 정합).

**실행 (P5, self-host 전용):** gate 통과 후 3파일 write·dedup·자가검증·telemetry는 산문 수기 대신 `scripts/wiki/bridge.py:emit_candidate`가 수행한다(기계적 I/O). 콘텐츠(SKILL 본문·eval shape)는 LLM이 저작해 인자로 넘기고, 헬퍼는 (1) presence-gate (2) dedup advisory soft-block(`_dedup_check` → `{overlap, conflict}`, 임계 `_DEDUP_THRESHOLD`=wiki rule 2-a 상속) (3) `<slug>-v<N>/` 멱등 write (4) `_validate_candidate_dir` 자가검증 FAIL 시 롤백(wiki 미오염) (5) `wiki_bridge_emit`/`wiki_bridge_skipped` telemetry 박제. dedup hit은 **hard-block 아님** — 헬퍼가 soft_block 반환 시 LLM이 사용자에 재확인.

## §2. M4 Feedback — wiki → dharness 재사용

다음 합성 설계(Phase 5) 진입 시 wiki `candidates/`에서 **promoted candidate**를 조회해, 재합성 대신 재사용을 우선한다. (조회원은 `candidates/*/eval-results.json`의 promotion 박제 단일 — `pages/tools/`는 wiki 측 승격-후 hoist 위치이지 dharness pull source 아님. `bridge.py:pull_promoted` 정합.)

- **pull 대상:** `candidates/<name>/eval-results.json`의 `promotion.verdict` + `evals.*.status`, 그리고 `meta.promoted_to`(`.claude/skills/<name>/` 승격분).
- **tier 의미:** Static=구조 PASS / LLM-Judge=adversarial eval PASS / MonteCarlo=trigger F1 ≥ champion. **3 tier 전부 PASS + `promotion.verdict` 박제** 시에만 "검증된 재사용 후보".
- **재사용 분기:** 합성하려는 skill이 promoted candidate와 의미 중복(트리거·목적) 시 → 재합성 대신 해당 candidate 재사용(또는 description 확장). 미승격(tier 미통과)분은 참고만, 재사용 강제 아님.

**실행 (P5, self-host 전용):** promoted 조회는 `scripts/wiki/bridge.py:pull_promoted`가 수행한다 — `candidates/*/eval-results.json` glob → **3 tier 전부 `status: PASS` + `promotion.verdict` 박제**분만 `[{slug, version, promoted_to, verdict}]`로 반환 + `wiki_bridge_pull {n_promoted}` telemetry, presence-gate 부재 시 `[]` + skip. 재사용 판단(의미중복 → 재사용 제안)·사용자 confirm은 LLM 레이어 — 헬퍼는 read-only 조회만(자동 graft 0).

## §3. M5 Schema gate (deterministic, `chain.py:check_wiki_candidate_schema`, S18)

push/pull contract 정합을 결정적으로 강제한다. **fixture-anchored** — `fixtures/wiki_candidate_example/`(canonical M1 산출물)를 검증한다. 실제 Emit candidate도 동일 gate를 통과해야 한다.

검증 항목:

1. candidate 디렉토리에 `SKILL.md` + `eval-results.json` + `changelog.md` 3 파일 존재.
2. `SKILL.md` frontmatter 필수 필드(§1-a) 전부 박제 + `meta.skill_kind != internal-capability` + `candidate_version` 정수.
3. `eval-results.json` 유효 JSON + 필수 키(§1-b) + `candidate_version` 정수 + `evals.{static,llm_judge,monte_carlo}` 3 키 존재.
4. `SKILL.md` `meta.candidate_version` == `eval-results.json` `candidate_version` (cross-field 정합).

fixture 부재 시 silent skip(presence-gated — 외부 install repo·fixture 미동봉 환경 무관).

## §4. 안전·정합

- **wiki 쓰기 = outward-facing.** 실제 candidates/ 박제는 사용자 gate 1회 후만. 본 doctrine·gate·fixture는 wiki repo를 변경하지 않는다.
- **per-wiki standalone 존중** — wiki 간 cross-link 금지(wiki schema doctrine). dharness는 "harness" 도메인 wiki만 대상.
- **raw immutable** — wiki `raw/` 미변경. Emit은 `candidates/`에만.
- **inflation guard** — 75% 중복 candidate Emit 금지, 30일 0-call archive는 wiki 측 enforcement(`§3` rule 2). dharness는 Emit 전 중복 1회 자가 점검.

## §5. cross-reference

- wiki 측 contract 단일 출처: `<wiki>/harness/candidates/README.md` + `_reference/WIKI-SCHEMA.md §7`(eval tier)·`§9.3`(gap)·`§11 rule 2`(inflation).
- canonical fixture: `fixtures/wiki_candidate_example/` (M5 gate 검증 대상).
- 결정적 검증: `chain.py:check_wiki_candidate_schema` (S18, doctrine-registry §3).
- 관련 plan: `RUNTIME-FEATURES-PLAN.md` P4.
