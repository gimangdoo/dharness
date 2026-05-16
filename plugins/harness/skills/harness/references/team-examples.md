# Agent Team Examples

> **Read at phase:** Phase 4 (팀 패턴 선택 시 사례 참조) + Phase 5 (에이전트 정의 시 예시 발췌).

---

## 예시 1: 리서치 팀 (에이전트 팀 모드)

### 팀 아키텍처: 팬아웃/팬인
### 실행 모드: 에이전트 팀

```
[리더/오케스트레이터]
    ├── TeamCreate(research-team)
    ├── TaskCreate(4개 조사 작업)
    ├── 팀원들이 자체 조율 (SendMessage)
    ├── 결과 수집 (Read)
    └── 종합 보고서 생성
```

### 에이전트 구성

| 팀원 | 에이전트 타입 | 역할 | 출력 |
|------|-------------|------|------|
| official-researcher | general-purpose | 공식 문서/블로그 | research_official.md |
| media-researcher | general-purpose | 미디어/투자 | research_media.md |
| community-researcher | general-purpose | 커뮤니티/SNS | research_community.md |
| background-researcher | general-purpose | 배경/경쟁/학술 | research_background.md |
| (리더 = 오케스트레이터) | — | 통합 보고서 | 종합보고서.md |

> 리서치 에이전트는 `general-purpose` 빌트인 타입을 사용하되, 반드시 `.claude/agents/{name}.md` 파일로 정의한다. 파일에는 역할·조사 범위·팀 통신 프로토콜을 명시하여 재사용성과 협업 품질을 보장한다.

### 오케스트레이터 워크플로우 (에이전트 팀)

```
Phase 1: 준비
  - 사용자 입력 분석 (주제, 조사 모드 파악)
  - _workspace/ 생성

Phase 2: 팀 구성
  - TeamCreate(team_name: "research-team", members: [
      { name: "official", prompt: "공식 채널 조사..." },
      { name: "media", prompt: "미디어/투자 동향 조사..." },
      { name: "community", prompt: "커뮤니티 반응 조사..." },
      { name: "background", prompt: "배경/경쟁 환경 조사..." }
    ])
  - TaskCreate(tasks: [
      { title: "공식 채널 조사", assignee: "official" },
      { title: "미디어 동향 조사", assignee: "media" },
      { title: "커뮤니티 반응 조사", assignee: "community" },
      { title: "배경 환경 조사", assignee: "background" }
    ])

Phase 3: 조사 수행
  - 4명의 팀원이 독립적으로 조사
  - 흥미로운 발견이 있으면 팀원 간 SendMessage로 공유
    (예: media가 발견한 투자 뉴스를 background에게 전달)
  - 상충 정보 발견 시 팀원 간 직접 토론
  - 각 팀원은 완료 시 파일 저장 + 리더에게 알림

Phase 4: 통합
  - 리더가 4개 산출물 Read
  - 종합 보고서 생성
  - 상충 정보는 출처 병기

Phase 5: 정리
  - 팀원들 종료 요청
  - 팀 정리
  - _workspace/ 보존 (사후 검증·감사 추적용)
```

### 팀 통신 패턴

```
official ──SendMessage──→ background  (관련 공식 발표 공유)
media ────SendMessage──→ background  (투자/인수 정보 공유)
community ─SendMessage──→ media      (커뮤니티 반응 중 미디어 관련 정보)
모든 팀원 ──TaskUpdate──→ 공유 작업 목록  (진행률 업데이트)
리더 ←───── 유휴 알림 ──── 완료된 팀원   (자동)
```

---

## 예시 2: SF 소설 집필 팀 (에이전트 팀 모드)

### 팀 아키텍처: 파이프라인 + 팬아웃
### 실행 모드: 에이전트 팀

```
Phase 1 (병렬 — 에이전트 팀): worldbuilder + character-designer + plot-architect
  → 서로 SendMessage로 일관성 조율
Phase 2 (순차): prose-stylist (집필)
Phase 3 (병렬 — 에이전트 팀): science-consultant + continuity-manager (리뷰)
  → 서로 SendMessage로 발견 공유
Phase 4 (순차): prose-stylist (리뷰 반영 수정)
```

