# Trigger Keyword Catalog — 10 Signal × Keyword Catalog

> **Read at phase:** Phase 5 (에이전트 description 작성) + Phase 5-2 (MCP·도구 자동 할당 시 signal 추출). agent description의 *자연어 트리거* 단어 선택 시 단일 출처. mcp-recommendation.md §1과 동반 read.

> **목적**: capability signal S1~S10 키워드 catalog 단일 출처. 4 위치에 분산된 키워드 정의(mcp-recommendation §1, permission-profiles §2, agent description prose, qa-agent-guide §6 도메인 catalog) 충돌·drift 방지. 본 문서는 *catalog*이지 *doctrine*이 아님 — 매칭 룰·점수화는 mcp-recommendation.md, 매핑은 permission-profiles.md.

---

## 1. 전체 카탈로그 (10 signal)

| Signal | Profile (§2) | Korean 키워드 | English 키워드 | 매칭 강도 |
|---|---|---|---|---|
| **S1 read-heavy** | web-research / reasoning-aux | 분석, 검토, 리서치, 요약, 조회, 검색, 탐색, 탐사, 진단, 감사, 점검 | analyze, review, research, summarize, query, search, explore, audit, inspect, investigate | strong |
| **S2 write-heavy** | code-test / external-integration | 생성, 작성, 편집, 수정, 커밋, 마이그레이션, 배포, 적용, 등록, 갱신 | create, write, edit, modify, commit, migrate, deploy, apply, register, update | strong |
| **S3 web-egress** | web-research | 웹, 외부 API, 스크래핑, 크롤링, 검색 엔진, fetch, 페이지, URL | web, external API, scrape, crawl, search engine, fetch, page, URL, HTTP | strong |
| **S4 db-egress** | external-integration / data-eng | DB, 데이터베이스, 쿼리, 스키마, 마이그레이션, 테이블, 인덱스, JOIN | database, query, schema, migration, table, index, JOIN, SQL | strong |
| **S5 ci/git** | code-test / external-integration | PR, issue, 리뷰, CI, CD, 릴리즈, 브랜치, 머지, 커밋 그래프, 워크플로우 | PR, issue, review, CI, CD, release, branch, merge, pipeline, workflow | strong |
| **S6 reasoning-aux** | reasoning-aux | 단계별, 추론, 사고 과정, 장기 메모리, 시간, 타임존, KG, 지식 그래프 | step-by-step, reasoning, chain-of-thought, long-term memory, time, timezone, knowledge graph | medium |
| **S7 ml-aux** (2026-05-14) | ml-pipeline | 모델, 학습, 평가, 하이퍼파라미터, 실험 추적, inference, feature, dataset, 라벨, 분류, 회귀, 추천 | model, training, evaluation, hyperparameter, experiment tracking, inference, feature, dataset, label, classification, regression, recommendation | strong |
| **S8 infra** (2026-05-14) | devops-infra | 배포, CI/CD, 인프라, 모니터링, Kubernetes, k8s, Terraform, SRE, oncall, 롤백, helm, IaC, observability | deploy, CI/CD, infrastructure, monitoring, Kubernetes, k8s, Terraform, SRE, oncall, rollback, helm, IaC, observability | strong |
| **S9 mobile** (2026-05-14) | mobile-native | iOS, Android, Swift, Kotlin, Flutter, React Native, Xcode, Gradle, emulator, build, IPA, APK, 모바일 | iOS, Android, Swift, Kotlin, Flutter, React Native, Xcode, Gradle, emulator, build, IPA, APK, mobile | strong |
| **S10 data-eng** (2026-05-14) | data-eng | ETL, ELT, data pipeline, Airflow, dbt, Spark, 스키마 변환, data warehouse, data lake, ingestion, lineage, DAG | ETL, ELT, data pipeline, Airflow, dbt, Spark, schema transform, data warehouse, data lake, ingestion, lineage, DAG | strong |

> **매칭 강도**: strong = description에 1회 등장만으로 trigger. medium = 2회+ 또는 인접 키워드 동시 매칭 시 trigger. weak = 본 catalog 미보유 (현 10 signal 모두 strong/medium만).

---

## 2. 복합 매칭 패턴

대부분 에이전트 description은 *복수 signal* 동시 매칭. 전형 조합:

| 패턴 조합 | 매칭 signal | 전형 에이전트 | profile 합성 |
|---|---|---|---|
| **web-researcher** | S1 + S3 + S6 | "외부 자료 분석 + 지식 누적 + 단계별 추론" | web-research + reasoning-aux |
| **code-reviewer** | S1 + S5 + S2 | "PR 리뷰 + 코드 분석 + 수정 제안" | code-test |
| **db-migrator** | S2 + S4 + S5 | "스키마 마이그레이션 + 커밋" | external-integration + code-test |
| **ml-experimenter** | S7 + S6 + S2 | "모델 학습 + 실험 추적 + 결과 작성" | ml-pipeline + reasoning-aux |
| **infra-deployer** | S8 + S2 + S5 | "배포 + 인프라 적용 + CI 통합" | devops-infra + code-test |
| **mobile-tester** | S9 + S1 + S5 | "iOS/Android 빌드 검토 + CI" | mobile-native + code-test |
| **data-engineer** | S10 + S4 + S2 | "ETL 파이프라인 + DB + 적용" | data-eng + external-integration |
| **ml-data-engineer** ⚠️ | S7 + S10 | "ML feature pipeline + 데이터 변환" | ml-pipeline + data-eng — **책임 과대 의심**: Phase 5.5 self-critique에서 `harness-split` 권고 (SKILL.md §Phase 5.5) |

