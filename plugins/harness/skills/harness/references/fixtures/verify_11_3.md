# §11-3 fixture — `enabledMcpjsonServers` 토글 효과 측정

> **6차 사이클 갱신** — Claude Code의 *deferred tool pool* 모델 발견 이후, 측정 메트릭이 "도구 노출 카운트"에서 "system prompt 토큰 + schema fetch 빈도"로 재정의되었다. 본 fixture는 그 새로운 메트릭에 맞춰 작성됨.

## 목적

`.claude/settings.json`의 `enabledMcpjsonServers` 배열에서 서버를 *빼면* — (A) 이름·description의 system-prompt 적재 자체가 차단되는지 vs (B) 적재는 되고 ToolSearch lazy-fetch만 차단되는지 vs (C) 토큰에는 영향 없고 호출만 게이트되는지 3분기 측정.

이 답은 Layer A(서버 토글) 가치를 확정한다 — *도구 카운트 측정으로는 분기 불가* (deferred pool은 항상 이름만 노출).

## 적용 스코프 — 필수 선조건

> **dharness root 자체는 불가** — dharness의 3 MCP(fetch/sequential-thinking/git)는 `~/.claude.json` `projects.{cwd}.mcpServers` (= `claude mcp add -s local`) 적재. `enabledMcpjsonServers`는 *project-scope `.mcp.json`* 등록분만 토글한다. 측정 유효성을 위해 다음 환경 필수:
>
> 1. dharness 외부 derived 프로젝트 1개 (`~/myproject` 등)
> 2. 해당 프로젝트에서 `claude mcp add <name> <cmd> -s project` 1회 이상 → `<myproject>/.mcp.json` 생성
> 3. `<myproject>/.claude/settings.json` 또는 `<myproject>/.claude/settings.local.json` 편집 권한

## 🆕 측정 환경 함정 — `enabledMcpjsonServers` 키의 *2 위치 동기화* + `hasTrustDialogAccepted` (12·13차 사이클 발견)

> **본 fixture가 단독 토글하는 `<derived>/.claude/settings.json` `enabledMcpjsonServers`는 활성화의 *충분조건이 아닐 수 있다*.** 12차 사이클(2026-05-10) 측정에서 다음 사실 empirical 확인:
>
> - `~/.claude.json`의 *프로젝트별 entry*에도 동일 키 `enabledMcpjsonServers`가 존재 (예: `~/.claude.json` `"C:/Users/user01/dharness-probe-test"` entry).
> - `<derived>/.claude/settings.json`을 `{}`로 비우고 `~/.claude.json`의 같은 키를 `["sqlite"]`로 갱신해도 — *베이스라인 B1*에서 sqlite MCP가 deferred pool에 적재 안 됨 (`mcp__sqlite__*` ToolSearch hit 0).
> - 즉 user-scope per-project entry의 enable 키 *단독*으로는 활성화 불충분.

