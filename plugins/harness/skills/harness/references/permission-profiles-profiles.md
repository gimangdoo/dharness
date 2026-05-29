# Permission Profiles — Capability Profiles (§2 본문)

> **Read at phase:** Phase 5-2 capability profile 결정 시. `permission-profiles.md` §0 진입 매트릭스가 본 파일로 진입 가이드 박제.
>
> P7 추가 분리(2026-05-28, PA5) — `permission-profiles.md` §2 8 profile 본문 ~7KB를 본 파일로 흡수. main §2는 1줄 redirect.

## §2. Capability Profiles (8종)

각 프로파일은 ① 빌트인 도구 ② MCP 후보 ③ 추천 toolset 필터 ④ 격리 권장 여부를 묶는다.

> **8 profile 분류 doctrine (2026-05-14 P6-11 확장 / 2026-05-27 PB1 축소)**: §2-1~§2-4는 *범용 4종* (PoC 완료 매트릭스 `permission-profiles-inventory.md §3-1` 박제). §2-5~§2-8은 *도메인 4종* (ml-pipeline / devops-infra / mobile-native / data-eng — 2026-05-14 신설). 도메인 4종은 §3-1 매트릭스 행 박제 대상 *외* — 시그널 매핑(`trigger-keyword-catalog.md §1` S7~S10 → §2 profile) + 범용 4 profile 재조합 + 도메인 permission bucket 권고(§3-1 박스)로 합성. 도메인 전용 MCP 격상은 `permission-profiles-dynamic-adoption.md §10` 절차로 cycle별 누적.

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
  - T1+ 후보(PoC 미완) — `github` (모델 PR·릴리즈), `huggingface-mcp`(추정), `wandb-mcp`(추정) — `permission-profiles-dynamic-adoption.md §10` 진입 필요
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
- **회수 doctrine:** `kubectl delete`/`terraform destroy` 등 비가역 명령은 §10-D rollback 절차로 회수 불가 — *사전 dry-run* gate 필수

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
