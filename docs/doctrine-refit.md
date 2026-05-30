# Doctrine drift refit — plugin upgrade 후 derived harness 보강

> [README](../README.md)로 돌아가기

dharness plugin doctrine이 업그레이드된 후(예: 새 invariant·새 권장 패턴 박제) 기존 derived harness를 새 doctrine으로 끌어올리는 절차. 단일 명령이 아니라 **기존 명령 조합** — 2026-05-23 (v0.11.0) 인프라.

## 1. 자동 알림 — version drift 1줄

- `harness-new`·`harness-baseline`이 합성·갱신 시점 `plugin.json` `version`을 `intent_profile.md` frontmatter `meta.dharness_version`에 박제 (`intent-profile-schema.md` §5).
- 이후 `/harness:harness-validate` 또는 `/harness:harness-status` 호출 시 baseline version ↔ 현 plugin version 비교 → mismatch면 ℹ️ refit 권고 1줄 자동 출력.

```text
ℹ️  dharness plugin upgrade 감지 — baseline `0.10.0` → 현 `0.11.0`.
   doctrine refit 권고: `/harness:harness-status --deep` + `/harness:harness-validate` 진단 후
   발견 항목별 `/harness:harness-evolve`(내부 add-skill/remove op)로 수정.
```

## 2. 진단 — status --deep + validate

| 진단 명령 | 영역 |
|---|---|
| `/harness:harness-status --deep` | LLM 추론 영역 — 책임 중복·트리거·통신 프로토콜·워크플로우 |
| `/harness:harness-validate` | 결정적 invariant — 인젝션 가드·model 필드·tools↔MCP·SKILL.md 빈 파일·파일명·telemetry 박제·dangling reference 등 |

## 3. 수정 — 항목별 매핑 (모두 `/harness:harness-evolve` 내부 op)

| 진단 발견 유형 | 수정 (evolve 피드백 → 내부 op) |
|---|---|
| 본문 누락 절(예: `입력 신뢰 경계`)·schema 위반 | `/harness:harness-evolve <피드백>` (edit-skill/edit-agent) |
| 누락 에이전트·스킬 | `/harness:harness-evolve "X 추가"` (add-agent/add-skill) |
| 책임 중복·통합 필요 | `/harness:harness-evolve "이 둘 합쳐"` (merge) |
| 책임 과부하·분할 필요 | `/harness:harness-evolve "X 쪼개"` (split) |
| 잘못 합성된 항목 제거 | `/harness:harness-evolve "X 제거"` (remove) |
| MCP 매트릭스 부적합 | `/harness:harness-evolve "X MCP 붙여"` (mcp-adopt) · 추천은 `/harness:harness-status --mcp` |

## 4. 재진단

수정 후 `/harness:harness-validate` 재실행 → 0 errors + version drift 라인 사라짐 확인. 사라지지 않으면 `harness-baseline`으로 `meta.dharness_version` 새 anchor 박제.
