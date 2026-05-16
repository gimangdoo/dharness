# Team Tools API — 6 도구 시그니처 박제

> **English POC (P7-1, 2026-05-14):** 영문 변환 [team-tools-api.en.md](./team-tools-api.en.md) 공존. P7-2 회귀 검증 통과까지 본 한국어 파일이 source of truth, cross-link 모두 `team-tools-api.md` 그대로.
>
> **Read at phase:** Sub-agent 활용 시 Phase 1/5/6/8 (격리 호출 패턴 필요 시점) + Phase 4 팀 설계 시 의사코드 검증.
>
> **목적**: `TeamCreate` / `SendMessage` / `TaskCreate` / `TaskUpdate` / `TaskGet` / `TaskOutput` 6 도구의 실 API schema 박제. SKILL.md Phase 4·5·7, `agent-design-patterns.md`, `orchestrator-template.md`, `team-examples.md` 의사코드 영역의 단일 출처 reference.
>
> **상태 표기 doctrine (2026-05-14)**:
> - `✅ verified` — Claude Code 공식 도구 카탈로그 박제 + 1회 이상 실호출 trial 박제
> - `📜 docs-only` — Claude Code 공식 문서 인용만, 실호출 미검증
> - `❓ inferred` — empirical 추론 (실 호출 결과 + 일반 Anthropic SDK 시그니처 추정)
>
> **읽는 phase**: Phase 4 (팀 구성 결정) · Phase 5 (에이전트 정의) · Phase 7 (오케스트레이션) — 각 phase에서 본 reference의 *해당 도구 섹션만* lazy load.

---

## §1 도구 사용 시나리오 매트릭스 (Phase 4 가이드)

| 시나리오 | 사용 도구 | 비고 |
|---|---|---|
| 2명 이상 협업 (기본 모드) | `TeamCreate` + `TaskCreate` + `SendMessage` | 템플릿 A 기본 |
| 단발 격리 위임 | `Agent` (Claude Code built-in, 본 reference 범위 외) | 템플릿 B |
| 비동기 작업 풀 | `TaskCreate` + `TaskGet` + `TaskOutput` | 작업 풀 + 폴링 |
| 진행 갱신 | `TaskUpdate` | status 전이 |
| 팀원 간 데이터 전달 | `SendMessage` | inbox 패턴 |

---

## §2 `TeamCreate` ❓ inferred

**목적**: 2명 이상의 에이전트로 구성된 팀을 생성. 팀명 + 멤버 N명 정의.

**시그니처** (의사 schema — 실 호출 trial 박제 권장):

```yaml
TeamCreate:
  parameters:
    team_name: string         # 필수 — 팀 식별자 (slug 형식)
    members:                  # 필수 — 멤버 배열 (≥2)
      - name: string          # 필수 — 멤버 식별자 (slug)
        agent_type: string    # 필수 — "general-purpose" | "Explore" | "Plan" | 커스텀 agent 이름
        model: string         # 선택 — "opus" | "sonnet" | "haiku" (기본 "opus")
        prompt: string        # 필수 — 역할 설명 + 작업 지시
        tools: [string]       # 선택 — 멤버별 도구 allowlist (frontmatter `tools:` 박제와 동기)
    description: string       # 선택 — 팀 목적 1줄
  returns:
    team_id: string           # 후속 SendMessage / TaskCreate에서 활용
    members: [object]         # 생성된 멤버 상세
```

**실패 모드** (empirical 추정):
- `team_name` 중복: 동일 세션 내 동일 팀명 재호출 시 에러
- `members` < 2: 단발 위임은 `Agent` 사용 (본 도구 범위 외)
- `agent_type` 미존재: `.claude/agents/{name}.md` 미존재 + 빌트인 타입도 아닌 경우

**예시**:

```yaml
TeamCreate(
  team_name: "research-team"
  members:
    - name: "researcher"
      agent_type: "general-purpose"
      model: "opus"
      prompt: "도메인 X 관련 자료를 수집한다."
      tools: ["WebSearch", "WebFetch", "Read"]
    - name: "synthesizer"
      agent_type: "general-purpose"
      model: "opus"
      prompt: "수집된 자료를 합성한다."
      tools: ["Read", "Write"]
)
```

**참고**: 정확한 시그니처는 Claude Code 공식 도구 카탈로그 + 실 호출 trial로 검증 필요. P1-1 AC: 실호출 trial 박제 또는 `claude-code-guide` agent 호출.

---

## §3 `SendMessage` ❓ inferred

**목적**: 팀원 간 메시지 전달. inbox 패턴 — 수신자가 후속 turn에서 폴링.

**시그니처**:

```yaml
SendMessage:
  parameters:
    team_id: string           # 필수 — TeamCreate 반환값
    from: string              # 필수 — 송신자 멤버 name
    to: string                # 필수 — 수신자 멤버 name
    content: string           # 필수 — 메시지 본문 (markdown 허용)
    metadata: object          # 선택 — 구조화 페이로드 (key-value)
  returns:
    message_id: string        # 추적용
    delivered: boolean        # inbox 적재 여부
```

**실패 모드**:
- `to`가 team의 members에 미존재
- `team_id` 미존재 또는 세션 만료
- `content` 빈 문자열

**예시**:

```yaml
SendMessage(
  team_id: "research-team-001"
  from: "researcher"
  to: "synthesizer"
  content: "1단계 자료 수집 완료. _workspace/01_researcher_findings.md 참조."
)
```

---

## §4 `TaskCreate` ❓ inferred

**목적**: 팀 작업 풀에 작업 N개 등록. 의존성·assignee 지정 가능.

**시그니처**:

