# Permission Profiles — MCP·도구 자동 할당 카탈로그

> **Read at phase:** Phase 5-2 (MCP·도구 자동 할당). 8 capability profile (4 범용 + 4 도메인) × MCP 매트릭스. mcp-recommendation.md와 동반 read.

Phase 5(에이전트 정의)에서 생성되는 에이전트에 빌트인 도구 + MCP 도구 + 권한을 자동 합성할 때 사용하는 카탈로그·결정 트리·합성 룰. Phase 5는 이 문서를 *참조*만 하고, 본 문서가 단일 진실 원천.

---

## 0. Closure Summary & Navigation (2026-05-14 M5 박제)

> **목적**: 본 문서 1100+ LOC. Phase 5-2 진입 LLM이 *어느 § 부터 read*해야 하는지 단일 진입점 표. *모든 § 다 read* 금지 — phase별 read 단축 + token 절감.

### 0-1. 한 줄 요약

도메인 한 문장 → ① **3-layer 권한 모델** (§1: A=서버 advertise / B=inline mcpServers / C=permissions allow/ask/deny) ② **8 capability profile** (§2: code-test / web-research / external-integration / reasoning-aux + ml-pipeline / devops-infra / mobile-native / data-eng) ③ **MCP 후보 inventory + 매트릭스** (§3, §3-1) ④ **결정 트리** (§4) ⑤ **합성 산출물 템플릿** (§5) → 자동 합성. 채택 절차는 §10. 검증 미완 항목은 §11 fixture로 후속 PoC.

### 0-2. 진입 § 매트릭스 — phase·작업별

| 작업 | 진입 § | 동반 read |
|---|---|---|
| Phase 5-2 합성 시작 (default) | §0 → §2 → §4 → §5-1 | mcp-recommendation.md §1 (signal 추출) |
| capability profile 결정 | §2 (8 profile 정의 — *전문 sub-grep만*) + §3-1 매트릭스 (권고 MCP 행) | — |
| MCP 후보 검색 | §3 (T0/T1/T2 inventory) + §3-1 매트릭스 | mcp-recommendation.md §2-3 (3축 점수) |
| 합성 산출물 YAML | §5-1 (inline mcpServers Layer B *default*) — anti-pattern은 §5-2 | — |
| settings.json permissions | §5-3 (Layer C 게이트) — 부수 효과 도구 deny 강제 | §3 default bucket |
| 안전 정책 검토 | §6 (자동 install/키 발급 금지) | — |
| dynamic adoption (run-time MCP 채택) | §10 5-step (discover → probe → confirm → install → reflect) | mcp-recommendation.md §5 절차 |
| 진행 가시성 (read-only 진단) | §3 + §3-1 (인벤토리) + §10-4 rollback 이력 | `/harness:harness-mcp-status` |
| 검증 상태 확인 | §8 (검증 상태 표) — PoC 미완 항목 식별 | §11 fixture |
| 실증 가능한 reproducer | §11-1~§11-4 (재현 레시피) | — |

### 0-3. § 분류 — *반드시 read* vs *조건부 read* vs *심화 read*

| 등급 | § | doctrine |
|---|---|---|
| **A. 반드시 read** (Phase 5-2 진입 시) | §1 (3-layer) / §2 (8 profile) / §4 (결정 트리) / §5-1 (합성 default) / §5-3 (permissions) | doctrine 무지 시 silent fail 위험 |
| **B. 조건부 read** | §3·§3-1 (MCP 후보 검색 시) / §5-2 (parent 적재 *예외*만 — 99% 케이스 X) / §10 (run-time 채택 시) / §6 (자동 install 금지 doctrine 확인) | 작업 의제별 진입 |
| **C. 심화 read** (특수 상황만) | §7 (Phase 5 호출 절차 디테일) / §8 (검증 상태 누적표) / §9 (Plugin subagent 제약) / §11 (실증 reproducer) | docs-level deep dive |

### 0-4. § 간 cross-reference

```
§1 (Layer 모델) ──┬─→ §5-1·§5-2·§5-3 (Layer A·B·C 구현)
                  └─→ §6 (Layer 안전 정책)
§2 (8 profile) ───┬─→ §3-1 매트릭스 (profile×MCP)
                  └─→ §4 결정 트리 (profile 매핑)
§3 inventory ─────┬─→ §3-1 매트릭스 (T0 검증 완료 7종 cross-mapping)
                  └─→ §10 dynamic adoption (T1+/T2~ 채택)
§4 결정 트리 ─────┬─→ §5-1·§5-2 합성 분기
                  └─→ mcp-recommendation.md (1-R 단계)
§5-1 inline ──────┬─→ §5-3 permissions deny (inline 도구 전체 advertise — Layer C 강제)
                  └─→ §11-2 spawn 측정 (parent isolation empirical)
§10 dynamic ──────┬─→ §3 inventory 갱신 = §3-1 매트릭스 동기 갱신
                  └─→ §10-4 rollback 이력
```

### 0-5. 8 profile 빠른 참조

| Profile | 시그널 | T0 권고 MCP | §3-1 행 |
|---|---|---|---|
| code-test | S2+S5 | git, filesystem | §3-1 행 1 |
| web-research | S1+S3 | fetch, memory | §3-1 행 2 |
| external-integration | S2+S4+S5 | sqlite (+T1+ github) | §3-1 행 3 |
| reasoning-aux | S6 | sequential-thinking, time | §3-1 행 4 |
| ml-pipeline (2026-05-14) | S7 | filesystem + sqlite + memory + sequential-thinking + git | §3-1 행 5 |
| devops-infra (2026-05-14) | S8 | git + filesystem + time + sequential-thinking | §3-1 행 6 |
| mobile-native (2026-05-14) | S9 | filesystem + git + sequential-thinking (+T1 playwright/chrome-devtools) | §3-1 행 7 |
| data-eng (2026-05-14) | S10 | sqlite + filesystem + git + memory + sequential-thinking | §3-1 행 8 |

> **Signal S1~S10 정의**: mcp-recommendation.md §1.

---

## 1. 3-layer 권한 모델

에이전트에 도구/MCP를 부여하는 경로는 3개. 토큰 비용·통제 입자도가 다르다.

| Layer | 메커니즘 | 컨텍스트 절감 | 실행 통제 | 적용 시점 |
|-------|---------|-------------|---------|---------|
| **A. 서버 측 toolset 필터** | MCP 서버의 `--toolsets` / env (예: `GITHUB_TOOLSETS=issues,prs`) | ⚠️ advertise 단계 축소 — *deferred pool 적재 영향은 미측정* [^A] | ✅ 미advertise = 호출 불가 | `.mcp.json` 등록 시 |
| **B. 서브에이전트 inline `mcpServers:`** | 에이전트 frontmatter에 inline 정의 | ✅ 서브에이전트 컨텍스트만 — **parent isolation empirical 확정** [^B] | ⚠️ inline 서버의 도구는 `tools:` allowlist로 안 줄어듦 — `permissions.deny`로 강제 [^B2] | Phase 5 합성 시 |
| **C. `permissions.allow/ask/deny`** | `.claude/settings.json` 패턴 매칭 | ❌ 정의 로드는 그대로 | ✅ 호출 시 승인/차단 | 보안 게이트 |

[^A]: Layer A의 *advertise 단계* 축소는 공식 docs + playwright `--caps=vision` probe(default 23종 vs +6 좌표 mouse)로 empirical 확정. 단 *Claude Code deferred pool 적재량*까지 비례 축소되는지는 미측정 — `~/.claude.json` 4-key gate(`enabledMcpjsonServers` user+project / `hasTrustDialogAccepted` / `disabledMcpjsonServers`) + `<derived>/.claude/settings.json` `enabledMcpjsonServers` 모두 mode-independent로 deferred pool 적재 제어 ✗ 부정(인터랙티브·`-p` 양쪽 empirical). 진짜 절감 채널 후보는 *server-side `--toolsets`/env*로 좁혀졌으나 deferred pool 효과는 derived 프로젝트의 인터랙티브 세션 재시작 측정이 필요한 외부 의제. 토큰 비용 추정에 ±50% 오차 caveat 유지. inline `mcpServers:` 패턴(Layer B parent isolation = empirical 확정)이 *확정된* 토큰 절감 채널.

[^B]: Layer B "컨텍스트 절감 ✅"는 P0 재현 검증으로 empirical 확정 — derived 프로젝트의 정정 schema(list-of-dicts + `type: stdio`) fixture로 spawn 후, [1] subagent 도구 풀에 inline 정의 도구 노출 ✓ + [2] parent `ToolSearch` 0 hit ✓ 양면 통과. 즉 inline 정의는 **subagent에만 connect되고 parent 컨텍스트에는 deferred pool에도 적재되지 않음**. 단일 inline 패턴(예: `data-analyst` = sqlite 1종) + *멀티 inline 패턴*(예: `web-research` = fetch + memory 2종 동시 등재) 모두 동일하게 parent isolation 보장 — §3-1 매트릭스 "채택 패턴 권고" 섹션의 통합 inline 예시 YAML 참조.

[^B2]: **새 발견 (P0 검증 부수 결과)** — frontmatter `tools:`에 inline 서버 도구 1종만 allowlist해도 advertise 도구 전체가 노출됨. 즉 **`tools:` allowlist는 inline 서버 도구를 줄이지 못한다**. inline 서버는 connect 시 advertise하는 모든 도구를 자동 노출. → **Layer C 통제는 inline 서버에 대해 `settings.json permissions.deny`로 강제해야** 한다 (§5-3 보강). Layer A(서버 측 toolset 필터)가 inline에서도 유효한 유일한 *advertise 축소* 채널 (§5-1-b Layer A+B 결합형 권고가 더 강해짐).

**우선순위:** A > B > C. **Layer B는 *parent isolation*에 ✅ 작동 (10차 P0 확정), 단 inline 서버의 *도구 카운트*는 `tools:` allowlist로 줄지 않음 — Layer A(서버 측 advertise 필터) 또는 Layer C `deny` 로만 통제.** 토큰 절감 채널은 A+B 조합, *agent별 도구 풀 형태 통제*는 A 단독, *호출 시점 게이트*는 C.

> **빌트인 baseline — Claude Code deferred tool pool (§11-1 6차 사이클 발견)**
>
> Claude Code 현 빌드는 등록 MCP 도구를 *deferred pool*로 관리한다 — SessionStart 시 system prompt에 *이름 + 짧은 description*만 적재되고, 전체 JSON schema는 `ToolSearch select:<name>`로 lazy-fetch될 때 적재. 즉 *baseline 적재 비용*은 도구 수 × ~20-50 tokens (이름+설명) 수준이며, schema 풀 적재(~200-500 tokens/도구)는 호출 시점에만 발생. 17 MCP 도구 등록 상태에서 SessionStart 비용 추정 ≈ 17 × 30 ≈ **500 tokens** (이전 추정 17 × 350 = 6000 tokens 대비 ~12x 절감).
>
> **함의:**
> - 의도 ②(적재 최소화)의 baseline 자체가 docs 추정보다 우호적. inline `mcpServers:` 패턴 없이도 약식 절감이 작동.
> - 단 도구 *이름·description*은 여전히 등록 도구 수에 비례 → Layer A(서버 advertise 축소)의 가치 유효
> - Layer B(subagent 격리)는 *deferred pool 자체를 subagent 안으로 이동* → parent에는 이름조차 안 나타남, schema lazy-fetch도 subagent 내부에서만 → 절감 폭은 더 큼
> - **§11-3 측정 메트릭 재정의** (6차 사이클 갱신 완료): "도구 카운트 변화"에서 "M1=system prompt 토큰 / M2=deferred pool 카운트 / M3=schema fetch 빈도" 3축 조합으로 — `references/fixtures/verify_11_3.md` 본문 반영됨, 외부 실행자는 갱신본 사용

---

## 2. Capability Profiles (8종)

각 프로파일은 ① 빌트인 도구 ② MCP 후보 ③ 추천 toolset 필터 ④ 격리 권장 여부를 묶는다.

> **8 profile 분류 doctrine (2026-05-14 P6-11 확장)**: §2-1~§2-4는 *범용 4종* (PoC 완료 매트릭스 §3-1 박제). §2-5~§2-8은 *도메인 4종* (2026-05-14 신설 — ml-pipeline / devops-infra / mobile-native / data-eng). 도메인 4종의 MCP 후보 다수는 PoC 미완 — §3-1 매트릭스 진입은 §10 dynamic adoption 절차로 cycle별 누적.

### 2-1. `code-test` — 테스트·코드 워크플로우
- **빌트인:** `Bash`, `Read`, `Edit`, `Glob`, `Grep`, `Write`
- **MCP 후보:** `playwright` (toolset=`browser,navigation`), `chrome-devtools`, `git`, `github` (toolset=`issues,prs,actions`)
- **격리:** Bash 호출이 빈번 → parent에 두는 게 효율적, MCP 부분만 서브에이전트 격리

### 2-2. `web-research` — 리서치·웹 검색
- **빌트인:** `WebFetch`, `WebSearch`
- **MCP 후보:** `fetch`, `brave-search`, `tavily`, `exa`, `firecrawl`, `memory` (KG로 도메인 사실 누적)
- **격리:** 강력 권장 — 검색 결과는 토큰 소비량이 크므로 서브에이전트가 요약만 반환
- **§3-1 매트릭스 박제 권고:** `fetch` + `memory` (14차 사이클 — `fixtures/synthesis_example/web-research/` 시나리오 참조)

### 2-3. `external-integration` — 외부 시스템 연결
- **빌트인:** `Bash`, `WebFetch`
- **MCP 후보:** `github`, `slack`, `notion`, `linear`, `sqlite`, `postgres`
- **격리:** 필수 — 데이터 유출 경계를 명확히, 서브에이전트가 의도된 ops만 수행

### 2-4. `reasoning-aux` — 추론 보조
- **빌트인:** (없음)
- **MCP 후보:** `sequential-thinking`, `memory`, `time`
- **격리:** 불필요 — parent에 직접 부착해도 토큰 비용 낮음

### 2-5. `ml-pipeline` — ML 학습·실험·모델 관리

> **도메인 시그널:** "모델/학습/평가/실험 추적/하이퍼파라미터/데이터셋/feature/inference"

