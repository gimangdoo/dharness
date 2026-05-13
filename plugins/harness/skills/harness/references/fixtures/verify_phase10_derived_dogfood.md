# Phase 10 derived dogfood verify (2026-05-12)

derived 프로젝트의 Phase 10 telemetry append 회로 실측 검증. *본 verify는 plugin host 본 폴더(self-host CM 운영 중)에서 수행. 외부 install user는 동등 절차를 본인 환경에서 재현 가능.*

## 환경
- 측정 host root (예시): `C:\Users\user01\awesome-files\dharness`
- derived: `<host>/_workspace/_dogfood/sample-research/` (작업 후 cleanup)
- PowerShell: 5.1 (Windows 11)

## 발견된 함정 (orchestrator-template 정정 반영)

| # | 함정 | 증상 | 정정 |
|---|------|------|------|
| 1 | `Get-Date -AsUTC` PS7+ 전용 | PS5.1에서 `parameter not found` 에러 → `$ts=null` | `[DateTime]::UtcNow` 사용 |
| 2 | `Add-Content -Encoding utf8` BOM 삽입 | 첫 라인 hex prefix `efbbbf` → JSON 파싱 실패 (`Unexpected UTF-8 BOM`) | `[System.IO.File]::AppendAllText` + `UTF8Encoding($false)` |
| 3 | 상대 경로 `_workspace\...` | cwd 변경 시 다른 위치에 작성 | `Resolve-Path -LiteralPath "."` 기반 절대경로 |
| 4 | hashtable `@{}` 키 순서 무작위 | JSON 키 순서가 매 실행 변동 → diff 노이즈 | `[ordered]@{}` |

host self-host CM counter helper도 BOM tolerantly 대응 — `open(path, encoding='utf-8-sig')`로 변경 (defensive).

## 검증 항목

| 항목 | 결과 |
|------|------|
| derived `_workspace/_telemetry/{date}.jsonl` 파일 생성 | ✓ |
| 첫 3 byte BOM 검사 (`7b2274` = `{"t`) | ✓ bomless |
| Korean trigger_keyword (`리서치` = U+B9AC,U+C11C,U+CE58) 보존 | ✓ |
| `harness_invocation` 1 + `agent_invocation` 2 라인 모두 JSON parse 성공 | ✓ |
| counter helper가 derived path에서 정확 카운트 | ✓ (1/2/0) |
| 11 invoc + 2 fail 추가 → 임계값 도달 alert_due=True | ✓ |
| `touch_last_adapt()` 후 카운터 reset → 0/0/0 alert_due=False | ✓ |
| `/harness:harness-adapt` 선조건 (telemetry + baseline 존재) 충족 | ✓ |

## 한계 (미검증)

- 실제 orchestrator skill 인보케이션 — Claude Code 세션 1개 한정, derived의 SKILL.md를 LLM 메모리에 로드해 워크플로우 실행은 별도 세션 필요.
- Drift 감지 룰 (5-1/5-2) — 실 데이터 부족, dogfood이라 의도적 drift 패턴 없음.

## 다음 액션 후보

- 실 derived (외부 프로젝트) 1개에 본 orchestrator 패턴 적용 후 30일 실 사용 → drift 감지 룰 실측.
- `_workspace/_dogfood/` 자체를 회귀 fixture로 보존 (현재는 작업 후 cleanup).
