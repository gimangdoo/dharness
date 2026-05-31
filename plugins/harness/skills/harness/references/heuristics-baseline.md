# Heuristics Baseline — 휴리스틱 임계값 통합 catalog

> **Read at phase:** lazy load. Phase 1·5-2·6·8·10 휴리스틱 임계값 baseline 단일 출처. 4 doc (`code-research.md` / `mcp-recommendation.md` / `runtime-adaptation.md` / `skill-testing-guide.md`)가 본 doc을 가리킨다.

본 catalog는 *baseline* — domain별 telemetry / 코드베이스 크기 / jargon 충돌 빈도에 맞춰 조정 권장. 임계값 변경 시 *원 doc 본문*은 변경하지 않고 본 표 행을 갱신한다. 도메인별 override는 `_baseline/intent_profile.md`의 `tuning_overrides` 또는 derived 프로젝트의 `_baseline/heuristic_overrides.md`에 박제.

원문 P2-4 — 2026-05-14 도입. PB2 — 2026-05-27 4 doc 표 1 파일로 통합.

---

## 목차

1. [Phase 1 — Code Research](#1-phase-1--code-research)
2. [Phase 5-2 — MCP Recommendation](#2-phase-5-2--mcp-recommendation)
3. [Phase 10 — Runtime Adaptation](#3-phase-10--runtime-adaptation)
4. [Phase 6·8 — Skill Testing](#4-phase-68--skill-testing)
5. [tuning override 규약](#5-tuning-override-규약)

---

## 1. Phase 1 — Code Research

원 doc: [`code-research.md`](code-research.md). Phase 1 분석 임계값은 *측정 분포 기반*. 코드베이스 크기에 따라 조정.

| 임계 | default | 근거 | tuning 권장 |
|---|---|---|---|
| quick vs deep 분기 키워드 (§5) | "간단/빠르게/quick/대략" → quick / "전체/깊이/자세히/deep" → deep | 휴리스틱 — 사용자 발화 키워드 매칭 | 명시 키워드 없으면 default quick. 코드베이스 >50k LOC면 deep 권장 |
| 핫스팟 churn 비율 (§9-1) | 5% 이상 | 휴리스틱 — long-tail 분포 cutoff | mature 코드베이스(>3 year)에선 3% 더 엄격 |
| 핫스팟 절대 변경 횟수 (§9-1) | 10회 이상 | 휴리스틱 — period_days=30 가정 | period_days=90이면 25회로 비례 확장 |
| churn 측정 period_days (§9-1) | 30일 | 휴리스틱 — release cycle 평균 | 큰 프로젝트(>1000 파일)는 90일 / fast-iteration startup은 14일 |
| 큰 프로젝트 기준 (§9-1) | >1000 파일 | 휴리스틱 — git log noise 누적 | monorepo는 >5000 / single-package는 >500 |
| 95-percentile outlier (§9) | percentile=95 | 측정 분포 기반 (heavy-tail 가정) | normal 추정 도메인은 99-percentile / strict는 90-percentile |
| 새 디렉토리 신호 (cross — `runtime-adaptation.md §5-5`) | 50+ files | 휴리스틱 — module 신설 단위 | 소규모(<10k LOC) 20+, monorepo 100+ |

override 박제 위치: `_baseline/project_profile.md`의 `analysis_overrides` 필드.

---

## 2. Phase 5-2 — MCP Recommendation

원 doc: [`mcp-recommendation.md`](mcp-recommendation.md). Phase 5-2 MCP 후보 점수 임계값. *deterministic* 아닌 휴리스틱. 도메인별 조정 권장.

| 임계 | default | 근거 | tuning 권장 |
|---|---|---|---|
| tier_weight R0 / R1 / R2 (mcp §2) | 1.0 / 0.7 / 0.4 | 휴리스틱 — verified 우선 + 외부 trust 단계적 감쇠 | R1 trust 강한 도메인(`anthropic/modelcontextprotocol` 사용 비중 ↑)에선 R1=0.85 권장 |
| E 도구 카운트 (mcp §3-1) ≤5 +2 / 6~15 +1 / 16+ 0 | — | 휴리스틱 — Claude Code deferred pool 적재 비례 비용 | 도메인 sub-grep으로 도구 5~10종 sweet spot. 16+는 toolset 필터로 분할 권장 |
| E 부수 효과 비중 (mcp §3-1) ≤30% +2 | — | 휴리스틱 — read-only 비중 70%+면 strict mode 가용 | 보안·규제 도메인에선 ≤20%로 더 엄격 |
| E lazy 다운로드 ≥50MB -2 (mcp §3-1) | — | 측정 (playwright Chromium ~120MB 22차 사이클) | 모바일 dev 도메인에선 패널티 -3 (디스크 제약) |
| S toolset enum ≥3 +2 (mcp §3-2) | — | 휴리스틱 (github 19 toolset / playwright 7 caps 사례) | toolset 미지원 MCP는 enum=1 fixed |
| A 신호 매칭 ≥2 +2 (mcp §3-3) | — | 휴리스틱 — 단일 신호 매칭은 false-positive 위험 | 모호 도메인(ML+data, mobile+web)에선 ≥3으로 강화 |
| A `verification_status` 페널티 (mcp §3-3) | ✓ +4 / 📜 -2 / ⚠️ -4 | mcp §3-0 status enum cross-mapping (P6-9) | spoof 우려 도메인(외부 npm 의존)에선 📜 -3로 강화 |
| wE / wS / wA default (mcp §3-4) | 0.4 / 0.3 / 0.3 | 휴리스틱 — Phase 5-2 합성 시점 효율 우선 | 보안·규제: wA=0.5 / 비용 민감(`budget_constrained`): wE=0.5 — `--weights=` 명시 override |
| top-K (mcp §4) | K=3 | 휴리스틱 — confirm gate 정보 과부하 방지 | 후보 풀 ≥10 도메인에선 K=5 권장 |
| 대안 후보 점수 차이 ≤1.0 | — | 휴리스틱 — clamp [0,10] 1점 차이 = 10% 갭 | tie-breaking 엄격 도메인에선 ≤0.5 |
| 거부 학습 ≥2회 → -2 페널티 (mcp §8) | — | 휴리스틱 — 1회 거부는 noise 가능 | derived 프로젝트 telemetry 누적 시 ≥3회로 보수적 운영 |

override 박제 위치: `--weights=` CLI override / 도메인 self-critique (Phase 5.5).

---

## 3. Phase 10 — Runtime Adaptation

원 doc: [`runtime-adaptation.md`](runtime-adaptation.md). Phase 10 telemetry drift 임계값. *empirical 측정 아닌* 휴리스틱. 도메인별 telemetry 누적 후 조정.

| 임계 | default | 근거 | tuning 권장 |
|---|---|---|---|
| drift 보고 건수/세션 (ra §7-7) | 5건 | 휴리스틱 — confirm gate 과부하 방지 | telemetry 신호 풍부 도메인(data eng / ML)에서 7~10건 |
| new_dependency minor / major (ra §5-5) | 1개 / ≥3개 | 휴리스틱 — 단일 추가는 기능 단위, 다중은 stack 변경 | 모노레포·monorepo lock 도메인에선 minor=2개, major=≥5개 |
| session 시작 project_signal 스캔 (ra §4-3) | ≤2초 | 측정 목표 (대화 응답성 보존) | 큰 monorepo (>100k LOC)에선 ≤5초 허용 |
| 이전 세션 캐시 재사용 (ra §4-3) | 7일 | 휴리스틱 — 일주일 cadence가 dependency drift 평균 주기 | 변동 큰 도메인(early-stage startup)에선 3일 / stable 도메인(LTS)에선 14일 |
| 새 디렉토리 신호 (ra §5-5) | 50+ files | 휴리스틱 — module 신설 단위 | 소규모 도메인에선 20+, monorepo에선 100+ |
| 커버리지 drift 신호 (ra §5-5) | ±15pp | 휴리스틱 — measurement noise 초과 변동 | 강한 quality gate 도메인에선 ±10pp / loose 도메인에선 ±20pp |
| confidence 자동 적용 (ra §8) | high + user_confirmed | 휴리스틱 — silent fail 방지 | 회귀 telemetry 누적 풍부 시 high 단독으로 완화 |
| 핫스팟 임계 (cross — `code-research-deep.md §2-1`) | 5% churn 또는 10회 변경 | 휴리스틱 — long-tail 분포 cutoff | mature 코드베이스에선 3% + 20회 (변동 가속) |
| 핫스팟 outlier (cross — `code-research-deep.md §2-5`) | 95-percentile | 측정 분포 기반 (heavy-tail 가정) | normal 분포 추정 도메인에선 99-percentile |

override 박제 위치: `_baseline/intent_profile.md`의 `tuning_overrides` 필드.

---

## 4. Phase 6·8 — Skill Testing

원 doc: [`skill-testing-guide.md`](skill-testing-guide.md). Phase 6·8 스킬 트리거 회귀 임계값. *경험치 기반* 휴리스틱. 도메인 복잡도에 따라 조정.

| 임계 | default | 근거 | tuning 권장 |
|---|---|---|---|
| 초기 테스트 프롬프트 개수 (st §2) | 2~3개 | 휴리스틱 — 핵심 + 엣지 + (선택) 복합 최소 커버 | 복잡 도메인(ML / 도메인 specific DSL)에선 5~7개 |
| 테스트 프롬프트 커버 카테고리 (st §2) | 핵심 사용 사례 / 엣지 / 복합 (선택) | 휴리스틱 — 흔한 실패 mode 분리 | 안전·규제 도메인에선 *부정 케이스* 추가 (잘못된 입력 거부 검증) |
| trigger 회귀 eval 쿼리 (st §7) | 20개 (should-trigger 10 + should-NOT 10) | 휴리스틱 — `8~10`은 floor, `10+10`은 도메인 모호도 흡수 | 단순 도메인 (CRUD) 8+8 / 모호 도메인 (ML "모델" 혼동) 15+15 |
| should-trigger / should-NOT 비율 (st §7) | 1:1 (10:10) | 휴리스틱 — false-positive ↔ false-negative 대칭 | recall 우선 도메인 (보안 검출) 12:8 / precision 우선 (cost-sensitive) 8:12 |
| Train/Test split (st §7) | 60% / 40% | 휴리스틱 — Train 12개로 description 튜닝 + Test 8개로 회귀 | 쿼리 ≥30개면 70/30 — 통계적 안정성 ↑ |
| near-miss 비율 (st §7) | should-NOT 쪽 다수 배치 | 휴리스틱 — 경계 모호함이 trigger 정확도 핵심 | 도메인 jargon 충돌 多 (ML "모델"/도메인 modeling)에선 ≥50% near-miss |
| trigger 정확도 floor (st §7) | 8개 미만 → 보장 불가 | 휴리스틱 — 변동성 누적 floor | 8개는 절대 floor, 10개 default 권장 |

override 박제 위치: `_baseline/intent_profile.md`의 `quality.test_rigor` 필드와 동기 갱신.

---

## 5. tuning override 규약

도메인별 임계값 override는 두 경로 중 하나:

1. **본 catalog 갱신** — 본 doc의 default 컬럼은 *모든 도메인 공통 baseline*. 변경하려면 별도 PR + 변경 이력 박제. 무분별한 default 변경 금지.
2. **derived 박제** — 특정 derived 프로젝트가 자체 임계값을 사용할 때 `_baseline/heuristic_overrides.md` 신설 + `_baseline/intent_profile.md`의 `tuning_overrides` 필드에 cross-ref. 본 catalog는 변경하지 않는다.

override 식별 표는 derived 측 `heuristic_overrides.md`에서 본 catalog 행 단위로 차이만 표기:

```markdown
| catalog 행 | default | override | 사유 |
|---|---|---|---|
| 핫스팟 churn 비율 | 5% | 3% | mature 코드베이스(>5 year) |
| top-K | 3 | 5 | MCP 후보 풀 12개 — 정보 다양성 우선 |
```

override 미동기화 (catalog default 갱신됨에도 derived override 미갱신) drift는 Phase 10 baseline drift로 surface.
