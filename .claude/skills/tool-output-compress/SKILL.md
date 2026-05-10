---
name: tool-output-compress
description: |
  cm-compressor 에이전트가 대용량 도구 출력(>10KB)을 압축할 때 사용하는 정책 스킬.
  도구별 압축 전략, auto-expand 예외 룰, raw 보존 경로 규칙을 정의한다.
  cm-compressor가 어떤 출력을 어떻게 압축해야 할지 판단이 필요할 때 이 스킬을 참조하라.
---

# tool-output-compress

cm-compressor가 도구 출력을 압축할 때 적용하는 정책과 전략을 정의한다.

## 압축 트리거 조건

| 조건 | 처리 |
|------|------|
| 출력 크기 < 10KB | 패스스루 (압축 없음) |
| 출력 크기 10KB ~ 100KB | 의미 압축 후 원본 저장 |
| 출력 크기 > 100KB | 강압축 (핵심 only) + 원본 저장 |

## 도구별 압축 전략

| 도구 | 압축 전략 | 보존 핵심 |
|------|---------|-----------|
| WebFetch / WebSearch | 핵심 섹션 추출 + URL + 날짜 | 관련 단락, 코드 블록 |
| Read (대용량 파일) | 파일 구조 + 관련 섹션 | 요청 키워드 주변 50줄 |
| Bash (긴 출력) | 오류 라인 + 마지막 20줄 + 통계 | exit code, stderr |
| Glob / Grep | 결과 수 + 상위 20개 경로 | 패턴 매칭 요약 |
| Agent 결과 | 핵심 결론 + 수행 작업 목록 | 결정 사항, 파일 변경 |
| 기타 | 앞 500토큰 + "... (전체: {path})" | 시작 부분 |

## Auto-expand 예외 룰

다음 경우에는 압축 없이 전체를 컨텍스트에 반환한다:

1. 사용자가 "전체 출력 보여줘" 또는 "압축하지 마"를 명시한 경우
2. 출력이 에러 메시지인 경우 (오류 컨텍스트 손실 방지)
3. 출력에 코드 diff가 포함된 경우 (patch 정합성 보장)

PostToolUse hook은 임계치 10KB(=10240바이트) 초과 시에만 cm-compressor를 트리거하므로 경계값 처리에 별도 마진이 필요하지 않다. 임계치 자체를 변경하려면 `_workspace/_hooks/post_tool_use.py`의 `THRESHOLD_BYTES`와 `cm-compressor.md`/`cm-orchestrator/SKILL.md`의 ">10KB" 표기를 함께 갱신한다.

## Raw 보존 경로 규칙

```
_workspace/_tool_outputs/{session_id}/{ts}_{tool}_{n}.{ext}
```

- `session_id`: 현재 세션의 고유 ID (6자 hex)
- `ts`: Unix timestamp (초 단위)
- `tool`: 도구 이름 (소문자, 하이픈)
- `n`: 세션 내 순번 (001부터)
- `ext`: 출력 유형별 확장자

| 도구 | ext |
|------|-----|
| WebFetch | .html 또는 .md |
| Read | .txt |
| Bash | .log |
| Glob / Grep | .txt |
| Agent | .md |
| 기타 | .txt |

## 압축 요약 형식

```markdown
[압축 요약 — {도구} 출력 | 원본: {raw_path} | {raw_size}→{compressed_size}]

{핵심 내용 요약}

> 전체 출력이 필요하면: {raw_path}
```

## 품질 기준

| 지표 | 목표 |
|------|------|
| 압축 비율 (compressed/raw) | < 0.1 (90% 압축) |
| 요약 토큰 | ≤ 500 |
| 정보 손실 | 핵심 결론 보존 필수 |

압축 비율 > 0.5이면 압축 효과가 미미 → telemetry ratio 필드로 Phase 10에 신호.

## 압축 실패 시 fallback

1. 1차: 도구별 전략 적용 시도
2. 2차: 앞 500토큰 잘라서 반환 + raw 경로 표시
3. 3차: raw 전체 반환 (압축 불가 명시)
