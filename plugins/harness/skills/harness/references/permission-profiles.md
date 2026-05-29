# Permission Profiles — MCP·도구 자동 할당 카탈로그 (메인 진입점)

> **Read at phase:** Phase 5-2 (MCP·도구 자동 할당). 본 메인은 *진입 매트릭스 + 3-layer 모델 + 결정 트리 + 안전 정책*만. 본문은 4 파일로 분리됨.

---

## 0. Closure & Navigation

### 0-1. 4 파일 분리 (P7 + PA5)

| 파일 | 내용 | 진입 시점 |
|---|---|---|
| **`permission-profiles.md`** (본 파일) | §0 진입 매트릭스 / §1 3-layer 모델 / §4 결정 트리 / §6 안전 정책 / §9 plugin subagent 제약 | Phase 5-2 합성 진입 (default) |
| **`permission-profiles-profiles.md`** | §2 8 capability profile 본문 (4 범용 + 4 도메인) | capability profile 결정 시 |
| **`permission-profiles-inventory.md`** | §3 MCP 후보 인벤토리 + §3-0 verification_status + §3-1 T0 매트릭스 | MCP 후보 검색 시 |
| **`permission-profiles-synthesis.md`** | §5-1 (inline `mcpServers:`) + §5-1-a/b/c + §5-2 (.mcp.json 예외) + §5-3 (settings.json) + §7 (Phase 5 호출 절차) | 에이전트 frontmatter 합성 시 |
| **`permission-profiles-dynamic-adoption.md`** | §10 + §10-A~G (트리거 / 5-step / 프로젝트 유형 / Rollback / inline update / 자동화 한계 / 병렬 세션) | run-time MCP 채택 시 |
| **`permission-profiles-empirical.md`** | §8 검증 상태 + §8-3 검증 기법 + §11-1~11-4 reproducer fixture | 검증 상태 확인·외부 reproducer 실행 시 |

### 0-2. 진입 § 매트릭스

| 작업 | 진입 § (파일) |
|---|---|
| Phase 5-2 합성 시작 (default) | 본 §0 → §1 (3-layer) → §4 (결정 트리) → synthesis.md §5-1 |
| capability profile 결정 | profiles.md §2 + inventory.md §3-1 |
| MCP 후보 검색 | inventory.md §3 + §3-1 |
| 합성 산출물 (inline / .mcp.json / settings.json) | synthesis.md §5-1·5-2·5-3 + §7 호출 절차 |
| 안전 정책 검토 | 본 §6 |
| run-time MCP 채택 | dynamic-adoption.md §10 5-step |
| 진행 가시성 (read-only 진단) | inventory.md §3 + dynamic-adoption.md §10-D rollback 이력 → `/harness:harness-mcp-status` |
| 검증 상태 확인 | empirical.md §8 |
| 외부 환경 reproducer | empirical.md §11-1~§11-4 |

### 0-3. 8 profile 빠른 참조 (시그널 → T0 권고 MCP)

| Profile | 시그널 | T0 권고 MCP | inventory.md §3-1 행 |
|---|---|---|---|
| code-test | S2+S5 | git, filesystem | 행 1 |
| web-research | S1+S3 | fetch, memory | 행 2 |
| external-integration | S2+S4+S5 | sqlite (+T1+ github) | 행 3 |
| reasoning-aux | S6 | sequential-thinking, time | 행 4 |
| ml-pipeline | S7 | filesystem + sqlite + memory + sequential-thinking + git | 박스 (4 범용 재조합) |
| devops-infra | S8 | git + filesystem + time + sequential-thinking | 박스 (4 범용 재조합) |
| mobile-native | S9 | filesystem + git + sequential-thinking (+T1 playwright/chrome-devtools) | 박스 (4 범용 재조합) |
| data-eng | S10 | sqlite + filesystem + git + memory + sequential-thinking | 박스 (4 범용 재조합) |

> **Signal S1~S10 정의:** `mcp-recommendation.md §1`. 8 profile 본문은 `permission-profiles-profiles.md §2`.

---

## 1. 3-layer 권한 모델

에이전트에 도구/MCP를 부여하는 경로는 3개. 토큰 비용·통제 입자도가 다르다.

