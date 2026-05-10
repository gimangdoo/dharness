# §11-1 fixture — `mcp__<server>__<tool>` 노출 패턴 검증

## 선조건

- dharness 프로젝트에 fetch / sequential-thinking / git 3 MCP가 등록되어 있음 (`claude mcp list`로 모두 ✓ Connected)
- 위 등록은 *이전* 세션에서 이뤄졌어야 함 (mid-session add는 §11-1과 무관)

## 실행

1. **현재 Claude Code 세션을 종료**
2. dharness 프로젝트에서 새 세션 시작
3. 첫 user 메시지로 다음을 그대로 입력:

```
ToolSearch query "mcp__"로 max_results 30 검색하고 발견된 모든 도구의 정확한 이름만 bullet로 나열해줘. 추가 설명 없이 이름만.
```

4. 응답을 아래 "결과 캡처" 섹션에 붙여넣음
5. permission-profiles.md §3 표 footnote 또는 본 fixture 결과 로그에 검증 일자·실제 노출 형태 기록
6. permission-profiles.md §8-2 "(γ) 다음 세션 시작 시 `mcp__<server>__<tool>` 노출 검증" 항목을 완료(✓)로 이동

## 예상 결과 (확인 필요)

- fetch 4종: `mcp__fetch__get_raw_text` / `get_rendered_html` / `get_markdown` / `get_markdown_summary`
- git 12종: `mcp__git__git_status` / `git_diff_unstaged` / `git_diff_staged` / `git_diff` / `git_commit` / `git_add` / `git_reset` / `git_log` / `git_create_branch` / `git_checkout` / `git_show` / `git_branch`
- sequential-thinking 1종: 형태 미확정 — 다음 중 하나
  - `mcp__sequential-thinking__sequentialthinking` (하이픈 보존)
  - `mcp__sequential_thinking__sequentialthinking` (언더스코어 변환)
  - `mcp__sequentialthinking__sequentialthinking` (구분자 제거)

## 핵심 관찰 포인트

서버명에 하이픈이 포함된 경우 도구 노출명에서 어떻게 처리되는가. 이 답은 §3 인벤토리에 새 MCP 추가 시 frontmatter `tools:` allowlist 작성 정확도를 좌우한다.

## 결과 캡처

(첫 실행자가 채움 — 응답 그대로 코드블럭에 붙여넣기)

```
[YYYY-MM-DD 결과]

```

## §8-2 갱신 액션

본 fixture 실행 후:
- permission-profiles.md §8-2의 미완 항목 1건을 ✓로 이동
- §3 인벤토리 표 sequential-thinking 행 도구 enumeration 컬럼에 정확한 노출명 footnote 추가
- 본 README 결과 로그에 한 행 추가
