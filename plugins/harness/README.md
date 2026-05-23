# Harness — Team-Architecture Factory for Claude Code

> 도메인 한 문장을 **에이전트 팀 + 스킬 세트**로 변환하는 메타 스킬.
> A meta-skill that turns a domain description into an agent team and the skills they use.

## 무엇인가

Claude Code용 메타 스킬 플러그인. 도메인/프로젝트 설명을 입력하면 11-phase 워크플로우로 에이전트 정의(`.claude/agents/`)와 스킬 세트(`.claude/skills/`)를 자동 생성한다.

다른 단일 에이전트/프롬프트 프레임워크와 달리 **팀 아키텍처 팩토리** — 6가지 사전 정의된 팀 패턴 중 도메인에 맞는 것을 선택하고 에이전트 협업 프로토콜을 함께 설계한다.

### 6 팀 아키텍처 패턴

| 패턴 | 적합한 작업 |
|------|----------|
| **Pipeline** | 단계별 순차 흐름 (분석 → 설계 → 검증) |
| **Fan-out / Fan-in** | 병렬 분기 → 결과 통합 (멀티 소스 리서치) |
| **Expert Pool** | 도메인별 전문가 풀에서 동적 선택 (티켓 라우팅) |
| **Producer-Reviewer** | 생성-비판 분리 (코드 작성 + 리뷰) |
| **Supervisor** | 메타 에이전트가 분배·모니터·종합 |
| **Hierarchical Delegation** | 상위 → 하위 위임, 결과 상위 통합 |

## 설치

### Plugin marketplace

```powershell
claude plugin marketplace add gimangdoo/dharness
claude plugin install harness@dharness
```

### Local (개발용)

```powershell
claude --plugin-dir <path>/plugins/harness
```

## 빠른 시작

새 도메인에 적용:

```text
/harness:harness-new 코드 리뷰를 자동화하는 도메인
```

→ 사용자 프로젝트의 `.claude/agents/{name}.md`·`.claude/skills/{name}/SKILL.md`·`CLAUDE.md`에 산출물 생성.

자연어 트리거도 가능:

```text
"하네스 구성해줘", "에이전트 팀 설계", "이 프로젝트 자동화 체계 만들어줘"
```

## 호출 방식

| 방식 | 발동 | 비용 통제 | 용도 |
|---|---|---|---|
| **자연어 트리거** | 자연 발화 ↔ skill description 매칭 | LLM이 자동 분기 | 자연스러운 발화 |
| **Slash command** | `/harness:harness-*` 결정적 호출 | Phase 범위 직접 지정 | 비용 회피, 트리거 확률 의존 제거 |

### Slash command 카탈로그 (17개)

**합성·확장 (5)**
```
/harness:harness-new <도메인> [--mode=single|derived]     # 하네스 신규 구축 (Phase 0-8 + Phase 10 인프라)
/harness:harness-add-agent <역할>                          # 에이전트 1명 추가 (Phase 4·5·7·8)
/harness:harness-add-skill <스킬>                          # 스킬 1개 추가/수정 (Phase 6·7·8)
/harness:harness-split <agent|skill> <원본> <결과 2+>     # 책임 분할 + 참조 갱신
/harness:harness-merge <agent|skill> <결과> <원본 2+>     # 책임 통합 + 참조 갱신
```

**제거·진화 (3)**
```
/harness:harness-remove <agent|skill> <이름>              # 1개 제거 + 잔여 참조 자동 정리
/harness:harness-evolve <피드백>                           # 피드백 반영 (Phase 9 수동 진화 진입점)
/harness:harness-adapt                                     # 관측 기반 적응 (Phase 10 telemetry drift)
```

**보조 (1)**
```
/harness:harness-grill <phase 0.5|2|5|9> [필드]           # 추궁 모드 — 모호 답안 1q씩 추천 답 + 사용자 확정
```

**진단·검증 (4)**
```
/harness:harness-status [--verbose]                        # 하네스 현황 (구성·기준선·drift·MCP, read-only)
/harness:harness-baseline                                  # 기준선 갱신 (Phase 1·2 재실행 + plugin version 박제)
/harness:harness-audit                                     # 추론 영역 감사 (책임·트리거·워크플로우, read-only)
/harness:harness-validate [--json] [--strict]              # 결정적 검증 (구조·스키마·체인 + version drift 알림, LLM 0)
```

**MCP (1 통합 + 3 원본 = 4)**
```
/harness:harness-mcp <recommend|adopt|status> [args]       # MCP 통합 진입점 (추천·채택·상태 라우터)
/harness:harness-mcp-recommend <에이전트|역할>             # MCP 후보 추천 (효율성·확장성·정확도 3축)
/harness:harness-mcp-adopt <사유>                          # MCP 신규 채택 (발견→탐침→확인→설치→반영 5단계)
/harness:harness-mcp-status                                # MCP 상태 진단 (인벤토리·도구·비용·정합, read-only)
```

> 통합 명령은 *추가* 진입점 — 기존 3 명령도 그대로 유지된다 (install 사용자 break-change 0). 신규 사용자에는 단일 진입점 권장.

