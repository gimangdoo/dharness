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

## 측정 로그

| 일자 | 환경 | K | B1 (M1/M2/M3) | B2 (M1/M2/M3) | 분기 | Layer A 결론 |
|------|------|---|--------------|---------------|------|-------------|
| 2026-05-10 | dharness-probe-test (사용자 부분 보고) | ? | (미측정) | M2≈6000~7000 (단위 모호 — 도구 카운트로 보면 비현실적, 토큰 또는 빌트인 포함 가능) | 보류 | (B1 미측정 + 단위 모호로 판정 불가) — 재측정 시 §B 절차의 입력 프롬프트를 "도구 *이름의 총 개수*"가 아닌 *명시 단위*(개수 / 토큰 / 문자 수)로 1줄씩 분리해 응답 받기 권장