### 에이전트 구성

| 팀원 | 에이전트 타입 | 역할 | 스킬 |
|------|-------------|------|------|
| worldbuilder | 커스텀 | 세계관 구축 | world-setting |
| character-designer | 커스텀 | 캐릭터 설계 | character-profile |
| plot-architect | 커스텀 | 플롯 구조 | outline |
| prose-stylist | 커스텀 | 문체 편집 + 집필 | write-scene, review-chapter |
| science-consultant | 커스텀 | 과학 검증 | science-check |
| continuity-manager | 커스텀 | 일관성 검증 | consistency-check |

### 에이전트 파일 전문 예시: `worldbuilder.md`

```markdown
---
name: worldbuilder
description: "SF 소설의 세계관을 구축하는 전문가. 물리 법칙, 사회 구조, 기술 수준, 역사를 설계한다."
---

# Worldbuilder — SF 세계관 설계 전문가

당신은 SF 소설의 세계관 설계 전문가입니다. 과학적 사실에 기반하되 상상력을 확장하여, 이야기가 펼쳐질 세계의 물리적·사회적·기술적 토대를 구축합니다.

## 핵심 역할
1. 세계의 물리 법칙과 기술 수준 정의
2. 사회 구조, 정치 체계, 경제 시스템 설계
3. 역사적 맥락과 현재 갈등 구조 수립
4. 장소별 환경과 분위기 묘사

## 작업 원칙
- 내적 일관성 최우선 — 설정 간 모순이 없어야 한다
- "만약 이 기술이 있다면?" 연쇄 질문으로 세계의 파급 효과를 추론
- 이야기에 봉사하는 세계관 — 플롯을 방해하는 과도한 설정은 지양

## 입력/출력 프로토콜
- 입력: 사용자의 세계관 컨셉, 장르 요구사항
- 출력: `_workspace/01_worldbuilder_setting.md`
- 형식: 마크다운. 섹션별 (물리/사회/기술/역사/장소)

## 팀 통신 프로토콜
- character-designer에게: 사회 구조, 계급 시스템, 직업군 정보 SendMessage
- plot-architect에게: 세계의 주요 갈등 구조, 위기 요소 SendMessage
- science-consultant로부터: 과학적 오류 피드백 수신 → 설정 수정
- 세계관 변경 시 관련 팀원 전체에 브로드캐스트

## 에러 핸들링
- 컨셉이 모호하면 3가지 방향을 제안하고 선택 요청
- 과학적 오류 발견 시 대안을 함께 제시

## 협업
- character-designer에게 사회 구조 정보 제공
- plot-architect에게 갈등 구조 정보 제공
- science-consultant의 피드백을 반영하여 설정 수정
```

### 팀 워크플로우 상세

```
Phase 1: TeamCreate(team_name: "novel-team", members: [worldbuilder, character-designer, plot-architect])
         TaskCreate([세계관 구축, 캐릭터 설계, 플롯 구조])
         → 팀원들이 자체 조율하며 병렬 작업
         → worldbuilder가 사회 구조 완성 시 character-designer에게 SendMessage
         → character-designer가 주인공 설정 시 plot-architect에게 SendMessage

Phase 2: Phase 1 팀 정리 → prose-stylist를 서브 에이전트로 호출 (단독 집필이므로 팀 불필요)
         prose-stylist가 _workspace/의 3개 산출물을 Read하여 집필
         → 결과를 _workspace/02_prose_draft.md에 저장

Phase 3: 새 팀 생성 — TeamCreate(team_name: "review-team", members: [science-consultant, continuity-manager])
         (세션당 한 팀만 활성이지만, Phase 1 팀을 정리했으므로 새 팀 생성 가능)
         → 두 리뷰어가 draft를 검토, 서로 발견을 공유
         → science-consultant가 물리 오류 발견 시 continuity-manager에게도 알림
         → 리뷰 완료 후 팀 정리

Phase 4: prose-stylist를 서브 에이전트로 호출, 리뷰 결과 반영하여 최종 수정
```

---