- **빌트인:** `Bash` (notebook execution / training script run), `Read`, `Edit`, `Write`, `Glob`, `Grep`
- **MCP 후보:**
  - T0 ✓ — `filesystem` (dataset/artifact path-roots 격리), `sqlite` (실험 추적 — MLflow 대체 또는 보조), `memory` (지식 그래프로 도메인 사실 누적), `sequential-thinking` (실험 설계 단계별 추론), `git` (모델 카드·실험 코드 버전)
  - T1+ 후보(PoC 미완) — `github` (모델 PR·릴리즈), `huggingface-mcp`(추정), `wandb-mcp`(추정) — §10 dynamic adoption 진입 필요
- **격리:** **강력 권장** — 데이터셋 read·notebook 실행 결과가 토큰 부담 크고, 모델 로드는 spawn 비용 큰 부수 효과 → 서브에이전트가 *실험 결과 요약만* 반환
- **default 권한 doctrine:** dataset read = `allow`, model write/checkpoint = `ask` (부수 효과 큼), 외부 dataset hub fetch = `ask` (PII·라이선스 surface)
- **PoC 미완 표기:** 본 profile은 T0 후보 5종만 §3-1 매트릭스에 cross-mapping 가능 (`filesystem`/`sqlite`/`memory`/`sequential-thinking`/`git`). 전용 MCP(huggingface/wandb 등)는 §3 행 추가 후 §3-1 진입

### 2-6. `devops-infra` — 인프라·배포·운영

> **도메인 시그널:** "배포/CI/CD/인프라/모니터링/스케줄링/롤백/SRE/oncall/Kubernetes/Terraform"

- **빌트인:** `Bash` (kubectl/terraform/aws-cli 호출), `Read`, `Edit`, `Write`
- **MCP 후보:**
  - T0 ✓ — `git`, `filesystem` (IaC 파일 path-roots), `time` (스케줄링 timezone 변환), `sequential-thinking` (롤백 절차 단계별)
  - T1+ — `github` (Actions toolset — CI/CD), `slack` (T2~ — 알림 채널)
  - PoC 미완 — `kubernetes-mcp`(추정), `terraform-mcp`(추정), `aws-mcp`(추정), `datadog-mcp`(추정) — §10 진입 필요
- **격리:** **필수** — production 변경 surface 극대 → 서브에이전트가 read-only 진단 → parent가 변경 confirm gate
- **default 권한 doctrine:** 모든 *변경* 도구(`apply`/`destroy`/`rollback`/`deploy`) `ask` 또는 `deny` default — 사용자 명시 confirm 없이 자동 `allow` 금지. `slack` 발화는 `ask` (production 알림은 회수 불가)
- **회수 doctrine:** `kubectl delete`/`terraform destroy` 등 비가역 명령은 §10-4 rollback 절차로 회수 불가 — *사전 dry-run* gate 필수

### 2-7. `mobile-native` — 모바일/네이티브 앱

> **도메인 시그널:** "iOS/Android/native/Swift/Kotlin/Flutter/React Native/Xcode/Gradle/emulator/build"

- **빌트인:** `Bash` (Xcode/Gradle build, simulator 제어), `Read`, `Edit`, `Write`, `Glob`, `Grep`
- **MCP 후보:**
  - T0 ✓ — `filesystem` (project root + iOS/Android subdir 격리), `git`, `sequential-thinking` (빌드 실패 디버깅 단계별)
  - T1 — `playwright` (mobile emulation `--browser=webkit` for iOS Safari 시뮬), `chrome-devtools` (Android WebView debug — Chrome remote debugging port)
  - PoC 미완 — `appium-mcp`(추정), `xcode-mcp`(추정), `android-mcp`(추정) — §10 진입 필요
- **격리:** **권장** — 빌드 toolchain (Xcode build, Gradle sync) 시간·spawn 비용 큼 → 서브에이전트가 빌드 후 실패 로그 요약만 반환
- **default 권한 doctrine:** `Bash` build 명령 `allow`, code signing / IPA upload / TestFlight 발화 `ask` (배포 surface). filesystem write는 native project root 격리 강제 (cross-project mutation 방지)
- **caveat:** `playwright --browser=webkit`은 iOS Safari *시뮬*만 — 실 device 측정은 본 profile 외부 (Appium 등 미완)

### 2-8. `data-eng` — 데이터 엔지니어링·ETL·파이프라인

> **도메인 시그널:** "ETL/ELT/data pipeline/Airflow/dbt/Spark/스키마 변환/data warehouse/data lake/ingestion"

- **빌트인:** `Bash` (dbt run / airflow CLI / spark-submit), `Read`, `Edit`, `Write`, `Glob`, `Grep`
- **MCP 후보:**
  - T0 ✓ — `sqlite` (로컬 staging/scratch DB), `filesystem` (data lake path-roots), `git` (pipeline 코드 버전), `memory` (스키마 사실 누적 — 컬럼 의미·lineage), `sequential-thinking` (스키마 마이그레이션 단계별)
  - T2~ — `postgres` (production warehouse — `read_query` only 강제 권장), PoC 미완: `snowflake-mcp`(추정), `bigquery-mcp`(추정), `databricks-mcp`(추정), `dbt-mcp`(추정) — §10 진입 필요
- **격리:** **필수** — DB 접근 boundary 명확화 + 대용량 query 결과 토큰 부담 → 서브에이전트가 *집계 결과 요약만* 반환, raw row 미반환
- **default 권한 doctrine:**
  - production DB 접근: `read_query` `allow`, `write_query`/`create_table`/`drop_table` `deny` default (마이그레이션은 별도 dedicated agent + 사용자 confirm)
  - staging/scratch DB: `read_query`/`write_query` `allow`, `drop_*` `ask`
  - PII 포함 테이블 query 결과는 서브에이전트가 hash/redact 후 parent에 반환 권장 (compliance 시그널 GDPR/HIPAA/PCI-DSS 매칭 시 hard 강제)
- **회수 doctrine:** `truncate`/`drop`/`delete` 등 비가역은 dry-run + 사용자 명시 confirm 2단 gate. backup 절차 박제 권장

---

## 3. MCP 후보 인벤토리 (Tier 분류)

`*` = 공식 reference (anthropic/modelcontextprotocol), `+` = API 키 필요, `~` = 유료/민감 데이터

### 3-0. verification_status 정책 (P6-9 — 2026-05-14)

§3 인벤토리의 각 MCP는 다음 3 status 중 하나로 분류 — Phase 5-2 *합성 default 풀* 포함 여부 결정.

| status | symbol | 합성 default 풀 | 점수 페널티 (`A` 정확도) | 사용 자격 |
|---|---|---|---|---|
| **probe-verified** | ✓ | 포함 | +4 (probe ✓ 보너스 — 기존 §3 점수표 정합) | 즉시 사용 가능. fixture source-grep 100% 일치 + 도구 enumeration 박제 |
| **docs-only** | 📜 | **제외** | -2 ("docs only" 페널티 — `mcp-recommendation.md §3` 매핑) | 사용자 명시 R-7 confirm + §10 Step 2 probe 통과 시 승격 |
| **pending** | ⚠️ | **제외** | -4 (대칭 페널티 — 박제 정보 부족) | §10 dynamic adoption 진입 + Step 2 probe 필수. inline `mcpServers:` 직접 합성 ❌ |

#### MCP × verification_status (2026-05-14 cycle 박제)

| MCP | status | 근거 |
|---|---|---|
| `fetch` / `sequential-thinking` / `git` / `sqlite` | ✓ | `fixtures/probe_*.js` 실행 OK + `tools/list` source-grep 100% 일치 (cycle ≤22) |
| `filesystem` / `time` / `memory` | ✓ (probe-only) | install 미수행이나 stdio JSON-RPC probe로 도구 enum 확정 (13~18차 cycle) |
| `playwright` | ✓ | 22차 외부 PowerShell probe 실행 — default 23종 + caps=vision +6종 empirical 확정 |
| `chrome-devtools` | 📜 → ✓ (verify-only) | 23차 npm/GitHub source verify 확정 (Google LLC org / Apache-2.0 / mcpName 정합). Node ≥20.19 host 환경 의존. probe 도구 enum은 host 측 별건 |
| `brave-search` / `tavily` / `exa` / `firecrawl` / `github` | 📜 | docs 박제 (17차) + 18차 fixture 준비. API 키 보유 후 §10 Step 2 probe 필수 |
| `slack` / `postgres` | ⚠️ | 이름·Tier·카테고리만 박제. 합성 default 풀 ❌ |

> **합성 default 풀 doctrine (P6-9):** Phase 5-2가 inline `mcpServers:` *자동 합성* 시 ✓ 외 status는 **금지**. 📜는 R-7 confirm gate에서 *제안*만, ⚠️는 §10 dynamic adoption 진입 안내 후 응답 종료.
>
> **점수 페널티 정합 (`mcp-recommendation.md §3` cross-reference):** docs-only `-2`, pending `-4`. 본 표 갱신 시 mcp-recommendation 양 doc 동시 적용 필수.
>
> **status 승격 워크플로우:** 📜 → ✓는 §10 Step 2 probe 1회로 자동 승격. ⚠️ → 📜는 trusted source 확인 + fixture 준비 (`fixtures/probe_<server>.js`) 후 확정. ⚠️ → ✓는 1단계 점프 ❌ (probe 완료가 docs 박제 확정을 함의 X — npm cross-check + source verify 별건).


| Tier | 정의 | 자동 적용 정책 |
|------|------|--------------|
| **T0** | 무키·로컬 only | 사용자 1회 동의 후 `allow` 가능 |
| **T1** | 무료 API 키 또는 PAT 필요 | 키 등록 + 사용자 명시 동의 → `allow` |
| **T2** | 유료 또는 민감 외부 시스템 | 항상 `ask`, 자동 `allow` 금지 |

