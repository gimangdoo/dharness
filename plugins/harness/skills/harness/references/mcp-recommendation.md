# MCP Recommendation — 합성 시점 자동 추천 엔진

> **Read at phase:** Phase 5-2 (MCP·도구 자동 할당). 10 signal (S1~S10) 추출 + 3축 점수 + 후보 풀 cascade. permission-profiles.md와 동반 read.

> **Cross-doc 인용 규약 (M3 단일 출처 — 2026-05-14):** 본 문서의 bare `§N`은 `permission-profiles.md §N`을 가리킨다 (본 doc은 permission-profiles의 §3·§3-1·§4·§10에 *합성 매핑·채택 절차*를 위임하기 때문에 cross-doc 비중 우세). 본 문서 *자체* 섹션 자기 인용은 `본 §1`·`본 §3` 형식으로 명시 또는 *섹션 헤더 인근*에서만 bare 사용. 예외(다른 doc 참조)는 인라인 명시.

> **휴리스틱 임계값 catalog + tuning 가이드 (P2-4 — 2026-05-14):** 본 doc의 임계값은 *deterministic* 아닌 휴리스틱. 도메인별 조정 권장.
>
> | 임계 | default | 근거 | tuning 권장 |
> |---|---|---|---|
> | tier_weight R0 / R1 / R2 (본 §2) | 1.0 / 0.7 / 0.4 | 휴리스틱 — verified 우선 + 외부 trust 단계적 감쇠 | R1 trust 강한 도메인(`anthropic/modelcontextprotocol` 사용 비중 ↑)에선 R1=0.85 권장 |
> | E 도구 카운트 (§3-1) ≤5 +2 / 6~15 +1 / 16+ 0 | — | 휴리스틱 — Claude Code deferred pool 적재 비례 비용 | 도메인 sub-grep으로 도구 5~10종 sweet spot. 16+는 toolset 필터로 분할 권장 |
> | E 부수 효과 비중 (§3-1) ≤30% +2 | — | 휴리스틱 — read-only 비중 70%+면 strict mode 가용 | 보안·규제 도메인에선 ≤20%로 더 엄격 |
> | E lazy 다운로드 ≥50MB -2 (§3-1) | — | 측정 (playwright Chromium ~120MB 22차 사이클) | 모바일 dev 도메인에선 패널티 -3 (디스크 제약) |
> | S toolset enum ≥3 +2 (§3-2) | — | 휴리스틱 (github 19 toolset / playwright 7 caps 사례) | toolset 미지원 MCP는 enum=1 fixed |
> | A 신호 매칭 ≥2 +2 (§3-3) | — | 휴리스틱 — 단일 신호 매칭은 false-positive 위험 | 모호 도메인(ML+data, mobile+web)에선 ≥3으로 강화 |
> | A `verification_status` 페널티 (§3-3) | ✓ +4 / 📜 -2 / ⚠️ -4 | §3-0 status enum cross-mapping (P6-9) | spoof 우려 도메인(외부 npm 의존)에선 📜 -3로 강화 |
> | wE / wS / wA default (§3-4) | 0.4 / 0.3 / 0.3 | 휴리스틱 — Phase 5-2 합성 시점 효율 우선 | 보안·규제: wA=0.5 / 비용 민감(`budget_constrained`): wE=0.5 — `--weights=` 명시 override |
> | top-K (§4) | K=3 | 휴리스틱 — confirm gate 정보 과부하 방지 | 후보 풀 ≥10 도메인에선 K=5 권장 |
> | 대안 후보 점수 차이 ≤1.0 | — | 휴리스틱 — clamp [0,10] 1점 차이 = 10% 갭 | tie-breaking 엄격 도메인에선 ≤0.5 |
> | 거부 학습 ≥2회 → -2 페널티 (§8) | — | 휴리스틱 — 1회 거부는 noise 가능 | derived 프로젝트 telemetry 누적 시 ≥3회로 보수적 운영 |
>
> 본 표는 *baseline* — `--weights=` / 도메인 self-critique (Phase 5.5)에서 override 가능. 임계값 변경 시 본 박스 행 갱신 권장.

