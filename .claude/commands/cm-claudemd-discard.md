---
description: "미적용 CLAUDE.md draft를 폐기 (보관: _workspace/_drafts/discarded/)"
argument-hint: "[<session_id>] (생략 시 모두 폐기)"
---

# /cm-claudemd-discard

미적용 draft 파일을 `_workspace/_drafts/discarded/`로 이동한다. 인자가 있으면 그 session_id 한 건만, 없으면 모든 pending draft.

## 컨텍스트

- **인자:** `[session_id]` (선택)
- **입력:** `_workspace/_drafts/*.md`
- **출력:** `_workspace/_drafts/discarded/`로 이동된 파일 목록

## 실행 절차

`py .claude/hooks/cm_commands.py claudemd-discard [session_id]`가 다음을 수행:

1. session_id 인자 → 매칭 draft 1건만, 미지정 → 모든 pending draft
2. 각 파일을 `_workspace/_drafts/discarded/`로 rename (덮어쓰기)
3. 이동 결과 출력

## 범위 외

- discarded/는 보관 — 영구 삭제는 별도 (수동 `rm` 또는 `/cm-reset`)
