---
description: "SessionEnd가 자동 생성한 CLAUDE.md '변경 이력' 표 행 draft를 실제 CLAUDE.md에 추가 (사유 인자 선택)"
argument-hint: "<session_id> [사유...]"
---

# /cm-claudemd-apply

`_workspace/_drafts/{date}_{session_id}.md`에 적재된 draft 행을 CLAUDE.md "변경 이력" 표에 삽입한다. 두 번째 인자 이후를 공백 join하여 사유 컬럼의 placeholder를 즉시 치환한다 (생략 시 placeholder 유지). apply된 draft는 `_workspace/_drafts/applied/`로 이동.

## 컨텍스트

- **인자:**
  - `<session_id>` (필수, draft 파일명에서 추출)
  - `[사유 텍스트...]` (선택, 인자 2번 이후 모두 공백 join하여 단일 사유로 사용)
- **입력:** `_workspace/_drafts/*_{session_id}.md`, `CLAUDE.md`
- **출력:** CLAUDE.md 표에 1행 추가됨 (사유는 인자가 있으면 치환, 없으면 placeholder 유지)

## 선조건 검증

- draft 파일이 `_workspace/_drafts/`에 있어야 함 (`/cm-status`로 pending count 확인)
- CLAUDE.md에 "변경 이력" heading 또는 strong 직후 markdown 표가 존재해야 함

## 실행 절차

`py .claude/hooks/cm_commands.py claudemd-apply <session_id> [사유...]`가 다음을 수행:

1. `_workspace/_drafts/*_{session_id}.md` 검색
2. draft의 ```` ``` ```` 블록 안 markdown table row 추출
3. 사유 인자가 있으면 `_sanitize_reason()`이 정규화 (줄바꿈 → 공백, `|` → `\|`) 후 placeholder 치환
4. CLAUDE.md "변경 이력" 표 마지막 row 다음에 삽입
5. draft 파일을 `_workspace/_drafts/applied/`로 이동

## 사용 예시

```text
# placeholder 유지 (기존 동작) — 이후 vim/IDE로 직접 편집 필요
/cm-claudemd-apply 9dae78

# 사유 즉시 치환 — 인자 2번 이후 공백 join
/cm-claudemd-apply 9dae78 단계 D draft 자동 회로 e2e 검증
/cm-claudemd-apply abc123 "Phase 5-2 PoC 완료 — §8-2 미완 5건 중 1건 해소"
```

## 사유 인자 안전 처리

| 입력 | 결과 |
|------|------|
| 인자 0개 | placeholder 유지 (backward compat) |
| `\|` 포함 | `\\|`로 escape (markdown 표 컬럼 깨짐 방지) |
| 줄바꿈 (`\n`/`\r`) | 공백으로 collapse (table row 1줄 강제) |
| strip 후 빈 문자열 | placeholder 유지 |
| draft에 placeholder 없음 | 사유 인자 무시 + 경고 출력 |

## 후속

- 미리 보기: 적용 전에 `cat _workspace/_drafts/{date}_{session_id}.md`로 draft 확인 가능
- 사유 누락 시 `/cm-status`가 placeholder 잔존을 표시하지 않으므로, 적용 후 CLAUDE.md 마지막 row를 점검 권장

## 범위 외

- draft 자동 생성은 SessionEnd 훅 책임 (`session_end.py:generate_draft`)
- 기존 CLAUDE.md 표 형식이 깨져있으면 silent fail (heading 또는 표 헤더-구분선 매칭)
- placeholder 상수 단일 출처: `.claude/hooks/_schema.py:DRAFT_REASON_PLACEHOLDER`