```yaml
TaskCreate:
  parameters:
    tasks:                    # 필수 — 작업 배열
      - title: string         # 필수 — 작업 제목
        description: string   # 필수 — 상세 지시
        assignee: string      # 선택 — 멤버 name (미지정 시 unclaimed)
        depends_on: [string]  # 선택 — 선행 작업 title 또는 task_id
        priority: string      # 선택 — "high" | "medium" | "low" (기본 "medium")
        metadata: object      # 선택
  returns:
    task_ids: [string]
```

**팀원당 5~6개 작업이 적정** (orchestrator-template.md doctrine).

**실패 모드**:
- `depends_on`이 미존재 task 참조 (cycle 검출 시 에러)
- `assignee`가 멤버 목록에 미존재

**예시**:

```yaml
TaskCreate(
  tasks:
    - title: "도메인 X 1차 자료 수집"
      description: "WebSearch로 키워드 3개로 자료 수집 후 _workspace/01_researcher.md에 저장"
      assignee: "researcher"
    - title: "수집 자료 합성"
      description: "_workspace/01_researcher.md를 입력으로 받아 _workspace/02_synthesizer.md 생성"
      assignee: "synthesizer"
      depends_on: ["도메인 X 1차 자료 수집"]
)
```

---

## §5 `TaskUpdate` ❓ inferred

**목적**: 작업 상태 전이. assignee가 작업 진행 중 호출.

**시그니처**:

```yaml
TaskUpdate:
  parameters:
    task_id: string           # 필수
    status: string            # 선택 — "pending" | "in_progress" | "completed" | "blocked" | "deleted"
    owner: string             # 선택 — assignee 변경
    description: string       # 선택 — 갱신
    metadata: object          # 선택 — merge
    addBlocks: [string]       # 선택 — 본 작업이 차단하는 task_ids
    addBlockedBy: [string]    # 선택 — 본 작업을 차단하는 task_ids
  returns:
    task: object              # 갱신된 작업 전체
```

**status 워크플로우**: `pending` → `in_progress` → `completed`. `blocked`는 지연 사유 박제. `deleted`는 영구 제거.

---

## §6 `TaskGet` ❓ inferred

**목적**: 단일 작업 상세 조회.

**시그니처**:

```yaml
TaskGet:
  parameters:
    task_id: string           # 필수
  returns:
    task: object              # title / description / status / owner / blockedBy / blocks / metadata / comments
```

---

## §7 `TaskOutput` ❓ inferred

**목적**: 작업의 *산출물* 조회. assignee가 작업 완료 시 output 박제, 후속 작업이 본 도구로 input 수신.

**시그니처**:

```yaml
TaskOutput:
  parameters:
    task_id: string           # 필수
    format: string            # 선택 — "raw" | "markdown" | "json" (기본 "raw")
  returns:
    output: string | object   # 작업 산출물
    produced_at: string       # ISO 시각
```

**파일 기반 산출물 패턴 (orchestrator-template.md 정합)**: assignee가 작업 결과를 `_workspace/{phase}_{name}_{artifact}.{ext}`에 저장 후 `TaskUpdate(metadata: {output_path: "..."})`로 박제. 후속 작업이 `TaskGet` + 경로로 직접 Read — `TaskOutput`은 *인라인 결과* 패턴에 활용 (작은 산출물).

---

## §8 호출 패턴 — 오케스트레이터 합성 (Phase 7 가이드)

```yaml
# 1) 팀 구성
team = TeamCreate(team_name: "{domain}-team", members: [...])

# 2) 작업 풀 등록
tasks = TaskCreate(tasks: [
  {title: "step1", assignee: "{m1}"},
  {title: "step2", assignee: "{m2}", depends_on: ["step1"]}
])

# 3) (옵션) 진행 모니터링 — 폴링 패턴
for task_id in tasks:
  task = TaskGet(task_id: task_id)
  if task.status == "blocked":
    handle_block(task)

# 4) 팀원 간 통신 — 인박스 패턴
SendMessage(team_id: team.team_id, from: "{m1}", to: "{m2}", content: "1단계 산출물 _workspace/01_m1.md")

# 5) 작업 갱신
TaskUpdate(task_id: tasks[0], status: "completed", metadata: {output_path: "_workspace/01_m1.md"})

# 6) 후속 작업이 산출물 수신
output = TaskOutput(task_id: tasks[0])
```

---

## §9 검증 doctrine (P1-1 AC 정합)

본 reference는 *플레이스홀더* — 실 호출 trial 박제로 정밀화 필요.

| AC | 박제 방법 | 우선순위 |
|---|---|---|
| 시그니처 정밀화 | (a) Claude Code 공식 도구 카탈로그 URL 인용 / (b) `claude-code-guide` agent 호출 / (c) trial-and-error 1회 실호출 | 🔴 High |
| 반환값 schema | trial 호출 결과 raw 박제 | 🔴 High |
| 실패 모드 | 의도적 에러 호출 후 응답 박제 (예: `team_name` 중복, `assignee` 미존재) | 🟡 Mid |
| 호출 예시 | 본 §8 패턴이 실 호출과 정합되는지 확인 | 🟡 Mid |

**doctrine**: 본 reference는 P1-1 진행 중 ❓ inferred → ✅ verified로 격상. SKILL.md / `agent-design-patterns.md` / `orchestrator-template.md` / `team-examples.md`의 의사코드 영역은 본 reference로 cross-link 유지.

---

## 참고

- 사용자 확정 (2026-05-14): P1-1 task 우선순위 🔴 High — Sp2 (self-critique sub-agent) doctrine과 의존성 직결. sub-agent 호출은 본 도구 schema 신뢰성에 의존.
- 출처 박제: 본 reference 작성 시점은 ❓ inferred 단계. 격상 작업은 별도 사이클.