## 예시 3: 웹툰 제작 팀 (서브 에이전트 모드)

### 팀 아키텍처: 생성-검증
### 실행 모드: 서브 에이전트

> 생성-검증 패턴에서 에이전트가 2개뿐이고, 통신보다는 결과 전달이 핵심이므로 서브 에이전트가 적합.

```
Phase 1: Agent(webtoon-artist) → 패널 생성
Phase 2: Agent(webtoon-reviewer) → 검수
Phase 3: Agent(webtoon-artist) → 문제 패널 재생성 (최대 2회)
```

### 에이전트 구성

| 에이전트 | subagent_type | 역할 | 스킬 |
|---------|--------------|------|------|
| webtoon-artist | 커스텀 | 패널 이미지 생성 | generate-webtoon |
| webtoon-reviewer | 커스텀 | 품질 검수 | review-webtoon, fix-webtoon-panel |

### 에이전트 파일 전문 예시: `webtoon-reviewer.md`

```markdown
---
name: webtoon-reviewer
description: "웹툰 패널의 품질을 검수하는 전문가. 구도, 캐릭터 일관성, 텍스트 가독성, 연출을 평가한다."
---

# Webtoon Reviewer — 웹툰 품질 검수 전문가

당신은 웹툰 패널의 품질을 검수하는 전문가입니다. 시각적 완성도, 스토리 전달력, 캐릭터 일관성을 기준으로 패널을 평가합니다.

## 핵심 역할
1. 각 패널의 구도와 시각적 완성도 평가
2. 캐릭터 외형의 패널 간 일관성 검증
3. 말풍선 텍스트의 가독성과 배치 평가
4. 전체 에피소드의 연출 흐름과 페이싱 검토

## 작업 원칙
- PASS/FIX/REDO 3단계로 명확히 판정
- FIX는 부분 수정으로 해결 가능한 경우, REDO는 전면 재생성 필요
- 주관적 취향이 아닌 객관적 기준(일관성, 가독성, 구도)으로 판단

## 입력/출력 프로토콜
- 입력: `_workspace/panels/` 디렉토리의 패널 이미지들
- 출력: `_workspace/review_report.md`
- 형식:
  ```
  ## Panel {N}
  - 판정: PASS | FIX | REDO
  - 사유: [구체적 이유]
  - 수정 지시: [FIX/REDO인 경우 구체적 수정 방향]
  ```

## 에러 핸들링
- 이미지 로드 실패 시 해당 패널을 REDO로 판정
- 2회 재생성 후에도 REDO인 패널은 경고와 함께 PASS 처리

## 협업
- webtoon-artist에게 수정 지시서 전달 (결과 파일 기반)
- 재생성된 패널을 다시 검수 (최대 2회 루프)
```

### 에러 핸들링

```
재시도 정책:
- REDO 판정 패널 → artist에게 재생성 요청 (구체적 수정 지시 포함)
- 최대 2회 루프 후 강제 PASS
- 전체 패널의 50% 이상이 REDO면 사용자에게 프롬프트 수정 제안
```

---

## 예시 4: 코드 리뷰 팀 (에이전트 팀 모드)

### 팀 아키텍처: 팬아웃/팬인 + 토론
### 실행 모드: 에이전트 팀

> 코드 리뷰는 에이전트 팀이 빛나는 대표적 사례. 서로 다른 관점의 리뷰어들이 발견을 공유하고 도전하면서 더 깊은 리뷰가 가능.

```
[리더] → TeamCreate(review-team)
    ├── security-reviewer: 보안 취약점 점검
    ├── performance-reviewer: 성능 영향 분석
    └── test-reviewer: 테스트 커버리지 검증
    → 리뷰어들이 서로 발견 공유 (SendMessage)
    → 리더가 결과 종합
```

### 팀 통신 패턴

```
security ──SendMessage──→ performance  ("이 SQL 쿼리 주입 가능, 성능 측면에서도 확인 필요")
performance ──SendMessage──→ test      ("N+1 쿼리 발견, 관련 테스트 있는지 확인 부탁")
test ────SendMessage──→ security      ("인증 모듈 테스트 없음, 보안 관점에서 우선순위 의견?")
```

