---
name: changelog-row-writer
description: 변경 이력 표에 한 행을 표준 형식으로 append 한다. "변경 이력 갱신"·"changelog 추가"·"이력 박제" 요청 시 트리거. 신규 파일 생성·전체 문서 재작성에는 트리거하지 않음.
meta:
  skill_kind: user-facing
  candidate_version: 1
  gap_source: pattern-synthesis
  static_tier: PASS
  llm_judge_tier: not-run
  mc_tier: not-run
  promoted_to: null
---

# changelog-row-writer

> **wiki bridge fixture (M1 Emit 산출물 예시).** dharness가 합성한 reusable skill을
> 로컬 wiki `candidates/<name>-v1/`로 Emit 할 때의 candidate 형태 canonical 예시.
> M5 schema gate(`chain.py:check_wiki_candidate_schema`)가 본 fixture를 검증한다.

## 트리거

- "변경 이력 갱신해줘" / "changelog에 이번 작업 추가" / "이력 한 줄 박제"
- NOT: "changelog 파일 새로 만들어" (신규 파일은 별도 skill) · 전체 문서 재작성

## 워크플로우

1. 대상 changelog 표 위치 확인 (`## 변경 이력` 헤더 하단 표).
2. 표 컬럼 스키마 읽기 (일자 / event / 본문).
3. 한 행 append — 기존 행 형식·정렬 유지, 위 컬럼 순서 준수.
4. append 후 표 깨짐 없는지 1회 확인.

## 입출력

- 입력: 변경 내용 1문단 + 대상 changelog 경로.
- 출력: 표에 1행 추가된 changelog (다른 행 불변).