Phase 5-2 합성 *직전* 각 에이전트에 대해 "효율성·확장성·정확도" 3축으로 MCP 후보를 검색·점수화·추천한다. 본 문서는 추천 엔진의 단일 출처 — Phase 5-2와 `/harness:harness-mcp-recommend`가 본 문서를 참조한다.

> **분계 (중복 방지):**
> - **합성 매핑**(profile → 후보) = `permission-profiles.md` §4 결정 트리
> - **채택 절차**(install → reflect) = `permission-profiles.md` §10 5-step + `/harness:harness-mcp-adopt`
> - **현황 진단**(read-only) = `/harness:harness-mcp-status`
> - **본 문서**(추천 점수·외부 검색) = Discover 강화 + 3축 점수화
>
> 추천은 *제안*만. 채택은 §10이, 매핑은 §4가 처리.

---

## 1. 입력 — 에이전트 description 신호 추출

Phase 5-2가 합성하는 에이전트 `.md` frontmatter `description:` + 본문 "핵심 역할" 섹션을 입력으로 받는다. LLM이 다음 **10 신호** (2026-05-14 P6-11 확장 — 기존 6 + 도메인 4)를 *추출*만 (강제 분류 X — 다중 매칭 허용).

### 1-1. 범용 6 신호 (4 capability profile 매핑)

| 신호 | 키워드 예시 | 매핑 후보 카테고리 |
|------|------------|------------------|
| **S1 read-heavy** | "분석/검토/리서치/요약/조회/검색" | research / reasoning-aux |
| **S2 write-heavy** | "생성/편집/커밋/마이그레이션/배포" | code-test / external-integration |
| **S3 web-egress** | "웹/외부 API/스크래핑/검색 엔진" | research |
| **S4 db-egress** | "DB/쿼리/스키마/마이그레이션" | external-integration |
| **S5 ci/git** | "PR/issue/리뷰/CI/릴리즈" | code-test / external-integration |
| **S6 reasoning-aux** | "단계별/추론/장기 메모리/시간/타임존" | reasoning-aux |

### 1-2. 도메인 4 신호 (2026-05-14 신설 — capability profile §2-5~§2-8 매핑)

| 신호 | 키워드 예시 | 매핑 capability profile | 합성 권고 (§3-1 매트릭스 행) |
|------|-----------|------------------------|-------------------------|
| **S7 ml-aux** | "모델/학습/평가/하이퍼파라미터/실험 추적/inference/feature/dataset" | `ml-pipeline` | `filesystem` + `sqlite` + `memory` + `sequential-thinking` + `git` (T0 5종 cross-mapping) — 전용 huggingface/wandb MCP는 §10 진입 후 |
| **S8 infra** | "배포/CI/CD/인프라/모니터링/Kubernetes/Terraform/SRE/oncall/롤백" | `devops-infra` | `git` + `filesystem` + `time` + `sequential-thinking` (T0 4종). 변경 명령은 `Bash` 빌트인 + 패턴 매칭 `ask`. kubernetes/terraform/aws/datadog MCP는 §10 진입 후 |
| **S9 mobile** | "iOS/Android/Swift/Kotlin/Flutter/React Native/Xcode/Gradle/emulator/build" | `mobile-native` | `filesystem` + `git` + `sequential-thinking` (T0 3종) + `playwright`(`--browser=webkit`)·`chrome-devtools` (T1, derived 프로젝트별). Appium/Xcode MCP는 §10 진입 후 |
| **S10 data-eng** | "ETL/ELT/data pipeline/Airflow/dbt/Spark/data warehouse/data lake/ingestion/lineage" | `data-eng` | `sqlite` + `filesystem` + `git` + `memory` + `sequential-thinking` (T0 5종). `postgres`는 T2~ — `read_query` only 강제 권장. snowflake/bigquery/databricks/dbt MCP는 §10 진입 후 |

**복합 매핑 허용** — 1 에이전트가 S1+S3+S6 (전형: web-researcher) 또는 S2+S5+S7 (전형: ml-experiment-pr-author) 동시 매칭 가능. 매칭된 신호 집합 → §3 후보 풀 검색 키.