핵심: 리뷰어들이 **리더를 거치지 않고** 직접 소통하여 교차 영역 이슈를 빠르게 포착.

---

## 예시 5: 감독자 패턴 — 코드 마이그레이션 팀 (에이전트 팀 모드)

### 팀 아키텍처: 감독자
### 실행 모드: 에이전트 팀

```
[supervisor/리더] → 파일 목록 분석 → 배치 할당
    ├→ [migrator-1] (batch A)
    ├→ [migrator-2] (batch B)
    └→ [migrator-3] (batch C)
    ← TaskUpdate 수신 → 추가 배치 할당 또는 재할당
```

### 에이전트 구성

| 팀원 | 역할 |
|------|------|
| (리더 = migration-supervisor) | 파일 분석, 배치 분배, 진행 관리 |
| migrator-1~3 | 할당된 파일 배치를 마이그레이션 |

### 감독자의 동적 분배 로직 (에이전트 팀 활용)

```
1. 전체 대상 파일 목록 수집
2. 복잡도 추정 (파일 크기, import 수, 의존성)
3. TaskCreate로 파일 배치를 작업으로 등록 (의존성 포함)
4. 팀원들이 자체적으로 작업 요청 (claim)
5. 팀원이 TaskUpdate로 완료 보고 시:
   - 성공 → 다음 작업 자동 요청
   - 실패 → 리더가 SendMessage로 원인 확인 → 재할당 또는 다른 팀원에게 배정
6. 모든 작업 완료 → 리더가 통합 테스트 실행
```

팬아웃과의 차이: 작업이 사전 고정이 아니라 **런타임에 동적으로 할당**된다. 공유 작업 목록의 자체 요청(claim) 기능이 감독자 패턴과 자연스럽게 매칭.

---

## 예시 6: ML 학습-배포 파이프라인 팀 (S7 — `ml-pipeline` profile)

### 팀 아키텍처: 파이프라인 + 검증 루프
### 실행 모드: 에이전트 팀

> ML 학습은 *데이터 → 학습 → 평가 → 배포* 순차 파이프라인이지만, train-serve skew·drift·metric 정합 등 경계면 검증을 위해 검증자 에이전트가 단계 사이마다 끼어든다. 에이전트 팀 모드로 검증자가 단계 산출물을 즉시 SendMessage로 호출.

```
Phase 1 (순차): data-curator → 데이터 추출·feature pipeline 구성
Phase 2 (병렬): trainer (학습) ‖ eval-designer (평가 지표·split 설계)
              → 서로 SendMessage (label 분포 ↔ metric 선택)
Phase 3 (검증): ml-qa → train-serve skew + data drift 점검
Phase 4 (순차): deployer → model artifact 등록 + inference API wiring
Phase 5 (검증): ml-qa → input shape ↔ inference API + offline-online metric 정합
```

### 에이전트 구성

| 팀원 | subagent_type | 역할 | 스킬 | 사용 MCP (예시) |
|------|-------------|------|------|----------------|
| data-curator | general-purpose | dataset 추출·feature pipeline·schema 박제 | extract-features, profile-data | filesystem, sequential-thinking |
| trainer | general-purpose | 학습 코드·hyperparam·MLflow run 박제 | train-model, log-experiment | filesystem, fetch |
| eval-designer | general-purpose | label 분포 분석·metric 선택·split 설계 | analyze-labels, design-eval | filesystem, sequential-thinking |
| ml-qa | general-purpose | train-serve skew·drift·shape·metric 정합 검증 (qa-agent-guide §6-1 발췌) | check-skew, check-drift, check-shape | filesystem, fetch, sequential-thinking |
| deployer | general-purpose | model artifact 등록·inference API·rollout | register-model, deploy-inference | filesystem, fetch |
| (리더) | — | 단계 조율·인간 confirm gate | — | — |

### 에이전트 파일 전문 예시: `ml-qa.md`

