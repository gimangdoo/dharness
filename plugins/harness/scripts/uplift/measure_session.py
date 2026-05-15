"""Q2 workflow uplift baseline — 세션 단위 telemetry 측정 (LLM-free).

`_workspace/_telemetry/*.jsonl`을 스캔해 session_id별 정량 지표를 집계.
no-harness baseline 세션 vs harness 세션 비교 시 입력 데이터로 사용.

Usage:
    py plugins/harness/scripts/uplift/measure_session.py [--json] [--session-id <id>]
    py plugins/harness/scripts/uplift/measure_session.py --label <baseline|harness> --session-id <id>

`--label`은 본 측정 결과를 `uplift_sessions.jsonl`에 박제할 때 group tag로 사용.
미지정 시 측정만 수행 + stdout 출력.

지표:
    - tool_invocations: tool_output_captured 이벤트 수
    - total_raw_size_bytes: raw_size 누계
    - agent_invocations / agent_failures / failure_ratio
    - duration_seconds: 첫 capture_init ~ 마지막 capture_finalize 간격
"""

from __future__ import annotations

import io
import json
import sys
import time
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[4]
TELEMETRY_DIR = REPO_ROOT / "_workspace" / "_telemetry"
UPLIFT_LOG = TELEMETRY_DIR / "uplift_sessions.jsonl"


def _parse_iso(ts: str) -> datetime | None:
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError):
        return None


def collect_events(session_filter: str | None) -> dict[str, list[dict]]:
    """session_id → events list. 파일 raw_lines 정렬 보존."""
    by_session: dict[str, list[dict]] = {}
    if not TELEMETRY_DIR.exists():
        return by_session
    for path in sorted(TELEMETRY_DIR.glob("*.jsonl")):
        # poc_dogfood_static.jsonl / uplift_sessions.jsonl 제외 — 본 측정은 세션 telemetry만
        if path.name in {"poc_dogfood_static.jsonl", "uplift_sessions.jsonl"}:
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    sid = event.get("session_id")
                    if not sid:
                        continue
                    if session_filter and sid != session_filter:
                        continue
                    by_session.setdefault(sid, []).append(event)
        except OSError:
            continue
    return by_session


def summarize(session_id: str, events: list[dict]) -> dict:
    tool_invocations = 0
    total_raw_size = 0
    agent_invocations = 0
    agent_failures = 0
    init_ts: str | None = None
    final_ts: str | None = None
    for e in events:
        etype = e.get("type")
        if etype == "tool_output_captured":
            tool_invocations += 1
            total_raw_size += int(e.get("raw_size") or 0)
        elif etype == "agent_invocation":
            agent_invocations += 1
        elif etype == "agent_failure":
            agent_failures += 1
        elif etype == "session_capture_init":
            if init_ts is None:
                init_ts = e.get("ts")
        elif etype == "session_capture_finalize":
            final_ts = e.get("ts")
    duration = None
    if init_ts and final_ts:
        a, b = _parse_iso(init_ts), _parse_iso(final_ts)
        if a and b:
            duration = int((b - a).total_seconds())
    failure_ratio = (
        round(agent_failures / agent_invocations, 4) if agent_invocations else None
    )
    return {
        "session_id": session_id,
        "tool_invocations": tool_invocations,
        "total_raw_size_bytes": total_raw_size,
        "agent_invocations": agent_invocations,
        "agent_failures": agent_failures,
        "failure_ratio": failure_ratio,
        "init_ts": init_ts,
        "final_ts": final_ts,
        "duration_seconds": duration,
    }


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    session_filter = None
    label = None
    for i, a in enumerate(argv):
        if a == "--session-id" and i + 1 < len(argv):
            session_filter = argv[i + 1]
        if a == "--label" and i + 1 < len(argv):
            label = argv[i + 1]

    by_session = collect_events(session_filter)
    summaries = [summarize(sid, evs) for sid, evs in sorted(by_session.items())]

    if label and session_filter and summaries:
        TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
        with open(UPLIFT_LOG, "a", encoding="utf-8") as fh:
            entry = dict(summaries[0])
            entry["label"] = label
            entry["recorded_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    report = {
        "section": "uplift_session",
        "session_filter": session_filter,
        "label": label,
        "sessions_count": len(summaries),
        "sessions": summaries,
    }

    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    icon = "✅" if summaries else "⚠️"
    print(f"{icon} uplift_session: {len(summaries)} sessions")
    for s in summaries:
        print(
            f"  - {s['session_id']}: tools={s['tool_invocations']} "
            f"raw={s['total_raw_size_bytes']}B agents={s['agent_invocations']}"
            f" fails={s['agent_failures']} (ratio={s['failure_ratio']})"
            f" duration={s['duration_seconds']}s"
        )
    if label and session_filter and summaries:
        print(f"  appended → {UPLIFT_LOG.relative_to(REPO_ROOT)} (label={label})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