> **🆕 13차 사이클 pre-flight 사전 검증 (2026-05-11, dharness 본 세션 read-only inspect)** — `~/.claude.json` 전수 grep으로 식별된 잠재 gate 4종:
>
> | 키 | 위치 | 현재 값 (`dharness-probe-test` entry) | 활성화 default |
> |---|---|---|---|
> | `enabledMcpjsonServers` | `~/.claude.json` projects.{abs}.* | `["sqlite"]` ✓ | 빈 배열 = 차단 |
> | `enabledMcpjsonServers` | `<derived>/.claude/settings.json` | `["sqlite"]` ✓ | 빈 배열 = 차단 |
> | `disabledMcpjsonServers` | `~/.claude.json` projects.{abs}.* | `[]` ✓ | 비어 있어야 통과 |
> | **`hasTrustDialogAccepted`** | `~/.claude.json` projects.{abs}.* | `true` ✓ | `false` = `.mcp.json` 신뢰 미승인 → MCP 적재 차단 |
>
> **🚨 13차 핵심 발견:** `hasTrustDialogAccepted: false` 상태였다면 `.mcp.json` 자체가 신뢰되지 않아 *모든* project-scope MCP가 적재 차단. 12차 사이클 측정 시 이 키 상태가 가설로 누락. 본 세션 read-only 점검 시점에는 `true` 상태이므로 — *측정 환경 4 gate 모두 충족*. cycle 12 측정 이후 갱신된 `<derived>/.claude/settings.json` `["sqlite"]` 추가 사실과 결합하면 **B1 베이스라인이 충족된 상태에서 첫 측정 가능**.
>
> **13차 권고 측정 절차 (gate 4종 충족 전제):**
>
> 1. *측정 직전* `~/.claude.json`의 `projects.{<derived-abs>}` entry에서 위 4 키 값을 한 번 더 확인 (Claude Code가 세션 종료마다 일부 키를 자동 갱신할 수 있음).
> 2. B1 측정: 위 표 그대로 — sqlite enabled, hasTrustDialogAccepted=true.
> 3. B2 측정: `<derived>/.claude/settings.json`의 `enabledMcpjsonServers`만 `[]`로 변경 (다른 키 미변경).
> 4. B1.M2 = 0이면 — 추가 차단 mechanism 잔존. 분기 진단:
>    - `claude --debug 2>&1 | grep -i "mcp\|sqlite"` (CLI 적재 로그)
>    - `claude mcp list` vs `claude mcp list -s project` 출력 비교 (Disabled vs Connected)
>    - **즉시 우회**: `.mcp.json` 등록을 `claude mcp add <name> ... -s local`로 변경 (user-scope local) — dharness의 fetch/git처럼 즉시 적재됨이 양면 검증됨 (대신 측정 의도(`-s project` `.mcp.json` 토글)와는 분리되므로 별도 측정 행으로 박제).

## 측정 메트릭 (재정의)

| 메트릭 | 측정 방법 | 의도 ② 직결 |
|--------|----------|-----------|
| **M1: system prompt 토큰** (도구 이름·description 적재량) | SessionStart 직후 첫 user 메시지에서 `claude --debug 2>&1 \| grep "tokens"` 또는 콘텐츠 확인 (정확치는 builds별 변동) — *근사* 측정 | ✓ baseline cost 절감 여부 |
| **M2: deferred pool 카운트** | 첫 user 메시지에서 `ToolSearch query "mcp__"`로 max_results 50 검색 후 발견 도구 카운트 | △ 적재 형태 분기 표지 |
| **M3: schema fetch 빈도** | typical user turn에서 `mcp__<server>__<tool>` 호출 직전 `ToolSearch select:<name>` 1회 발생 여부 | ✓ per-turn 변동 비용 |

세 메트릭의 조합으로만 분기 판정 가능 — *도구 카운트 단독은 deferred-pool 인공물에 가려서 분기 표지가 되지 않음*.

## 실행

### 1단계 — 베이스라인 (모든 MCP enabled)

1. `<myproject>/.claude/settings.json`을 확인하여 `enabledMcpjsonServers`가 *없거나* 모든 서버를 포함하는지 확인 (없으면 기본=전체 enabled)
2. 새 세션 시작 (`<myproject>` parent에서 `claude` 호출)
3. 첫 user 메시지:
   ```
   다음 3가지를 알려줘:
   (1) 시스템 프롬프트에 등장하는 mcp__* 도구 이름의 총 개수
   (2) 첫 도구의 description 길이 (문자 수)
   (3) ToolSearch select:<name> 호출이 시스템 프롬프트에 명시된 사용법인지 (yes/no)
   ```
4. 응답을 **(M1·M2·M3) 베이스라인 = B1**로 기록

### 2단계 — 토글 OFF

1. 세션 종료
2. `<myproject>/.claude/settings.json` 편집 — 다음 키 추가/갱신:
   ```json
   {
     "enabledMcpjsonServers": []
   }
   ```
3. 새 세션 시작
4. 첫 user 메시지로 1단계와 동일 입력
5. 응답을 **(M1·M2·M3) 토글 OFF = B2**로 기록

### 3단계 — 분기 판정