> **키워드 단일 출처**: 본 §1 표는 *signal → profile 매핑 룰* 박제. *키워드 catalog* (Korean·English 양 언어 + should/NOT 예시 + 복합 매칭 패턴 + 확장 doctrine) 단일 출처는 `trigger-keyword-catalog.md` (P6-8, 2026-05-14). LLM이 description 작성 또는 signal 추출 시 본 §1과 동반 read.

> **도메인 4 신호 doctrine (2026-05-14 P6-11):**
> - S7~S10은 *전용 MCP가 PoC 미완*인 경우가 대부분 → 합성 default는 *T0 5종 cross-mapping*. §3 점수에서 `A` (정확도) `-2 docs only` 페널티 자동 적용
> - 시그널 단어 매칭만으로 *전용 MCP 자동 합성 X* — §10 dynamic adoption 진입을 사용자에게 R-7 confirm 단계에서 *제안*만
> - S7~S10 중 *2개 이상* 동시 매칭 시 (예: S7+S10 = ML data eng) **에이전트 책임 *과대* 의심** — Phase 5.5 self-critique에서 `harness-split` 권고 후보 (SKILL.md §Phase 5.5)

---

## 2. 후보 풀 — 3-tier 소스

### Tier R0: §3 인벤토리 (verified)

`permission-profiles.md` §3 + §3-1 매트릭스 — probe 완료 + 도구 enumeration 박제됨. **default 1차 출처.** 점수 가중 ×1.0.

> **R0 필터 (P6-9 — 2026-05-14):** R0 후보 풀은 `permission-profiles.md §3-0` `verification_status = probe-verified` (✓ symbol)만 포함. `docs-only` (📜) 행은 R1로 강등 — `pending` (⚠️) 행은 후보 풀 제외 (§10 dynamic adoption 진입 안내만).

### Tier R1: 공식 reference

`github.com/modelcontextprotocol/servers` — anthropic/modelcontextprotocol 메인 카탈로그. probe 미완이지만 출처 trust ✓. 점수 가중 ×0.7. WebFetch로 README index 1회 조회 후 후보 발췌.

### Tier R2: 외부 큐레이션

- `awesome-mcp-servers` 또는 동급 큐레이션 (사용자 발화로 trust 받은 출처만)
- npm 레지스트리 `mcp-server-*` / `@*/mcp-*` 검색 (WebSearch)
- 점수 가중 ×0.4. *반드시* §10 Step 2 probe 통과 후 점수 산정 — 미probe 후보는 결과 표기 시 "📜 docs only" 라벨.

> **출처 위계 강제:** R0 매칭이 있으면 R1·R2 검색은 생략 가능 (효율). R0 미매칭일 때만 R1 → R2 cascade. 사용자가 명시적으로 "최신 후보까지" 요청하면 cascade 전부 실행.

---

## 3. 점수화 — 3축 (0~10)

각 후보 MCP × 에이전트 페어에 대해 산출:

### 3-1. 효율성 (Efficiency) — `E`

토큰·spawn·deferred-pool 비용 관점. 높을수록 비용 효율 좋음.

| 항목 | 점수 |
|------|------|
| Layer A toolset 필터 지원 (`--toolsets`/env) | +3 |
| 도구 카운트 ≤5 | +2 / 6~15 | +1 / 16+ | 0 |
| 부수 효과 도구 비중 ≤30% (read-only 우세) | +2 |
| inline 패턴(`mcpServers:` Layer B) 호환 — stdio/http/sse/ws | +2 |
| spawn 시 lazy 다운로드 ≥50MB (e.g. browser binary) | -2 |
| API 키 quota 소진 (T1+/T2~) | -1 |

clamp [0, 10].

### 3-2. 확장성 (Scalability) — `S`

여러 에이전트·세션·도메인에 재사용 가능한 정도. 높을수록 미래 가치.

| 항목 | 점수 |
|------|------|
| 2+ capability profile 교차 매칭 (§3-1 cross-mapping) | +3 |
| toolset enumeration ≥3 (도메인별 부분 enable) | +2 |
| T0 (무키·로컬) | +2 / T1 (무료 키) | +1 / T1+/T2~ | 0 |
| 공식 reference (`*` mark) — 장기 유지보수 ✓ | +2 |
| mid-session add 후 다음 세션 전파 ✓ (= 모든 MCP 동일하므로 baseline) | +1 |
| Node engines pin / OS 종속 (e.g. chrome-devtools Node 20.19+) | -1 |