| MCP | Tier | 카테고리 | install 명령 (검증 시점) | 도구 enumeration |
|-----|------|---------|-----------------|---|
| `fetch` (mcp-server-fetch-typescript) | T0 | research | `claude mcp add fetch -- npx -y mcp-server-fetch-typescript` ✓ | 4종: `get_raw_text`, `get_rendered_html`, `get_markdown`, `get_markdown_summary` ✓ |
| `sequential-thinking` * | T0 | reasoning-aux | `claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking` ✓ | 1종: `sequentialthinking` ✓ |
| `filesystem` * | T0 | code-test | `claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem <allowed-path-1> [<allowed-path-2>...]` ✓ probe-only (13차 사이클 후속, plugin host 본 저장소 미install — `fixtures/probe_filesystem.js`) | 14종 ✓: **read 10종** = `read_file`, `read_text_file`, `read_media_file`, `read_multiple_files`, `list_directory`, `list_directory_with_sizes`, `directory_tree`, `search_files`, `get_file_info`, `list_allowed_directories` + **write 4종** = `write_file`, `edit_file`, `create_directory`, `move_file` (default 권고: read 10종 `allow`, write 4종 `deny` 또는 `ask` — 빌트인 Read/Write/Edit과 중복이라 *capability profile = code-test의 path-roots 격리 가치*가 핵심 사용 사례) |
| `git` * (Python, uvx) | T0 | code-test | `claude mcp add git <uvx-abs-path> -- mcp-server-git --repository <repo-abs>` ✓ (uvx는 `pip install --user uv` 후 `%APPDATA%\Python\Python312\Scripts\uvx.exe`) | 12종 ✓: `git_status`, `git_diff_unstaged`, `git_diff_staged`, `git_diff`, `git_commit`, `git_add`, `git_reset`, `git_log`, `git_create_branch`, `git_checkout`, `git_show`, `git_branch` (모두 `repo_path` required, 변형 도구는 `target`/`message`/`files`/`branch_name`/`revision`/`branch_type` 추가 required) |
| `time` * | T0 | reasoning-aux | `claude mcp add time <uvx-abs-path> -- mcp-server-time` ✓ probe-only (Python, uvx 경유 — `fixtures/probe_time.js`) | 2종 ✓ (모두 read-only): `get_current_time` (`required=[timezone]`), `convert_time` (`required=[source_timezone,time,target_timezone]`) — 부수 효과 0, default 권고: 2종 모두 `allow` |
| `memory` * | T0 | reasoning-aux / web-research (cross-mapping) | `claude mcp add memory -- npx -y @modelcontextprotocol/server-memory` ✓ probe-only (Knowledge Graph storage, npm — `fixtures/probe_memory.js`) | 9종 ✓: **read 3종** = `read_graph`, `search_nodes` (`required=[query]`), `open_nodes` (`required=[names]`) + **create/add write 3종** = `create_entities`, `create_relations`, `add_observations` + **delete write 3종** = `delete_entities`, `delete_observations`, `delete_relations`. default 권고: read 3 `allow` / create+add 3 `ask` / delete 3 `deny` (destructive). plugin host self-host CM (운영 시)은 자체 sqlite 사용 — memory MCP는 *외부 derived 프로젝트의 persistent knowledge graph* 용도. **§3-1 매트릭스에선 `web-research` 행에 매핑** (Knowledge Graph는 외부 리서치 사실 누적용) — `reasoning-aux` profile에서도 도메인 사실 회상에 사용 가능 (capability profile은 mutually exclusive 아님) |
| `sqlite` * | T0 | external-integration | `claude mcp add sqlite <uvx-abs-path> -- mcp-server-sqlite --db-path <db-abs-path>` ✓ (8차 사이클, derived 프로젝트에서 검증; **`--db-path`는 절대경로 필수** — 상대경로면 health check `✗ Failed to connect`) | 6종 ✓: `read_query`, `write_query`, `create_table`, `list_tables`, `describe_table`, `append_insight` (read 3종을 allow, `write_query`/`create_table`/`append_insight` 3종을 deny/ask로 게이트 권장) |
| `playwright` (microsoft/playwright-mcp) | T1 | code-test | `claude mcp add playwright -- npx -y @playwright/mcp@latest [--caps=vision,pdf,devtools,network,storage,testing,config] [--browser=chromium\|firefox\|webkit\|msedge] [--isolated] [--headless]` ✅ probe-only empirical (22차 사이클, 외부 PowerShell `node fixtures/probe_playwright.js` 1회 — 본 세션 classifier 차단, 17차 §6 재확인 우회) | ✅ **probe ✓ 23종 default (22차 empirical, 17차 docs 박제 일부 정정)**: **navigation 2종** = `browser_navigate`, `browser_navigate_back` + **interaction 10종** = `browser_click`, `browser_drag`, `browser_hover`, `browser_select_option`, `browser_type`, `browser_press_key`, `browser_drop`, `browser_fill_form`, `browser_file_upload`, `browser_handle_dialog` + **inspect 4종** = `browser_snapshot`, `browser_take_screenshot`, `browser_wait_for`, `browser_console_messages` + **network 2종 (default)** = `browser_network_requests`, `browser_network_request` (🆕 22차 정정 — 17차 docs는 *caps=network opt-in*으로 추정했으나 *default에 2종 포함*) + **browser control 4종** = `browser_close`, `browser_resize`, `browser_evaluate`, `browser_run_code_unsafe` (⚠️ RCE-equivalent — 항상 `deny` 권고) + **tabs 1종** = `browser_tabs`. **caps=vision +6종 (22차 empirical 정정 — 17차 추정 5종 → 6종)** = `browser_mouse_move_xy`, `browser_mouse_click_xy`, `browser_mouse_drag_xy`, `browser_mouse_down`, `browser_mouse_up`, `browser_mouse_wheel` (🆕 *coordinate-based mouse 조작* — screenshot은 default에 이미 포함, vision의 진짜 의미는 좌표 기반 mouse 활성화 — vision-guided clicking). 다른 caps(pdf/devtools/network/storage/testing/config) 분해 측정 미완 — 외부 측정 권고: `$env:PLAYWRIGHT_FLAGS="--caps=<X>"; node fixtures/probe_playwright.js`로 각 caps의 추가 도구 enum. **부수 효과**: 첫 spawn 시 Chromium ~120MB lazy 다운로드 (browser_navigate 호출 시점) — **tools/list 단계엔 미발생** (22차 empirical 확정 — npx 패키지만 fetch, browser binary는 lazy) — 사용자 명시 confirm은 첫 navigate 시점에만 필요 |
| `chrome-devtools` (ChromeDevTools/chrome-devtools-mcp) | T1 | code-test | `claude mcp add chrome-devtools -- npx -y chrome-devtools-mcp@latest` (auto-launch — **default**) 또는 외부 Chrome 연결 시 `--browser-url=http://127.0.0.1:9222` 또는 `--ws-endpoint=<url>` (선조건: `chrome --remote-debugging-port=9222 --user-data-dir=<dir>`). 📜 docs 박제 (17차 사이클) + ✅ **패키지 출처 verify 확정** (23차 사이클): npm Author=**Google LLC** / Maintainers=mathias·orkon·google-wombot / GitHub `ChromeDevTools` org (39.2k★) / Apache-2.0 / latest v0.25.0 (2026-05-06) / mcpName `io.github.ChromeDevTools/chrome-devtools-mcp` — spoofing 위험 0, fixture `probe_chrome_devtools.js` "후보 1" 표기 ✅로 승급. 🚫 **Node engines 함정 (23차 empirical)**: 모든 49 versions이 `node ^20.19 \|\| ^22.12 \|\| >=23` 요구 (npm view 7 버전 cross-check); 측정 host 세션 v18.15.0에서 fixture 직접 spawn → `ERROR: chrome-devtools-mcp does not support Node v18.15.0` 즉시 종료. derived 프로젝트별 §10 진입 시 사용자 측 Node 20.19+ 가용성 확인 필수 (`--autoConnect` flag는 추가로 Chrome 144+ 요구). | 📜 docs 박제 44종 (17차 사이클): **input 10종** = `click`, `drag`, `fill`, `fill_form`, `handle_dialog`, `hover`, `press_key`, `type_text`, `upload_file`, `click_at` + **navigation 6종** = `close_page`, `list_pages`, `navigate_page`, `new_page`, `select_page`, `wait_for` + **emulation 2종** = `emulate`, `resize_page` + **performance 3종** = `performance_analyze_insight`, `performance_start_trace`, `performance_stop_trace` + **network 2종** = `get_network_request`, `list_network_requests` + **debugging 8종** = `evaluate_script`, `get_console_message`, `lighthouse_audit`, `list_console_messages`, `take_screenshot`, `take_snapshot`, `screencast_start`, `screencast_stop` + **memory 4종** = `take_memory_snapshot`, `get_memory_snapshot_details`, `get_nodes_by_class`, `load_memory_snapshot` + **extensions 5종** = `install_extension`, `list_extensions`, `reload_extension`, `trigger_extension_action`, `uninstall_extension` (⚠️ `install_extension`/`uninstall_extension` 권한 격상 — `deny` 권고) + **3p/webmcp 4종** = `execute_3p_developer_tool`, `list_3p_developer_tools`, `execute_webmcp_tool`, `list_webmcp_tools` (⚠️ `execute_*` 임의 코드 surface — `deny` 권고). **부수 효과**: auto-launch 모드는 Chromium 다운로드 또는 시스템 Chrome 기동 |
| `brave-search` * (brave/brave-search-mcp-server) | T1+ | research | `claude mcp add brave-search -e BRAVE_API_KEY=<key> -- npx -y @brave/brave-search-mcp-server --transport stdio` 📜 docs 박제 (17차 사이클 — API 키 보유 시점에 PoC) + 🔧 fixture: `fixtures/probe_brave_search.js` (18차 사이클) | 📜 docs 박제 8종 (17차 사이클): `brave_web_search`, `brave_local_search`, `brave_video_search`, `brave_image_search`, `brave_news_search`, `brave_summarizer`, `brave_place_search`, `brave_llm_context`. **모두 read-only** — default 권고 8종 `allow` (단 API quota 소진 부수 효과 — T1+에선 `ask`로 게이트 권장) |
| `tavily` (tavily-ai/tavily-mcp) | T1+ | research | `claude mcp add tavily -e TAVILY_API_KEY=<key> -- npx -y tavily-mcp@latest` 📜 docs 박제 (17차 사이클) + 🔧 fixture: `fixtures/probe_tavily.js` (18차 사이클 — 도구명 하이픈 첫 케이스 검증 의제 포함) | 📜 docs 박제 4종 (17차 사이클): `tavily-search`, `tavily-extract`, `tavily-map`, `tavily-crawl`. ⚠️ **하이픈 도구명** — `mcp__<server>__<tool>` 노출 시 변환 룰 확인 필요 (sequential-thinking 패턴은 `mcp__sequential-thinking__sequentialthinking`로 도구명 자체엔 하이픈 없음, tavily는 도구명에 하이픈 — 첫 케이스). 모두 read-only 검색·추출 — default 권고 4종 `allow` |
| `exa` (exa-labs/exa-mcp-server) | T1+ | research | `claude mcp add exa -e EXA_API_KEY=<key> -- npx -y exa-mcp-server` (또는 remote: `https://mcp.exa.ai/mcp?exaApiKey=<key>&tools=web_search_exa,web_fetch_exa,web_search_advanced_exa`) 📜 docs 박제 (17차 사이클) + 🔧 fixture: `fixtures/probe_exa.js` (18차 사이클 — deprecated 7종 자동 태깅 inline) | 📜 docs 박제 (17차 사이클): **default 2종** = `web_search_exa`, `web_fetch_exa` + **opt-in 1종** = `web_search_advanced_exa` + **deprecated 7종** = `get_code_context_exa`, `company_research_exa`, `crawling_exa`, `people_search_exa`, `linkedin_search_exa`, `deep_researcher_start`, `deep_researcher_check`, `deep_search_exa` (deprecated는 사용 권고 X). 모두 read-only — default 권고 3종 `allow` |
| `github` (github/github-mcp-server) | T1+ | external-integration | ⚠️ **No npm package** (17차 사이클 docs 정정 — 기존 §3 행이 npm 가정이었음). Docker: `claude mcp add github -- docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN=<pat> -e GITHUB_TOOLSETS=context,repos,issues,pull_requests,users ghcr.io/github/github-mcp-server` 또는 Go 바이너리: `go build -o github-mcp-server ./cmd/github-mcp-server && ./github-mcp-server stdio` 📜 docs 박제 (17차 사이클 정정) + 🔧 fixture: `fixtures/probe_github.js` (18차 사이클 — Docker spawn + `GITHUB_TOOLSETS` 3 조합 비교 측정 의도) | ✅ `GITHUB_TOOLSETS` env: 19종(`context`/`repos`/`issues`/`pull_requests`/`users` 5종 default + `actions`/`code_security`/`copilot`/`dependabot`/`discussions`/`gists`/`git`/`labels`/`notifications`/`orgs`/`projects`/`secret_protection`/`security_advisories`/`stargazers`) + 특수 `all`. 도구별 enum은 PAT 필요 — toolset당 ~5-15 도구 추정, 실 enum은 사용자 측 키 보유 시점에 별건 |
| `firecrawl` (mendableai/firecrawl-mcp-server) | T2~ | research | `claude mcp add firecrawl -e FIRECRAWL_API_KEY=fc-<key> -- npx -y firecrawl-mcp` (자체호스팅 시 `-e FIRECRAWL_API_URL=<endpoint>`) 📜 docs 박제 (17차 사이클 — 유료 quota 소진 부수 효과로 T2~) + 🔧 fixture: `fixtures/probe_firecrawl.js` (18차 사이클 — deprecated 4종 자동 태깅 + `firecrawl_browser_execute` 🚫 deny 권고 inline) | 📜 docs 박제 14종 (17차 사이클): **read 5종** = `firecrawl_scrape`, `firecrawl_search`, `firecrawl_map`, `firecrawl_extract`, `firecrawl_check_batch_status` + **batch/crawl 4종** = `firecrawl_batch_scrape`, `firecrawl_crawl`, `firecrawl_check_crawl_status`, `firecrawl_agent`, `firecrawl_agent_status` (⚠️ 대규모 API quota 소진 — `ask` 권고) + **deprecated browser 4종** = `firecrawl_browser_create`, `firecrawl_browser_execute`, `firecrawl_browser_list`, `firecrawl_browser_delete` (사용 권고 X). default 권고: read 5종 `ask` (T2~) / batch+crawl `ask` / `firecrawl_browser_execute` `deny` (임의 코드 실행) |
| `slack` | T2~ | external-integration | (PoC 미완) | (PoC 미완) |
| `postgres` * | T2~ | external-integration | (PoC 미완) | DB 접속 문자열로 제한 |

> **검증된 도구 참조 패턴 (frontmatter `tools:`)**: `mcp__<server>__<tool>` — 예: `mcp__fetch__get_markdown`, `mcp__sequential-thinking__sequentialthinking`. **서버명·도구명의 하이픈/언더스코어는 문자열 그대로 보존됨 (§11-1 6차 사이클 ✓ 확정)** — sequential-thinking이 `mcp__sequential-thinking__sequentialthinking`으로 노출됨이 다음 세션 SessionStart deferred tool list로 측정 완료. 17종 모두 §3 인벤토리 enumeration과 100% 일치.

> "검증 미완"은 본 문서 작성 시점에 실제 install·도구 enumeration·옵션 확인이 안 된 항목 — PoC에서 채워야 함.

> ⚠️ **PoC 미완 항목 사용 시 안전 룰 (§10 진입 전 필수)**
>
> 본 표에서 "(PoC 미완)" 표기된 항목(`filesystem`/`time`/`memory`/`playwright`/`chrome-devtools`/`brave-search`/`tavily`/`exa`/`firecrawl`/`slack`/`postgres`)은 **이름·Tier·카테고리만 박제된 *추정 후보***이다. 다음 셋 모두 미검증:
> - 실제 install 명령 (특히 패키지 spoofing 변형 가능성)
> - 도구 enumeration (이름·required params·schema)
> - toolset 필터 옵션 (env 또는 CLI flag)
>
> **§10 dynamic adoption 진입 시 필수 단계 (Step 2 pre-install probe 1회)**:
> 1. trusted source 확인(§8-3 안전 룰) — github.com/modelcontextprotocol/servers 또는 사용자 명시 trust
> 2. probe_sqlite.js 패턴으로 stdio JSON-RPC 핑 → 도구 enumeration 확정
> 3. 결과를 §3 표 행에 채움 (cycle별 누적 — §8-2 진척표와 동일 방식)
>
> **요약:** PoC 미완 항목은 *이름이 박제되었어도 사용 자격은 없음*. §10 진입을 거치지 않고 inline `mcpServers:` 합성에 직접 사용하면 schema mismatch / 패키지 spoof / 잘못된 toolset env 등으로 silent fail 가능.

> ⚠️ **"install 명령" 컬럼의 용도 — 합성 산출물용 default 아님**
>
> 본 컬럼의 `claude mcp add ...` 명령은 *PoC enumeration·검증 환경 install* 형태이며, `~/.claude.json` projects.{cwd}.mcpServers (= scope `local`) 또는 `.mcp.json` (= scope `project`) 적재 = **parent 컨텍스트에 도구 정의 적재**. 이 경로는 §5-2의 anti-pattern과 동일한 토큰 비용을 부담한다.
>
> **합성 산출물에서는 §5-1 inline `mcpServers:`가 default** — 본 컬럼의 install 명령에서 *동일 패키지명·인자*를 추출해 inline `command:`/`args:`/`env:` 필드로 옮기되, 등록 자체(`claude mcp add`)는 **생략**한다. 예: `claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=... -e GITHUB_TOOLSETS=pull_requests -- npx -y @modelcontextprotocol/server-github` → §5-1-b의 inline `mcpServers.github` 블록으로 변환.
>
> 본 컬럼을 그대로 실행해도 되는 경우는 (1) 본 PoC처럼 도구 enumeration 검증 (2) §5-2의 3 예외 조건 — *그 외에는 §5-1 변환*.

---

## 3-1. 검증 완료 T0 MCP × capability profile 매트릭스 (14차 사이클 P2 1차 종합 보고)

§3 인벤토리에서 PoC 완료된 **T0 MCP 7종 (총 48 도구)** 을 capability profile별로 매트릭스화한 *런타임 가용 default 카탈로그*. Phase 5-2 합성 시 §4 결정 트리가 capability profile을 확정하면 본 표에서 해당 행을 1차 후보로 발췌한다.

