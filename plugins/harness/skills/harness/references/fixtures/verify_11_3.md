# §11-3 fixture — `enabledMcpjsonServers` 토글 효과 측정

## 목적

`.claude/settings.json`의 `enabledMcpjsonServers` 배열에서 서버를 *빼면* — (A) 컨텍스트 적재 자체가 차단되는지 vs (B) 적재는 되고 호출만 차단되는지 분기 측정.

이 답은 Layer A(서버 토글)가 진짜 토큰 절감 효과인지 vs 호출 게이트(Layer C)와 동급인지 결정.

## 선조건

- dharness 프로젝트 (또는 임의 derived 프로젝트)에 `.mcp.json` 또는 `~/.claude.json` `projects.{path}.mcpServers`로 등록된 MCP 1개 이상
- 사전에 `claude mcp list`로 등록 MCP 카운트 K 확인 (예: dharness = 3 = fetch/sequential-thinking/git)

## 실행

### 1단계 — 베이스라인 (모든 MCP enabled)

1. `.claude/settings.json`을 확인하여 `enabledMcpjsonServers`가 *없거나* 모든 서버를 포함하는지 확인 (없으면 기본=전체 enabled)
2. 새 세션 시작
3. 첫 user 메시지:
   ```
   ToolSearch query "mcp__"로 max_results 50 검색해서 발견된 도구 카운트만 숫자로 답해줘.
   ```
4. 응답 카운트를 **N1**로 기록

### 2단계 — 토글 OFF

1. 세션 종료
2. `.claude/settings.json` 편집 — 다음 키 추가/갱신:
   ```json
   {
     "enabledMcpjsonServers": []
   }
   ```
3. 새 세션 시작
4. 첫 user 메시지로 1단계와 동일 입력
5. 응답 카운트를 **N2**로 기록

### 3단계 — 분기 판정

| 관찰 | 해석 | Layer A 효과 |
|------|------|-------------|
| `N2 == 0` | 적재 자체 차단 | ✓ 토큰 절감 효과 확정 |
| `N2 == N1` | 적재는 그대로, 호출만 차단 | ✗ 토큰 절감 X (Layer C와 동급) |
| `0 < N2 < N1` | 부분 적재 (서버별 차등) | △ 서버별 동작 다름 — 추가 조사 필요 |

### 4단계 — 복원

1. 세션 종료
2. `.claude/settings.json`의 `enabledMcpjsonServers` 키를 *제거*하거나 모든 서버를 다시 포함
3. 베이스라인 상태로 복원 확인 (선택) — 새 세션에서 N1과 동일 카운트 재현

## 결과 기록

다음 표를 본 fixture 마지막 "측정 로그" 섹션에 한 행 추가:

```
| 일자 | 환경 | K (등록 MCP) | N1 (enabled) | N2 (disabled) | 분기 | Layer A 결론 |
|------|------|-------------|--------------|---------------|------|-------------|
| 2026-05-?? | dharness | 3 | ?? | ?? | ?/?/?  | ?? |
```

§1 표의 Layer A 행 "컨텍스트 절감" 셀에도 검증 일자·결과 footnote 추가.

## 핵심 관찰 포인트

- **`N2 == 0`이면** §10 5-step의 Step 5 (reflect)에서 *불필요한 MCP는 settings.json에서 제외하는 것이 토큰 절감*임을 확정 — 신규 채택 시 무조건 enable 권장
- **`N2 == N1`이면** Layer A는 토큰 측면에서 무용 → §1 표 갱신 + §10 권장 절차에서 settings.json 토글 제거
- **부분 적재이면** 서버별로 측정 → §3 인벤토리 표에 "토글 응답성" 컬럼 신설 검토

## 측정 로그

(empty — 첫 실행자가 채움)

| 일자 | 환경 | K | N1 | N2 | 분기 | Layer A 결론 |
|------|------|---|----|----|------|-------------|