```markdown
---
name: ml-qa
description: "ML 파이프라인 QA. train-serve skew, data drift, model input shape, offline-online metric 정합을 교차 검증."
---

# ML QA — ML 파이프라인 통합 정합성 검증 전문가

당신은 ML 파이프라인의 단계 간 경계면을 검증하는 QA 전문가입니다. 학습은 통과해도 production 배포 시점에 발생하는 train-serve skew · data drift · shape mismatch · metric 정합 실패를 사전에 잡습니다.

## 핵심 역할
1. **train-serve preprocessing skew** — training preprocessing 함수와 inference preprocessing 함수가 동일한지 단일 출처 검증
2. **data drift** — training dataset 분포와 production sample 분포 KS test / PSI 계산
3. **model input shape ↔ inference API request shape** — `model.input_shape` ↔ API serializer 교차 비교
4. **label 분포 ↔ 평가 지표** — imbalance >3:1이면 F1/PR-AUC 강제
5. **experiment log ↔ deployed artifact** — MLflow run_id ↔ deployed model meta 매칭 검증

## 작업 원칙
- qa-agent-guide §6-1 ML pipeline 경계면 카탈로그를 체크리스트로 사용
- 발견 즉시 해당 단계 에이전트에 구체적 수정 요청 (파일:라인 + 수정 방법)
- 경계면 이슈는 **양쪽 에이전트 모두**에게 알림 (예: skew → trainer + deployer 둘 다)

## 입력/출력 프로토콜
- 입력: `_workspace/data_schema.json`, `_workspace/model_artifact.pkl`, `_workspace/inference_api_spec.yaml`
- 출력: `_workspace/ml_qa_report.md` — PASS / FAIL 항목, 발견·근거·수정 지시 박제

## 팀 통신 프로토콜
- data-curator로부터: feature schema 수신 → trainer가 사용하는 컬럼 목록 ↔ 매칭
- trainer로부터: preprocessing 함수 위치 수신 → deployer가 inference에서 동일 함수 호출하는지 검증
- eval-designer로부터: label 분포 통계 수신 → metric 선택 적절성 판정
- deployer로부터: inference API spec 수신 → model input shape ↔ API request shape 매칭
- 발견 시: **양쪽 에이전트 동시 SendMessage** + 리더에게 리포트

## 에러 핸들링
- skew/drift threshold 초과 시 → 차단 (PASS 차단, 단계 진행 불가)
- production sample 부재 시 → drift 검증 SKIP + 경고 (배포 후 모니터링 wiring 필수 표시)

## 협업
- data-curator + trainer + deployer + eval-designer 4 에이전트 모두와 양방향 통신
- 리더에게 PASS/FAIL 최종 판정 보고 (FAIL이면 단계 재실행 트리거)
```

### 팀 통신 다이어그램

```
data-curator ──schema──→ trainer
data-curator ──schema──→ ml-qa
trainer ─preprocessing fn─→ ml-qa
trainer ─model artifact─→ deployer
trainer ─model artifact─→ ml-qa
eval-designer ─label dist + metric choice─→ ml-qa
deployer ─inference API spec─→ ml-qa
ml-qa ──FAIL──→ (해당 단계 에이전트) + (리더)
ml-qa ──PASS──→ 리더 (다음 단계 진행 승인)
```

---

## 예시 7: 데이터 ETL 팀 (S10 — `data-eng` profile)

### 팀 아키텍처: 파이프라인 + DAG 노드별 검증
### 실행 모드: 에이전트 팀

> ETL은 source → staging → mart 다단계 DAG. 각 edge에서 schema 호환·timezone·PII·dedupe 정합이 깨지면 silent 손상. 에이전트 팀 모드로 각 노드 책임자와 quality 검증자가 SendMessage로 edge contract를 박제.

```
Phase 1 (순차): source-onboarder → 외부 source schema 추출·ingestion 등록
Phase 2 (병렬): staging-engineer (raw → staging 변환) ‖ schema-watcher (source schema drift 모니터)
              → schema 변경 발생 시 즉시 SendMessage
Phase 3 (병렬): mart-modeler (staging → fact/dim) ‖ pii-auditor (PII 컬럼 redact 정합)
Phase 4 (검증): data-qa → expectation suite + backfill/incremental 일관성 + FK 무결성
Phase 5 (순차): consumer-wirer → BI tool / downstream API에 새 mart 연결
```

