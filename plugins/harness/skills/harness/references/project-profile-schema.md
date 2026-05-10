# Project Profile Schema

Phase 1 Code Research의 표준 출력 형식. 코드베이스 분석으로 수집한 5축 객관적 신호를 구조화한 schema.

---

## 목차

1. [개요](#1-개요)
2. [Schema 풀 명세](#2-schema-풀-명세)
3. [Quick scan vs Deep audit 출력 차이](#3-quick-scan-vs-deep-audit-출력-차이)
4. [Greenfield 최소 형태](#4-greenfield-최소-형태)
5. [파일 형식](#5-파일-형식)
6. [Intent Profile로의 매핑](#6-intent-profile로의-매핑)
7. [Greenfield 인스턴스 예시](#7-greenfield-인스턴스-예시)
8. [Brownfield 인스턴스 예시 (Deep audit)](#8-brownfield-인스턴스-예시-deep-audit)
9. [검증 룰](#9-검증-룰)

---

## 1. 개요

### Intent Profile과의 차이

| | Intent Profile | Project Profile |
|---|---|---|
| 입력 | 사용자 발화 | 코드베이스 파일 |
| 성격 | 주관적 의도·계획 | 객관적 측정값 |
| 변화 빈도 | 의도 변경 시 (드물게) | 코드 변경에 따라 (자주) |
| 누락 처리 | `meta.open_questions` | `meta.unanalyzed`, `meta.confidence_low` |
| Phase 10 활용 | 의도 변화 신호 | 코드 변화 신호 (drift 감지) |

### 핵심 설계 원칙

1. **신호 + 근거 분리** — 모든 추출 값에 "어떤 파일/명령에서 나왔는지" 근거를 함께 기록한다. 단순히 `language: typescript`가 아니라 `language: typescript (source: package.json#devDependencies, tsconfig.json 존재)`. 근거는 (a) 사용자 검토 시 신뢰성 판단, (b) Intent Profile 자동 채우기 시 confidence 결정, (c) Phase 10에서 baseline 변화 추적의 anchor.

2. **모드 명시** — Quick scan과 Deep audit의 출력은 동일 schema를 공유하되, 미수집 축은 `meta.unanalyzed`에 등록. 다운스트림은 누락된 축을 직접 추론하지 않고 명시적으로 다룬다.

3. **측정값과 해석 구분** — schema는 측정값(coverage_percent: 67)만 담고, 해석("커버리지가 낮음")은 담지 않는다. 해석은 Phase 3 Domain Analysis가 수행. 이유: 같은 67%도 프로젝트 단계에 따라 다르게 해석되어야 한다.

4. **t=0 anchor** — Phase 10 Runtime Adaptation의 기준점. 이 schema의 측정값들이 추후 변경되면 그것이 곧 baseline drift의 신호.

---

## 2. Schema 풀 명세

```yaml
version: 1
project_type: greenfield | brownfield
scan_mode: minimal | quick | deep   # greenfield=minimal, brownfield=quick|deep
scanned_at: ISO8601 timestamp
scan_root: string                   # 분석 대상 디렉토리 (보통 ".")

stack:
  languages: [{ name, version, percent_loc, source }]
  frameworks: [{ name, version, role, source }]   # role: "frontend"|"backend"|"build"|"test"|...
  build_tools: [{ name, version, source }]
  test_tools: [{ name, version, source }]
  package_manager: { name, lockfile_present, source }
  runtime: { name, version_pinned, source }       # node, python, go, ...

architecture:
  structure_pattern: monorepo | multi-package | flat | layered | feature-based | domain-driven | unknown
  entry_points: [path]
  key_directories:
    - path: string
      purpose: string                # 추론된 목적. 예: "API routes", "shared types"
      file_count: int
  module_boundaries:                  # 식별된 명확한 경계
    - name: string
      path: string
      public_interface: string | null
  data_flow_summary: string           # 본문에 자유 서술

convention:
  file_naming:
    case_style: kebab | snake | camel | pascal | mixed
    consistency_score: 0.0-1.0        # 1.0 = 완벽히 일관됨
  component_naming:                   # 프론트엔드 프로젝트만
    case_style: kebab | snake | camel | pascal | mixed
  test_location: collocated | separate | mirror | mixed
  formatter:
    tool: string | null               # prettier, black, gofmt, ...
    config_file: path | null
  linter:
    tool: string | null
    config_file: path | null
    strict_level: off | warn | error
  type_checking:
    tool: string | null               # typescript, mypy, ...
    strictness: off | basic | strict | extreme

# --- Deep audit only fields below ---

maturity:
  test_coverage:
    tool: string | null
    line_coverage_percent: float | null
    branch_coverage_percent: float | null
    measured_from: path | null        # 커버리지 리포트 파일
  ci_cd:
    provider: string | null           # github_actions, gitlab_ci, circleci, ...
    workflows: [{ name, triggers: [string], stages: [string] }]
  documentation:
    readme_present: bool
    readme_quality: minimal | standard | comprehensive
    api_docs_present: bool
    adr_count: int                    # docs/adr/, docs/decisions/ 등
    inline_comment_density: float     # 주석 라인 / 전체 코드 라인
  type_safety:
    coverage_percent: float | null    # any/Any 사용 비율의 보수
    strict_files_percent: float | null
  dependency_health:
    total_count: int
    outdated_count: int
    deprecated_count: int
    known_vulnerabilities: int

pain_points:
  churn_hotspots:                     # 최근 N일간 변경 빈도 상위
    - path: string
      change_count: int
      period_days: int
      percent_of_total_churn: float
  todo_markers:
    total_count: int
    by_type: { TODO: int, FIXME: int, HACK: int, XXX: int }
    examples: [{ path, line, marker, comment }]   # 최대 5개
  skipped_tests:
    total_count: int
    examples: [{ path, name, reason }]            # 최대 5개
  deprecated_usages:
    - api_or_pattern: string
      occurrences: int
      replacement_recommended: string | null
  complexity_outliers:                # 복잡도 이상치
    - path: string
      metric_name: string             # cyclomatic, file_loc, function_loc, ...
      value: float
      threshold: float

meta:
  unanalyzed: [string]                # 스캔 모드로 인해 수집 안 한 섹션. 예: ["maturity", "pain_points"]
  confidence_low: [string]            # 측정 가능했지만 신뢰도 낮은 필드. dot-path 형식
  scan_warnings: [string]             # 스캔 중 발생한 경고. 예: "node_modules 미설치 — dependency_health 추정치"
  source_file_count: int              # 분석된 소스 파일 수
  total_loc: int                      # 전체 코드 라인 수
```

### `source` 필드 규약

신호의 출처를 표현하는 표준 형식:
- 단일 파일: `"package.json"`
- 파일 + 위치: `"package.json#dependencies"` (JSON Pointer 또는 섹션명)
- 다중 파일: `["package.json", "tsconfig.json"]`
- 명령 결과: `"cmd: git log --since=30days"`
- 추론: `"inferred from: <근거>"` (직접 측정 아닌 경우)

이 규약은 Phase 10 Runtime Adaptation이 baseline drift를 감지할 때 "어떤 파일을 다시 봐야 하는지" 결정하는 데 사용된다.

---

## 3. Quick scan vs Deep audit 출력 차이

| 섹션 | Quick scan | Deep audit |
|------|:---:|:---:|
| `stack` | ✓ | ✓ |
| `architecture` | ✓ (key_directories는 상위 2단계만) | ✓ (전체 트리) |
| `convention` | ✓ | ✓ |
| `maturity` | ✗ → `meta.unanalyzed` | ✓ |
| `pain_points` | ✗ → `meta.unanalyzed` | ✓ (git churn 분석 포함) |

Quick scan에서 누락된 축은 `meta.unanalyzed`에 명시:
```yaml
meta:
  unanalyzed: [maturity, pain_points]
```

이렇게 하면 Phase 2의 자동 추론이 해당 섹션을 건드리지 않고, 사용자가 deep audit을 명시 요청할 때 점진적으로 채울 수 있다.

---

## 4. Greenfield 최소 형태

Greenfield는 5축 조사를 건너뛰고 최소 정보만 기록한다. 이유: 코드가 없어 측정할 대상이 없음.

```yaml
version: 1
project_type: greenfield
scan_mode: minimal
scanned_at: 2026-05-09T10:00:00Z
scan_root: "."

stack: {}
architecture:
  structure_pattern: unknown
  entry_points: []
  key_directories: []
  module_boundaries: []
convention: {}

meta:
  unanalyzed: [stack, architecture, convention, maturity, pain_points]
  source_file_count: 0
  total_loc: 0
  detection_signals:                  # greenfield 판정 근거
    - "git: initial commit only"
    - "no package manifests found"
    - "directory contents: README.md, .gitignore, LICENSE"
```

다운스트림(Phase 2)은 `project_type: greenfield`만 보고 자동 추론 단계를 완전히 건너뛴다.

---

## 5. 파일 형식

### 위치
`_workspace/_baseline/project_profile.md`

### 구조
intent_profile.md와 동일한 패턴: YAML frontmatter (구조화 필드) + 마크다운 본문 (서술 + 다이어그램).

```markdown
---
version: 1
project_type: brownfield
scan_mode: deep
...
---

# Project Profile

## Stack Summary
{본문 서술 — frontmatter의 stack 섹션을 자연어로 요약}

## Architecture Overview
{디렉토리 트리 + 데이터 흐름 자유 서술}

## Convention Notes
{코드 컨벤션의 특이사항 서술}

## Maturity Assessment
{측정값의 자연어 정리}

## Pain Points Detail
{핫스팟별 상세, churn graph 등}

## Scan Notes
{경고, 미분석 영역, 신뢰도 낮은 항목 설명}
```

frontmatter는 기계 읽기용, 본문은 사람 읽기용. 두 표현이 충돌하면 frontmatter가 ground truth.

---

## 6. Intent Profile로의 매핑

Phase 2-3 (brownfield 자동 추론) 단계에서 project_profile의 각 필드가 intent_profile의 어느 필드를 채우는지의 매핑 룰. 이 매핑이 명시적이어야 추론 과정이 결정적이고 재현 가능해진다.

| Project Profile 필드 | → Intent Profile 필드 | 변환 룰 |
|---|---|---|
| `stack.languages[].name`, `stack.frameworks[].name` | `constraints.tech_stack.locked_in` | 매니페스트에 있으면 locked_in (이미 도입되어 변경 어려움) |
| `architecture.entry_points` | `architecture.deployment_target` | 빌드 출력 형태로 추론. `next.config` → web, `*.podspec` → mobile, ... |
| `convention.formatter`, `convention.linter` | `quality.documentation_level` 보조 신호 | 도구 존재 시 최소 `code_comments` 이상 |
| `maturity.test_coverage.line_coverage_percent` | `quality.test_rigor` | 0% → none / <30% → smoke / 30-70% → unit / >70% → integration / TDD 패턴 감지 시 tdd |
| `maturity.ci_cd.provider`, `workflows` | `workflow.ci_cd` | 없음 → none / lint만 → lint / test 단계 → test / 다단계 → full_pipeline |
| `meta.source_file_count`, git contributors | `constraints.team.size` | contributor 수 기반 추정. 1 → solo, 2-5 → small, ... |
| `maturity.documentation` | `quality.documentation_level` | api_docs_present + 인라인 밀도로 매핑 |
| `pain_points.churn_hotspots` | `meta.open_questions` | "{path}가 활발히 변경 중인데 전담 에이전트가 필요한가?" 형태 질문 생성 |
| `pain_points.skipped_tests` | `meta.open_questions` | "{path}의 스킵된 테스트가 의도된 것인가?" |

### 신뢰도 결정

추론된 필드는 다음 룰로 confidence를 분류:

| Confidence | 조건 |
|-----------|------|
| **High** | 직접 측정값 (manifest, config 파일에서 명시) → 사용자 확인 없이 채워도 됨 |
| **Medium** | 다중 신호의 일치 (예: jest.config + 커버리지 리포트 + CI에서 실행) |
| **Low** | 단일 약한 신호 또는 추정 (예: contributor 수로 team size 추정) → `meta.confidence_low`에 등록 |

`meta.confidence_low`에 등록된 필드는 Phase 2-3의 "확인" 단계에서 우선적으로 사용자에게 제시된다.

---

## 7. Greenfield 인스턴스 예시

```markdown
---
version: 1
project_type: greenfield
scan_mode: minimal
scanned_at: 2026-05-09T09:00:00Z
scan_root: "."

stack: {}
architecture:
  structure_pattern: unknown
  entry_points: []
  key_directories: []
  module_boundaries: []
convention: {}

meta:
  unanalyzed: [stack, architecture, convention, maturity, pain_points]
  source_file_count: 0
  total_loc: 0
  detection_signals:
    - "git status: initial commit only (1 commit, README only)"
    - "no manifests: package.json, requirements.txt, Cargo.toml, go.mod, pom.xml, Gemfile not found"
    - "directory contents: README.md (12 lines), .gitignore"
---

# Project Profile

## Greenfield Detection

이 프로젝트는 다음 신호로 greenfield로 분류되었다:

- Git 이력: 초기 커밋 1개만 존재 (README 추가)
- 패키지 매니페스트: 6개 검사 모두 부재
- 소스 파일: 없음

## Next Step

5축 조사를 건너뛰고 즉시 Phase 2 Project Inquiry로 진행한다. Intent Profile은 사용자 입력만으로 채워진다.
```

---

## 8. Brownfield 인스턴스 예시 (Deep audit)

가상 프로젝트: 위 intent_profile 예시의 "기존 Next.js 커머스 사이트"

```markdown
---
version: 1
project_type: brownfield
scan_mode: deep
scanned_at: 2026-05-09T11:30:00Z
scan_root: "."

stack:
  languages:
    - { name: typescript, version: "5.4.x", percent_loc: 87, source: "tsconfig.json, *.ts/*.tsx files" }
    - { name: css, version: null, percent_loc: 9, source: "*.css files" }
    - { name: sql, version: null, percent_loc: 4, source: "prisma/migrations/*.sql" }
  frameworks:
    - { name: next, version: "14.2.3", role: frontend, source: "package.json#dependencies" }
    - { name: react, version: "18.3.1", role: frontend, source: "package.json#dependencies" }
    - { name: prisma, version: "5.14.0", role: orm, source: "package.json#dependencies, schema.prisma" }
    - { name: tailwindcss, version: "3.4.3", role: styling, source: "package.json, tailwind.config.ts" }
  build_tools:
    - { name: next, version: "14.2.3", source: "package.json#scripts.build" }
  test_tools:
    - { name: vitest, version: "1.6.0", source: "package.json#devDependencies, vitest.config.ts" }
    - { name: playwright, version: "1.44.0", source: "package.json#devDependencies" }
  package_manager:
    name: pnpm
    lockfile_present: true
    source: "pnpm-lock.yaml"
  runtime:
    name: node
    version_pinned: true
    source: ".nvmrc (20.12.2), package.json#engines"

architecture:
  structure_pattern: feature-based
  entry_points:
    - "src/app/(shop)/page.tsx"
    - "src/app/api/**/route.ts"
  key_directories:
    - { path: "src/app", purpose: "Next.js App Router pages and API routes", file_count: 87 }
    - { path: "src/features", purpose: "Feature modules (cart, checkout, product)", file_count: 124 }
    - { path: "src/lib", purpose: "Shared utilities and clients", file_count: 23 }
    - { path: "prisma", purpose: "DB schema and migrations", file_count: 18 }
    - { path: "tests/e2e", purpose: "Playwright E2E suites", file_count: 14 }
  module_boundaries:
    - { name: "features/cart", path: "src/features/cart", public_interface: "src/features/cart/index.ts" }
    - { name: "features/checkout", path: "src/features/checkout", public_interface: "src/features/checkout/index.ts" }
    - { name: "features/product", path: "src/features/product", public_interface: "src/features/product/index.ts" }
  data_flow_summary: |
    User → App Router page → Server Component → Prisma client → PostgreSQL.
    Mutations through Server Actions. Cart state in cookies + Server Component.
    No global client-side store (React Query 부분 사용).

convention:
  file_naming:
    case_style: kebab
    consistency_score: 0.94
  component_naming:
    case_style: pascal
  test_location: mixed   # unit은 collocated, e2e는 separate
  formatter:
    tool: prettier
    config_file: ".prettierrc.json"
  linter:
    tool: eslint
    config_file: ".eslintrc.json"
    strict_level: error
  type_checking:
    tool: typescript
    strictness: strict   # tsconfig.json#compilerOptions.strict = true

maturity:
  test_coverage:
    tool: vitest
    line_coverage_percent: 67.4
    branch_coverage_percent: 58.1
    measured_from: "coverage/coverage-summary.json"
  ci_cd:
    provider: github_actions
    workflows:
      - name: "ci"
        triggers: ["pull_request", "push to main"]
        stages: ["lint", "typecheck", "test", "e2e"]
      - name: "deploy"
        triggers: ["push to main"]
        stages: ["build", "deploy-vercel"]
  documentation:
    readme_present: true
    readme_quality: standard
    api_docs_present: false
    adr_count: 3        # docs/adr/0001-*.md, 0002-*.md, 0003-*.md
    inline_comment_density: 0.08
  type_safety:
    coverage_percent: 96.2   # any 사용 3.8%
    strict_files_percent: 100.0
  dependency_health:
    total_count: 47
    outdated_count: 8
    deprecated_count: 1     # request@2.x
    known_vulnerabilities: 0

pain_points:
  churn_hotspots:
    - { path: "src/features/checkout/handlers.ts", change_count: 23, period_days: 30, percent_of_total_churn: 18.4 }
    - { path: "src/app/api/orders/route.ts", change_count: 17, period_days: 30, percent_of_total_churn: 13.6 }
    - { path: "src/features/cart/store.ts", change_count: 11, period_days: 30, percent_of_total_churn: 8.8 }
  todo_markers:
    total_count: 34
    by_type: { TODO: 24, FIXME: 7, HACK: 2, XXX: 1 }
    examples:
      - { path: "src/features/checkout/handlers.ts", line: 142, marker: "FIXME", comment: "race condition with stock check" }
      - { path: "src/lib/payment.ts", line: 87, marker: "TODO", comment: "retry policy not implemented" }
  skipped_tests:
    total_count: 4
    examples:
      - { path: "tests/e2e/checkout.spec.ts", name: "concurrent purchase same item", reason: "flaky on CI" }
      - { path: "src/features/cart/store.test.ts", name: "merge guest cart on login", reason: "WIP since 2026-03" }
  deprecated_usages:
    - { api_or_pattern: "request package", occurrences: 3, replacement_recommended: "fetch + undici" }
    - { api_or_pattern: "Next.js getServerSideProps", occurrences: 0, replacement_recommended: null }   # 잔존 없음, 마이그레이션 완료
  complexity_outliers:
    - { path: "src/features/checkout/handlers.ts", metric_name: "cyclomatic", value: 47, threshold: 20 }
    - { path: "src/lib/pricing.ts", metric_name: "function_loc", value: 312, threshold: 100 }

meta:
  unanalyzed: []
  confidence_low:
    - "constraints.team.size (contributor 수 기반 추정)"
  scan_warnings:
    - "node_modules 미설치 — dependency_health.outdated_count는 npm registry 직접 조회 결과"
  source_file_count: 287
  total_loc: 18432
---

# Project Profile

## Stack Summary

TypeScript 기반 Next.js 14 풀스택 (App Router). Prisma ORM + PostgreSQL.
테스팅은 Vitest (단위/통합) + Playwright (E2E) 조합. pnpm 워크스페이스이며
Node 20.12.2로 핀 고정.

## Architecture Overview

Feature-based 구조 — `src/features/` 하위에 cart, checkout, product 3개 도메인이
명확한 public interface(`index.ts`)로 분리됨. App Router 페이지가 feature 모듈을
조합하는 패턴. 글로벌 client store 없음, Server Component + Server Actions 우선.

```
src/
├── app/                   # 페이지 + API routes (87 files)
├── features/
│   ├── cart/              # ← public interface 명확
│   ├── checkout/          # ← churn hotspot (이력 23 changes/30d)
│   └── product/
├── lib/                   # 공유 유틸 (23 files)
└── ...
```

## Maturity Assessment

- 라인 커버리지 67.4%, 브랜치 58.1% — feature 내 unit 테스트 우선, e2e는 핵심 시나리오만
- CI 단계 완비 (lint/typecheck/test/e2e), 배포 자동화도 존재
- ADR 3개 — 의사결정 기록 문화 있음
- 타입 안전성 강함 (strict 100%, any 3.8%)
- deprecated 1건 (`request` 패키지) — 마이그레이션 권장

## Pain Points Detail

### Churn Hotspots
`src/features/checkout/handlers.ts`가 30일간 23회 변경 — 전체 churn의 18.4%.
복잡도도 임계 초과 (cyclomatic 47, threshold 20). **추천 시스템 추가 시 checkout 영역과의 결합도 주의 필요.**

### 알려진 문제
- FIXME: checkout handlers의 재고 체크 race condition (line 142)
- 스킵 테스트: 동시 구매 시나리오 (flaky on CI) — 본질적 동시성 이슈일 가능성

## Scan Notes

`meta.confidence_low`: 팀 크기는 git contributor 5명 기반 추정 (`small`).
실제 활성 멤버 수와 다를 수 있음 → Phase 2-3에서 사용자 확인 필요.
```

**주의 깊게 볼 점:**
- 모든 측정값에 `source` 필드로 근거 명시
- `pain_points.churn_hotspots`가 본문 서술과 연결되어 "추천 시스템 추가 시 checkout 결합도 주의"같은 도메인 grounded 통찰로 이어짐 → Phase 2-3의 "코드 grounded 질문" 재료
- `meta.confidence_low`로 team size를 표시 → Phase 2-3에서 우선 확인 대상

---

## 9. 검증 룰

Phase 1 종료 시 project_profile.md가 다음 룰을 통과해야 한다.

### 필수 룰

| 룰 | 검증 |
|----|------|
| `version`, `project_type`, `scan_mode`, `scanned_at` 존재 | frontmatter 최상위 |
| `scan_mode = minimal` ↔ `project_type = greenfield` | 일관성 |
| `scan_mode = quick` 시 `meta.unanalyzed`에 `[maturity, pain_points]` 포함 | 명시적 누락 |
| `scan_mode = deep` 시 `meta.unanalyzed = []` | 모든 축 수집 완료 |
| `stack`이 비어있지 않음 (brownfield) | 매니페스트 1개 이상 검출 필요 |

### 권장 룰

| 룰 | 의미 |
|----|------|
| 모든 `stack.frameworks[]` 항목에 `source` 채워짐 | 근거 추적성 |
| `pain_points.churn_hotspots` 측정 시 `period_days` 명시 | 30일 기본, 사용자 요청 시 다른 기간 |
| `confidence_low`에 등록된 필드는 본문 "Scan Notes"에 설명 | 사용자 검토 가독성 |

### Cross-section 룰

| 조합 | 룰 |
|------|----|
| `stack.test_tools = []` + `maturity.test_coverage.line_coverage_percent != null` | 모순 — 도구 없이 커버리지 측정 불가 |
| `architecture.module_boundaries = []` + `architecture.structure_pattern = feature-based` | 경고 — 패턴은 검출됐는데 경계가 명확하지 않음 |
| `pain_points.todo_markers.total_count > 100` + `total_loc < 5000` | 경고 — 코드 대비 TODO 밀도 비정상적으로 높음 |

검증 실패 시 사용자에게 보고하고 재스캔 여부를 묻는다. 단순 누락(예: source 미기입)은 자동 수정 시도.