| 관찰 (M2 = 도구 카운트) | 관찰 (M1 = baseline 토큰) | 해석 | Layer A 효과 |
|---|---|---|---|
| `B2.M2 == 0` | `B2.M1 << B1.M1` | 적재 자체 차단 (이름·description 모두 빠짐) | ✓ baseline + per-turn 모두 절감 |
| `B2.M2 == 0` | `B2.M1 ≈ B1.M1` | 표면 카운트만 0, 토큰은 동일 | △ 측정 노이즈 의심 — 재측정 권장 |
| `B2.M2 == B1.M2` | `B2.M1 ≈ B1.M1` | 적재는 그대로, 호출만 차단 | ✗ Layer A는 Layer C와 동급 (토큰 무용) |
| `0 < B2.M2 < B1.M2` | 부분 변동 | 서버별 차등 | △ 서버별 toggle 응답성 다름 — 서버별 분리 측정 |

추가 메트릭 M3(schema fetch 빈도)는 baseline 보정 — *도구가 적재되어 있어도 호출되지 않으면 schema는 추가 비용이 0*임을 확인.

### 4단계 — 복원

1. 세션 종료
2. `<myproject>/.claude/settings.json`의 `enabledMcpjsonServers` 키를 *제거*하거나 모든 서버를 다시 포함
3. 베이스라인 상태로 복원 확인 (선택) — 새 세션에서 B1과 동일 응답 재현

## 결과 기록

다음 표를 본 fixture 마지막 "측정 로그" 섹션에 한 행 추가:

```
| 일자 | 환경 | K (.mcp.json 등록 MCP) | B1 (M1/M2/M3) | B2 (M1/M2/M3) | 분기 | Layer A 결론 |
|------|------|----------------------|--------------|---------------|------|-------------|
| 2026-05-?? | <myproject> | ? | ?/?/? | ?/?/? | ? | ?? |
```

§1 표의 Layer A 행 "컨텍스트 절감" 셀에도 검증 일자·결과 footnote 추가.

## 핵심 관찰 포인트

- **`B2.M1 << B1.M1`이면** Layer A가 *baseline 절감*으로 작용 → §10 5-step Step 5에서 *불필요한 MCP는 settings.json에서 명시적 제외*가 토큰 절감으로 직접 반영됨을 확정
- **`B2.M1 ≈ B1.M1` 이고 `B2.M2 == 0`이면** 토큰 노이즈 관찰 — *deferred pool 카운트 0이라도 schema가 캐싱되어 system prompt에 잔존 가능* 시나리오 검증 필요
- **`B2.M2 == B1.M2`이면** §1 Layer A 컬럼을 "호출 게이트만 (Layer C와 동급)"으로 정정 + §10에서 settings.json 토글 가이드 제거
- **부분 적재이면** 서버별로 분리 측정 → §3 인벤토리 표에 "Layer A 응답성" 컬럼 신설 검토

## 외부 액션 카드 (13차 사이클 — gate 4종 충족, B1 측정 ready)

> 본 세션은 derived 프로젝트의 새 Claude Code 세션을 spawn할 수 없음. 사용자가 외부 터미널에서 1회 실행하면 §11-3 P1 closure 가능. **예상 시간 ~5분.**

### Step 1 — B1 베이스라인 측정 (gate 모두 ON)

```powershell
cd C:\Users\user01\dharness-probe-test
claude
```

**첫 user 메시지 (그대로 복사):**

```
system-reminder에 적재된 deferred tool 명단에서 "mcp__"로 시작하는 항목을 그대로 1줄씩 보고해줘. 카운트 추정하지 말고 *원문 그대로* 보여줘 — 0개여도 그렇게 보고.
```

응답 받으면 그대로 본 fixture "측정 로그"에 13차 사이클 B1 행으로 1행 추가.

### Step 2 — B2 토글 OFF 측정

세션 종료 후:

```powershell
# 편집: <derived>/.claude/settings.json의 enabledMcpjsonServers를 [] 로 변경
notepad C:\Users\user01\dharness-probe-test\.claude\settings.json
# 또는 PowerShell로 직접:
# Set-Content C:\Users\user01\dharness-probe-test\.claude\settings.json '{"enabledMcpjsonServers": []}' -Encoding utf8

claude
```

같은 첫 메시지로 응답 받음 → B2 행으로 1행 추가.

### Step 3 — 분기 판정 + 복원

본 fixture §3단계 표로 B1/B2 비교 → Layer A 결론 확정.

