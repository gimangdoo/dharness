# §11-3 P3-(c) fixture — 인터랙티브 `claude` vs `claude -p` 비교 측정

> **목적**: 13·15·16차 사이클 누적 closure(`claude -p` 모드에서 `~/.claude.json` 4-key gate matrix *전부* falsified)가 *`claude -p` non-interactive mode 한정 결과*인지, 인터랙티브 `claude` 세션에서도 동일한지 분리 측정. P3 전체의 *유일한* 결정적 미해소 분기.
>
> **caveat 출처**: 13·15·16차 사이클은 `claude -p`(print mode, 1-shot non-interactive)로만 측정. `-p` 모드는 workspace trust dialog skip + auto-trust 부수 효과가 있어, *4-key gate 매트릭스 전부*가 모드 자체에 의해 무시됐을 가능성 — 16차 B8(`disabledMcpjsonServers=["sqlite"]` 명시 차단도 무력)으로 가설 사실상 확정. **본 fixture는 그 가설의 *결정적* 검증**.
>
> **누적 falsification 매트릭스 (13·15·16차):**
>
> | gate 키 | 토글값 | cycle | M2 |
> |---|---|---|---|
> | project-scope `enabledMcpjsonServers` | `[]` | 13차 B2 | 6 ✗ |
> | user-scope `enabledMcpjsonServers` | `[]` | 15차 B6 | 6 ✗ |
> | `hasTrustDialogAccepted` | `false` | 15차 B7 | 6 ✗ |
> | `disabledMcpjsonServers` | `["sqlite"]` 명시 차단 | 16차 B8 | 6 ✗ |
>
> → 모든 분기에서 M2=6 (sqlite 6종 그대로 적재). 인터랙티브에서 어느 하나라도 0(또는 <6)이면 *`-p` 한정 caveat* 확정 + 그 키가 진짜 gate.

## 적용 스코프

- derived 프로젝트(`C:\Users\user01\dharness-probe-test`) 활용 — 13차 측정과 동일 환경 재사용
- gate 4종 충족 상태 (13차 pre-flight 박제 그대로):
  - `~/.claude.json` projects.{abs}.enabledMcpjsonServers = `["sqlite"]` ✓
  - `~/.claude.json` projects.{abs}.disabledMcpjsonServers = `[]` ✓
  - `~/.claude.json` projects.{abs}.hasTrustDialogAccepted = `true` ✓
  - `<derived>/.claude/settings.json` = `{"enabledMcpjsonServers": ["sqlite"]}` ✓
- **본 세션 직접 실행 불가** — 인터랙티브 `claude` spawn은 외부 PowerShell 필요

## 측정 메트릭

13차 B1/B2와 동일 — M2(deferred pool 카운트 — `mcp__sqlite__*` 도구 enumeration count).

## 외부 실행 절차 (PowerShell, ~5분)

### Step 0 — pre-flight 검증

```powershell
cd C:\Users\user01\dharness-probe-test

# (a) gate 4종 충족 확인
node -e "const d=JSON.parse(require('fs').readFileSync(process.env.USERPROFILE+'/.claude.json','utf8'));const e=d.projects['C:/Users/user01/dharness-probe-test'];console.log(JSON.stringify({en:e.enabledMcpjsonServers,dis:e.disabledMcpjsonServers,tr:e.hasTrustDialogAccepted}))"
# 기대: {"en":["sqlite"],"dis":[],"tr":true}

# (b) settings.json 현재 상태
Get-Content .claude\settings.json
# 기대: {"enabledMcpjsonServers": ["sqlite"]}
```

gate 미충족 시 13차 B1 ready 상태로 복원 후 진행 (verify_11_3.md "외부 액션 카드" Step 1 참조).

### Step 1 — B8 측정 (인터랙티브 + gate ALL ON)

```powershell
cd C:\Users\user01\dharness-probe-test
claude
```

**첫 user 메시지 (그대로 복사):**

```
system-reminder에 적재된 deferred tool 명단에서 "mcp__sqlite__"로 시작하는 항목을 그대로 1줄씩 보고해줘. 카운트 추정하지 말고 *원문 그대로* 보여줘 — 0개여도 그렇게 보고.
```

응답에서 `mcp__sqlite__*` 시작 도구 enumeration count = **B8.M2**.

> **기대**: 13차 B1과 같은 6종 (`append_insight`/`create_table`/`describe_table`/`list_tables`/`read_query`/`write_query`). 다르면 *인터랙티브 vs `-p` mode 차이* 첫 empirical 증거.

세션 종료 (`/exit` 또는 Ctrl+D).

### Step 2 — B9 측정 (인터랙티브 + settings.json `[]` 토글 OFF)

```powershell
# settings.json 토글 OFF
Set-Content C:\Users\user01\dharness-probe-test\.claude\settings.json '{"enabledMcpjsonServers": []}' -Encoding utf8

# 새 인터랙티브 세션
cd C:\Users\user01\dharness-probe-test
claude
```

같은 첫 메시지로 응답 받음 → **B9.M2** 캡처.

세션 종료.

### Step 3 — 분기 판정