| Layer | 메커니즘 | 컨텍스트 절감 | 실행 통제 | 적용 시점 |
|-------|---------|-------------|---------|---------|
| **A. 서버 측 toolset 필터** | MCP 서버의 `--toolsets` / env (예: `GITHUB_TOOLSETS=issues,prs`) | ⚠️ advertise 단계 축소 (deferred pool 적재 효과 미측정) | ✅ 미advertise = 호출 불가 | `.mcp.json` 등록 시 |
| **B. 서브에이전트 inline `mcpServers:`** | 에이전트 frontmatter에 inline 정의 | ✅ 서브에이전트 컨텍스트만 — **parent isolation empirical 확정** | ⚠️ inline 서버의 도구는 `tools:` allowlist로 안 줄어듦 — `permissions.deny`로 강제 | Phase 5 합성 시 |
| **C. `permissions.allow/ask/deny`** | `.claude/settings.json` 패턴 매칭 | ❌ 정의 로드는 그대로 | ✅ 호출 시 승인/차단 | 보안 게이트 |

**우선순위:** A > B > C. **Layer B는 parent isolation에 ✅ (10차 P0 확정), 단 inline 서버의 도구 카운트는 `tools:` allowlist로 줄지 않음 — Layer A(서버 측 advertise 필터) 또는 Layer C `deny` 로만 통제.** 토큰 절감 채널은 A+B 조합, agent별 도구 풀 형태 통제는 A 단독, 호출 시점 게이트는 C.

> **3-layer empirical 검증·footnote·deferred pool baseline:** `permission-profiles-empirical.md §8-1`.

---

## 2. Capability Profiles (분리됨 → `permission-profiles-profiles.md`)

8 profile (`code-test` / `web-research` / `external-integration` / `reasoning-aux` + `ml-pipeline` / `devops-infra` / `mobile-native` / `data-eng`) 본문 = [`permission-profiles-profiles.md §2`](./permission-profiles-profiles.md). 빠른 참조는 본 문서 §0-3.

---

## 3. MCP 후보 인벤토리 (분리됨 → `permission-profiles-inventory.md`)

§3 인벤토리 표 + §3-0 verification_status 정책 + §3-1 검증 완료 T0 매트릭스 = [`permission-profiles-inventory.md`](./permission-profiles-inventory.md). Phase 5-2 합성 시 inventory.md를 read 후 본 §4 결정 트리로 이동.

---

## 4. 매핑 결정 트리

Phase 5에서 에이전트 명세를 받았을 때:

```
1. 에이전트 description에서 capability 추론
   → LLM이 후보 profile 1~N개 *제안*만 (다중 선택 가능)
   → 사용자 confirm 전엔 합성 금지

1-R. (옵션·default ON) MCP Recommendation 엔진 호출
   → mcp-recommendation.md §1 신호 추출 (10 신호 — 범용 6 S1~S6 + 도메인 4 S7~S10)
   → §2 후보 풀 cascade (R0 inventory.md §3·§3-1 → R1 modelcontextprotocol/servers → R2 외부 큐레이션)
   → §3 3축 점수 (효율성/확장성/정확도) — top-K 표 + 권고 조합
   → R-7 confirm gate → 채택은 dynamic-adoption.md §10 5-step로 인계
   ※ 도메인 신호 S7~S10 매칭 시 profile §2-5~§2-8 매핑 — 전용 MCP는 T0 5종 cross-mapping default, 전용 MCP는 §10 진입 제안만

2. 사용자 confirm된 profile들에 대해 후보 MCP 열거
   → `claude mcp list`로 install 여부 체크

3. 분기 (default = inline `mcpServers:` parent 격리):
   a) toolset 필터 지원 MCP (github/playwright 등) → synthesis.md §5-1-b Layer A+B 결합형
      → inline `mcpServers:` 의 env/args에 toolset 필터 박음
      → 에이전트 frontmatter `tools:`엔 필터링된 도구명만 allowlist (Layer C)
      → parent 미적재 + 서버 측 advertise 축소 동시 달성
   b) toolset 미지원 MCP (fetch/sqlite 등) → synthesis.md §5-1-a Layer B 단독
      → 서브에이전트 inline `mcpServers:`로 격리
      → frontmatter `tools:`에 필요 도구만 열거
      → parent 미적재만 (서버 측 도구 풀은 그대로)
   c) MCP 미install (런타임 신규 채택 필요) → dynamic-adoption.md §10 진입
      → /harness:harness-mcp-adopt 5-step (discover → probe → confirm → install → reflect)
      → 자동 install·자동 키 발급 금지 (§6)
   d) parent 직접 호출 필연성 (드문 케이스) → synthesis.md §5-2 .mcp.json (anti-pattern)
      → §5-2의 3 예외 조건 충족 시에만, enabledMcpjsonServers allowlist 의무

4. 합성 산출물 (default 패치):
   - 에이전트 .md frontmatter `tools:` + inline `mcpServers:` (default)
   - 프로젝트 .claude/settings.json `permissions.allow/ask/deny`
   - 프로젝트 .mcp.json mcpServers (synthesis.md §5-2 예외 조건 시에만)
   - _workspace/_baseline/changelog.md 변경 이력 1행 (Phase 7-4)
```