### 명령 분기 doctrine (2026-05-14, doctrine drift refit 행 2026-05-23)

| 의도 | 명령 |
|---|---|
| 사용자 *명시 피드백* (자유 텍스트) | `evolve` |
| 시스템 *자동 drift 감지* (telemetry) | `adapt` |
| 명시적 *제거·분할·통합* (격리) | `remove` / `split` / `merge` |
| *LLM 추론* 영역 감사 (의미·일관성) | `audit` |
| *deterministic* 영역 검증 (구조·schema·chain) | `validate` |
| 진행 가시성 *단일 진입점* | `status` |
| 모호 답안 *1q-at-a-time* 추궁 | `grill` |
| *plugin upgrade* 후 doctrine refit | `validate` + `audit` 진단 → `evolve`·`add-*`·`remove`로 수정 (자동 알림은 status·validate에서 ℹ️ 1줄) |

### Doctrine drift refit 워크플로우 (2026-05-23, v0.11.0)

dharness plugin doctrine 자체가 업그레이드된 후(예: 새 invariant 추가) 기존 derived harness를 새 doctrine으로 끌어올리는 절차. 단일 명령이 아니라 *기존 명령 조합*:

1. **자동 알림** — `harness-new`·`harness-baseline`이 합성·갱신 시점 `meta.dharness_version`을 `intent_profile.md`에 박제. 이후 `/harness:harness-status` 또는 `/harness:harness-validate` 호출 시 baseline version ↔ 현 plugin `version` 비교 → mismatch면 ℹ️ refit 권고 1줄 출력.
2. **진단** — `/harness:harness-audit` (LLM 추론 영역) + `/harness:harness-validate` (결정적 invariant). 새 doctrine 위반 항목 enumeration.
3. **수정** — 진단 보고서 항목별로 `/harness:harness-evolve` (피드백 형식), `/harness:harness-add-skill`·`-add-agent` (누락 항목), `/harness:harness-remove`·`-merge`·`-split` (구조 변경).
4. **재진단** — `/harness:harness-validate` 0 errors 확인.

## 워크플로우 개요

```
Phase 0   기존 하네스 감사 (drift 감지)
Phase 1   Code Research (객관 baseline)
Phase 2   Project Inquiry (주관 의도)
Phase 3   도메인 분석 (객관 + 주관 합성)
Phase 4   팀 아키텍처 설계 (6 패턴 중 선택)
Phase 5   에이전트 정의 생성 (.claude/agents/)
Phase 5-2 도구·MCP 자동 할당 (제안 + 사용자 confirm)
Phase 6   스킬 생성 (.claude/skills/)
Phase 7   통합·오케스트레이션 (CLAUDE.md 포인터)
Phase 8   검증·테스트 (트리거 should/should-NOT)
Phase 9   사용자 피드백 기반 진화
Phase 10  Runtime Adaptation (telemetry drift 자동 감지)
```

상세는 `skills/harness/SKILL.md` 본문 + `skills/harness/references/` 참조.

## 핵심 설계 원칙

1. **에이전트 팀이 기본 실행 모드** — 2명 이상 협업이면 반드시 팀 먼저 검토 (서브 에이전트는 단일 작업 대안).
2. **모든 에이전트는 `.claude/agents/{name}.md` 파일로 정의** — 빌트인 타입 포함 필수. 재사용성·협업 프로토콜·"누가/어떻게" 분리.
3. **CLAUDE.md에 하네스 포인터 등록** — 새 세션에서 오케스트레이터 스킬 자동 트리거.
4. **하네스는 진화하는 시스템** — Phase 9(수동) + Phase 10(자동 telemetry drift)로 baseline 지속 갱신.
5. **MCP 자동 install·자동 `allow` 승급 금지** — T0(무키·로컬)이라도 사용자 confirm gate 통과 필수.

## 산출물 구조 (생성 후)

```
<derived-project>/
├── .claude/
│   ├── agents/
│   │   └── {agent-name}.md           # 에이전트 정의 (frontmatter + 본문)
│   └── skills/
│       └── {skill-name}/
│           ├── SKILL.md              # 스킬 본문
│           └── references/           # (선택) 보조 자료
├── _workspace/
│   ├── _baseline/                    # project_profile.md + intent_profile.md (meta.dharness_version 박제) + changelog.md (skeleton)
│   └── _telemetry/                   # Phase 10 capture 출력
└── CLAUDE.md                         # 하네스 포인터 (운영·구조·규칙)
```

## 호환성·제약

- Claude Code CLI / desktop / VS Code extension 지원.
- 에이전트 모델 `opus` 권장 (하네스 품질이 추론 능력에 직결).
- MCP 채택은 사용자 명시 confirm gate 필수 — 자동 install 정책 미지원.
- `.harness-host` marker file이 존재하는 디렉토리는 self-host 격리 영역 — `harness-mcp-*` 명령은 해당 위치에서 차단됨.

## 라이선스·저장소

- Repository: <https://github.com/gimangdoo/dharness>
- Issues: 본 plugin 관련 이슈는 dharness repo issue tracker.