| 관찰 | 해석 | 13차 결론에 미치는 영향 |
|---|---|---|
| B8=6 AND B9=6 (`-p` B1=B2=6과 동일) | 인터랙티브에서도 토글 무력 — 13차 결론 ✓ 일반화 | project-scope `settings.json` 토글은 진짜로 deferred pool 영향 0 (auto-trust 부수 효과 아님). user-scope 채널 식별이 핵심 다음 단계. |
| B8=6 AND B9=0 (`-p`와 다름) | 인터랙티브에서는 토글 작동 — 13차 결론은 `-p` 한정 caveat | settings.json 토글은 *인터랙티브 모드 한정* 절감 채널. `-p` 사용자에게는 무력 caveat 박제. |
| B8=0 AND B9=0 | gate 4종 충족인데 인터랙티브에서 sqlite 미적재 — 인터랙티브가 `-p`보다 더 엄격한 trust 게이트 적용 | 추가 차단 mechanism 잔존 — `~/.claude.json` user-scope per-project entry 키 추가 측정 필요. 12차 사이클 함정 재발. |
| B8=6 AND B9=6 + B8.도구명 ≠ B9.도구명 | 카운트는 같으나 enum 내용 다름 — 부분 토글 효과 | 매우 드문 분기 — 서버별 차등 토글 가능성 박제. |

### Step 4 — 복원

```powershell
Set-Content C:\Users\user01\dharness-probe-test\.claude\settings.json '{"enabledMcpjsonServers": ["sqlite"]}' -Encoding utf8
```

### Step 5 — 결과 박제

`verify_11_3.md` "측정 로그" 표에 2행 (B8 + B9) 추가:

```
| 2026-05-?? | dharness-probe-test 인터랙티브 (P3-(c) B8 — gate ALL ON) | sqlite (.mcp.json type:stdio + abs uvx) | M2=? / 도구 enum=...   | (B9 행) | (B9 후 판정) | 13차 -p mode 비교 — 인터랙티브 결과 박제 |
| 2026-05-?? | dharness-probe-test 인터랙티브 (P3-(c) B9 — settings.json [] 토글 OFF) | sqlite (.mcp.json 미변경) | (B8 행 참조) | M2=? / 도구 enum=... | <분기 표 참조> | <분기 결론> |
```

본 README `fixtures/README.md` "결과 로그"에 1행:

```
| 2026-05-?? | §11-3 P3-(c) | dharness-probe-test 인터랙티브 1+1 세션 | B8=? / B9=? — <분기 결론> | permission-profiles.md §1[^A] footnote + §8-2 P3-(c) ✓ 이동 |
```

`permission-profiles.md`:
- §1 [^A] footnote에 P3-(c) 결과 1줄 (인터랙티브 모드 결과 박제)
- §8-2 P3-(c) interactive vs `-p` 비교 항목 → ✅ 이동

### Step 6 — P3-(b)·P3-(c) 합산 분석 (인터랙티브 측정 후 갱신)

P3-(b) verify_11_3_p3b.ps1 v3 closure 결과(15·16차) 기준 합산 진단 매트릭스:

| 인터랙티브 측정 결과 | 13·15·16차 `-p` 결과 | 합산 해석 |
|---|---|---|
| **B8=6 AND B9=6 (인터랙티브 = `-p`)** | 4-key gate matrix 전부 falsified | 인터랙티브에서도 토글 무력 — gate 매트릭스 *전부 mode-independent*. `~/.claude.json` 측 gate 키는 *호출 시점 게이트*에만 작동, deferred pool 적재는 별도 채널. server-side `--toolsets`/env가 진짜 컨텍스트 절감 채널일 가능성. `-p` auto-trust caveat 제거. |
| **B8=6 AND B9=0 (인터랙티브에서 enabled=[] 토글만 작동)** | `-p`만 우회 | `enabledMcpjsonServers` toggle은 *인터랙티브 모드 한정* 절감 채널. `-p` 사용자에게는 무력. 합성 가이드를 모드별로 분리 필요. |
| **B8=0 (인터랙티브에서 4-key 모두 ON에도 미적재)** | gate ON 충족 무력 | `claude -p` mode는 의도적으로 trust 우회. 인터랙티브는 더 엄격한 검사. `~/.claude.json` user-scope per-project entry의 *별도 키* 또는 *세션 단위 approval cache* 등 추가 mechanism. |
| **부분 토글 (도구별 분기)** | 일부 우회 | 매우 드문 분기 — 서버별 차등 토글 가능성. |

> **가장 가능성 높은 결과**: **B8=6 AND B9=6 (mode-independent falsification)** — gate matrix가 그저 *deferred pool 적재 제어 도구가 아닐* 가능성. 그 경우 §1 [^A] footnote의 "진짜 절감 채널 후보"가 *server-side `--toolsets`/env로 좁혀짐* → 그것이 *유일하게 미측정 + 유효 가설*로 남는 채널.

## 핵심 관찰 포인트

- **B8.M2 = 6**이면 인터랙티브 모드도 settings.json 토글 무력 → 13차 결론의 **mode-independent 보편성** 확정 → `-p` auto-trust caveat *제거 가능*.
- **B9.M2 < B8.M2**이면 인터랙티브가 진짜 토글 응답성 보유 → 13차 결론은 `-p` 한정 → `synthesis_example/` 합성 가이드의 `enabledMcpjsonServers` 권고를 *모드별로 분리* 박제 필요.
- 본 측정의 가장 가능성 높은 결과는 **B8=B9=6** (mode-independent). 그 시점에 P3-(c) closure → user-scope toggle (P3-(b))이 진짜 gate임을 합산 empirical 확정.

## cleanup

별도 cleanup 불요 — 13차 ready 상태로 복원 (Step 4)이 곧 다음 측정의 baseline.
