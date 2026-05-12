# CLAUDE.md — dharness

## 저장소 구성

`harness` plugin 단일 저장소. 도메인 한 문장을 받아 에이전트 팀 + 스킬 세트로 변환하는 메타 스킬 팩토리.

- `plugins/harness/` — `harness` plugin (외부 install 대상)
  - `skills/harness/SKILL.md` — 메타 스킬 본체 (Phases 0-10)
  - `skills/harness/references/` — 설계 가이드 (permission-profiles, design-patterns 등)
  - `commands/harness-*.md` — `/harness:harness-*` 슬래시 커맨드 7종
- `.claude-plugin/marketplace.json` — `harness` plugin 단일 카탈로그

신규 사용자 단일 출처: [`README.md`](./README.md) + [`plugins/harness/skills/harness/SKILL.md`](./plugins/harness/skills/harness/SKILL.md).

---

## In-session 컨텍스트 가드라인

세션 *내부*의 토큰 부피는 워크플로우 선택으로 줄인다. Claude Code의 자동 컨텍스트 압축·subagent 격리·도구별 truncation에 위임.

| 상황 | 권장 |
|------|------|
| 5+ 파일 cross-cutting 조사 | `Agent` (Explore/general-purpose) 위임 — 요약만 반환 |
| 큰 디렉토리 탐색 | `Glob`/`Grep` 우선 → 위치 확인 후 `Read` offset/limit |
| 큰 commit history | `git log -p` 대신 `git log --oneline` + 타겟 commit만 `git show` |
| 큰 diff | `git diff --stat` 우선 → 관심 영역만 `git diff -- <path>` |
| 같은 파일 반복 read | 한 번 읽고 conversation 내 재참조 — 재read는 mtime 변경 시만 |