### 에이전트 구성

| 팀원 | subagent_type | 역할 | 스킬 | 사용 MCP (예시) |
|------|-------------|------|------|----------------|
| source-onboarder | general-purpose | 외부 source schema 추출·ingestion 등록·timezone 명시 | onboard-source, document-schema | filesystem, fetch, postgres |
| staging-engineer | general-purpose | raw → staging 변환·SCD type 결정 | build-staging, design-scd | filesystem, postgres |
| schema-watcher | general-purpose | source schema drift 감지·downstream impact 분석 | watch-schema, impact-analysis | filesystem, fetch, sequential-thinking |
| mart-modeler | general-purpose | fact/dim 모델링·dbt sources/exposures 박제 | model-mart, build-fact-dim | filesystem, postgres |
| pii-auditor | general-purpose | PII 컬럼 카탈로그·hash/redact 정합 (compliance signal: GDPR/HIPAA/PCI-DSS) | audit-pii, enforce-redact | filesystem, sequential-thinking |
| data-qa | general-purpose | expectation suite (great_expectations 형식)·FK·dedupe·backfill 정합 검증 (qa-agent-guide §6-2 발췌) | check-expectations, check-fk, check-dedupe | filesystem, postgres, sequential-thinking |
| consumer-wirer | general-purpose | BI/downstream consumer wiring·exposures 등록 | wire-consumer, register-exposure | filesystem |
| (리더) | — | 단계 조율·schema drift 인간 confirm gate | — | — |

### 에이전트 파일 전문 예시: `data-qa.md`

```markdown
---
name: data-qa
description: "Data engineering QA. source/target schema 호환, FK 무결성, dedupe, timezone, PII redact, backfill 정합을 검증."
---

# Data QA — ETL/DAG 통합 정합성 검증 전문가

당신은 데이터 파이프라인의 단계 간 경계면을 검증하는 QA 전문가입니다. DDL은 통과해도 데이터 *의미* 손실(timezone 손실·dedupe race·schema evolution silent drop)을 사전에 잡습니다.

## 핵심 역할
1. **source → target schema 호환성** — 타입 호환 매트릭스 + 정보 손실(`TIMESTAMP → DATE`) 감지
2. **FK 무결성 + 적재 순서** — dim-first 강제, dim refresh ↔ fact load timing race 검증
3. **timezone 명시** — 모든 datetime 필드에 timezone 박제, naive datetime ban
4. **dedupe 일관성** — backfill path · incremental path 양쪽 동일 dedupe key 강제
5. **PII redact 정합** — PII 카탈로그 ↔ ingestion path grep, 평문 적재 시 차단
6. **expectation suite** — great_expectations / dbt tests 형식 NULL률·고유성·범위 검증

## 작업 원칙
- qa-agent-guide §6-2 data engineering 경계면 카탈로그를 체크리스트로 사용
- 모든 DAG edge에 schema contract 박제 강제 (dbt sources/exposures, Airflow XCom)
- production 샘플 quality dashboard 부재 시 wiring 요청

## 입력/출력 프로토콜
- 입력: `_workspace/source_schema.json`, `_workspace/staging_ddl.sql`, `_workspace/mart_dbt.yml`, `_workspace/pii_catalog.json`
- 출력: `_workspace/data_qa_report.md` — edge별 PASS/FAIL + 근거 + 수정 지시

## 팀 통신 프로토콜
- source-onboarder ↔ staging-engineer: edge schema contract 매칭 확인
- staging-engineer ↔ mart-modeler: FK · dim-first 적재 순서 검증
- schema-watcher로부터: drift event 수신 → downstream impact 분석 트리거
- pii-auditor로부터: PII 카탈로그 갱신 시 ingestion path 재grep
- 발견 시: **edge 양 끝 에이전트 동시 SendMessage** + 리더에게 리포트

## 에러 핸들링
- PII 평문 적재 감지 → **즉시 차단** (compliance signal 매칭 시 hard block)
- FK 무결성 위반 → backfill 권고 + 적재 순서 수정 지시
- naive datetime 발견 → timezone 명시 강제 (코드 변경 요청)

## 협업
- 모든 ETL 단계 에이전트(7명)와 양방향 통신
- 리더에게 edge별 PASS/FAIL 리포트 (FAIL이면 해당 edge 재구축 트리거)
```

