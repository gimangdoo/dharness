# Code Research 방법론

Phase 1 Code Research의 실행 가이드. 코드베이스를 분석해 `project_profile.md`(`references/project-profile-schema.md`의 schema 준수)를 채우는 절차와 휴리스틱.

---

## 목차

1. [개요](#1-개요)
2. [Greenfield / Brownfield 감지](#2-greenfield--brownfield-감지)
3. [조사 모드 결정](#3-조사-모드-결정)
4. [공통: 분석 대상 제외 룰](#4-공통-분석-대상-제외-룰)
5. [Stack 축 조사](#5-stack-축-조사)
6. [Architecture 축 조사](#6-architecture-축-조사)
7. [Convention 축 조사](#7-convention-축-조사)
8. [Maturity 축 조사 (deep only)](#8-maturity-축-조사-deep-only)
9. [Pain Points 축 조사 (deep only)](#9-pain-points-축-조사-deep-only)
10. [신뢰도 결정 알고리즘](#10-신뢰도-결정-알고리즘)
11. [병렬 실행 전략](#11-병렬-실행-전략)
12. [폴백 전략](#12-폴백-전략)

---

## 1. 개요

### 핵심 원칙

1. **측정값 + 근거** — 모든 추출 값은 `source` 필드와 함께 기록. 단순한 형식이 아니라, 사용자 검증·confidence 결정·baseline 재실행 시 비교 기반.
2. **빠른 신호 우선** — 매니페스트 파일은 단 한 번의 read로 stack의 80%를 알 수 있다. AST 파싱이나 grep 전수 조사는 매니페스트가 부족할 때만 폴백.
3. **휴리스틱은 명시적** — 애매한 경우 "이 휴리스틱으로 결정함"을 `meta.scan_warnings`에 기록. 사용자가 검토 시 어디를 의심해야 하는지 알 수 있게.
4. **언어 중립 우선, 특이사항은 분기** — 가능한 한 언어 무관한 접근(파일 확장자 통계, 디렉토리 패턴)으로 시작하고, 언어별 깊이는 필요할 때만.

### 시그널 우선순위

| 우선순위 | 신호 종류 | 비용 | 신뢰도 |
|---|---|---|---|
| 1 | 매니페스트 / 설정 파일 (package.json, tsconfig.json, ...) | 낮음 (단일 read) | 높음 |
| 2 | 디렉토리 구조 / 파일명 패턴 | 낮음 (ls 또는 glob) | 중간 |
| 3 | 도구 명령 결과 (`npm outdated`, `git log`) | 중간 | 높음 |
| 4 | 파일 내용 grep / AST 파싱 | 높음 | 상황별 |

이 순서로 시도하고, 1~2번에서 충분한 답이 나오면 3~4번을 건너뛴다.

---

## 2. Greenfield / Brownfield 감지

### 검사 순서

세 신호를 순차로 확인하고, 둘 이상 해당하면 **greenfield**로 분류:

#### 신호 1: Git 이력 부재 또는 빈약

```bash
# .git 부재
test -d .git || echo "NO_GIT"

# 또는 initial commit만 존재
git rev-list --count HEAD 2>/dev/null
# 결과가 1이면 greenfield 강한 신호 (단, 초기 import 후 1 커밋일 수도 있으니 다른 신호와 결합)
```

#### 신호 2: 패키지 매니페스트 부재

다음 매니페스트 파일들을 검사. 하나도 없으면 greenfield 강한 신호:

```
package.json, package-lock.json, pnpm-lock.yaml, yarn.lock,
requirements.txt, pyproject.toml, Pipfile, poetry.lock,
Cargo.toml, Cargo.lock,
go.mod, go.sum,
pom.xml, build.gradle, build.gradle.kts,
Gemfile, Gemfile.lock,
composer.json,
mix.exs,
*.csproj, *.fsproj
```

#### 신호 3: 소스 파일 부재

```bash
# 일반 소스 확장자 검색 (제외 룰 적용)
find . -type f \
  \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.tsx" \
     -o -name "*.go" -o -name "*.rs" -o -name "*.java" -o -name "*.rb" \
     -o -name "*.php" -o -name "*.cs" -o -name "*.swift" -o -name "*.kt" \) \
  -not -path "*/node_modules/*" -not -path "*/.venv/*" -not -path "*/dist/*" \
  | head -1
# 결과 비어있으면 greenfield 강한 신호
```

### 판정

| 신호 매칭 수 | 분류 |
|---|---|
| 3개 모두 | greenfield (확실) |
| 2개 | greenfield (`scan_warnings`에 미매칭 신호 명시) |
| 1개 이하 | brownfield |

### 경계 케이스

- **신규 프로젝트지만 매니페스트만 생성됨** (예: `npm init` 직후): 매니페스트는 있지만 dependencies가 비어있고 소스 파일도 없음 → brownfield의 minimum scan으로 처리. `scan_warnings`에 "매니페스트만 존재, 실질 코드 없음" 기록.
- **문서 전용 저장소** (소스 코드 없이 마크다운만): brownfield로 처리하되 stack 섹션이 비어있는 게 정상. structure_pattern을 `flat`으로 분류.

---

## 3. 조사 모드 결정

### 자동 룰

```
파일 수 ≤ 100 → Quick scan
파일 수 > 100 → Deep audit
```

파일 수는 위 신호 3의 검색 결과에 모든 코드 파일 확장자(.css, .scss, .html, .vue, .svelte, .yaml, ...)를 포함해 카운트.

### 사용자 키워드 오버라이드

| 사용자 표현 | 강제 모드 |
|---|---|
| "간단히 파악", "빠르게", "quick", "대략" | Quick |
| "전체 점검", "깊이 분석", "자세히", "deep", "철저히" | Deep |
| 명시 없음 | 자동 룰 |

### 모드 전환 가능

Quick으로 시작했다가 사용자가 깊은 분석을 요청하면 Deep으로 점진 확장 가능. 이 경우 stack/architecture/convention 결과는 보존하고 maturity/pain_points만 추가 수집. `scan_mode`를 `quick`에서 `deep`으로 변경.

---

## 4. 공통: 분석 대상 제외 룰

모든 축의 조사에서 다음 디렉토리/파일을 제외:

```
node_modules/, .venv/, venv/, env/, .env/,
dist/, build/, out/, target/, .next/, .nuxt/, .svelte-kit/,
.cache/, .turbo/, .parcel-cache/,
__pycache__/, .pytest_cache/, .mypy_cache/, .ruff_cache/,
coverage/, .coverage/, htmlcov/,
.git/, .svn/, .hg/,
vendor/, bower_components/,
*.min.js, *.min.css, *.bundle.js,
*.lock 파일 자체 (Cargo.lock 등) — 단, 존재 여부 확인 시는 검사
```

ripgrep(`rg`)을 사용한다면 `.gitignore`를 자동 존중하므로 추가 옵션 불필요. `find`나 `grep`은 명시적 `--exclude`/`-not -path` 필요.

---

## 5. Stack 축 조사

목표: `stack.languages`, `stack.frameworks`, `stack.build_tools`, `stack.test_tools`, `stack.package_manager`, `stack.runtime` 채우기.

### 5-1. 매니페스트 파일 read

가장 비용 효율적인 단계. 다음을 우선순위로 read:

| 매니페스트 | 추출 가능 항목 |
|---|---|
| `package.json` | dependencies, devDependencies, scripts (build/test/start), engines.node, packageManager |
| `pyproject.toml` | [project] dependencies, [tool.poetry], [tool.black], [tool.ruff], [tool.pytest] |
| `requirements.txt` | dependencies (버전 핀 단순) |
| `Cargo.toml` | [dependencies], [dev-dependencies], [build-dependencies] |
| `go.mod` | module name, require directives, go version |
| `pom.xml` / `build.gradle` | dependencies, plugins |
| `Gemfile` | gem dependencies |

### 5-2. 프레임워크 역할 분류

dependencies에서 알려진 프레임워크를 식별하고 `role` 필드 설정:

| Role | 패턴 |
|---|---|
| **frontend** | react, vue, svelte, angular, next, nuxt, remix, astro, solid, qwik |
| **backend** | express, fastify, koa, nestjs, hono, fastapi, django, flask, rails, gin, echo, axum, actix |
| **fullstack** | next, nuxt, remix (frontend 역할로도 분류, dual-role) |
| **mobile** | react-native, flutter, expo, swiftui, jetpack-compose |
| **orm** | prisma, typeorm, sequelize, sqlalchemy, gorm, diesel |
| **styling** | tailwindcss, styled-components, emotion, sass, postcss |
| **build** | webpack, vite, rollup, esbuild, parcel, turbopack, swc |
| **test** | jest, vitest, mocha, playwright, cypress, pytest, go test 표준 |
| **state** | redux, zustand, mobx, jotai, recoil, pinia |

알려지지 않은 프레임워크는 `role: "unknown"`으로 기록하고 본문에 패키지명 노출.

### 5-3. 언어별 LOC 분포

```bash
# tokei 가용 시 (가장 정확)
tokei --output json

# 폴백: 파일 확장자별 라인 수 집계
find . -type f -name "*.{ext}" -not -path "...제외..." -exec wc -l {} + | tail -1
```

`percent_loc`는 (해당 언어 라인 수) / (전체 코드 라인 수). 5% 미만 언어는 생략 가능 (단, 본문 서술에는 언급).

### 5-4. Package manager 식별

lockfile 우선:

```
package-lock.json → npm
yarn.lock → yarn
pnpm-lock.yaml → pnpm
bun.lockb → bun
poetry.lock → poetry
Pipfile.lock → pipenv
uv.lock → uv
Cargo.lock → cargo
go.sum → go modules
```

lockfile 부재 시 매니페스트의 `packageManager` 필드 또는 사용자에게 확인.

### 5-5. Runtime 버전 핀

```
.nvmrc, .node-version → node
.python-version, pyproject.toml#requires-python → python
go.mod#go directive → go
rust-toolchain.toml, rust-toolchain → rust
```

`engines` 필드(package.json)도 보조 신호.

---

## 6. Architecture 축 조사

목표: `architecture.structure_pattern`, `entry_points`, `key_directories`, `module_boundaries`, `data_flow_summary`.

### 6-1. Structure pattern 감지

다음 신호를 순서대로 확인:

```
신호 → 패턴

pnpm-workspace.yaml | lerna.json | turbo.json | nx.json
+ packages/* OR apps/*       → monorepo

go.work + 다중 go.mod          → multi-package
Cargo.toml [workspace]          → multi-package

src/features/* OR src/modules/* (도메인 이름)
+ 각 디렉토리 내 자체 완결적 구조 → feature-based

src/domain/, src/infrastructure/, src/application/  → domain-driven (DDD)

src/controllers/, src/services/, src/repositories/   → layered (전통 MVC)

src/ 또는 lib/ 하위에 평탄한 파일 구조        → flat

위 어느 것도 명확하지 않음                    → unknown
```

복합 케이스(예: monorepo + 각 패키지가 layered)는 `structure_pattern: monorepo`로 표기하고 본문에 추가 설명.

### 6-2. Entry points 식별

```
package.json#main, package.json#scripts.start, package.json#scripts.dev
pyproject.toml#[project.scripts]
go.mod 위치의 main.go, cmd/*/main.go
Cargo.toml#[[bin]] 또는 src/main.rs
build.gradle#mainClass

웹 프레임워크별 관용:
  Next.js: src/app/**/page.tsx, src/pages/**/*.tsx
  Django: */urls.py, manage.py
  Rails: config/routes.rb, app/controllers/
  Express: src/index.{ts,js}, src/app.{ts,js}
```

### 6-3. Key directories

상위 2단계의 디렉토리를 list화하고 각각의 목적을 추론:

```bash
# 디렉토리별 파일 수
find . -type d -not -path "...제외..." -mindepth 1 -maxdepth 2 \
  -exec sh -c 'echo "$(find "$1" -type f -not -path "...제외..." | wc -l) $1"' _ {} \; \
  | sort -rn
```

목적 추론은 디렉토리 이름 휴리스틱:
- `src/` → 메인 소스
- `tests/`, `test/`, `__tests__/`, `spec/` → 테스트
- `docs/` → 문서
- `scripts/`, `bin/` → 빌드/유틸 스크립트
- `lib/` → 공유 유틸
- `components/` → UI 컴포넌트
- `pages/`, `app/` → 라우팅 (Next.js, Nuxt 등)
- `features/`, `modules/`, `domains/` → 기능 모듈
- `migrations/`, `prisma/` → DB 스키마
- 알 수 없음: 본문에 노출하고 사용자 확인

### 6-4. Module boundaries

명확한 경계의 신호:
- 디렉토리 루트에 `index.ts` / `index.js` / `__init__.py` / `mod.rs` (public interface 패턴)
- 디렉토리 자체 매니페스트 (monorepo 패키지)
- `package.json#exports`로 명시적 노출 제어

각 경계 발견 시 `public_interface` 필드에 진입 파일 경로 기록. 없으면 `null`.

### 6-5. Data flow summary

본문 자유 서술. 추론 단서:
- 주요 entry point의 import 그래프 (top-level imports만)
- HTTP 핸들러 → 서비스 → 리포지토리 → DB 같은 layered 흐름 식별
- 클라이언트-서버 분리 시 두 흐름 별도 서술

이 항목은 정형화된 측정값이 아니므로 추론에 자신 없으면 "분석 보류"로 기록.

---

## 7. Convention 축 조사

목표: `file_naming`, `component_naming`, `test_location`, `formatter`, `linter`, `type_checking`.

### 7-1. 파일 naming consistency

```bash
# 소스 파일명 추출 (확장자 제외)
find src -type f -name "*.ts" -not -path "...제외..." -exec basename {} .ts \; \
  | grep -v "^index$" \
  > /tmp/filenames.txt

# 패턴별 매칭 수 카운트
kebab=$(grep -cE "^[a-z]+(-[a-z0-9]+)*$" /tmp/filenames.txt)
snake=$(grep -cE "^[a-z]+(_[a-z0-9]+)*$" /tmp/filenames.txt)
camel=$(grep -cE "^[a-z][a-zA-Z0-9]*$" /tmp/filenames.txt)
pascal=$(grep -cE "^[A-Z][a-zA-Z0-9]*$" /tmp/filenames.txt)
```

`consistency_score = max(매칭) / total`. 0.85 미만이면 `case_style: mixed`.

### 7-2. 도구 설정 파일 검출

```
포매터:
  .prettierrc(.json|.js|.yaml|.toml), prettier.config.{js,mjs}
  package.json#prettier
  pyproject.toml#[tool.black], pyproject.toml#[tool.ruff.format]
  rustfmt.toml, .rustfmt.toml
  .editorconfig
  gofmt (도구 자체, 설정 불필요)

린터:
  .eslintrc(.json|.js|.yaml), eslint.config.{js,mjs}
  pyproject.toml#[tool.ruff], .ruff.toml, ruff.toml
  pyproject.toml#[tool.flake8], .flake8, setup.cfg
  pyproject.toml#[tool.mypy], mypy.ini
  golangci-lint.yaml, .golangci.yml
  rubocop.yml, .rubocop.yml

타입 체커:
  tsconfig.json (strict 옵션 확인)
  pyproject.toml#[tool.mypy] (strict 옵션 확인)
  pyrightconfig.json
  Sorbet for Ruby (sorbet/config)
```

### 7-3. Strictness 추정

```
TypeScript:
  tsconfig.json#compilerOptions.strict = true                  → strict
  noImplicitAny + strictNullChecks 일부만                       → basic
  strict 옵션 없음                                             → off

ruff (Python):
  select에 다수 룰셋 + line-length 제한                        → strict
  기본 룰만                                                     → basic
  설정 없음                                                     → off

eslint:
  recommended + 추가 strict 플러그인 (typescript-eslint/strict 등) → error
  recommended만                                                  → warn
  설정 없거나 비활성                                             → off
```

### 7-4. Test location

```
collocated: src/foo/bar.test.ts (파일과 같은 디렉토리)
separate:   tests/foo/bar.test.ts (전용 디렉토리, 미러링 안 됨)
mirror:     src/foo/bar.ts ↔ tests/foo/bar.test.ts (구조 미러링)
mixed:      위 패턴들이 혼재
```

판정: 무작위 5~10개 테스트 파일을 샘플링하여 위 패턴 매칭.

---

## 8. Maturity 축 조사 (deep only)

### 8-1. Test coverage

```
coverage 디렉토리 검출:
  coverage/coverage-summary.json (Jest, Vitest)
  .coverage 파일 + coverage.xml (Python coverage)
  coverage.out (Go)
  cobertura.xml, lcov.info

리포트 파일이 있으면 read하여 line/branch coverage 추출.
없으면:
  설정만 있는지 (jest.config, vitest.config, .coveragerc) → null로 표기, scan_warnings에 "리포트 미생성"
  설정도 없음 → tool: null
```

### 8-2. CI/CD 설정

```
검색 위치:
  .github/workflows/*.{yml,yaml}     → github_actions
  .gitlab-ci.yml                      → gitlab_ci
  .circleci/config.yml                → circleci
  Jenkinsfile                         → jenkins
  bitbucket-pipelines.yml             → bitbucket
  azure-pipelines.yml, .azure-pipelines.yml → azure_devops
  .drone.yml                          → drone
```

각 워크플로우 파일에서 `name`, `on:` (triggers), `jobs.*.steps[].run` 명령에서 stages 추출:
- `lint`, `eslint`, `ruff` 명령 → `stages: [lint]`
- `test`, `pytest`, `vitest`, `jest` → `stages: [test]`
- `tsc --noEmit`, `mypy`, `pyright` → `stages: [typecheck]`
- `playwright`, `cypress`, `e2e` → `stages: [e2e]`
- `build`, `npm run build` → `stages: [build]`
- `deploy`, `vercel`, `firebase deploy` → `stages: [deploy]`

### 8-3. Documentation

| 측정값 | 방법 |
|---|---|
| `readme_present` | README.md 존재 여부 |
| `readme_quality` | 라인 수 + 섹션 수: <50줄 → minimal, 50-200 → standard, >200 → comprehensive |
| `api_docs_present` | docs/ 디렉토리, openapi.yaml/json, swagger.json, JSDoc/TSDoc 출력 여부 |
| `adr_count` | docs/adr/, docs/decisions/, doc/architecture/ 하위 마크다운 파일 수 |
| `inline_comment_density` | 주석 라인 / 전체 라인 (언어별 주석 패턴: `//`, `#`, `/*...*/`) |

### 8-4. Type safety

TypeScript의 경우:
```bash
# any 사용 빈도
rg --no-heading -c '\bany\b' --type ts | awk -F: '{sum+=$2} END {print sum}'

# 전체 타입 어노테이션 위치 추정
rg --no-heading -c ':' --type ts | awk -F: '{sum+=$2} END {print sum}'
```

`coverage_percent = 1 - (any 사용 / 추정 어노테이션)`. 추정치이므로 `confidence_low`에 등록 권장.

Python의 경우 mypy 리포트 활용 또는 `# type: ignore` 빈도로 추정.

### 8-5. Dependency health

```
Node.js:
  npm outdated --json              → outdated_count
  npm audit --json                 → known_vulnerabilities
  package.json + npm registry 조회 → deprecated 검출

Python:
  pip list --outdated --format=json
  safety check --json (또는 pip-audit)

Rust:
  cargo outdated --format=json
  cargo audit --json

Go:
  go list -u -m -json all
  govulncheck ./...
```

도구 미설치 시 lockfile 자체 분석으로 추정 (정확도 떨어짐, `confidence_low`에 등록).

---

## 9. Pain Points 축 조사 (deep only)

### 9-1. Git churn 분석

```bash
# 최근 30일 변경 횟수 상위 파일
git log --since="30 days ago" --name-only --pretty=format: \
  | grep -v "^$" \
  | sort | uniq -c | sort -rn \
  | head -20

# 전체 churn 대비 비율 계산용 총 변경 수
git log --since="30 days ago" --name-only --pretty=format: \
  | grep -v "^$" | wc -l
```

`period_days`는 30일 기본. 큰 프로젝트(>1000 파일)는 90일로 확장 권장.

핫스팟 임계: 전체 churn의 5% 이상 또는 절대 변경 횟수 10회 이상. 둘 다 만족하지 않으면 핫스팟 아님.

### 9-2. TODO marker

```bash
# ripgrep 사용 (빠름, .gitignore 자동 존중)
rg -n --type-add 'src:*.{ts,tsx,js,jsx,py,go,rs,java,rb,php,swift,kt}' \
   --type src \
   '\b(TODO|FIXME|HACK|XXX)\b'
```

집계:
- `total_count`: 전체 매칭 수
- `by_type`: marker별 카운트
- `examples`: 최대 5개 (다양한 파일에서 샘플링)

### 9-3. Skipped tests

언어별 패턴:

```
JavaScript/TypeScript:
  it.skip(, xit(, describe.skip(, xdescribe(, test.skip(

Python (pytest):
  @pytest.mark.skip, @pytest.mark.skipif, @unittest.skip

Go:
  t.Skip(, t.Skipf(

Ruby (RSpec):
  xit(, skip, xdescribe(

Rust:
  #[ignore]
```

각 매칭에서 위 라인의 코멘트(`reason`)도 함께 추출:

```bash
rg -B1 'it\.skip\(' --type ts
# 결과에서 //, /* 형태 코멘트가 있으면 reason으로 캡처
```

### 9-4. Deprecated usages

검출 대상:
- 매니페스트의 deprecated 패키지 (npm/pip 등 도구가 알려줌)
- 알려진 deprecated API 패턴 (프레임워크 마이그레이션 가이드 기반)
- 프로젝트의 `@deprecated` JSDoc/TSDoc 어노테이션

대표 패턴 예시 (확장 가능):
```
Next.js: getServerSideProps, getStaticProps (App Router에서 더 이상 권장 안 됨)
React: componentWillMount, componentWillReceiveProps
Node: fs.exists (callback)
Python: imp 모듈, asyncio.coroutine
```

### 9-5. Complexity outliers

도구 가용 시:
- JavaScript/TypeScript: `eslint-plugin-sonarjs`, `complexity-report`
- Python: `radon cc`, `wily`
- Go: `gocyclo`
- Rust: `cargo-geiger` (다른 메트릭이지만 보조)

폴백 — 함수/파일 길이 기반 휴리스틱:
- 단일 파일 >500줄
- 단일 함수 >100줄 (언어별 구분 필요)

임계는 임의가 아닌 측정 분포 기반: 전체의 95-percentile 초과 시 outlier로 분류.

---

## 10. 신뢰도 결정 알고리즘

각 측정값에 다음 룰을 적용해 confidence 결정 (project-profile-schema.md 6장의 매핑에서 사용):

```
직접 측정 (manifest, config 파일에서 명시) → high
다중 신호 일치 (예: 3개 이상의 source가 일치) → medium
단일 신호 + 휴리스틱 추정              → low → meta.confidence_low에 등록
```

### Confidence 영향 요인

| 요인 | Confidence 하향 |
|---|---|
| 도구 미설치로 폴백 사용 (예: tokei 없이 파일 확장자만으로 LOC 추정) | -1 단계 |
| 단일 파일 신호 + 다른 신호와 충돌 | -1 단계 |
| 추론 (예: contributor 수로 team size 결정) | low로 강제 |

### 본문 기록

`meta.confidence_low`에 등록된 항목은 `# Scan Notes` 섹션에서 사람이 읽을 수 있게 설명:

```markdown
## Scan Notes

### Confidence Low
- **constraints.team.size**: git contributor 수(5명)로 `small` 추정.
  실제 활성 멤버는 다를 수 있음. Phase 2-3에서 확인 필요.
- **type_safety.coverage_percent**: any 사용 빈도(rg) 기반 추정.
  실제 타입 어노테이션 비율과 다를 수 있음.
```

---

## 11. 병렬 실행 전략

### Quick scan

5축 중 3축만 수집하고 매니페스트/설정 파일 read가 대부분이므로 직접 실행. 서브 에이전트 불필요.

### Deep audit

5축 모두 수집하고 git churn 등 시간 소요 작업 포함. 다음 패턴 권장:

```
[리더 = Code Research 오케스트레이터]
  ├── Agent(stack-analyst, run_in_background=true)
  ├── Agent(architecture-analyst, run_in_background=true)
  ├── Agent(convention-analyst, run_in_background=true)
  ├── Agent(maturity-analyst, run_in_background=true)
  └── Agent(pain-points-analyst, run_in_background=true)
```

각 서브 에이전트는 자기 축의 결과를 `_workspace/_baseline/_partial/{axis}.yaml`에 기록.
리더가 모든 결과를 모아 `project_profile.md`로 합성.

> Phase 1은 Code Research 자체가 mini-pipeline이지만, 이는 메인 하네스 워크플로우의 일부. 메인 SKILL.md의 Phase 4 팀 아키텍처와 혼동하지 말 것.

### 의존성

축 간 의존성은 거의 없음. 단:
- pain_points의 churn 분석은 architecture의 key_directories를 활용해 "feature 디렉토리별 churn 비교" 같은 derived 통찰 가능 — 이는 모든 축 수집 후 후처리 단계.

---

## 12. 폴백 전략

### 도구 부재 시

| 가용 도구 없음 | 폴백 |
|---|---|
| tokei/cloc | `find` + `wc -l` (정확도 낮음, `confidence_low`) |
| ripgrep | `grep -r` + 명시적 `--exclude` (느림, 결과 동일) |
| `npm outdated` 등 (network access 없음) | lockfile 직접 분석으로 outdated 추정. 정확도 낮음 |
| coverage 리포트 미생성 | `null`로 두고 `scan_warnings`에 명시 |
| `git`은 있지만 `--since` 옵션 무관하게 commit 부족 | period_days 단축 (예: 7일) 또는 churn 분석 생략 |

### 큰 코드베이스 (>10,000 파일)

- 파일 수 카운트만으로도 시간 소요 — 상위 디렉토리부터 점진 탐색
- git churn은 `--since="14 days ago"` 등 단축
- `key_directories`는 file_count 상위 10개만 보고

### Monorepo

- 각 패키지를 독립 sub-scan으로 처리하고 결과를 패키지별로 모아 `architecture.module_boundaries`에 기록
- stack은 루트 + 각 패키지의 매니페스트를 모두 읽어 통합

### Git 미사용 프로젝트

- pain_points.churn_hotspots 생략 → `unanalyzed`에 등록
- 다른 축은 정상 수집 가능
