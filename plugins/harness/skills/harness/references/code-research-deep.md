# Code Research — Deep Audit 축 (Maturity / Pain Points)

> **베이스:** [code-research.md](./code-research.md) — deep audit 전용 2축(Maturity·Pain Points) 상세 조사 기법 분리분 (2026-05-31 doc 분할 #2). quick scan은 §5-7만, deep audit 시 본 2축 추가. 신뢰도 결정·병렬 실행·폴백은 베이스 단일 출처.

> **휴리스틱 임계값 baseline:** Pain Points 핫스팟 임계값은 [`heuristics-baseline.md §1`](heuristics-baseline.md#1-phase-1--code-research) 단일 출처.

---

## 목차

1. [Maturity 축 조사 (deep only)](#1-maturity-축-조사-deep-only)
2. [Pain Points 축 조사 (deep only)](#2-pain-points-축-조사-deep-only)

---

## 1. Maturity 축 조사 (deep only)

### 1-1. Test coverage

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

### 1-2. CI/CD 설정

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

### 1-3. Documentation

| 측정값 | 방법 |
|---|---|
| `readme_present` | README.md 존재 여부 |
| `readme_quality` | 라인 수 + 섹션 수: <50줄 → minimal, 50-200 → standard, >200 → comprehensive |
| `api_docs_present` | docs/ 디렉토리, openapi.yaml/json, swagger.json, JSDoc/TSDoc 출력 여부 |
| `adr_count` | docs/adr/, docs/decisions/, doc/architecture/ 하위 마크다운 파일 수 |
| `inline_comment_density` | 주석 라인 / 전체 라인 (언어별 주석 패턴: `//`, `#`, `/*...*/`) |

### 1-4. Type safety

TypeScript의 경우:
```bash
# any 사용 빈도
rg --no-heading -c '\bany\b' --type ts | awk -F: '{sum+=$2} END {print sum}'

# 전체 타입 어노테이션 위치 추정
rg --no-heading -c ':' --type ts | awk -F: '{sum+=$2} END {print sum}'
```

`coverage_percent = 1 - (any 사용 / 추정 어노테이션)`. 추정치이므로 `confidence_low`에 등록 권장.

Python의 경우 mypy 리포트 활용 또는 `# type: ignore` 빈도로 추정.

### 1-5. Dependency health

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

## 2. Pain Points 축 조사 (deep only)

### 2-1. Git churn 분석

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

### 2-2. TODO marker

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

### 2-3. Skipped tests

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

### 2-4. Deprecated usages

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

### 2-5. Complexity outliers

도구 가용 시:
- JavaScript/TypeScript: `eslint-plugin-sonarjs`, `complexity-report`
- Python: `radon cc`, `wily`
- Go: `gocyclo`
- Rust: `cargo-geiger` (다른 메트릭이지만 보조)

폴백 — 함수/파일 길이 기반 휴리스틱:
- 단일 파일 >500줄
- 단일 함수 >100줄 (언어별 구분 필요)

임계는 임의가 아닌 측정 분포 기반: 전체의 95-percentile 초과 시 outlier로 분류.