clamp [0, 10].

### 3-3. 정확도 (Accuracy) — `A`

목적 도구 매핑 정확도 + 검증 상태. 높을수록 hallucination/spoof 위험 낮음.

> **verification_status 단일 출처:** 다음 표의 `probe ✓` / `docs only` / `pending` 분류는 `permission-profiles.md §3-0` (P6-9 — 2026-05-14)의 status enum 박제. 본 표 갱신 시 §3-0 동시 적용 필수.

| 항목 | 점수 |
|------|------|
| `verification_status = probe-verified` (§3-0 ✓ — §3 행 ✓ symbol) | +4 |
| 도구 enumeration source-grep 100% 일치 | +2 |
| 신호 매칭 ≥2 (예: S1+S3 둘 다 매칭) | +2 |
| 패키지 출처 verify (npm Author + GitHub org cross-check) | +1 |
| 부수 효과 도구가 deny 권고 박제됨 (§3 default bucket) | +1 |
| spoof 위험 미해소 (출처 unverified) | -3 |
| `verification_status = docs-only` (§3-0 📜) | -2 |
| `verification_status = pending` (§3-0 ⚠️ — P6-9 2026-05-14 신설) | -4 |

clamp [0, 10].

> **합성 default 풀 필터 (P6-9):** R-2 R0 검색 시 *§3-0 status = ✓ 만* default 풀에 포함. 📜·⚠️ 후보는 R-7 confirm gate에서 *제안*만 — inline `mcpServers:` 자동 합성 ❌.

### 3-4. 종합 점수

```
Total = (E × wE) + (S × wS) + (A × wA)
default 가중 wE=0.4, wS=0.3, wA=0.3
```

사용자가 정확도 우선 도메인(예: 보안/규제)이면 wA를 0.5로, 비용 민감(`tech_stack.budget_constrained`)이면 wE를 0.5로 조정 가능. 가중 변경은 *명시* 요청 시에만.

**가중 ×Tier (출처 위계):**
```
Adjusted = Total × tier_weight
R0 tier_weight=1.0 / R1=0.7 / R2=0.4
```

---

## 4. 출력 — 추천 표

에이전트 1명당 top-K (default K=3) 후보를 표로 출력:

```
[에이전트: web-researcher]
신호 매칭: S1(read-heavy) + S3(web-egress) + S6(reasoning-aux)

| Rank | MCP                | Tier | 도구수 | E   | S   | A   | Total | Adj  | 출처 |
|------|--------------------|------|-------|-----|-----|-----|-------|------|------|
| 1    | fetch              | T0   |   4   | 8   | 7   | 9   | 8.0   | 8.0  | R0 ✓ |
| 2    | memory             | T0   |   9   | 7   | 9   | 9   | 8.3   | 8.3  | R0 ✓ |
| 3    | brave-search       | T1+  |   8   | 6   | 6   | 5   | 5.7   | 4.0  | R1   |

권고 조합: fetch + memory (§3-1 web-research 행 박제 — Layer B 단독)
대안 (API 키 보유 시): + brave-search (검색 quota — settings.json ask 필수)
```

**필드 정의:**
- `Adj` = `Total × tier_weight`
- `출처` = R0/R1/R2 + (probe ✓ 여부)
- `권고 조합` = §3-1 매트릭스 행 매핑 + 점수 상위 후보 *교차*
- `대안` = 점수 차이 ≤1.0 후보 또는 사용자 키 보유 시점에 승급 가능 후보

---

## 5. 절차 — Phase 5-2 통합 7-step

```
R-1. 신호 추출 — 본 §1 10 신호 (S1~S10) LLM 추론, 매칭 신호 집합 박제
R-2. R0 검색 — `permission-profiles.md §3·§3-1`에서 신호별 후보 grep
R-3. R0 매칭 부족 시 R1 cascade — modelcontextprotocol/servers README WebFetch
R-4. (선택) R2 cascade — 사용자 명시 동의 시 npm/큐레이션 WebSearch
R-5. 후보별 §3 점수 산출 (E, S, A) — probe 미완 후보는 A 페널티
R-6. top-K 표 출력 + 권고 조합 1줄
R-7. AskUserQuestion confirm gate → 채택 결정은 §10 Step 3·4·5로 인계
```

