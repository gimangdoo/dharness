# Harness — Team-Architecture Factory for Claude Code

> 도메인 한 문장을 **에이전트 팀 + 스킬 세트**로 변환하는 메타 스킬.
> A meta-skill that turns a domain description into an agent team and the skills they use.

[![Version](https://img.shields.io/badge/version-1.2.0-7c6bf0)](./CHANGELOG.md)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](./LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-v2.x+-34d399)](https://claude.ai/code)

---

## 무엇인가

`harness`는 Claude Code 플러그인입니다. 사용자가 도메인/프로젝트를 한 문장으로 설명하면, 해당 도메인에 특화된 **에이전트 3~5명**과 그들이 사용할 **스킬 세트**를 `.claude/agents/`·`.claude/skills/`에 자동 생성합니다.

다른 단일 에이전트/프롬프트 프레임워크와 달리, harness는 **팀 아키텍처 팩토리**입니다 — 6가지 사전 정의된 팀 패턴 중 도메인에 맞는 것을 선택하고 에이전트 협업 프로토콜을 함께 설계합니다.

### 6 팀 아키텍처 패턴

| 패턴 | 적합한 작업 |
|------|----------|
| **Pipeline** | 단계별 순차 흐름 (분석 → 설계 → 검증) |
| **Fan-out / Fan-in** | 병렬 분기 → 결과 통합 (멀티 소스 리서치) |
| **Expert Pool** | 도메인별 전문가 풀에서 동적 선택 (티켓 라우팅) |
| **Producer-Reviewer** | 생성-비판 분리 (코드 작성 + 리뷰) |
| **Supervisor** | 메타 에이전트가 분배·모니터·종합 |
| **Hierarchical Delegation** | 상위 → 하위 위임, 결과 상위 통합 |

---

## Quickstart (5분)

```bash
# 1. 마켓플레이스 등록
claude plugin marketplace add revfactory/harness

# 2. 플러그인 설치 + Agent Teams 플래그
claude plugin install harness@harness
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# 3. 한 문장으로 하네스 생성
claude "build a harness for a fintech risk-assessment team"
# 또는
claude "하네스 구성해줘 — 핀테크 리스크 평가 팀"
```

상세 절차·실패 FAQ는 [`docs/quickstart.md`](./docs/quickstart.md).

---

## 프로젝트 구조

```
.
├── .claude-plugin/        # 플러그인·마켓플레이스 메타데이터
├── skills/
│   └── harness/           # 메타 스킬 본체 (SKILL.md + references/)
├── docs/                  # 사용자 문서
│   ├── quickstart.md
│   └── experimental-dependency.md
├── _workspace/            # 릴리스 감사·런치 산출물 (개발자용)
├── .github/               # 이슈·PR 템플릿
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE                # Apache-2.0
└── index.html             # 랜딩 페이지 (GitHub Pages)
```

---

## 문서 인덱스

| 문서 | 용도 |
|------|------|
| [`docs/quickstart.md`](./docs/quickstart.md) | 5분 안에 첫 하네스 생성 |
| [`docs/experimental-dependency.md`](./docs/experimental-dependency.md) | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 플래그 의존성 설명 |
| [`skills/README.md`](./skills/README.md) | 스킬 디렉토리 인덱스 + 11개 references 가이드 |
| [`skills/harness/SKILL.md`](./skills/harness/SKILL.md) | 메타 스킬 정의 (11 Phase 워크플로우) |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | 기여 가이드 + 응답 SLA |
| [`CHANGELOG.md`](./CHANGELOG.md) | 버전별 변경 이력 |

### Skill 워크플로우 한눈에

`harness` 메타 스킬은 11단계로 동작합니다:

| Phase | 이름 | 출력 |
|-------|------|------|
| 0 | Pre-flight 감사 | 신규/확장/유지보수 분기 |
| 1 | Code Research | `_workspace/_baseline/project_profile.md` |
| 2 | Project Inquiry | `_workspace/_baseline/intent_profile.md` |
| 3 | 도메인 분석 | 작업 유형 + 충돌 분석 |
| 4 | 팀 아키텍처 | 모드 + 패턴 + 분리 기준 |
| 5 | 에이전트 정의 | `.claude/agents/{name}.md` |
| 6 | 스킬 생성 | `.claude/skills/{name}/SKILL.md` |
| 7 | 오케스트레이션 | 통합 스킬 + CLAUDE.md 포인터 |
| 8 | 검증 (7단계) | 구조·실행·트리거·드라이런·반복 개선 |
| 9 | 진화 (수동) | 사용자 피드백 → 에이전트/스킬 갱신 |
| 10 | Runtime Adaptation | telemetry → drift 감지 → 제안+승인 |

상세는 [`skills/harness/SKILL.md`](./skills/harness/SKILL.md).

---

## 사전 요구사항

- **Claude Code v2.x 이상** (Agent Teams API 지원)
- 환경 변수 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (왜 필요한지: [`docs/experimental-dependency.md`](./docs/experimental-dependency.md))

---

## 기여

기여 환영. 시작 전 [`CONTRIBUTING.md`](./CONTRIBUTING.md)의 **응답 SLA**(PR 1차 응답 72h, Issue triage 48h)와 PR 컨벤션을 확인해주세요.

- 버그: `.github/ISSUE_TEMPLATE/bug_report.yml`
- 기능 제안: `.github/ISSUE_TEMPLATE/feature_request.yml`
- 토론: GitHub Discussions

---

## 라이선스

[Apache-2.0](./LICENSE) © revfactory
