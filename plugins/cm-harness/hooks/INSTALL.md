# CM 훅 설치 가이드

CM 시스템이 라이프사이클 이벤트를 자동으로 캡처하려면 사용자가 **직접**
`.claude/settings.json`에 hooks 섹션을 등록해야 한다. 자동 모드의 권한 정책상 에이전트는
훅 등록 파일을 임의로 쓸 수 없다 — 보안 경계.

## 설치 절차

1. 현재 `.claude/settings.local.json`을 백업
2. 아래 JSON을 `.claude/settings.json`(공유 설정) 또는 `.claude/settings.local.json`
   (로컬 전용)에 병합
3. Claude Code 재시작 또는 새 세션에서 효과 확인

## 등록할 JSON

훅 등록 전 `plugins/cm-harness/hooks/*.py` 스크립트 내용을 직접 검토하라. 본 디렉토리의
스크립트는 다음 작업만 수행한다 (외부 송신 없음):

- `session_start.py` — session_id 발급, 디렉토리·DB 부트스트랩, telemetry 1줄 append
- `post_tool_use.py` — raw.jsonl append + 10KB 초과 시 `_tool_outputs/` 보존
- `session_end.py` — transcript.md 평탄화, sessions UPDATE, telemetry 1줄 append

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "python \"${CLAUDE_PROJECT_DIR}/plugins/cm-harness/hooks/session_start.py\"" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "python \"${CLAUDE_PROJECT_DIR}/plugins/cm-harness/hooks/post_tool_use.py\"" }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          { "type": "command", "command": "python \"${CLAUDE_PROJECT_DIR}/plugins/cm-harness/hooks/session_end.py\"" }
        ]
      }
    ]
  }
}
```

**matcher 주의사항:**
- `SessionStart` / `SessionEnd`는 matcher가 이벤트 서브타입(`startup`/`resume`/`clear` 등)으로 해석된다. 모든 서브타입에 대해 작동시키려면 matcher 키를 **생략**한다 (위 예시처럼).
- `PostToolUse`는 matcher가 도구 이름 정규식이다. `""`(빈 문자열) 또는 `".*"`가 모든 도구 매칭. `"*"`는 정규식으로 무효이므로 사용 금지.
- 경로는 `${CLAUDE_PROJECT_DIR}`로 안전하게 절대화. cwd가 프로젝트 루트가 아닌 환경에서도 정상 작동한다.

기존 settings 파일에 다른 키가 있으면 `hooks` 키만 병합하라.

## 검증

설치 후 새 Claude Code 세션을 열고:

```
python plugins/cm-harness/hooks/cm_commands.py status
```

- `sessions` 카운트가 1 이상 → SessionStart 훅 정상 동작
- 도구 사용 후 세션 종료 → 다음 세션에서 `python plugins/cm-harness/hooks/cm_commands.py sessions` 실행 시 직전 세션의 `tools_used` 컬럼이 채워짐 → PostToolUse + SessionEnd 훅 정상 동작 (`tools_used`는 SessionEnd 평탄화 단계에서 기록되므로 같은 세션 내에서는 비어있다)

## 비활성화

훅이 실수로 등록됐거나 일시 비활성화하려면 `.claude/settings.json`에서 `hooks` 키만
제거하면 된다. CM 시스템의 다른 부분(스킬·에이전트·DB)은 영향 없음.

## 의존성

훅 스크립트는 표준 라이브러리만 사용하므로 추가 설치 불필요. Python 3.11+ 가정.
대시보드 워커는 별도 — `plugins/cm-harness/worker/README.md` 참조.

## Python 런처 선택 — 플랫폼별 주의

훅 명령에서 사용할 인터프리터 이름은 **OS 환경에 따라 다르다**:

| 플랫폼 | 권장 명령 | 이유 |
|--------|----------|------|
| **Windows (Python 공식 인스톨러 사용)** | `py` | bare `python`은 Microsoft Store 스텁(`%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe`)에 매핑되어 exit 9009로 실패할 수 있다. `py`는 Windows Python Launcher로 안정적. |
| **Windows (Python을 PATH에 직접 추가했음)** | `python` 또는 `py` | 둘 다 동작 |
| **macOS / Linux** | `python3` 또는 `python` | 보통 `python`이 Python 3을 가리키지만 일부 배포판은 `python3` 필요 |

검증: `python --version` 실행 후 exit code가 0이 아니거나 Microsoft Store가 열리면
`py --version`으로 대체 — 정상 출력되면 settings의 `command`를 `py ...`로 변경한다.
