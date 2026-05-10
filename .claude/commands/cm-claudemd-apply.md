---
description: "SessionEnd가 자동 생성한 CLAUDE.md '변경 이력' 표 행 draft를 실제 CLAUDE.md에 추가"
argument-hint: "<session_id>"
---

# /cm-claudemd-apply

`_workspace/_drafts/{date}_{session_id}.md`에 적재된 draft 행을 CLAUDE.md "변경 이력" 표에 삽입한다. apply된 draft는 `_workspace/_drafts/applied/`로 이동.

## 컨텍스트

- **인자:** `<session_id>` (필수, draft 파일명에서 추출)
- **입력:** `_workspace/_drafts/*_{session_id}.md`, `CLAUDE.md`
- **출력:** CLAUDE.md 표에 1행 추가됨

## 선조건 검증

- draft 파일이 `_workspace/_drafts/`에 있어야 함 (`/cm-status`로 pending count 확인)
- CLAUDE.md에 "변경 이력" heading 또는 strong 직후 markdown 표가 존재해야 함

## 실행 절차

`py .claude/hooks/cm_commands.py claudemd-apply <session_id>`가 다음을 수행:

1. `_workspace/_drafts/*_{session_id}.md` 검색
2. draft의 ```` ``` ```` 블록 안 markdown table row 추출
3. CLAUDE.md "변경 이력" 표 마지막 row 다음에 삽입
4. draft 파일을 `_workspace/_drafts/applied/`로 이동

## 후속

- 사유 컬럼이 placeholder인 채로 추가됨 — CLAUDE.md를 직접 편집해 사유를 채울 것
- 미리 보기: 적용 전에 `cat _workspace/_drafts/{date}_{session_id}.md`로 draft 확인 가능

## 범위 외

- draft 자동 생성은 SessionEnd 훅 책임 (`session_end.py:generate_draft`)
- 기존 CLAUDE.md 표 형식이 깨져있으면 silent fail (heading 또는 표 헤더-구분선 매칭)
