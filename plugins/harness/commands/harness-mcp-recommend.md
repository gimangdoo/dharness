---
description: 합성 시점 또는 합성 후 추가 에이전트에 대해 MCP 후보를 3축(효율성·확장성·정확도) 점수로 추천. 채택은 인계 — `/harness:harness-mcp-adopt`가 처리. 읽기 전용 + 외부 검색 가능.
argument-hint: <에이전트명 또는 역할 한 문장> [--refresh] [--cascade=R0|R1|R2] [--weights=E,S,A]
---

# Harness — MCP Recommend

`references/mcp-recommendation.md` 엔진을 *명시* 호출하는 진입점. Phase 5-2 합성 *중*에는 SKILL.md가 자동 트리거하지만, 본 명령은 (a) 기존 에이전트에 후보 보강 (b) 합성 후 점검 (c) 대안 후보 탐색 시 사용한다.

## 컨텍스트

- **인자**: `$ARGUMENTS`
  - 1st token: 에이전트명(`.claude/agents/<name>.md` 존재) 또는 역할 한 문장(미존재 = 가상 에이전트 평가)
  - `--refresh`: `_workspace/_baseline/mcp_catalog.jsonl` 캐시 강제 갱신
  - `--cascade=R0|R1|R2`: 후보 풀 cascade 깊이 (default R0 매칭 부족 시 R1, 명시 시 강제)
  - `--weights=E,S,A`: 가중 override (예: `--weights=0.5,0.2,0.3`), 합=1.0
- **입력**: derived 프로젝트의 `.claude/agents/<name>.md` (있으면) + `permission-profiles.md` §3·§3-1 + `mcp-recommendation.md` 엔진 + (캐시) `_workspace/_baseline/mcp_catalog.jsonl`
- **출력**: top-K 추천 표 + 권고 조합 + AskUserQuestion confirm gate → confirm 시 `/harness:harness-mcp-adopt` 1줄 명령 출력 (자동 실행 금지)

## 선조건 검증

1. derived 프로젝트의 `.claude/agents/`에 1명 이상 존재 — 미충족 시 "하네스 미합성 — `/harness:harness-new` 먼저 실행" 안내 후 중단. *단* `$ARGUMENTS`가 역할 한 문장이면 가상 평가로 진행 (산출물 없음 — 추천 표만).
2. **Host repo guard ❌** — `pwd`에 `.harness-host` marker file 존재 시 self-host 격리 안내 후 중단.
3. `--weights` 합 != 1.0 ± 0.01이면 형식 에러 후 중단.

## 실행 절차 — 7-step

`references/mcp-recommendation.md` §5의 R-1~R-7을 그대로 따른다. 본 명령은 *진입점·인자 파싱·결과 표시* 책임만.

### R-1. 신호 추출

- `$ARGUMENTS`가 기존 에이전트명이면 `.claude/agents/<name>.md` 읽고 frontmatter `description:` + 본문 "핵심 역할" 발췌
- 역할 한 문장이면 그 문장 자체가 입력
- mcp-recommendation.md §1 6 신호(S1~S6) 중 매칭 신호 집합 추출 — LLM 직접 분류

### R-2. R0 검색 (Tier R0 = §3 인벤토리 + §3-1 매트릭스)

- §1 신호 → §3-1 capability profile 행 매핑
- 매칭 행의 권고 MCP 발췌 (예: S1+S3 → web-research 행 → fetch + memory)
- §3 인벤토리에서 추가 매칭 후보 grep (Tier T0 우선)

### R-3. R1 cascade (R0 매칭 ≤2 또는 `--cascade=R1` 명시)

- 캐시 `_workspace/_baseline/mcp_catalog.jsonl` hit이면 발췌 → step R-5
- miss 또는 `--refresh`면 `https://github.com/modelcontextprotocol/servers` README WebFetch 1회 → 후보 추출 → 캐시 갱신
- R1 후보는 §3 미박제이므로 "📜 R1 cascade — probe 미완" 라벨

### R-4. R2 cascade (사용자 명시 `--cascade=R2` 시에만)

- WebSearch `mcp-server npm` / `awesome-mcp-servers` — 후보 5~10개 발췌
- 모든 후보에 **출처 verify gate**: npm Author + GitHub org cross-check 필수 (mcp-recommendation.md §2 R2 doctrine + permission-profiles.md §8-3 안전 룰)
- spoof 의심 후보는 점수 산정 *전*에 사용자에게 표시 후 trust 받기

### R-5. 점수 산출

각 후보 × 에이전트에 대해 `mcp-recommendation.md` §3의 E/S/A 점수 산출:

- **E (효율성)**: toolset 필터 지원 / 도구 카운트 / 부수 효과 비중 / inline 호환 / lazy 다운로드 / API quota
- **S (확장성)**: cross-profile / toolset enumeration / Tier / 공식 reference / OS 종속
- **A (정확도)**: probe 완료 / source-grep 일치 / 신호 매칭 카운트 / 출처 verify / deny 박제 / spoof 위험

`Total = E×wE + S×wS + A×wA`, `Adjusted = Total × tier_weight (R0=1.0/R1=0.7/R2=0.4)`.

가중 default `wE=0.4 / wS=0.3 / wA=0.3`. `--weights=` 인자로 override.

### R-6. top-K 표 + 권고 조합

```
[에이전트: <name 또는 가상-역할>]
신호 매칭: <S1>+<S3>+...
가중: wE=0.4 / wS=0.3 / wA=0.3

| Rank | MCP | Tier | 도구수 | E | S | A | Total | Adj | 출처 | 비고 |
|------|-----|------|--------|---|---|---|-------|-----|------|------|
| ... |

권고 조합: <MCP 1> + <MCP 2> (§3-1 <profile> 행 박제 또는 새 조합)
대안: <MCP> (조건: <키 보유 등>)
```

K = default 3 (인자로 변경 가능: `--top=N`).

### R-7. confirm gate

`AskUserQuestion`으로 사용자 선택 받음:
1. 권고 조합 그대로 채택 → `/harness:harness-mcp-adopt <사유>` 명령 1줄 출력 (실행 X)
2. 대안 후보로 변경 → 변경된 조합으로 1번 명령 재출력
3. 보류 → 결과만 보관 (`_workspace/_baseline/mcp_catalog.jsonl` 캐시 외 산출물 없음)
4. 거부 → `_workspace/_telemetry/_mcp_recommendation.jsonl`에 거부 사유 1행 append (`mcp-recommendation.md` §8 거부 학습)

**자동 install/permissions 갱신 ❌** — 본 명령은 *추천*까지만. 채택은 사용자가 명시적으로 `/harness:harness-mcp-adopt` 실행.

## 출력 형식 예시

```
✅ MCP 추천 — agent: web-researcher

신호 매칭: S1(read-heavy) + S3(web-egress) + S6(reasoning-aux)
캐시: hit (_workspace/_baseline/mcp_catalog.jsonl, age=3d)
cascade: R0 + R1 (R0 매칭 2건 / R1 보강 1건)

| Rank | MCP          | Tier | 도구수 | E | S | A | Total | Adj  | 출처 | 비고                          |
|------|--------------|------|--------|---|---|---|-------|------|------|-------------------------------|
| 1    | memory       | T0   |   9    | 7 | 9 | 9 | 8.3   | 8.3  | R0✓  | §3-1 web-research 권고        |
| 2    | fetch        | T0   |   4    | 8 | 7 | 9 | 8.0   | 8.0  | R0✓  | §3-1 web-research 권고        |
| 3    | brave-search | T1+  |   8    | 6 | 6 | 5 | 5.7   | 4.0  | R1   | 📜 docs only — API 키 필요    |

권고 조합: memory + fetch (§3-1 web-research 행 — Layer B 단독, deny 박제 필요)
대안: + brave-search (조건: BRAVE_API_KEY 보유 + settings.json ask 박제)

다음 단계: 권고 조합 채택 시 다음 명령 실행
  /harness:harness-mcp-adopt "web-researcher S1+S3 — fetch + memory 박제"
```

## 캐시 관리

- 기본: 30일 TTL, 자동 갱신 — `--refresh` 강제 갱신
- 위치: `_workspace/_baseline/mcp_catalog.jsonl`
- 1행/후보 schema: `mcp-recommendation.md` §6 참조
- 본 명령은 캐시 갱신 시 *변경 사실*만 사용자에게 보고 (자동 commit ❌ — 사용자 manual)

## Rollback / 거부 학습

- 채택 후 회수: `/harness:harness-mcp-adopt` §10-4 절차
- 본 추천에서 *거부*: R-7 옵션 4 — `_workspace/_telemetry/_mcp_recommendation.jsonl` 1행 누적. 동일 에이전트에 동일 후보 ≥2회 거부 시 차회 추천에서 -2점 페널티 (mcp-recommendation.md §8)

## 범위 외

- **자동 install/키 발급/permissions 갱신 ❌** — `/harness:harness-mcp-adopt`로 인계
- **Host repo (`.harness-host` marker 존재)**: 선조건 (2)로 차단
- **MCP 서버 자체 디버깅**: MCP 서버 issue tracker

## 후속 명령어

- 채택: `/harness:harness-mcp-adopt <사유>`
- 채택 후 정합 진단: `/harness:harness-mcp-status`
- baseline 신호 변경 후 재추천: `/harness:harness-baseline` 후 본 명령 `--refresh`