---

## 5. 합성 산출물 (분리됨 → `permission-profiles-synthesis.md`)

§5-1 (inline `mcpServers:` — *default*) + §5-1-a (Layer B 단독) + §5-1-b (Layer A+B 결합 — *최강 패턴*) + §5-1-c (모델 by role) + §5-2 (`.mcp.json` 예외) + §5-3 (`settings.json` Layer C) = [`permission-profiles-synthesis.md`](./permission-profiles-synthesis.md). 본 §4 결정 트리 분기 a~d는 모두 synthesis.md 본문으로 진입.

---

## 6. 안전 정책

1. **자동 install 금지** — MCP 등록은 항상 사용자 명시 동의. 에이전트 합성은 *제안*만.
2. **`allow` 자동 승급은 T0 한정** — T1·T2는 사용자 confirm 후에만 `allow`로, 기본값은 `ask`.
3. **민감 도구는 `deny`로 명시** — 삭제·force push·외부 메시지 발송 류는 화이트리스트가 아니라 *블랙리스트*로 박제 (`mcp__github__delete_*`, `mcp__slack__post_message` 등).
4. **plugin host 본체 read-only invariant 보존** — Phase 5 합성은 *생성 대상 프로젝트*의 `.claude/`·`.mcp.json`만 건드리며, plugin 본 저장소의 `plugins/harness/` 류 plugin 정의는 절대 수정하지 않음.
5. **환각 봉쇄** — LLM 제안 후보는 inventory.md §3 표 또는 `claude mcp list` 결과로 교집합 검증. 표에 없고 인벤토리에도 없는 MCP는 사용자에게 별도 검토 요청.

> **회수 불가 명령·dry-run gate doctrine:** `kubectl delete` / `terraform destroy` / `drop` / `truncate` 등 비가역 명령은 dynamic-adoption.md §10-D rollback 절차로 회수 불가 — *사전 dry-run* gate 필수.

---

## 7. Phase 5 호출 절차 (분리됨 → `permission-profiles-synthesis.md §7`)

Phase 5-1 → 5-2 a~f 호출 절차 = [`permission-profiles-synthesis.md §7`](./permission-profiles-synthesis.md#7-phase-5에서의-호출-절차). 본 §4 결정 트리와 함께 read.

---

## 8. 검증 상태 (분리됨 → `permission-profiles-empirical.md`)

§8 공식 docs 확정 사실 + §8-1 empirical 검증 + §8-2 요약 + §8-3 재사용 기법 = [`permission-profiles-empirical.md §8`](./permission-profiles-empirical.md). 외부 도입자 미완 항목은 §11 reproducer로 진행.

---

## 9. Plugin subagent 제약

본 `harness` 플러그인이 *생성하는* 에이전트는 **target 프로젝트의 `.claude/agents/`에 직접 작성**되므로 synthesis.md §5-1의 inline `mcpServers:` 패턴이 모두 작동한다. 그러나 만약 누군가 derived 하네스를 plugin 형태로 패키징하면, *plugin 내부* `agents/` 의 subagent에 대해서는 다음 필드가 무시된다 (docs §"Choose the subagent scope"):

- `mcpServers` (보안)
- `permissionMode`
- `hooks`

**이 경우의 우회**: 플러그인 install 후 파일을 `.claude/agents/`에 복사하거나, `.claude/settings.json` `permissions.allow` 패턴으로 세션 단위 허용을 명시. **즉 "MCP-owning subagent" 패턴은 *생성 산출물 위치가 .claude/agents/일 때만 완전 작동*** — 본 문서는 이 가정에 의존한다.

---

## 10. Dynamic MCP Adoption (분리됨 → `permission-profiles-dynamic-adoption.md`)

§10 + §10-A~§10-G (트리거 신호 / 5-step 채택 절차 / 프로젝트 유형별 패턴 / Rollback / inline update / 자동화 한계 / 병렬 세션 운용) = [`permission-profiles-dynamic-adoption.md`](./permission-profiles-dynamic-adoption.md) 단일 출처. `/harness:harness-mcp-adopt` 슬래시 커맨드 본문에서 호출.

---

## 11. 실증 reproducer (분리됨 → `permission-profiles-empirical.md §11`)

§11-1 (다음 세션 노출 패턴) + §11-2 (parent isolation) + §11-3 (`enabledMcpjsonServers` 토글) + §11-4 (§10 5-step e2e sqlite 시연) = [`permission-profiles-empirical.md §11`](./permission-profiles-empirical.md#11-실증-가능한-테스트-레시피--8-2-미완-항목-reproducer). 외부 환경(다음 세션·derived 프로젝트·API 키) 의존.