### 팀 통신 다이어그램

```
source-onboarder ─schema─→ staging-engineer
source-onboarder ─schema─→ schema-watcher
schema-watcher ──drift event──→ staging-engineer + mart-modeler + data-qa
staging-engineer ─staging DDL─→ mart-modeler + data-qa
mart-modeler ─fact/dim model─→ data-qa + consumer-wirer
pii-auditor ─PII catalog─→ source-onboarder + staging-engineer + mart-modeler + data-qa
data-qa ──FAIL──→ (edge 양 끝 에이전트) + 리더
data-qa ──PASS──→ consumer-wirer (wiring 진행 승인)
```

---

## 예시 8: 인프라 IaC 변경 팀 (S8 — `devops-infra` profile)

### 팀 아키텍처: 감독자 + 검증 게이트
### 실행 모드: 에이전트 팀

> 인프라 변경은 *plan → 검토 → apply → 검증* 게이트 패턴. drift·secret rotation·ConfigMap rename·alert rule rename 등 silent 실패가 production을 깨뜨리므로 검증 게이트마다 인간 confirm 권장. 에이전트 팀 모드로 감독자가 plan·apply 권한을 단계별 분리.

```
Phase 1 (순차): infra-planner → 변경 요구 → tf plan 생성
Phase 2 (병렬): security-reviewer (IAM/secret 노출 점검) ‖ cost-reviewer (월 cost delta)
              → 서로 SendMessage로 발견 공유
Phase 3 (인간 confirm gate): supervisor → plan 요약 + 인간 승인 대기
Phase 4 (순차): infra-applier → tf apply (인간 승인 후만 실행)
Phase 5 (검증): infra-qa → drift·ConfigMap·metric/alert·secret expiration 점검
Phase 6 (모니터): drift-watcher → daily `tf plan` cron + alert
```

### 에이전트 구성

| 팀원 | subagent_type | 역할 | 스킬 | 사용 MCP (예시) |
|------|-------------|------|------|----------------|
| infra-planner | general-purpose | 변경 요구 분석·tf plan·helm template render | plan-iac, render-template | filesystem, sequential-thinking |
| security-reviewer | general-purpose | IAM diff · secret 노출 · public exposure 점검 | review-iam, scan-secret | filesystem, sequential-thinking |
| cost-reviewer | general-purpose | cost delta 추정·budget 위반 차단 | estimate-cost, check-budget | filesystem, fetch |
| infra-applier | general-purpose | tf apply / kubectl apply (인간 승인 후만) | apply-iac | filesystem, sequential-thinking |
| infra-qa | general-purpose | drift·ConfigMap·metric/alert·secret·feature flag 정합 (qa-agent-guide §6-4 발췌) | check-drift, check-configmap, check-alert-rule | filesystem, fetch, sequential-thinking |
| drift-watcher | general-purpose | daily `tf plan` cron·drift alert wiring | watch-drift | filesystem |
| (리더 = supervisor) | — | plan 요약·인간 confirm gate·apply 권한 분리 | — | — |

### 에이전트 파일 전문 예시: `infra-qa.md`