> **자동화 한계 (§10-6과 동일 doctrine):**
> - R-1 ~ R-6 자동 (LLM 추론 + grep + WebFetch + 점수)
> - R-7 confirm 사용자 게이트 — *추천 채택*도 명시 동의 필요
> - 외부 install·키 등록·permissions 갱신은 §10이 처리

---

## 6. 캐시 — 비용 완화

R1·R2 검색은 외부 호출(WebFetch/WebSearch)이라 합성마다 반복하면 비용 큼. 다음 캐시를 사용:

| 파일 | 내용 | TTL |
|------|------|-----|
| `_workspace/_baseline/mcp_catalog.jsonl` | R1/R2 검색 결과 (이름·URL·tier·도구 카운트 추정·발췌일) | 30일 (사용자 명시 갱신 또는 `/harness:harness-mcp-recommend --refresh`) |

캐시 hit이면 WebFetch/WebSearch 생략. miss 또는 expired면 cascade 재실행 후 캐시 갱신.

**캐시 schema (jsonl 1행/후보):**
```json
{"name": "...", "tier": "T1+", "category": "research", "source": "R1|R2",
 "source_url": "...", "tool_count_est": 8, "verified_at": "2026-MM-DD",
 "notes": "..."}
```

---

## 7. 회로 — 결과가 §10·§4와 어떻게 연결되는가

```
Phase 5-2 합성 시작
  ↓
  ├─ §4 결정 트리 (capability profile 매핑)
  │   ↓
  │   capability profile N개 확정
  │   ↓
  └─ §본 문서 5절 R-1~R-6 (추천 점수)
      ↓
      top-K 표 + 권고 조합
      ↓
      R-7 AskUserQuestion (confirm gate)
      ↓
      ┌─────────────────┬─────────────────┐
      ↓                 ↓                 ↓
   채택 (=§10 Step 3·4·5)  보류 (Phase 5-2 진행)  거부 (대안 후보로 R-5 재실행)
```

- §4가 *어떤 profile에 어떤 후보*를 매핑한다면, 본 추천은 *후보들 간 점수*를 산출.
- §10이 *채택 절차*라면, 본 추천은 *채택 전 의사결정 자료*를 제공.
- 셋이 합쳐서 합성 시점 자동 추천 → 사용자 confirm → 채택 → reflect 완결.

---

## 8. 추천 거부 학습 (옵션 — 13차 사이클 사용 drift 활용)

사용자가 추천 후보 X를 *반복* 거부하면 (≥2회), 본 에이전트 description 기반의 점수 표에서 X를 자동 -2점 페널티 후 재정렬. 거부 학습은 `_workspace/_telemetry/_mcp_recommendation.jsonl`에 누적:

```json
{"ts": "...", "agent": "web-researcher", "candidate": "firecrawl",
 "decision": "rejected", "reason": "T2~ quota 부담"}
```

§10-4 rollback과 별개 — 채택 *전* 거부는 본 jsonl, 채택 *후* 회수는 §10-4 변경 이력 표.

---

## 9. 한계와 범위 외

- **자동 install/키 발급/permissions 자동 승급 ❌** — §6 정책 동일 적용.
- **R2 외부 큐레이션의 spoof 검증 ❌** — 사용자가 trust 명시 + §10 Step 2 probe 필수.
- **추천 정확도 자체 평가 ❌** — 채택 후 실제 사용 빈도는 Phase 10 telemetry 영역.
- **plugin host 본 저장소 자체에 적용 ❌** — host self-host CM 격리(운영 중인 경우). 추천은 *derived 프로젝트* 합성 시에만.

---

## 10. 참고

- `permission-profiles.md` §3·§3-1·§4·§10 — 단일 출처 인벤토리·매핑·채택 절차
- `/harness:harness-mcp-recommend` — on-demand 진입점 (합성 후 추가 에이전트 점검용)
- `/harness:harness-mcp-adopt` — 채택 5-step 진입점
- `/harness:harness-mcp-status` — 채택 후 정합 진단