복원:
```powershell
Set-Content C:\Users\user01\dharness-probe-test\.claude\settings.json '{"enabledMcpjsonServers": ["sqlite"]}' -Encoding utf8
```

### Step 4 — 본 fixture 박제

측정 로그 표에 2행 추가 + 본문 §1 [^A] 셀 → ✅ 또는 ✗로 승급 + §8-2 §11-3 항목 → ✓ 이동 + permission-profiles.md 12차 사이클 진척 라인 다음에 13차 closure 라인 1줄 추가.

만약 B1.M2=0이면 — gate 4종 충족인데도 차단됨 → "추가 차단 mechanism 잔존" 박제 + Step 3에서 `-s local` 즉시 우회 측정으로 분기 (별도 행).

---

## 측정 로그

| 일자 | 환경 | K | B1 (M1/M2/M3) | B2 (M1/M2/M3) | 분기 | Layer A 결론 |
|------|------|---|--------------|---------------|------|-------------|
| 2026-05-10 | dharness-probe-test (사용자 부분 보고) | ? | (미측정) | M2≈6000~7000 (단위 모호 — 도구 카운트로 보면 비현실적, 토큰 또는 빌트인 포함 가능) | 보류 | (B1 미측정 + 단위 모호로 판정 불가) — 재측정 시 §B 절차의 입력 프롬프트를 "도구 *이름의 총 개수*"가 아닌 *명시 단위*(개수 / 토큰 / 문자 수)로 1줄씩 분리해 응답 받기 권장 |
| 2026-05-10 | dharness-probe-test (12차 사이클 재측정) | sqlite (`.mcp.json`, `-s project`, ✓ Connected, abs-path uvx) | M2=0/M1=?/M3=yes — `~/.claude.json` user-scope entry `enabledMcpjsonServers=["sqlite"]` + `<derived>/.claude/settings.json={}` 상태에서도 sqlite 미적재 | (미측정 — B1.M2=0이라 토글 측정 의의 없음) | 보류 | **추가 차단 mechanism 미확정** — B1 베이스라인 자체가 0이라 토글 효과 분기 측정 불가. fixture verify_11_3.md "측정 환경 함정" 섹션에 차단 후보 4종 (CLI 인터랙티브 approval / `disabledMcpjsonServers` / `enableAllProjectMcpServers` 유사 키 / 빌드별 정책) 박제. 즉시 우회는 `-s local` 재등록 (의도와는 분리된 별도 측정 행) |
| 2026-05-11 | dharness 본 세션 read-only inspect (13차 사이클 pre-flight) | sqlite (`.mcp.json` type:stdio + abs uvx + abs db) | (미측정 — 본 세션은 derived 프로젝트 새 세션 불가) | (미측정) | pre-flight ✓ | **gate 4종 모두 충족 확인** — (a) `~/.claude.json` projects.{<derived>}.enabledMcpjsonServers=["sqlite"] ✓ (b) `<derived>/.claude/settings.json` enabledMcpjsonServers=["sqlite"] ✓ (c) disabledMcpjsonServers=[] ✓ (d) **hasTrustDialogAccepted=true ✓ — 13차 사이클 새 발견 키**. 12차 사이클 측정 이후 `<derived>/.claude/settings.json`이 `{}`→`["sqlite"]`로 갱신되어 *충분조건 모두 충족 상태*. 외부 실행자가 `cd C:\Users\user01\dharness-probe-test && claude` 후 첫 메시지로 §외부 액션 카드의 ground-truth 캡처만 실행하면 B1 즉시 가능 |
| 2026-05-11 | dharness 본 세션 + `claude -p` non-interactive one-shot (13차 사이클 B1) | sqlite (`.mcp.json` type:stdio + abs uvx + abs db) | **M2=6 / M1=미측정 / M3=미측정** — sqlite 6종 도구 모두 deferred pool에 적재: `mcp__sqlite__{append_insight,create_table,describe_table,list_tables,read_query,write_query}`. §3 인벤토리 enumeration 100% 일치 | (B2 행에서 측정) | (B2 후 판정) | gate 4종 충족 + `claude -p` 모드에서 sqlite 도구 6종 전부 적재 empirical 확정. **caveat**: `-p` 모드는 workspace trust dialog skip — `hasTrustDialogAccepted`를 자동 통과. 사용자 entry는 이미 `true`라 인터랙티브와 결과 동일해야 하지만, 인터랙티브 비교 측정은 후속 의제. |
| 2026-05-11 | dharness 본 세션 + `claude -p` (13차 사이클 B2 — settings.json `enabledMcpjsonServers=[]` 토글 OFF) | sqlite (`.mcp.json` 미변경) + `<derived>/.claude/settings.json={"enabledMcpjsonServers":[]}` | **M2=6 — B1과 동일** (sqlite 6종 도구 모두 그대로 deferred pool에 적재). 토글 OFF에도 적재 카운트 *불변* | M2=6 | **✗ Layer A 없음 — project-scope settings.json 토글은 deferred pool에 영향 0** | 🚨 **결정적 empirical**: `<derived>/.claude/settings.json` `enabledMcpjsonServers` 키는 deferred pool 적재를 *전혀* 제어하지 못함. 적재의 active gate는 다른 채널 — 가장 강한 후보: `~/.claude.json` projects.{<derived>}.enabledMcpjsonServers (user-scope per-project entry). 부가 가설: `-p` 모드 auto-trust 부수 효과로 settings.json 토글이 무시됨 가능성 잔존 (인터랙티브 비교 측정은 후속 의제). **§1 Layer A 추정 가치 재정의 필요** — "서버 측 toolset 필터"와 "Claude Code-side `enabledMcpjsonServers` 토글"은 *서로 다른 채널*이며, 본 측정은 후자만 empirical 부정. 전자(server-side `--toolsets`/env)는 별도 검증 미완. |
| 2026-05-11 | dharness 본 세션 + `claude -p` (15차 사이클 B5 — gate 4 ALL ON baseline 재현) | sqlite (`.mcp.json` 미변경) + `~/.claude.json` projects entry: `enabledMcpjsonServers=["sqlite"]`/`hasTrustDialogAccepted=true`/`disabledMcpjsonServers=[]` + `<derived>/.claude/settings.json={"enabledMcpjsonServers":["sqlite"]}` | **M2=6** — 13차 B1과 정확히 동일 (sqlite 6종 모두 적재) | (B6/B7 행에서 측정) | (B6/B7 후 판정) | 15차 P3-(b) 측정 시리즈의 base reference. 13차 closure 이후 4 gate가 모두 ON 상태에서도 측정 재현성 유지 확정 (세션 간 안정성) |
| 2026-05-11 | dharness 본 세션 + `claude -p` (15차 사이클 B6 — `~/.claude.json` user-scope `enabledMcpjsonServers=[]` 단독 OFF) | sqlite (`.mcp.json` 미변경) + `~/.claude.json` projects entry: `enabledMcpjsonServers=[]`/`hasTrustDialogAccepted=true`/`disabledMcpjsonServers=[]` + `<derived>/.claude/settings.json={"enabledMcpjsonServers":["sqlite"]}` (settings.json은 KEEP ON, user-scope만 OFF) | **M2=6 — B5와 동일** (sqlite 6종 모두 그대로 적재). user-scope `enabledMcpjsonServers=[]` 단독 OFF로는 적재 차단 안 됨 | M2=6 | **✗ Layer A 없음 — user-scope `enabledMcpjsonServers` 토글도 deferred pool 영향 0** | 🚨🚨 **2차 결정적 empirical**: 13차 closure가 후보로 지목한 `~/.claude.json` user-scope `enabledMcpjsonServers`도 *진짜 gate 아님*. project-scope + user-scope *양쪽 모두* deferred pool 적재 제어 불가. 남은 gate 후보 = `hasTrustDialogAccepted` 또는 `disabledMcpjsonServers` 또는 `-p` 모드 auto-trust |
| 2026-05-11 | dharness 본 세션 + `claude -p` (15차 사이클 B7 — `hasTrustDialogAccepted=false` 단독 OFF) | sqlite (`.mcp.json` 미변경) + `~/.claude.json` projects entry: `enabledMcpjsonServers=["sqlite"]`/`hasTrustDialogAccepted=false`/`disabledMcpjsonServers=[]` + `<derived>/.claude/settings.json={"enabledMcpjsonServers":["sqlite"]}` (enabled 복원, trust만 OFF) | **M2=6 — B5와 동일** (sqlite 6종 모두 그대로 적재). `hasTrustDialogAccepted=false`로도 적재 차단 안 됨 | M2=6 | **✗ Layer A 없음 — `hasTrustDialogAccepted` 토글도 deferred pool 영향 0 (적어도 `-p` 모드에서)** | 🚨🚨🚨 **3차 결정적 empirical**: 13차 closure pre-flight가 도입한 4번째 gate 키 `hasTrustDialogAccepted`도 *진짜 gate 아님*. `-p` 모드에서는 *모든* `~/.claude.json` 측 gate 키가 우회됨. → 강력 가설로 격상: **`claude -p` 모드는 `.mcp.json` 존재만으로 적재 + interactive `claude`는 trust dialog로 차단**. 검증 미완 잔존: (i) 인터랙티브 `claude` 비교 (인터랙티브 spawn 의제) (ii) `disabledMcpjsonServers=["sqlite"]` 명시 차단 |
| 2026-05-11 | dharness 본 세션 + 15차 FINAL restore | `~/.claude.json` projects entry: `enabledMcpjsonServers=["sqlite"]`/`hasTrustDialogAccepted=true`/`disabledMcpjsonServers=[]` (gate 4 ALL ON 복원) | (측정 없음) | (측정 없음) | restore ✓ | **15차 사이클 closure** — 측정 시리즈 종료 후 baseline 상태 자동 복원 (`verify_11_3_p3b.ps1` FINAL Set-Gate). 다음 측정 의제(인터랙티브 비교 / `disabledMcpjsonServers` 명시 차단)는 본 baseline 위에서 진행 가능 |
| 2026-05-11 | dharness 본 세션 + `claude -p` (16차 사이클 B8 — `disabledMcpjsonServers=["sqlite"]` 단독 ON, *명시 차단*) | sqlite (`.mcp.json` 미변경) + `~/.claude.json` projects entry: `enabledMcpjsonServers=["sqlite"]`/`hasTrustDialogAccepted=true`/**`disabledMcpjsonServers=["sqlite"]`** + `<derived>/.claude/settings.json={"enabledMcpjsonServers":["sqlite"]}` (다른 키 ALL ON, disabled만 명시 차단) | **M2=6 — B5와 동일** (sqlite 6종 모두 그대로 적재). `disabledMcpjsonServers=["sqlite"]`로 *명시 차단*해도 적재 차단 안 됨 | M2=6 | **✗ Layer A 없음 — `disabledMcpjsonServers` 명시 차단도 deferred pool 영향 0 (`-p` 모드)** | 🚨🚨🚨🚨 **4차 결정적 empirical (마지막 미측정 gate falsified)**: `~/.claude.json` 측 *4-key gate 매트릭스 전부* falsified — (1) project-scope settings.json `enabledMcpjsonServers=[]` ✗ (13차) (2) user-scope `enabledMcpjsonServers=[]` ✗ (15차 B6) (3) `hasTrustDialogAccepted=false` ✗ (15차 B7) (4) **`disabledMcpjsonServers=["sqlite"]` 명시 차단 ✗ (16차 B8)**. 단순 토글이 아닌 *명시 차단* 키조차 무력 → `claude -p` 모드는 *모든* `.mcp.json`-측 gate를 우회하여 적재 사실상 확정. 인터랙티브 `claude` 비교만이 *유일한* 미해소 분기 — 가설 검증 1건으로 P3 전체 closure 가능. 산출물: `verify_11_3_p3b.ps1` v3 (4-key matrix 지원 — Set-Gate에 `$disabled` 파라미터 + B8 호출 추가) |
| 2026-05-11 | dharness 본 세션 + 16차 FINAL restore | `~/.claude.json` projects entry: `enabledMcpjsonServers=["sqlite"]`/`hasTrustDialogAccepted=true`/`disabledMcpjsonServers=[]` (gate 4 ALL ON 복원) | (측정 없음) | (측정 없음) | restore ✓ | 16차 사이클 closure — v3 FINAL Set-Gate가 disabled=[] 포함 4-key 모두 baseline 복원 |