---

## 3. should-trigger vs should-NOT-trigger 예시

### 3-1. S7 ml-aux

✅ should trigger:
- "이미지 분류 모델 학습 결과 분석" (모델 + 학습 + 분석 → S7 strong + S1)
- "추천 시스템 hyperparameter tuning 자동화" (추천 + hyperparameter → S7 strong)
- "feature engineering pipeline 검증" (feature + pipeline → S7 medium + S10)

❌ should NOT trigger:
- "모델 회의록 작성" — "모델"이 ML 모델이 아닌 도메인 *modeling* 의미. 인접 키워드(학습/inference/dataset) 부재 → S7 미매칭
- "data analysis dashboard" — S1 매칭이나 S7 키워드 0 → S7 미매칭 (대신 S1 + S10)

### 3-2. S8 infra

✅ should trigger:
- "Kubernetes manifest 배포 자동화" (Kubernetes + 배포 → S8 strong)
- "Terraform drift 감지 + alert" (Terraform → S8 strong)
- "SRE oncall runbook 작성" (SRE + oncall → S8 strong + S2)

❌ should NOT trigger:
- "프로젝트 인프라 설계 문서" — "인프라" 1회, 인접 키워드(배포/Kubernetes/Terraform) 부재 → S8 weak (medium 미달)
- "CI green 유지" — S5 매칭, infra 단어 부재 → S5 only

### 3-3. S9 mobile

✅ should trigger:
- "iOS 빌드 실패 디버깅" (iOS + 빌드 → S9 strong)
- "Android APK 서명 자동화" (Android + APK → S9 strong + S2)

❌ should NOT trigger:
- "mobile-friendly UI" — "mobile" 1회, 인접 키워드 부재 → S9 weak. 대신 frontend UI signal (현 catalog 외부)
- "모바일 사용자 분석" — "모바일" 1회, build/native 키워드 부재 → S9 미매칭, S1 + S10 매칭

### 3-4. S10 data-eng

✅ should trigger:
- "Airflow DAG 마이그레이션" (Airflow + DAG → S10 strong + S2)
- "dbt model 작성" (dbt + model → S10 + S7? — "model" 도메인 모호: S10 우세 — dbt 컨텍스트)

❌ should NOT trigger:
- "data scientist 워크플로우" — "data" 1회, ETL/Airflow/Spark 키워드 부재 → S10 미매칭. 대신 S7 매칭 (ML 컨텍스트)

---

## 4. cross-language 정합 룰 (Korean ↔ English)

대부분 키워드는 *원어 그대로* 사용 (technical term 보존). 단 일부는 의미상 동등:

| Korean | English (등가) | 매칭 시 동등 처리 |
|---|---|---|
| 분석 | analyze / analysis | ✅ |
| 리서치 | research | ✅ |
| 배포 | deploy / deployment | ✅ |
| 마이그레이션 | migrate / migration | ✅ |
| 데이터 파이프라인 | data pipeline | ✅ |
| 추론 | reasoning / inference | ⚠️ inference는 S7(ML), reasoning은 S6 — context로 disambiguate |
| 모델 | model | ⚠️ ML 모델 vs 도메인 모델링 — 인접 키워드로 disambiguate |
| 모바일 | mobile | ✅ |
| 인프라 | infrastructure | ✅ |

> **disambiguation 룰** (LLM 추론):
> - "모델 학습" → S7 (training이 인접)
> - "도메인 모델 설계" → S6 또는 외부 (modeling은 reasoning-aux 또는 catalog 외부)
> - "추론 모델" → S7 (inference model)
> - "단계별 추론" → S6 (step-by-step reasoning)
> - "Knowledge Graph 추론" → S6 (KG-based)

---

## 5. catalog 확장 doctrine

새 도메인 발견 시 본 catalog 행 추가 절차:

1. **신규 signal Sn 정의** — capability profile §2-N에 대응 (신규 profile 신설 또는 기존 profile 분기)
2. **키워드 set 박제** — Korean + English 양 언어 + 매칭 강도 (strong/medium/weak)
3. **should/NOT 예시 4건 박제** (§3 패턴)
4. **mcp-recommendation.md §1 신호 표 갱신**
5. **permission-profiles.md §2-N 신설 + §3-1 매트릭스 행 추가**
6. **qa-agent-guide.md §6 도메인 카탈로그 신설** (해당 도메인 경계면 패턴 박제)

> **트리거**: derived 프로젝트에서 기존 10 signal로 분류 안 되는 에이전트 description 발화 ≥3건 누적 시 신규 signal 의제 (Phase 9 evolve 또는 Phase 10 adapt).

---

## 6. cross-reference

- 매칭 룰·점수화 → `mcp-recommendation.md` §1·§3
- profile 매핑 → `permission-profiles.md` §2·§3-1·§4
- 도메인 경계면 catalog → `qa-agent-guide.md` §6
- 합성 시 자연어 트리거 doctrine → `skill-writing-guide.md` (description 작성 룰)