**검증 완료 카운트:**
- `fetch` 4 + `sequential-thinking` 1 + `git` 12 + `sqlite` 6 + `filesystem` 14 + `time` 2 + `memory` 9 = **48 도구** (+ github toolset 카탈로그 19 enum)
- 모두 [§8-3 stdio JSON-RPC `tools/list` 핑](#8-3-재사용-가능한-검증-기법)으로 source-grep 100% 일치 검증 (`fixtures/probe_*.js`)

### 매트릭스

| capability profile | 권고 MCP (T0) | 도구 카운트 | Layer 결합 | default 권한 bucket | mid-session add 후 미전파? |
|---|---|---|---|---|---|
| **code-test** | `git` + `filesystem` | 12 + 14 | §5-1-a Layer B 단독 (둘 다 toolset 필터 미지원) | `git` 12종 ask (commit/checkout/reset이 부수 효과) / `filesystem` read 10종 `allow` + write 4종 `deny` (빌트인 Read/Write/Edit과 중복 — `filesystem`의 가치는 *path-roots 격리*) | ✅ 다음 세션부터 |
| **web-research** | `fetch` + `memory` | 4 + 9 | §5-1-a Layer B 단독 (fetch/memory 모두 toolset 필터 미지원) | `fetch` 4종 `allow` (모두 read-only) / `memory` read 3종 `allow` + create/add 3종 `ask` + delete 3종 `deny` | ✅ 다음 세션부터 |
| **external-integration** | `sqlite` (+ T1+ `github` 별도) | 6 | §5-1-a Layer B 단독 (sqlite는 toolset 미지원) / `github`는 §5-1-b Layer A+B 결합 (env `GITHUB_TOOLSETS`) | `sqlite` read 3종 `allow` + write 3종 `deny` (read-only 강제) | ✅ 다음 세션부터 |
| **reasoning-aux** | `sequential-thinking` + `time` | 1 + 2 | §5-1-a Layer B 단독 (toolset 미지원, 둘 다 부수 효과 0) | 3종 모두 `allow` (read-only) | ✅ 다음 세션부터 |
| **ml-pipeline** (2026-05-14 신설) | `filesystem` + `sqlite` + `memory` + `sequential-thinking` + `git` (T0만, cross-mapping 5종) | 14 + 6 + 9 + 1 + 12 = 42 | §5-1-a Layer B 단독 (전부 toolset 미지원 — 5 MCP 동시 등록 부담 ↑ → *합성 시 도메인별로 2~3종 선별* 권장) | dataset read `allow` / 모델 write·실험 DB write `ask` / git commit `ask` | ✅ 다음 세션부터 (전용 MCP huggingface/wandb 등은 §10 진입 후 추가) |
| **devops-infra** (2026-05-14 신설) | `git` + `filesystem` + `time` + `sequential-thinking` (T0 4종) | 12 + 14 + 2 + 1 = 29 | §5-1-a Layer B 단독 | git 12종 `ask` (commit/checkout/reset 부수 효과) / filesystem write `deny` (IaC 변경은 명시 confirm) / time 2종 `allow` / `kubectl`/`terraform` 등은 `Bash` 빌트인으로 — 변경 도구 패턴 매칭 `ask` | ✅ 다음 세션부터 (kubernetes/terraform/aws MCP는 §10 진입 후 추가) |
| **mobile-native** (2026-05-14 신설) | `filesystem` + `git` + `sequential-thinking` (T0 3종) + `playwright`/`chrome-devtools` (T1, derived 프로젝트별) | 14 + 12 + 1 + 23 + 44 | §5-1-a Layer B 단독 (T0) / §5-1-b Layer A+B (playwright caps 필터) | filesystem write iOS/Android root 격리 / git `ask` / playwright `browser_run_code_unsafe` `deny` (RCE-equivalent) / chrome-devtools `install_extension`/`execute_*` `deny` | ✅ 다음 세션부터 (Appium/Xcode MCP는 §10 진입 후 추가) |
| **data-eng** (2026-05-14 신설) | `sqlite` + `filesystem` + `git` + `memory` + `sequential-thinking` (T0 5종) | 6 + 14 + 12 + 9 + 1 = 42 | §5-1-a Layer B 단독 | sqlite `read_query` `allow` / `write_query` `ask` / `create_table`/`drop_table` `deny` (마이그레이션은 dedicated agent) / filesystem data lake path-root 격리 | ✅ 다음 세션부터 (postgres T2~ + snowflake/bigquery/databricks/dbt MCP는 §10 진입 후 추가) |

> **매트릭스의 권고는 *제안*이지 default 강제가 아님** — §4 결정 트리의 사용자 confirm 게이트가 항상 우선. 사용자 도메인이 매트릭스 외 조합을 요구하면 (예: web-research에 `git` 필요) §10 dynamic adoption 절차로 후보 확장.

> **도메인 4종 cross-mapping doctrine (2026-05-14):** 도메인 profile 4종(ml-pipeline/devops-infra/mobile-native/data-eng)은 *전용 T0 MCP가 거의 없음* — T0 5종(`filesystem`/`sqlite`/`memory`/`git`/`sequential-thinking`/`time`)을 도메인 시그널 매칭에 따라 *재조합*하는 형태. 전용 MCP(huggingface/kubernetes/appium/snowflake 등)는 PoC 미완 — §10 dynamic adoption 진입 후 §3 행 추가 → 본 매트릭스 행 갱신. PoC 미완 항목은 "후보 풀에서 *옵션*"이지 default 합성 사용 X.

### 채택 패턴 권고 — 7 MCPs 통합 inline `mcpServers:` (참고 예시)

capability profile이 2종 이상이 겹치는 *멀티 도메인 에이전트*는 inline `mcpServers:`에 여러 MCP를 동시 정의 가능. 단 **inline 서버는 advertise 도구 *전부* 노출**(10차 cycle P0 새 발견)되므로 부수 효과 도구는 `permissions.deny`에 박제 필수.

```yaml
mcpServers:
  - filesystem:
      type: stdio
      command: npx
      args: ["-y", "@modelcontextprotocol/server-filesystem", "<allowed-path>"]
  - git:
      type: stdio
      command: <uvx-abs-path>
      args: ["mcp-server-git", "--repository", "<repo-abs>"]
  - sqlite:
      type: stdio
      command: <uvx-abs-path>
      args: ["mcp-server-sqlite", "--db-path", "<db-abs>"]
```

> 위 YAML은 **list-of-dicts + `type: stdio`** 필수 (9차 cycle docs RESOLUTION). 합성 직후 *현재 세션* 미전파, 다음 세션부터 사용 가능 (4차 cycle empirical).

### 카탈로그 사용 흐름

1. Phase 5-2 합성 시 §4 결정 트리가 에이전트 description → capability profile N개 *제안*
2. 본 §3-1 매트릭스에서 profile별 권고 MCP 행 매핑
3. 매핑 후보를 사용자에게 AskUserQuestion으로 confirm (Tier·도구 카운트·default permissions 동봉)
4. 사용자 confirm 후 §5-1 inline `mcpServers:` 패턴으로 합성 — 동시에 §3-1의 default 권한 bucket을 `permissions` 산출물로 박제

### 미완 잔존 (P3/P4 수준 — 본 §3-1 매트릭스 *외부* 영역)

| Tier | MCP | 막힘 사유 | 진척 | 해소 후 매트릭스 행 |
|---|---|---|---|---|
| T1 | `playwright` ✅ probe ✓ / `chrome-devtools` 출처 ✅ + 실 probe 미완 | toolset 필터 형태가 CLI flag — env 키 없음 | ✅ **playwright probe-only empirical 확정** (default 23종 + caps=vision +6종 = 29). **chrome-devtools 부분 진척**: 패키지 출처 verify 확정(Google LLC + ChromeDevTools 공식 org + Apache-2.0 + mcpName, docs 44 카운트 100% 일치) + 🚫 **Node engines 함정**(모든 49 versions이 `node ^20.19 \|\| ^22.12 \|\| >=23` 요구). 실 probe enum은 derived 프로젝트별 §10 dynamic adoption + Node 20.19+ 환경 가용 시점. | playwright → code-test 행에 추가 가능 / chrome-devtools는 출처 ✅ + 실 enum은 *외부 의제* (Node 환경 + 사용자 결정) |
| T1+ | `github` | toolsets enum은 ✓ 확정(19종) — 실 install·도구 풀 측정만 PoC 미완 (PAT 필요) | 📜 docs 박제 — **No npm package** (Docker/Go 바이너리만). install 명령·env·toolset 옵션 박제. | external-integration 행에 *결합형* 별도 박제 (PAT 보유 시점) |
| T1+ | `brave-search` / `tavily` / `exa` | API 키 발급 필요 | 📜 docs 박제 (brave 8 / tavily 4 (도구명 하이픈 첫 케이스) / exa 3 active + 7 deprecated) | web-research 행 확장 (각 키 보유 시점) |
| T2~ | `firecrawl` / `slack` / `postgres` | 유료 또는 민감 외부 시스템 | 📜 docs 박제 (firecrawl 10 active + 4 deprecated browser) — slack/postgres 미완 | research / external-integration 행에 ask-only 부기 |

> **본 매트릭스의 closure 기준:** "PoC enumeration ✓"가 되는 시점에 본 §3-1에 행 추가 — `tier·profile·도구 카운트·default permissions·Layer 결합` 5컬럼 동시 박제. 추가 절차는 §10 5-step + §10 Step 5 (a) 인벤토리 갱신 = §3 행 갱신 + 본 §3-1 매트릭스 동시 갱신.

---

## 4. 매핑 결정 트리

Phase 5에서 에이전트 명세를 받았을 때:

```
1. 에이전트 description에서 capability 추론
   → LLM이 후보 profile 1~N개 *제안*만 (다중 선택 가능)
   → 사용자 confirm 전엔 합성 금지

1-R. (옵션·default ON) MCP Recommendation 엔진 호출
   → mcp-recommendation.md §1 신호 추출 (10 신호 — 범용 6 S1~S6 + 도메인 4 S7~S10)
   → §2 후보 풀 cascade (R0 §3·§3-1 → R1 modelcontextprotocol/servers → R2 외부 큐레이션)
   → §3 3축 점수 (효율성/확장성/정확도) — top-K 표 + 권고 조합
   → R-7 confirm gate → 채택은 §10 5-step로 인계
   ※ 후보 매핑(§4 본 트리)은 *어떤 profile에 어떤 MCP*, 추천(mcp-recommendation.md)은 *후보 간 점수*
   ※ 도메인 신호 S7~S10 매칭 시 capability profile §2-5~§2-8 매핑 — 전용 MCP는 PoC 미완 다수 → T0 5종(filesystem/sqlite/memory/git/sequential-thinking) cross-mapping default, 전용 MCP는 §10 dynamic adoption 진입 제안만

2. 사용자 confirm된 profile들에 대해 후보 MCP 열거
   → `claude mcp list`로 install 여부 체크

3. 분기 (default = inline `mcpServers:` parent 격리):
   a) toolset 필터 지원 MCP (github/playwright 등) → §5-1-b Layer A+B 결합형
      → inline `mcpServers:` 의 env/args에 toolset 필터 박음
      → 에이전트 frontmatter `tools:`엔 필터링된 도구명만 allowlist (Layer C)
      → parent 미적재 + 서버 측 advertise 축소 동시 달성
   b) toolset 미지원 MCP (fetch/sqlite 등) → §5-1-a Layer B 단독
      → 서브에이전트 inline `mcpServers:`로 격리
      → frontmatter `tools:`에 필요 도구만 열거
      → parent 미적재만 (서버 측 도구 풀은 그대로)
   c) MCP 미install (런타임 신규 채택 필요) → §10 dynamic adoption 진입
      → /harness:harness-mcp-adopt 5-step (discover → probe → confirm → install → reflect)
      → 자동 install·자동 키 발급 금지 (§6)
   d) parent 직접 호출 필연성 (드문 케이스) → §5-2 .mcp.json (anti-pattern)
      → §5-2의 3 예외 조건 충족 시에만, enabledMcpjsonServers allowlist 의무

4. 합성 산출물 (default 패치):
   - 에이전트 .md frontmatter `tools:` + inline `mcpServers:` (default)
   - 프로젝트 .claude/settings.json `permissions.allow/ask/deny`
   - 프로젝트 .mcp.json mcpServers (§5-2 예외 조건 시에만)
   - CLAUDE.md 변경 이력 1행 (Phase 7-4)
```

---

## 5. 합성 산출물 템플릿

> ✅ **9차 사이클 RESOLUTION (2026-05-10)** — 8차 EMPIRICAL CAVEAT(§11-2 spawn 시 도구 노출 0건)의 진짜 원인이 *frontmatter `mcpServers:` schema mismatch*임이 확정되었다. 공식 docs(`https://code.claude.com/docs/en/sub-agents` §"Scope MCP servers to a subagent") 발췌 결과 schema는 **list-of-dicts** 형태이며 inline definition에 `type: stdio`(또는 `http`/`sse`/`ws`) 필드가 *필수*. 우리 fixtures는 plain dict + type 누락이었음 → silent skip되어 inline MCP가 subagent에 connect되지 않았다. 9차 사이클에 모든 inline `mcpServers:` 예시를 list-of-dicts + `type:` 형태로 일괄 정정 완료. **재현 검증** (§11-2 spawn 재실행)으로 contradiction 해소를 확정 권장 — derived 프로젝트에서 정정된 fixture 사용 시 도구가 노출되어야 함.

> 📜 **공식 docs verbatim 발췌 (2026-05-10 채록)**
>
> 출처: `https://code.claude.com/docs/en/sub-agents` §"Scope MCP servers to a subagent" (페이지 제목: "Create custom subagents")
> 발췌일: 2026-05-10 (9차 사이클 schema RESOLUTION 시점)
>
> > **개요 (verbatim):**
> >
> > "Use the `mcpServers` field to give a subagent access to MCP servers that aren't available in the main conversation. Inline servers defined here are connected when the subagent starts and disconnected when it finishes. String references share the parent session's connection."
> >
> > "Each entry in the list is either an inline server definition or a string referencing an MCP server already configured in your session"
>
> **공식 YAML 예시 (verbatim):**
>
> ```yaml
> ---
> name: browser-tester
> description: Tests features in a real browser using Playwright
> mcpServers:
>   # Inline definition: scoped to this subagent only
>   - playwright:
>       type: stdio
>       command: npx
>       args: ["-y", "@playwright/mcp@latest"]
>   # Reference by name: reuses an already-configured server
>   - github
> ---
>
> Use the Playwright tools to navigate, screenshot, and interact with pages.
> ```
>
> **schema 정합 (verbatim):**
>
> "Inline definitions use the same schema as `.mcp.json` server entries (`stdio`, `http`, `sse`, `ws`), keyed by the server name."
>
> **의도 ②③ 직접 지원 (verbatim — *parent 미적재 fact 확정 출처*):**
>
> "To keep an MCP server out of the main conversation entirely and avoid its tool descriptions consuming context there, define it inline here rather than in `.mcp.json`. The subagent gets the tools; the parent conversation does not."
>
> **추출 fact (이 4 발췌로 확정):**
> 1. `mcpServers:`는 **list** (각 항목 `-` prefix) — plain dict는 schema mismatch
> 2. 각 list 항목은 (a) **inline definition** = `<server-name>:` key + `type:` (`stdio`/`http`/`sse`/`ws` 중 하나) + 그 외 필드 / (b) **string reference** = 이미 설정된 서버 이름 1개
> 3. inline 정의의 schema는 **`.mcp.json` server entries와 동일**
> 4. inline 패턴이 **parent 미적재**의 1차 채널 — `.mcp.json` 등록 시 parent가 적재됨
>
> **fact 4가 우리의 §5-1-b "Layer A+B 결합" 패턴과 §11-2 측정 의도의 *공식 출처*. 이 발췌가 변경되면(미래 docs 갱신) 본 문서 §5-1 일괄 재검토 트리거 발동.**

### 5-1. 에이전트 frontmatter (Layer B 격리 — *권장*: inline `mcpServers`)

inline로 MCP 서버를 선언하면 parent 대화에 도구 정의가 적재되지 않는다 (공식 docs §"Configure MCP servers"). 반면 `.mcp.json`에 등록하면 parent에 적재되며, `tools:` allowlist는 *subagent 측 가시성만* 통제한다.

> 🆕 **10차 사이클 새 발견 — `tools:` allowlist는 inline 서버 도구를 줄이지 못한다 (P0 P0 재현 검증 empirical)**
>
> P0 재현 검증 결과: frontmatter `tools:`에 `mcp__fetch__get_markdown` *1종만* allowlist했는데도 inline 서버의 **4종 전부** (`get_raw_text`/`get_rendered_html`/`get_markdown`/`get_markdown_summary`) 모두 subagent 도구 풀에 노출됨.
>
> **함의:**
> - `tools:` allowlist는 빌트인 도구·`.mcp.json` 등록 inherit pool은 줄이지만, **inline `mcpServers:` 정의의 도구는 advertise되는 모든 도구가 자동 노출**됨.
> - 따라서 *inline 서버의 도구 카운트 통제*는 두 채널뿐:
>   1. **Layer A** — 서버 측 toolset 필터 (`args:`/`env:`로 `--toolsets=...` / `GITHUB_TOOLSETS=...` 박음, §5-1-b 패턴) — 서버가 advertise 자체를 안 하면 connect 후에도 도구 0종
>   2. **Layer C** — `settings.json permissions.deny`로 호출 시점 차단 (적재는 그대로지만 호출 불가)
> - **§5-1-b Layer A+B 결합형 권고가 더 강해짐** — toolset 필터 지원 MCP는 *반드시* args/env로 advertise 축소. 미지원 MCP(fetch 등)는 `permissions.deny`로 부수 효과 도구 차단 (§5-3 deny 권고 강화).
>
> **합성 가이드 갱신 (10차 cycle):** Phase 5-2 합성 시 `tools:` allowlist는 *의도 표현* (작성자가 어떤 도구를 사용할 의도인지 명시)으로 박제하되, **실제 도구 풀 통제는 Layer A 또는 deny에 의존**. allowlist에 1종만 적었다고 해서 다른 도구가 호출 *불가*가 되는 게 아님 — 여전히 호출 가능하므로 deny가 강제 채널.

#### 5-1-a. Layer B 단독 (toolset 미지원 MCP — fetch/brave-search/sqlite 등)

```yaml
---
name: web-researcher
description: ...
model: opus
tools:
  - WebFetch
  - WebSearch
  - mcp__brave_search__web_search
  - mcp__fetch__fetch
mcpServers:
  - brave-search:
      type: stdio
      command: npx
      args: ["-y", "@modelcontextprotocol/server-brave-search"]
      env: { BRAVE_API_KEY: "${BRAVE_API_KEY}" }
  - fetch:
      type: stdio
      command: npx
      args: ["-y", "@modelcontextprotocol/server-fetch"]
---
```

> **Schema 정합 (9차 사이클 docs 발췌)**: `mcpServers:`는 **list-of-dicts** 형태 (`-`로 시작), 각 항목 안에 `<server-name>:` key + `type: stdio`(또는 `http`/`sse`/`ws`) 필수. dict-style (`-` 없음 + `type:` 누락)은 schema mismatch로 silent skip되어 inline MCP가 적재 안 됨이 §11-2 contradiction의 진짜 원인이었음.

#### 5-1-b. Layer A+B 결합형 (toolset 지원 MCP — github/playwright 등) — *최강 패턴*

inline `mcpServers:`의 `env:` 또는 `args:`에 toolset 필터까지 박으면 (1) 서버가 advertise하는 도구 자체가 줄고 (= **Layer A**, 진짜 토큰 절감) (2) 그 줄어든 풀이 subagent에만 connect됨 (= **Layer B**, parent 미적재) (3) 그 안에서도 `tools:` allowlist로 가시화 (= **Layer C**). **의도 ②③(세션 적재 최소화 + agent-only 접근)을 동시에 달성하는 정공법.**

```yaml
---
name: gh-pr-reviewer
description: GitHub PR 메타데이터 조회 + diff 리뷰 (read-only)
model: opus
tools:
  - Read
  - Grep
  - mcp__github__list_pull_requests
  - mcp__github__get_pull_request
  - mcp__github__get_pull_request_diff
mcpServers:
  - github:
      type: stdio
      command: npx
      args: ["-y", "@modelcontextprotocol/server-github"]
      env:
        GITHUB_PERSONAL_ACCESS_TOKEN: "${GH_TOKEN}"
        GITHUB_TOOLSETS: "pull_requests"   # 19종 default+추가 toolsets 중 PR만 advertise → Layer A 서버측 필터
---
```

**효과 (추정 — §11-3 측정 후 확정):**

| 패턴 | 서버 advertise | subagent 컨텍스트 적재 | parent 컨텍스트 적재 |
|------|---------------|----------------------|------------------|
| `.mcp.json` + 무토글 (anti-pattern) | 19 toolset × 평균 ~5 도구 ≈ **90+** | ≈ 90+ (inherit) | **≈ 90+** ❌ |
| 5-1-a (Layer B만) | (해당 없음 — toolset 미지원 MCP) | allowlist 도구만 | 0 ✓ |
| **5-1-b (Layer A+B 결합)** | **PR toolset만 ≈ 5~7 도구** | 5~7 (allowlist 일치) | **0** ✓ |

**toolset 필터 적용 가능 MCP** (§3 표 기준):

- `github` — `env: GITHUB_TOOLSETS=...` (19종, §3 footnote 카탈로그)
- `playwright` — `args: ["--caps=...", "--isolated", "--browser=chromium"]` 등 CLI flag
- 기타 toolset 미지원 MCP — 5-1-a 패턴 사용

> **선택 가이드:** 합성 대상 MCP가 toolset 필터를 지원하면 **무조건 5-1-b**. 미지원이면 5-1-a. 둘 다 inline `mcpServers:`라서 parent 미적재는 동일.

### 5-1-c. 모델 선택 by agent role (Q2 doctrine, 2026-05-16)

frontmatter `model:` 필드는 *capability profile 단독*이 아니라 *agent role 축*으로 결정한다. 과거 "전 에이전트 `model: opus` 일괄" 박제는 비용 ~7배. 본 doctrine은 합성 시 *역할*에 매핑.

| agent role 축 | recommended `model:` | 근거 |
|---|---|---|
| **synthesis / 추론 합성** (메인 작성자·QA boundary check·orchestrator) | `opus` | 다중 신호 통합 + 정합성 결정 — 추론 깊이 직결 |
| **review / 비판** (code-reviewer·security-auditor·design-reviewer) | `opus` | cross-artifact 비교 + edge case 발굴 |
| **write / 생성** (code-author·schema-migration·doc-author) | `opus` | 산출물 품질 회복 비용 큼 |
| **read-only / 탐색** (`Explore` 타입·log-grepper·codebase-mapper) | `sonnet` | summarization 위주 — 비용 ~7배 ↓, 품질 손실 미미 |
| **read-only / 요약** (web-researcher·doc-summarizer·log-analyst) | `sonnet` | input parsing + 압축 — sonnet 충분 |
| **결정성 검증** (validate script 호출·structure check) | (모델 불요 — script) | LLM 호출 0 |

**Profile × role 매트릭스:**

| capability profile (§2) | 전형 role | recommended |
|---|---|---|
| `code-test` | synthesis (PR 작성) / review (PR 리뷰) | opus |
| `web-research` | read-only 요약 | **sonnet** |
| `external-integration` | write (DB migration / API 통합) | opus |
| `reasoning-aux` | synthesis (단계별 추론) | opus |
| `ml-pipeline` | synthesis (실험 설계) / read-only (결과 요약) | opus / sonnet 혼합 |
| `devops-infra` | write (배포·rollback) | opus |
| `mobile-native` | write (빌드 디버깅) | opus |
| `data-eng` | write (마이그레이션) / read-only (집계 요약) | opus / sonnet 혼합 |

**합성 시 절차:**

1. Phase 5 에이전트 정의 작성 시 본 §5-1-c 표로 role 매핑
2. `model:` 필드 박제 — opus default, read-only 명시 시 sonnet
3. `permissions.deny`에 변경 도구 박제는 동일 (model 선택과 무관)
4. 사용자 명시 override 가능 — "보수적으로 전부 opus로" / "비용 우선 sonnet 최대화"

> **위반 시 검출:** `validate/chain.py` `check_agent_model_field()`가 frontmatter `model:` 누락을 FAIL (P0-2 doctrine 정합). 단 sonnet 매핑이 적절한지의 *판정*은 LLM 영역 — Phase 5.5 self-critique에서 다룬다.

### 5-2. `.mcp.json` — *예외* 케이스 (anti-pattern, parent 적재 불가피한 경우만)

> ⚠️ **합성 default 아님 (의도 ②③ 위반 패턴)** — `.mcp.json` 등록은 parent 컨텍스트에도 도구 정의를 적재해 토큰을 소비하며, agent-only 접근 원칙도 깨진다. **합성 가이드의 default는 §5-1 inline `mcpServers:` 패턴**이며, 본 §5-2는 다음 *세 가지 예외 조건*에 한정해 사용한다:
>
> 1. **parent (메인 세션)가 해당 MCP 도구를 직접 호출**해야 하는 필연성 — 예: 슬래시 커맨드 본문에서 `mcp__<name>__<tool>` 직접 호출, 오케스트레이터가 subagent 위임 없이 직접 사용
> 2. **여러 subagent가 같은 MCP를 공유**해야 하고 inline 중복 비용이 더 큰 경우 (드문 케이스)
> 3. **개발팀 공유 (`-s project`)** — `.mcp.json`을 commit해서 모든 팀원이 동일 MCP 사용 (이 경우도 parent 적재 비용은 감수)
>
> 의심스러우면 §5-1로. 위 3 조건 어느 것도 명확히 충족 안 되면 **inline 패턴이 정답**.

```json
{
  "mcpServers": {
    "github": {
      "command": "...",
      "env": { "GITHUB_TOOLSETS": "issues,pull_requests,actions" }
    }
  }
}
```

> **본 패턴 사용 시 의무 사항:**
> - `enabledMcpjsonServers` allowlist를 명시 — 적재 도구 제한 (§11-3 토글 효과 측정 후 확정)
> - `permissions.deny`로 민감 도구 블랙리스트 동시 박제 (§5-3 + §6.3)
> - parent 컨텍스트의 토큰 비용을 `/harness:harness-mcp-status` §섹션 1·6에서 정기 점검

### 5-3. `.claude/settings.json` (모든 패턴 공통 — Layer C 게이트)

```jsonc
{
  "permissions": {
    "allow": [
      "mcp__fetch__fetch",
      "mcp__brave_search__web_search"
    ],
    "ask": [
      "mcp__github__create_issue"
    ],
    "deny": [
      "mcp__github__delete_repository"
    ]
  },
  "enabledMcpjsonServers": ["github", "brave-search", "fetch"]
}
```

> **`enabledMcpjsonServers` 적용 범위:** 본 키는 **§5-2 (`.mcp.json`) 패턴 사용 시에만 유효**. §5-1 inline `mcpServers:` 패턴은 본 키와 무관 — agent 시작 시 inline 정의로 직접 connect한다. 따라서 default 합성(§5-1)에서는 `enabledMcpjsonServers` 키 자체가 settings.json에 부재해도 무방 (`synthesis_example/settings.json` 박제 예시 참조).
>
> **`permissions.allow/ask/deny`**는 두 패턴 모두에 유효 — *호출 시점*에 적용되는 Layer C 게이트라서 inline·`.mcp.json` 무관하게 작동.

> 🆕 **10차 사이클 deny 권고 강화 — inline 서버 + 부수 효과 도구 (P0 새 발견 함의)**
>
> P0 재현 검증으로 확정: inline `mcpServers:` 정의의 도구는 frontmatter `tools:` allowlist로 *줄지 않는다* (4종 전부 노출). 따라서 부수 효과 도구를 *확실히* 차단하려면 다음 두 채널 중 하나 *반드시* 적용:
>
> 1. **Layer A 서버 측 advertise 필터** — toolset 필터 지원 MCP(github/playwright)는 `args:`/`env:`로 advertise 도구 자체를 줄임 (§5-1-b 패턴). 미지원 MCP는 이 채널 사용 불가.
> 2. **Layer C `permissions.deny`** — toolset 미지원 MCP(fetch/sqlite 등)에서 부수 효과·DDL·write 도구는 *반드시* `deny` 박제. `ask`로 두면 사용자가 prompt에서 실수로 confirm 시 호출됨 — *strict read-only*가 의도라면 `deny`만 안전.
>
> **권고 패턴 (sqlite 같은 read/write 양면 MCP):**
>
> ```jsonc
> {
>   "permissions": {
>     "allow": ["mcp__sqlite__read_query", "mcp__sqlite__list_tables", "mcp__sqlite__describe_table"],
>     "deny":  ["mcp__sqlite__write_query", "mcp__sqlite__create_table", "mcp__sqlite__append_insight"]
>   }
> }
> ```
>
> *왜 `ask`가 아닌 `deny`인가:* `ask`는 prompt 발생 → 사용자 confirm 시 통과. read-only가 *의도된 정책*이라면 confirm 자체를 차단하는 `deny`가 정합. `ask`는 사용자 판단을 매번 묻고 싶은 경계 case에만.
>
> **진단 채널** (11차 사이클 박제): 본 deny 정합 누락은 `/harness:harness-mcp-status` §4의 신규 점검 항목 — agent별 inline `mcpServers:` advertise 도구를 enumerate(§3 인벤토리 또는 §8-3 stdio probe) 후 부수 효과 도구가 `permissions.deny`에 박제되어 있는지 검출. 휴리스틱 prefix(`write_/insert_/update_/delete_/remove_/append_/create_/set_/commit_/push_/exec*/run_`)는 의심 신호일 뿐, 최종 판정은 사용자 도메인 지식. 합성 *후* 정정은 §10-5 inline 정의 갱신 절차 5-step.



---

## 6. 안전 정책

1. **자동 install 금지** — MCP 등록은 항상 사용자 명시 동의. 에이전트 합성은 *제안*만.
2. **`allow` 자동 승급은 T0 한정** — T1·T2는 사용자 confirm 후에만 `allow`로, 기본값은 `ask`.
3. **민감 도구는 `deny`로 명시** — 삭제·force push·외부 메시지 발송 류는 화이트리스트가 아니라 *블랙리스트*로 박제 (`mcp__github__delete_*`, `mcp__slack__post_message` 등).
4. **plugin host 본체 read-only invariant 보존** — Phase 5 합성은 *생성 대상 프로젝트*의 `.claude/`·`.mcp.json`만 건드리며, plugin 본 저장소의 `plugins/harness/`·`plugins/cm-harness/` 류 plugin 정의는 절대 수정하지 않음.
5. **환각 봉쇄** — LLM 제안 후보는 본 문서의 인벤토리 표 또는 `claude mcp list` 결과로 교집합 검증. 표에 없고 인벤토리에도 없는 MCP는 사용자에게 별도 검토 요청.

---

## 7. Phase 5에서의 호출 절차

```
Phase 5-1: 기존 에이전트 정의 작성
Phase 5-2: 도구·MCP 합성 (이 문서 적용 지점)
  a. 에이전트 description 분석 → profile 후보 제안
  b. `claude mcp list` 실행 → 인벤토리 확인
  c. 사용자에게 매핑 confirm (AskUserQuestion)
     - 토글 지원 MCP는 §5-1-b (Layer A+B 결합) 권장
     - 미지원 MCP는 §5-1-a (Layer B 단독)
     - parent 직접 호출 필연성 확인되면 §5-2 (anti-pattern, 예외 조건 명시)
  d. 산출물 합성 (§4의 default 패치 4종)
  e. 변경 사항을 CLAUDE.md 변경 이력에 1줄로 기록
  f. 사후 정합 점검: `/harness:harness-mcp-status` (parent 적재 비용 ⚠️ 항목 확인)
```

---

## 8. 검증 상태

### 8-1. 공식 docs로 확정된 사실 ✓ + empirical 검증 ✓✓

- ✓ **Subagent는 자체 컨텍스트 윈도우를 가짐** (docs §sub-agents intro)
- ✓ **기본은 모든 도구 inherit (MCP 포함)** — `tools:` allowlist를 명시해야 제한됨 (docs §"Configure tools")
- ✓ **`tools:` allowlist에 MCP 도구를 안 적으면 subagent는 MCP 호출 불가**, 단 `.mcp.json` 등록 MCP는 *parent 컨텍스트에는 여전히 적재*됨
- ✓✓ **Inline `mcpServers:` frontmatter — parent 컨텍스트 미적재 (10차 P0 empirical 확정)** — subagent 시작 시 connect, 종료 시 disconnect (docs §"Configure MCP servers": *"Use the mcpServers field to give a subagent access to MCP servers that aren't available in the main conversation"*). **2026-05-10 P0 재현 검증으로 *parent ToolSearch 0 hit + subagent 도구 노출 4종* 양면 통과** — 결과 박제: `fixtures/README.md` "결과 로그" 2026-05-10 §11-2 P0 행.
- ✓ **`disallowedTools`는 inherit pool에서 제거**, `tools` 명시 시엔 그것만 허용 (`disallowedTools` 우선 적용 후 `tools` resolve)
- ✓ **🆕 `tools:` allowlist는 inline 서버 도구를 줄이지 못함 (10차 새 발견)** — inline `mcpServers:`로 connect된 서버는 advertise 도구 *전부* subagent에 노출. allowlist 1종 명시도 4종 전부 노출. inline 서버의 도구 카운트 통제는 Layer A(서버 측 advertise 필터) 또는 Layer C `permissions.deny`로만. → §1 Layer B 셀 [^B2] 박제 + §5-1 새 발견 caveat 참조.

### 8-2. 검증 상태 요약

**✓ Empirical 확정:**
- T0 MCP 7종 install + 도구 enumeration (총 48 도구) — fetch 4 / sequential-thinking 1 / git 12 / sqlite 6 / filesystem 14 / time 2 / memory 9. 모두 JSON-RPC `tools/list` stdio 핑으로 검증, §3 인벤토리 = §3-1 매트릭스 cross-reference.
- T1 playwright probe-only — default 23종 + `--caps=vision` +6종 (좌표 기반 mouse). docs 박제 vs 실 probe 100% 일치.
- T1 chrome-devtools 패키지 출처 — npm Author=Google LLC + Apache-2.0 + GitHub `ChromeDevTools` org 39.2k★ + mcpName `io.github.ChromeDevTools/chrome-devtools-mcp` 3-source 교차 일치 (spoofing 위험 0). docs 박제 44 도구 카운트와 README 100% 일치. 단 engines `node ^20.19 || ^22.12 || >=23` 요구 — Node 18에서 spawn hard fail.
- **§11-2 inline `mcpServers:` parent isolation 양면 검증** — derived 프로젝트의 정정 schema(list-of-dicts + `type: stdio`) fixture spawn 시 [1] subagent 도구 풀에 inline 정의 도구 노출 [2] parent `ToolSearch` 0 hit. inline 정의는 *subagent에만* connect되고 parent 컨텍스트 deferred pool에는 미적재.
- **§11-4 §10 5-step e2e 시연** — derived 프로젝트에서 sqlite MCP 채택 워크플로우 전체 reproducer (Discover→Probe→Confirm→Install→Reflect 4 산출물).
- **mid-session 미전파** — 3개 MCP가 `claude mcp list`에서 `✓ Connected`인 동일 세션의 부모 측 `ToolSearch` "mcp__" → 0 hit + `Explore` 서브에이전트 spawn 후 inherit pool 점검 → 0 hit. MCP 도구 풀은 SessionStart 시 1회 materialize, mid-session add는 다음 세션부터 반영.
- **§6 자동 install 금지 정책 enforcement** — Anthropic auto-mode classifier가 `npx -y <pkg>` 패턴을 *untrusted external code execution outside trusted repo*로 자동 차단 (T0/T1 모두 동일). 사용자 명시 동의 후 통과.
- **mcp gate 키 mode-independent falsification** — `~/.claude.json` 4-key gate(project-scope/user-scope `enabledMcpjsonServers` + `hasTrustDialogAccepted` + `disabledMcpjsonServers` 명시 차단) 모두 deferred pool 적재를 제어하지 못함 (인터랙티브·`-p` 양쪽 empirical). `.mcp.json` 존재만으로 적재.

**📜 Docs 박제 (외부 환경에서 empirical 확정 대기):**
- T1+ MCP 5종 — brave-search 8 / tavily 4 (도구명 하이픈) / exa 3 active + 7 deprecated / firecrawl 10 active + 4 deprecated browser / github toolsets 19 (Docker/Go 바이너리, npm 미지원). 모두 API 키 보유 시점에 [`fixtures/probe_*.js`](./fixtures/) 복사 실행으로 enum 확정 가능.
- T1 chrome-devtools 44 도구 — 실 probe spawn은 Node 20.19+ 환경 + 외부 PowerShell 1회 필요.

**✅ 합성 룰 empirical 확정:**
- inline `mcpServers:` frontmatter schema는 **list-of-dicts + 각 항목에 `type: stdio` 필수** — plain dict는 silent skip (공식 docs `https://code.claude.com/docs/en/sub-agents` 발췌).
- `tools:` allowlist는 inline 서버 도구를 줄이지 못함 — advertise 도구 전체 노출. 부수 효과 도구 차단은 `permissions.deny`로 강제 (`ask` 강등은 부족).
- uvx-기반 MCP는 `command:` 필드에 *uvx 절대경로* 필수, path 인자(`--db-path`/`--repository`)도 *절대경로* 필수 — 상대경로면 health check `✗ Failed to connect`.
- `claude mcp add` 기본 스코프 = `local` (`~/.claude.json` projects.{path}.mcpServers — 다른 프로젝트 누수 없음).

**⚠️ 영구 외부 의제 (plugin host 본 저장소 측정 부적합):**
- Layer A server-side `--toolsets`/env 채널의 *deferred pool* 적재 효과 — advertise 단계 축소는 empirical 확정(playwright caps probe)이나 plugin host 세션 deferred pool 카운트 변화는 derived 프로젝트의 인터랙티브 세션 재시작 측정이 필요.
- T1 chrome-devtools 실 probe enum diff (Node 20.19+ 환경)
- T1+ 5종 실 spawn enum (API 키)
- 모두 외부 도입자의 §10 dynamic adoption 시점에 자연 진행.

### 8-3. 재사용 가능한 검증 기법

**stdio JSON-RPC `tools/list` 직접 핑** — Claude 세션 재시작 없이 MCP 서버의 도구 카탈로그를 empirical하게 enumerate하는 패턴. 임시 Node 스크립트로 (1) `initialize` (2) `notifications/initialized` (3) `tools/list` 3 메시지를 stdio에 write하고 응답을 파싱. 도구 enumeration을 install 없이 일회성 npx로 수행 가능 (probe fixture 11종이 `./fixtures/probe_*.js`).

> ⚠️ **패키지 출처 검증 — probe도 코드 실행이다**
>
> `npx -y <pkg>` / `uvx <pkg>` 둘 다 임의 패키지를 *실행*한다 (probe도 spawn → 코드 실행 surface). install이 아니어서 "가벼움"이 아니며, **install과 동일 위협 모델**이 적용된다 (§6 정책의 install 금지 정신과 일관).
>
> **probe 실행 전 필수 확인:**
> 1. 패키지 이름이 다음 trusted source 중 하나에 있는가? (이름 spoofing 주의 — `mcp-server-fetch` vs `mcp-server-fetch-typescript` 같은 변형 패키지 존재)
>    - 공식 reference: `github.com/modelcontextprotocol/servers` (anthropic/MCP 메인테이너)
>    - 본 §3 인벤토리에 ✓로 박제된 검증 완료 패키지
>    - 사용자가 *명시적으로 trust*한 source (예: 회사 내부 npm 레지스트리)
> 2. trust 안 되는 패키지면 **probe도 실행 금지** — 사용자에게 출처 확인 요청 후 명시 동의 받음
> 3. probe 실행 시에도 *최소 권한* 환경에서 (예: `--no-network` flag 가능 시 적용)
>
> **추가 안전 룰:** §3 인벤토리에 📜 docs 박제만 있고 ✅ empirical 미확정 항목(`tavily`/`exa`/`firecrawl`/`slack`/`postgres`/`brave-search` + chrome-devtools 실 probe enum)은 *§3에 박제는 되었지만 도구 enumeration empirical 검증이 미완*. 이들도 §10 dynamic adoption 진입 시점에 위 1·2 단계 동일 적용.

---

## 9. Plugin subagent 제약

본 `harness` 플러그인이 *생성하는* 에이전트는 **target 프로젝트의 `.claude/agents/`에 직접 작성**되므로 §5-1의 inline `mcpServers:` 패턴이 모두 작동한다. 그러나 만약 누군가 derived 하네스를 plugin 형태로 패키징하면, *plugin 내부* `agents/` 의 subagent에 대해서는 다음 필드가 무시된다 (docs §"Choose the subagent scope"):

- `mcpServers` (보안)
- `permissionMode`
- `hooks`

**이 경우의 우회**: 플러그인 install 후 파일을 `.claude/agents/`에 복사하거나, `.claude/settings.json` `permissions.allow` 패턴으로 세션 단위 허용을 명시. **즉 "MCP-owning subagent" 패턴은 *생성 산출물 위치가 .claude/agents/일 때만 완전 작동*** — 본 문서는 이 가정에 의존한다.

---

## 10. Dynamic MCP Adoption — 프로젝트 진행에 따른 MCP 신규 채택

§3 인벤토리는 정적 스냅샷. 실제 프로젝트는 (a) 도메인이 바뀌거나 (b) phase가 진행되면서 (c) 사용자가 직접 요구하면서 새 MCP가 필요해진다. 이 절차는 **합성 시점이 아닌 *런타임 시점*의 MCP 도입**을 다룬다.

> **적용 경계:** 본 §10 절차는 *derived 프로젝트의 `.claude/`* (= 사용자가 본 메타 스킬로 새로 합성한 프로젝트)를 대상으로 한다. **plugin host 본 저장소 자체는 self-host CM 격리 영역**(운영 중인 경우) — `plugins/harness/`는 read-only invariant이고, host 본 저장소의 `.claude/`는 (운영 시) host self-host CM의 자체 진화 기록자라 §10 채택 대상이 아니다. 단, 본 PoC를 위해 plugin host 프로젝트에서 MCP를 install·검증하는 행위는 *예외적 검증 환경* — `~/.claude.json` `projects.{host}.mcpServers`에 격리되며 derived 프로젝트로 누수되지 않음.

### 10-1. 트리거 신호 (3종)

| # | 신호 | 발생 위치 | 자동 감지 가능? |
|---|------|---------|---------------|
| T1 | **도메인/phase 전환** — baseline 갱신 후 신규 capability 등장 (예: prototype→deploy로 이동하면서 cloud provider integration 필요) | Phase 1·9 / `_workspace/_baseline/*.md` diff | ✅ Phase 9에서 baseline 비교로 감지 |
| T2 | **에이전트 합성 시 인벤토리 미충족** — §4 결정 트리 분기 `c)` 발동 | Phase 5-2 | ✅ `claude mcp list` 결과 vs profile 후보 차집합 |
| T3 | **사용자 명시 요청** — "Slack 알림 보내는 에이전트", "DB 마이그레이션 검증" 등 | 임의 시점 | ❌ 항상 사용자 발화 기반 |

### 10-2. 5-step 채택 절차 (모든 트리거 공통)

```
Step 1. Discover — 후보 식별
  - 1차 출처: 본 문서 §3 인벤토리 (이미 검증된 항목)
  - 2차 출처: 공식 reference (github.com/modelcontextprotocol/servers)
  - 3차 출처: npm 레지스트리 검색 (`mcp-server-*`, `@*/mcp-*`), awesome-mcp-servers 류 큐레이션
  - LLM 환각 방지: 후보 이름은 반드시 위 3개 출처 중 하나에서 *원문 발췌* (URL 동봉)

Step 2. Pre-install probe — install 없이 도구 enumerate (§8-3 기법 재사용)
  - **패키지 출처 검증 (필수, §8-3 안전 룰)**:
      1. trusted source 확인 — github.com/modelcontextprotocol/servers / 본 §3 인벤토리 ✓ 항목 / 사용자 명시 trust 중 하나
      2. 미trust 패키지면 probe 실행 금지 — 사용자에게 출처 확인 요청
      3. probe도 코드 실행이라 install과 동일 위협 모델
  - 일회성 spawn으로 stdio JSON-RPC `initialize` → `notifications/initialized` → `tools/list`
  - 명령 패턴:
      npx -y <pkg>            # npm 기반
      uvx <pkg> [-- <args>]   # Python 기반
      docker run --rm -i <img> # docker 기반
  - 결과: 도구 목록·required params·schema → 사용자 confirm 자료
  - install 영구화 전이라 *config 부작용*은 0 (PATH 등록·~/.claude.json 수정 없음). 단 *코드 실행 부작용*은 0이 아님 — 패키지 코드가 spawn된다.

Step 3. User confirm gate (필수)
  - AskUserQuestion 으로 Tier 분류·필요 키·대안 빌트인 함께 제시
  - 자동 install 금지 (§6) — 사용자 클릭으로만 진행
  - T2 / 키 필요 항목은 키 등록 절차도 함께 제시

Step 4. Install + 적재
  - 스코프 결정: 기본 `local` (이 프로젝트만, `~/.claude.json` projects.{path}.mcpServers)
                  팀 공유 필요 시 `project` (`./.mcp.json` commit 대상)
                  본인 모든 프로젝트엔 `user` (`~/.claude.json` 전역)
  - 명령:
      claude mcp add <name> <command> [args...] [-e KEY=VAL ...] [-s local|project|user]
  - toolset 필터 동시 적용 (Layer A): GitHub `GITHUB_TOOLSETS=...`, Playwright `--caps=...` 등
  - 검증: `claude mcp list` → `✓ Connected` 확인 (실패 시 stderr 확인)
  - **경로 인자는 절대경로 필수** — `--db-path ./...`, `--repository ./...` 등 상대경로는 health check 실행 시 cwd가 `claude` 호출 디렉토리와 다를 수 있어 `✗ Failed to connect` 발생 (8차 사이클 sqlite 시연 empirical). uvx 실행자 자체도 PATH 미통과 시 spawn 실패하므로 절대경로 (`%APPDATA%\Python\Python312\Scripts\uvx.exe`) 권장.

Step 5. Reflect — 4 산출물 동시 패치 (atomicity 분계 주의)
  a. **§3 인벤토리 표** — 새 행 추가 (Tier·카테고리·install 명령·도구 enumeration)
       ⚠️ *atomicity 범위 외* — 본 행은 plugin host 본 저장소(`plugins/harness/skills/harness/references/permission-profiles.md`) 편집이라 외부 install 도입자에게는 *읽기 전용*. PR 또는 plugin host 본 저장소 직접 편집 권한이 있는 도입자만 적용 가능. 권한이 없는 도입자는 본 (a)를 *권고로 보고*만 출력 (변경 이력에 "§3 인벤토리 갱신은 plugin host 본 저장소 PR 필요" 표기).
  b. **에이전트 frontmatter `tools:`** — 영향 받는 .claude/agents/*.md에 `mcp__<name>__<tool>` 추가 (subagent-only면 §5-1 inline `mcpServers:` 권장)
  c. **`.claude/settings.json` `permissions.{allow,ask,deny}`** — Tier 정책 반영 (T0=allow / T1·T2=ask / 민감 도구=deny)
  d. **CLAUDE.md 변경 이력** — Phase 7-4 형식 1행: `| {date} | MCP 채택: {name} | {tier}/{category} | {trigger 사유} |`

  **atomic 적용 범위:** (b)·(c)·(d) 3개만 atomic 묶음. 셋 중 하나라도 실패하면 전부 rollback (§10-4 절차로). (a)는 plugin host 본 저장소 편집이라 별도 트랙 — atomic 그룹에 포함되지 않음. 도입자 권한 부재 시 (a) 권고 메시지만 남기고 (b)(c)(d) atomic 진행.
```

### 10-3. 프로젝트 유형별 채택 패턴 (참고)

| 프로젝트 유형 | phase별 자주 등장하는 MCP |
|--------------|----------------------|
| **Web 서비스** | prototype: `fetch`/`sequential-thinking` → develop: `git`/`playwright`/`chrome-devtools` → integrate: `github`(toolset=`pull_requests,actions`)/`postgres` → ops: `slack`/`linear` |
| **Data 파이프라인** | prototype: `sequential-thinking` → develop: `sqlite`/`filesystem` → integrate: `postgres`/`github` → ops: `slack` |
| **Mobile/Embedded** | develop: `git`/`filesystem` → integrate: `github`(toolset=`actions,issues`) → release: `notion`/`linear` |
| **Research/Analysis** | 전 phase: `fetch`/`brave-search`/`tavily`/`exa` + `sequential-thinking` + 후반 `firecrawl`/`memory` |
| **DevOps/Infra** | develop: `git`/`filesystem` → integrate: `github`(toolset=`actions,security_advisories,dependabot`) → ops: `slack` + custom webhooks |

> 위 매트릭스는 *제안 후보군*일 뿐 강제 아님. 사용자 confirm 게이트는 모든 케이스 동일.

### 10-4. Rollback 절차

기존 채택을 되돌릴 때 (성능 문제·정책 위반·미사용):

```
1. claude mcp remove <name> [-s local|project|user]
2. 영향 받는 에이전트 frontmatter `tools:`에서 해당 mcp__<name>__* 제거
3. .claude/settings.json `permissions.{allow,ask,deny}` 정리
4. §3 인벤토리는 KEEP (PoC 결과는 미래 재채택 자료) — 행 끝에 "(2026-MM-DD rolled back: 사유)" 부기
5. CLAUDE.md 변경 이력 1행: `| {date} | MCP 회수: {name} | {원래 채택일} | {회수 사유} |`
```

### 10-5. inline 정의 갱신 절차 (rollback 아님)

채택은 유지하되 *inline `mcpServers:` 정의*를 수정해야 할 때 (DB 경로 변경 / uvx 경로 환경 차이 / toolset 확장·축소 / 환경 변수 키 이름 변경 등). rollback이 아니므로 §10-4와 별도 절차.

**갱신 트리거 (5종):**

| # | 신호 | 예시 |
|---|------|------|
| U1 | **DB/repo 경로 변경** | `--db-path` / `--repository`이 가리키는 파일 이동 또는 이름 변경 |
| U2 | **uvx/실행자 경로 변경** | OS 마이그레이션 / Python 버전 업그레이드 / Homebrew → user-install |
| U3 | **toolset 필터 조정** | github의 `GITHUB_TOOLSETS=pull_requests` → `pull_requests,issues` (Layer A 확장) |
| U4 | **환경 변수 키 변경** | `GH_TOKEN` → `GITHUB_PERSONAL_ACCESS_TOKEN` (서버 버전 업그레이드 시) |
| U5 | **MCP 서버 버전 pin 변경** | `npx -y @org/mcp-server@1.0` → `@1.2` |

**갱신 5-step:**

```
Step 1. Locate — 영향 받는 inline 정의 위치 식별
  - <derived>/.claude/agents/*.md 모든 파일에서 frontmatter `mcpServers:` 안의 해당 서버 항목 검색
  - 같은 서버를 inline로 가진 agent가 N개면 N개 모두 동기화 대상

Step 2. Pre-update probe (선택, U2/U5에 권고)
  - 새 command/args/env 조합으로 §8-3 stdio 핑 1회 — 도구 enumeration이 *기존 카탈로그와 동일*인지 확인
  - U3(toolset 확장)이면 도구 카운트 변화 사전 확인 가능
  - 출처 검증은 §10 Step 2와 동일 (trusted source 확인)

Step 3. User confirm gate (필수)
  - 변경 전후 diff를 사용자에게 표기 — 특히 U3·U4는 권한 surface 변화라 동의 필수
  - U1/U2 같은 단순 경로 정정도 확인 받음 — 자동 적용 금지

Step 4. Apply — 영향 받는 N개 agent.md 모두 동시 갱신 (atomic)
  - inline `mcpServers:`의 command/args/env 필드 직접 편집
  - **YAML schema 보존**: list-of-dicts + `type: stdio` 형태 유지 (9차 사이클 확정)
  - parent의 `~/.claude.json` projects.{cwd}.mcpServers는 *별도 출처* — `claude mcp remove <name>` + `claude mcp add ...`로 정합 갱신 (inline-only 패턴이면 parent 등록 자체가 없으므로 skip)

Step 5. Reflect — 갱신 사실 박제
  a. CLAUDE.md 변경 이력 1행: `| {date} | MCP 정의 갱신: {server} | inline 정의 (N개 agent) | {U1~U5 사유 + before/after 요약} |`
  b. §3 인벤토리 행은 변경 사항이 *인벤토리 차원*인 경우(예: install 명령 footnote)에만 갱신 — agent별 inline 변경은 인벤토리 무관
  c. **mid-session 미전파 — 다음 세션부터 갱신 정의 적용** (§5-1 cycle 4 사실, install·update 동일)
```

**rollback과의 차이:**

| | rollback (§10-4) | update (§10-5) |
|---|---|---|
| 채택 자체 | 회수 (`claude mcp remove`) | 유지 |
| agent `tools:` allowlist | 해당 `mcp__<name>__*` 제거 | 변경 없음 (U3이면 추가 가능) |
| settings.json permissions | 정리 | 변경 없음 (U3 toolset 확장 시 부분 갱신 가능) |
| CLAUDE.md 변경 이력 | "MCP 회수" | "MCP 정의 갱신" |
| 인벤토리 §3 | "(rolled back)" 부기 | 변경 없음 (footnote만) |

**자동화 한계:** Step 1·2는 자동(grep·probe), Step 3·4는 사용자 게이트. Step 5는 자동 작성 후 사용자 확인.

### 10-6. 자동화 한계와 권장 진입점

| 자동화 가능 | 자동화 금지 (사용자 게이트) |
|------------|------------------------|
| Trigger 감지 (T1·T2) | install 실행 |
| 후보 discovery + URL 발췌 | API 키 발급·등록 |
| Pre-install probe + 도구 enumeration 표시 | `permissions.allow` 등록 (T0 외) |
| 산출물 4종 *제안* | 산출물 4종 *적용* |

**권장 진입점:** Phase 5-2 합성 시 자연 발화 (T2 트리거) → 사용자 confirm → 채택. 별도 슬래시 커맨드(`/harness:harness-add-mcp`)는 *후속 도입 고려 대상*이며 본 문서 작성 시점엔 미구현.

### 10-7. 병렬 세션 운용 패턴 (Pattern A — 단일 writer + 외부 측정)

§10·§11의 측정·채택 작업을 *복수 세션 병렬*로 진행하려는 경우의 운영 doctrine. 13차 사이클 closure 직후 plugin host 운영 결정으로 채택 (host self-host CM 운영 시 doctrine — 외부 install user는 단일 writer 권장만 따르면 됨).

**공유 자원 충돌 분석:**

| 자원 | 동시 쓰기 위험 |
|------|---------------|
| `~/.claude.json` (사용자 단일 파일) | 🔴 `claude mcp add` 동시 호출 시 last-writer-wins (데이터 손실) |
| `<derived>/.claude/settings.json` | 🔴 토글 측정 두 세션이 동시 편집 |
| plugin host `observations.db` (host self-host CM hook, 운영 시) | 🟡 default 모드 lock contention (WAL 미설정) |
| plugin host git index | 🔴 동시 commit 충돌 |
| Claude Code session context | 🟢 각 세션 격리 |

**Pattern A 운영 룰:**

1. **Single-writer 보장**: 단 한 세션만 `claude mcp add`·settings.json 편집·plugin host commit 책임. 다른 세션은 *읽기 전용*.
2. **외부 측정 분리**: P3-(c) 인터랙티브 측정 등 plugin host 외부 환경 의존 작업은 사용자가 별도 vscode.dev 터미널 탭에서 read-only 실행 → 결과 텍스트만 본 세션에 붙여넣기.
3. **`claude -p` one-shot 활용**: plugin host 세션의 Bash 도구로 `claude -p` 다중 호출 가능 (cycle 13 B1·B2 패턴) — 단, 같은 시점 동시 호출은 `~/.claude.json` 캐시 race 위험이라 순차 호출 권장.
4. **사용자 매뉴얼 게이트**: `~/.claude.json` 또는 `<derived>/.claude/settings.json` 쓰기는 auto-mode classifier가 자주 차단 — 사용자 PowerShell 1줄로 명시 게이트 (cycle 13 B2 토글 패턴). **🆕 15차 사이클 강 empirical (2026-05-11 측정 host 환경):** auto-mode classifier는 `~/.claude.json` user-scope 쓰기의 *첫* 호출은 통과시키지만 *후속* 쓰기는 일관 차단함이 양면 확인됨 (B6 측정의 `claude -p` 호출 차단 + 후속 복원 쓰기도 동일 차단). 복원조차 차단되는 상태에서 환경이 "perturbed restored-blocked"로 남을 위험 — *반드시* 매뉴얼 게이트 fixture(`fixtures/verify_11_3_p3b.ps1`) 또는 사용자 외부 PowerShell 1탭으로 측정 진행 + FINAL Set-Gate로 자동 복원 보장. plugin host 세션 Bash로 `~/.claude.json`을 *연속* 편집 시도하면 perturbed 상태 risk.

**기각된 대안:**

- **Pattern B (branch 분리)**: host self-host CM `observations.db`는 branch 격리 안 됨 — CM 데이터 의도적 단일성 보존. 측정용 일시 branch는 가능하나 merge 시점에 `verify_*.md`·`README.md` 충돌 해결 필요.
- **Pattern C (git worktree)**: worktree별로 `_workspace/_memory/observations.db`가 분리되어 CM 누적 가시성 깨짐 (host self-host CM 설계 의도 위반). 측정 외 작업에서는 권장 안 함.

**병렬화 ROI 권장 영역:**

| 영역 | 병렬화 가치 | 권장 패턴 |
|------|-----------|-----------|
| P2 T1+/T2+ probe (API 키별) | 🟢 높음 — 키별 독립 spawn | 키 도착 즉시 단발 probe 1 세션/키, 결과만 본 세션 박제 |
| P3-(c) interactive vs `-p` 비교 | 🟡 중간 — 측정 자체는 1회성 | 사용자 측 별도 터미널 1탭 (~5분), 결과 텍스트 회수 |
| P3-(a) server-side `--toolsets` | 🔴 낮음 — `~/.claude.json` 쓰기 직렬 | 본 세션 직렬 (mcp remove → 다른 env로 mcp add → 측정 → revert) |
| P3-(b) user-scope toggle | 🔴 낮음 — 동일 | 본 세션 직렬 |
| plugin host commit | 🔴 항상 직렬 | 단일 세션 |

---

## 11. 실증 가능한 테스트 레시피 — §8-2 미완 항목 reproducer

§8-2의 미완 항목 각각을 외부 환경(다음 세션·derived 프로젝트·API 키)에서 *복사 실행*만으로 재현할 수 있도록 박제. 각 레시피는 자기 완결적 — 본 문서 외 다른 컨텍스트 불필요.

> **적용 경계:** 본 §11 fixture들은 *외부 검증 환경*(다음 세션·derived 프로젝트·재시작·신규 install) 의존이라 plugin host 세션에서는 mid-session 직접 실행 불가. §11-2의 `mcp-isolation-probe.agent.md`는 특히 *plugin host 본 저장소 밖의 derived 프로젝트* `.claude/agents/`에 복사해야 하며, host 본 저장소 `.claude/agents/`(self-host CM 운영 시)에는 두지 않는다 (격리 위반). §10과 동일한 분계 — 본 fixture 결과는 derived 프로젝트 동작 검증이지 host 자체 동작 검증이 아니다.

### 11-1. `mcp__<server>__<tool>` 노출 패턴 검증 (다음 세션)

▶ **Fixture:** [`./fixtures/verify_11_1.md`](./fixtures/verify_11_1.md) — 다음 세션에서 첫 user 메시지로 입력할 프롬프트 + 결과 캡처 템플릿 + §3 표 갱신 액션 박제 완료.

**목적:** mid-session add된 MCP가 다음 세션 시작 시 실제 어떤 도구명으로 노출되는지 (특히 하이픈을 포함한 서버명 `sequential-thinking`이 `mcp__sequential-thinking__*` 또는 `mcp__sequential_thinking__*` 중 어느 것인지).

**선조건:** 본 세션에서 fetch/sequential-thinking/git 3개 MCP 등록 완료 (`claude mcp list`로 ✓ Connected 확인).

**절차:**
```
1. Claude Code 세션 종료 후 재시작 (같은 plugin host 프로젝트)
2. 첫 user 메시지에 다음 한 줄 입력:
   "ToolSearch query 'mcp__'로 max_results 20 검색하고 발견된 모든 도구의 정확한 이름만 bullet로 나열해줘"
3. 응답에서 `mcp__fetch__*`, `mcp__git__*`, `mcp__sequential-thinking__*` (또는 `_thinking_`) 패턴을 확인
4. 결과를 §3 표 footnote 또는 §11-1 끝에 검증 일자 + 실제 노출 형태로 기록
```

**예상 결과 (확인 필요):**
- fetch 4종: `mcp__fetch__get_raw_text` / `get_rendered_html` / `get_markdown` / `get_markdown_summary`
- git 12종: `mcp__git__git_status` / `git_diff_unstaged` / ... / `git_branch`
- sequential-thinking 1종: `mcp__sequential-thinking__sequentialthinking` (하이픈 보존 가능성 높음)

### 11-2. 서브에이전트 inline `mcpServers:` parent isolation 측정 (derived 프로젝트)

▶ **Fixture:** [`./fixtures/mcp-isolation-probe.agent.md`](./fixtures/mcp-isolation-probe.agent.md) — derived 프로젝트 `.claude/agents/` 위치에 그대로 복사 가능한 ready-to-spawn 에이전트 파일 (frontmatter `tools:` allowlist + inline `mcpServers:` + 출력 파싱 형식까지 박제).

**목적:** §5-1 합성 템플릿이 실제로 (a) subagent에는 도구 노출 (b) parent에는 미적재 — 양쪽 동시 검증.

**선조건:** plugin host 본 저장소 *밖*의 derived 프로젝트 1개 (예: `~/myproject/`). plugin host 본 저장소는 host self-host CM 격리 영역(운영 시)이라 부적합.

**절차:**

1. derived 프로젝트에 다음 파일 생성 — `~/myproject/.claude/agents/mcp-isolation-probe.md`:

   ```yaml
   ---
   name: mcp-isolation-probe
   description: MCP isolation empirical probe — inline mcpServers를 갖고 도구 노출 보고
   model: opus
   tools:
     - Bash
     - mcp__fetch__get_markdown
   mcpServers:
     - fetch:
         type: stdio
         command: npx
         args: ["-y", "mcp-server-fetch-typescript"]
   ---

   당신의 단일 책임: 자신의 도구 풀을 점검하여 다음을 보고한다.
   1. `mcp__fetch__*` 도구가 보이는가? 보인다면 정확한 이름 모두 나열.
   2. 위 목록 외에 inline `mcpServers:`가 합성한 다른 `mcp__*` 도구가 있는가?
   3. ToolSearch가 가용하면 query "mcp__"로 max_results 10 검색 결과 보고.
   ```

2. parent에서 `claude mcp list`로 fetch가 등록되어 있지 않음을 확인 (등록되어 있다면 `claude mcp remove fetch` 선행).

3. parent에서 `Agent` tool로 위 subagent를 spawn:
   ```
   subagent_type: "mcp-isolation-probe"
   prompt: "위 책임 수행"
   ```

4. **검증 1 (도구 노출):** subagent 응답에 `mcp__fetch__get_markdown`이 노출되어야 함.

5. **검증 2 (parent isolation):** subagent 종료 후 parent에서 `ToolSearch` query `"mcp__fetch__"` → 결과 0 (적재 안 됨)이어야 함. 적재되어 있다면 inline 합성이 isolation을 깨고 있음 → §8-1 확정 사실 재검증 필요.

**관찰 포인트:** Agent tool 호출 시 `subagent_type`에 임의 이름(=agent.md의 `name:`)이 전달 가능한지가 핵심 — 안 되면 Task tool 또는 다른 spawn 경로 시도.

### 11-3. `enabledMcpjsonServers` 토글의 효과 측정 (재시작 필요)

▶ **Fixture:** [`./fixtures/verify_11_3.md`](./fixtures/verify_11_3.md) — 7차 사이클 갱신본. 베이스라인(B1) → 토글 OFF → 측정(B2) → 3축 메트릭 분기 판정 → 복원 4단계. **3축 메트릭 = M1(system prompt 토큰) / M2(deferred pool 카운트) / M3(schema fetch 빈도)** — deferred pool 발견 이후 도구 카운트 단독으로는 분기 표지가 되지 않으므로 3축 조합 필수.

**목적:** `.claude/settings.json`의 `enabledMcpjsonServers` 배열에서 서버를 *빼면* — (A) 컨텍스트 적재 자체가 차단되는지 vs (B) 적재는 되고 호출만 차단되는지.

**선조건:** 프로젝트에 `.mcp.json` 또는 `~/.claude.json` projects.{path}.mcpServers로 등록된 MCP 1개 이상.

**절차 (요약 — 자세한 입력 프롬프트는 fixture 참조):**
```
1. 베이스라인 측정: 모든 MCP enabled 상태에서 세션 시작 → 첫 turn에 (M1, M2, M3) 측정 → B1
     M1: system prompt 토큰 — mcp__* 도구 이름·description 적재량 (근사)
     M2: deferred pool 카운트 — ToolSearch "mcp__" 검색 hit 수
     M3: schema fetch 빈도 — typical turn에서 ToolSearch select:<name> 발생 여부
2. 세션 종료 후 .claude/settings.json 편집:
     { "enabledMcpjsonServers": [] }
3. 세션 재시작 → 동일 절차로 B2 측정
4. 분기 (3축 조합):
     B2.M2 == 0  AND  B2.M1 << B1.M1   → 적재 자체 차단 ✓ (Layer A 진짜 효과)
     B2.M2 == 0  AND  B2.M1 ≈ B1.M1     → 표면 카운트만 0 (재측정 권장)
     B2.M2 == B1.M2 AND B2.M1 ≈ B1.M1   → 호출만 차단 (Layer A는 Layer C와 동급)
     0 < B2.M2 < B1.M2                  → 서버별 차등 (분리 측정)
```

**기록처:** §1 표의 Layer 비교 컬럼 "컨텍스트 절감" 셀에 검증 결과 footnote 추가.

### 11-4. §10 Dynamic Adoption e2e 시연 — SQLite 분석 시나리오

▶ **Fixture:** [`./fixtures/probe_sqlite.js`](./fixtures/probe_sqlite.js) — Step 2 pre-install JSON-RPC stdio probe ready-to-run (UVX_PATH/DB_PATH만 환경 맞게 조정). Step 3 user confirm 통과 후 install 직전 도구 enumeration 자동 수행. (mcp_probe_git.js 동일 패턴, target만 sqlite로 교체)

**목적:** §10의 5-step 절차가 실제 흐름으로 동작함을 1회 reproducer로 박제.

**시나리오:** "데이터 분석 에이전트가 로컬 SQLite DB(`./data/app.db`)를 조회해야 하는데 `sqlite` MCP가 인벤토리에 있지만 PoC 미완 상태."

**5-step 실행:**

```
[Step 1 — Discover]
  - 1차: §3 인벤토리에 sqlite 행 존재 (T0, external-integration)
  - 2차: github.com/modelcontextprotocol/servers → mcp-server-sqlite 패키지 확인
  - 후보 확정: mcp-server-sqlite (uvx 실행)

[Step 2 — Pre-install probe (§8-3 기법)]
  Node 임시 스크립트 작성:
    const { spawn } = require('child_process');
    const child = spawn('uvx', ['mcp-server-sqlite', '--db-path', './data/app.db'],
                        { stdio: ['pipe','pipe','pipe'] });
    // initialize → notifications/initialized → tools/list (§8-3 패턴)
  결과: read_query / write_query / list_tables / describe_table / append_insight 등 enumerate
  → install 없이 도구 카탈로그 확보

[Step 3 — User confirm gate]
  AskUserQuestion:
    "sqlite MCP install 진행? Tier=T0 (로컬 DB 파일만), 도구 5종 확인됨,
     키 불필요. install 시 .claude/settings.json에 allow=mcp__sqlite__read_query만 등록 추천 (write/append는 ask)"

[Step 4 — Install + 적재]
  claude mcp add sqlite <uvx-abs-path> -- mcp-server-sqlite --db-path ./data/app.db
  claude mcp list  # ✓ Connected 확인
  스코프: 기본 local (이 프로젝트만) — 팀 공유 필요 시 -s project로 .mcp.json commit

[Step 5 — Reflect (4 산출물)]
  a. permission-profiles.md §3 sqlite 행 갱신 — 도구 enumeration 채움
  b. .claude/agents/data-analyst.md frontmatter `tools:`에:
       mcp__sqlite__read_query, mcp__sqlite__list_tables, mcp__sqlite__describe_table
     (write_query / append_insight는 의도적 제외 — Tier 정책상 ask)
  c. .claude/settings.json:
       "permissions": {
         "allow": ["mcp__sqlite__read_query", "mcp__sqlite__list_tables", "mcp__sqlite__describe_table"],
         "ask":   ["mcp__sqlite__write_query", "mcp__sqlite__append_insight"]
       }
  d. CLAUDE.md 변경 이력 1행:
       | {date} | MCP 채택: sqlite | T0/external-integration | data-analyst가 ./data/app.db 분석 필요 (T2 트리거) |
```

**검증 게이트:** 위 5-step을 *실제 derived 프로젝트*에서 1회 수행하여 (a) ✓ Connected (b) 다음 세션에서 `mcp__sqlite__read_query` 노출 (§11-1과 동일 검증) (c) settings.json `allow`로 read_query 무프롬프트 호출 (d) write_query 호출 시 ask 프롬프트 발생 — 4가지 동시 통과 시 §10 워크플로우 stable로 확정. 미통과 항목은 §10에 footnote로 박제.
