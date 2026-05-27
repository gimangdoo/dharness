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
| ml-pipeline (2026-05-14) | S7 | filesystem + sqlite + memory + sequential-thinking + git | §3-1 박스 (4 범용 재조합, PB1 위임) |
| devops-infra (2026-05-14) | S8 | git + filesystem + time + sequential-thinking | §3-1 박스 (4 범용 재조합, PB1 위임) |
| mobile-native (2026-05-14) | S9 | filesystem + git + sequential-thinking (+T1 playwright/chrome-devtools) | §3-1 박스 (4 범용 재조합, PB1 위임) |
| data-eng (2026-05-14) | S10 | sqlite + filesystem + git + memory + sequential-thinking | §3-1 박스 (4 범용 재조합, PB1 위임) |

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
> - **§11-3 측정 메트릭 재정의** (6차 사이클 갱신 완료): "도구 카운트 변화"에서 "M1=system prompt 토큰 / M2=deferred pool 카운트 / M3=schema fetch 빈도" 3축 조합으로 — 측정 fixture `verify_11_3.md`은 `archive/full-history` branch의 `fixtures/` 하위에 박제

---

## 2. Capability Profiles (8종)

각 프로파일은 ① 빌트인 도구 ② MCP 후보 ③ 추천 toolset 필터 ④ 격리 권장 여부를 묶는다.

> **8 profile 분류 doctrine (2026-05-14 P6-11 확장 / 2026-05-27 PB1 축소)**: §2-1~§2-4는 *범용 4종* (PoC 완료 매트릭스 §3-1 박제). §2-5~§2-8은 *도메인 4종* (ml-pipeline / devops-infra / mobile-native / data-eng — 2026-05-14 신설). 도메인 4종은 §3-1 매트릭스 행 박제 대상 *외* — 시그널 매핑(`trigger-keyword-catalog.md §1` S7~S10 → §2 profile) + 범용 4 profile 재조합 + 도메인 permission bucket 권고(§3-1 박스)로 합성. 도메인 전용 MCP 격상은 §10 dynamic adoption 절차로 cycle별 누적.

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

## 3. MCP 후보 인벤토리 (분리됨 → `permission-profiles-inventory.md`)

> **P7 분리(2026-05-23):** §3 인벤토리 표 + §3-0 verification_status 정책 + §3-1 검증 완료 T0 매트릭스 (~150 LOC) → [`permission-profiles-inventory.md`](./permission-profiles-inventory.md) 단일 출처. **본 main 본문엔 잔존하지 않음** — Phase 5-2 합성 시 inventory.md를 read 후 본 §4 결정 트리로 이동.

본 sentinel 다음에 §3 본문(verification_status 표 + MCP enumeration 표 + matrix)이 있었으나 P7 분리로 전부 inventory.md로 이양됐다. 사용 절차:

1. Phase 5-2 진입 → `permission-profiles-inventory.md` read (MCP 후보 enumerate + verification_status 분류 + capability profile × T0 매트릭스)
2. 본 §4 결정 트리로 돌아와 profile 매핑
3. `permission-profiles-synthesis.md` §5-1 진입 → inline `mcpServers:` 작성


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
   - _workspace/_baseline/changelog.md 변경 이력 1행 (Phase 7-4)
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

### 5-1. 에이전트 frontmatter (분리됨 → `permission-profiles-synthesis.md`)

> **P7 분리(2026-05-23):** §5-1 (Layer B 단독) + §5-1-a + §5-1-b (Layer A+B 결합) + §5-1-c (모델 by role, Q2 doctrine) ~120 LOC → [`permission-profiles-synthesis.md`](./permission-profiles-synthesis.md) 단일 출처. Phase 5-2 에이전트 합성 시 본 §5 진입 *전에* synthesis.md read.

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
  e. 변경 사항을 _workspace/_baseline/changelog.md 변경 이력에 1줄로 기록
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

## 10. Dynamic MCP Adoption (분리됨 → `permission-profiles-dynamic-adoption.md`)

> **P7 분리(2026-05-23):** §10 + §10-1~§10-7 (트리거 신호 / 5-step 채택 절차 / 프로젝트 유형별 패턴 / Rollback / inline update / 자동화 한계 / 병렬 세션 운용) ~190 LOC → [`permission-profiles-dynamic-adoption.md`](./permission-profiles-dynamic-adoption.md) 단일 출처. `/harness:harness-mcp-adopt` 슬래시 커맨드 본문에서 호출.

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
  d. _workspace/_baseline/changelog.md 변경 이력 1행:
       | {date} | MCP 채택: sqlite | T0/external-integration | data-analyst가 ./data/app.db 분석 필요 (T2 트리거) |
```

**검증 게이트:** 위 5-step을 *실제 derived 프로젝트*에서 1회 수행하여 (a) ✓ Connected (b) 다음 세션에서 `mcp__sqlite__read_query` 노출 (§11-1과 동일 검증) (c) settings.json `allow`로 read_query 무프롬프트 호출 (d) write_query 호출 시 ask 프롬프트 발생 — 4가지 동시 통과 시 §10 워크플로우 stable로 확정. 미통과 항목은 §10에 footnote로 박제.