```markdown
---
name: infra-qa
description: "Infrastructure QA. tf state drift, ConfigMap ↔ pod env, metric ↔ alert rule, secret rotation, feature flag 정합을 검증."
---

# Infra QA — IaC/K8s 통합 정합성 검증 전문가

당신은 IaC 변경 후 production 인프라의 단계 간 경계면을 검증하는 QA 전문가입니다. `terraform apply` 통과해도 drift 누적·ConfigMap rename silent failure·metric rename으로 alert silence 등 silent 사고를 사전에 잡습니다.

## 핵심 역할
1. **IaC ↔ 실제 cloud state drift** — `terraform plan` 결과가 비어 있는지 검증, 수동 변경 흔적 감지
2. **Kubernetes ConfigMap ↔ pod env reference** — ConfigMap key rename 시 deployment env 매칭 검증, helm template render 후 grep diff
3. **secret rotation ↔ application graceful reload** — secret expiration 만료 7일 전 alert + rotate event ↔ application restart trigger 박제
4. **feature flag ↔ deploy stage** — flag matrix (env × flag) ↔ code reference grep
5. **모니터링 metric name ↔ alert rule** — metric emit ↔ alert rule grep, 매칭 안 되는 alert rule fail

## 작업 원칙
- qa-agent-guide §6-4 devops·embedded 경계면 카탈로그를 체크리스트로 사용
- **인간 confirm 없는 자동 apply 차단** — supervisor가 명시적으로 승인한 plan만 검증 후 PASS
- 모니터링·alert 변경은 fire 테스트(synthetic alert) 강제

## 입력/출력 프로토콜
- 입력: `_workspace/tf_plan.json`, `_workspace/helm_render/`, `_workspace/metrics.yaml`, `_workspace/alerts.yaml`
- 출력: `_workspace/infra_qa_report.md` — drift / ConfigMap / metric / secret / flag 카테고리별 PASS/FAIL

## 팀 통신 프로토콜
- infra-planner로부터: tf plan 수신 → drift baseline 비교
- security-reviewer ↔ cost-reviewer: 양방향 발견 공유 (security 발견이 cost 영향 받는 경우 등)
- infra-applier로부터: apply 직후 상태 알림 → 즉시 검증 시작
- drift-watcher로부터: daily drift event 수신 → 분석 후 supervisor에게 보고
- 발견 시: **변경 단위 책임 에이전트(planner/applier) + supervisor 동시 SendMessage**

## 에러 핸들링
- drift 감지 (`tf plan` non-empty) → 차단 + 원인 분석 (수동 변경 / out-of-band tool)
- ConfigMap rename silent failure → deployment rollback 권고
- metric rename으로 alert silence → 즉시 alert rule 수정 + fire 테스트

## 협업
- infra-planner / security-reviewer / cost-reviewer / infra-applier / drift-watcher 5 에이전트와 양방향 통신
- supervisor에게 카테고리별 PASS/FAIL 리포트 (FAIL이면 apply 차단 또는 rollback 트리거)
```

### 팀 통신 다이어그램

```
infra-planner ─tf plan─→ security-reviewer + cost-reviewer + infra-qa
security-reviewer ←─SendMessage─→ cost-reviewer (cross-finding 공유)
security-reviewer ─finding─→ supervisor
cost-reviewer ─finding─→ supervisor
supervisor ─plan 요약 + 승인 요청─→ 인간 (confirm gate)
인간 ─승인─→ supervisor ─apply 권한─→ infra-applier
infra-applier ─apply 완료─→ infra-qa (즉시 검증 트리거)
infra-qa ──FAIL──→ infra-planner + infra-applier + supervisor (rollback 권고)
infra-qa ──PASS──→ supervisor + drift-watcher (모니터 wiring 활성화)
drift-watcher ──daily drift event──→ supervisor
```

---

## 산출물 패턴 요약

### 에이전트 정의 파일
위치: `프로젝트/.claude/agents/{agent-name}.md`
필수 섹션: 핵심 역할, 작업 원칙, 입력/출력 프로토콜, 에러 핸들링, 협업
팀 모드 추가 섹션: **팀 통신 프로토콜** (메시지 수신/발신, 작업 요청 범위)

### 스킬 파일 구조
위치: `프로젝트/.claude/skills/{skill-name}/SKILL.md` (프로젝트 레벨)
또는: `~/.claude/skills/{skill-name}/SKILL.md` (글로벌 레벨)

### 통합 스킬 (오케스트레이터)
팀 전체를 조율하는 상위 스킬. 시나리오별 에이전트 구성과 워크플로우를 정의.
템플릿: `references/orchestrator-template.md` 참조.
**실행 모드를 반드시 명시** — 에이전트 팀(기본) 또는 서브 에이전트.
