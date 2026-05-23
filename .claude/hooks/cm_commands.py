"""/cm-* 슬래시 커맨드 결정적 핸들러 (dharness self-host).

사용법 (repo root에서):
    py .claude/hooks/cm_commands.py status
    py .claude/hooks/cm_commands.py sessions [--limit N]
    py .claude/hooks/cm_commands.py reset --confirm
    py .claude/hooks/cm_commands.py prune [--older-than DAYS] [--confirm]
    py .claude/hooks/cm_commands.py claudemd-list
    py .claude/hooks/cm_commands.py claudemd-apply <session_id>
    py .claude/hooks/cm_commands.py claudemd-discard [<session_id>]

결정적 작업만 처리한다. DB·디렉토리 부트스트랩은 SessionStart 훅 또는 reset 시
자동 수행되므로 별도 init 명령 없음.
"""

from __future__ import annotations

import argparse
import contextlib
import re
import shutil
import sqlite3
import sys
import time
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _schema import (
    CHANGELOG_MD,
    DB_PATH,
    DDL,
    DRAFT_REASON_PLACEHOLDER,
    DRAFTS_APPLIED,
    DRAFTS_DIR,
    DRAFTS_DISCARDED,
    MEMORY_ROOT,
    REPO_ROOT,
    TELEMETRY_DIR,
    TOOL_OUTPUTS,
)

PRUNE_DEFAULT_DAYS = 90  # 3개월 — memory-search 검색 속도와 history 잔존의 균형
TELEMETRY_FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.jsonl$")
DRAFT_FILENAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_[A-Za-z0-9]+\.md$")

COUNT_TABLES = ("observations", "sessions")
CHANGELOG_ROW_WARN_THRESHOLD = 40

DRAFT_ROW_RE = re.compile(r"^```\s*\n(\| .*?\|)\s*\n```", re.MULTILINE)
ROW_LINE_RE = re.compile(r"^\s*\|.+\|\s*$")
SEP_LINE_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@contextlib.contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    """close 보장 context manager. `with _connect() as conn:` 형태로 사용."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _ensure_db() -> bool:
    if DB_PATH.exists():
        return True
    print("observations.db 미존재 — 새 Claude Code 세션을 시작하면 SessionStart 훅이 자동 생성합니다.")
    return False


def _init_storage() -> list[tuple]:
    """디렉토리 + DB 스키마 부트스트랩. cmd_reset이 wipe 후 호출."""
    created = []
    for sub in ("sessions", "observations"):
        p = MEMORY_ROOT / sub
        existed = p.exists()
        p.mkdir(parents=True, exist_ok=True)
        created.append((p, existed))
    existed = TOOL_OUTPUTS.exists()
    TOOL_OUTPUTS.mkdir(parents=True, exist_ok=True)
    created.append((TOOL_OUTPUTS, existed))

    db_existed = DB_PATH.exists()
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(DDL)
    created.append((DB_PATH, db_existed))
    return created


def cmd_status() -> int:
    if not _ensure_db():
        return 1
    with _connect() as conn:
        counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in COUNT_TABLES}
        recent = conn.execute(
            "SELECT COUNT(*) FROM sessions WHERE date(started_at) >= date('now', '-7 days')"
        ).fetchone()[0]
        dh_events = conn.execute("SELECT COUNT(*) FROM observations WHERE section='dharness_event'").fetchone()[0]
    pending_drafts = list(DRAFTS_DIR.glob("*.md")) if DRAFTS_DIR.exists() else []
    history_rows = _count_changelog_rows()

    print(f"📊 CM 상태 ({REPO_ROOT.name})")
    print(f"  observations:        {counts['observations']} (dharness_event {dh_events})")
    print(f"  sessions:            {counts['sessions']} (최근 7일: {recent})")
    print(f"  changelog draft:     {len(pending_drafts)} pending")
    if history_rows is not None:
        warn = "  ⚠ 표가 길어졌습니다 — archive 검토 권장" if history_rows >= CHANGELOG_ROW_WARN_THRESHOLD else ""
        print(f"  CHANGELOG.md:        {history_rows} rows{warn}")
    return 0


def _count_changelog_rows() -> int | None:
    """CHANGELOG.md '변경 이력' 표의 데이터 row 수. 표 미발견 시 None."""
    if not CHANGELOG_MD.exists():
        return None
    try:
        lines = CHANGELOG_MD.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    span = _find_change_history_table(lines)
    if not span:
        return None
    header_idx, last_row_idx = span
    # header + separator + data rows. data rows = last_row_idx - (header_idx + 1)
    return max(0, last_row_idx - header_idx - 1)


def cmd_sessions(limit: int) -> int:
    if not _ensure_db():
        return 1
    with _connect() as conn:
        rows = conn.execute("""
            SELECT session_id, date, duration_min, tools_used
            FROM sessions ORDER BY date DESC, started_at DESC LIMIT ?
        """, (limit,)).fetchall()
    print(f"📅 최근 {len(rows)}개 세션")
    for r in rows:
        dur = f"{r['duration_min']}m" if r['duration_min'] else "—"
        print(f"  {r['date']} {r['session_id']} {dur:>5} tools={r['tools_used'] or '[]'}")
    return 0


def cmd_reset(confirmed: bool) -> int:
    if not confirmed:
        print("⚠️  --confirm 플래그 없이는 실행 불가. /cm-reset 슬래시 커맨드 본문의 확인 절차를 따르세요.")
        return 1
    if MEMORY_ROOT.exists():
        shutil.rmtree(MEMORY_ROOT)
    if TOOL_OUTPUTS.exists():
        shutil.rmtree(TOOL_OUTPUTS)
    print("🗑️  _memory/, _tool_outputs/ 삭제됨")
    for p, existed in _init_storage():
        marker = "(existing)" if existed else "(created)"
        print(f"  {'✅' if existed else '🆕'} {p.relative_to(REPO_ROOT)} {marker}")
    return 0


# ---------------------------- prune (partial GC) ----------------------------

def _collect_prune_targets(cutoff_date: str) -> dict:
    """cutoff_date (YYYY-MM-DD) *이전* 데이터를 대상으로 삭제 후보 enumerate.

    반환: {sessions: [(sid, date), ...], session_dirs: [Path, ...],
           tool_output_dirs: [Path, ...], telemetry_files: [Path, ...],
           applied_drafts: [Path, ...], discarded_drafts: [Path, ...],
           observation_rows: int, session_rows: int}
    """
    targets = {
        "sessions": [], "session_dirs": [], "tool_output_dirs": [],
        "telemetry_files": [], "applied_drafts": [], "discarded_drafts": [],
        "observation_rows": 0, "session_rows": 0,
    }
    if not DB_PATH.exists():
        return targets
    with _connect() as conn:
        rows = conn.execute(
            "SELECT session_id, date FROM sessions WHERE date < ? ORDER BY date ASC",
            (cutoff_date,),
        ).fetchall()
        sids = [r["session_id"] for r in rows]
        targets["sessions"] = [(r["session_id"], r["date"]) for r in rows]
        targets["session_rows"] = len(sids)
        if sids:
            placeholders = ",".join("?" * len(sids))
            n = conn.execute(
                f"SELECT COUNT(*) FROM observations WHERE session_id IN ({placeholders})",
                sids,
            ).fetchone()[0]
            targets["observation_rows"] = n
    # 디렉토리·파일 enumerate.
    sessions_root = MEMORY_ROOT / "sessions"
    for sid, _ in targets["sessions"]:
        d = sessions_root / sid
        if d.exists():
            targets["session_dirs"].append(d)
        t = TOOL_OUTPUTS / sid
        if t.exists():
            targets["tool_output_dirs"].append(t)
    # telemetry: filename에 박힌 date 비교.
    if TELEMETRY_DIR.exists():
        for p in sorted(TELEMETRY_DIR.glob("*.jsonl")):
            m = TELEMETRY_FILENAME_RE.match(p.name)
            if m and m.group(1) < cutoff_date:
                targets["telemetry_files"].append(p)
    # applied/discarded drafts: filename 박힌 date 비교 — pending drafts는 prune 대상 아님.
    for sub in (DRAFTS_APPLIED, DRAFTS_DISCARDED):
        if not sub.exists():
            continue
        key = "applied_drafts" if sub == DRAFTS_APPLIED else "discarded_drafts"
        for p in sorted(sub.glob("*.md")):
            m = DRAFT_FILENAME_RE.match(p.name)
            if m and m.group(1) < cutoff_date:
                targets[key].append(p)
    return targets


def _format_prune_summary(targets: dict, cutoff_date: str, dry_run: bool) -> str:
    head = "🔍 [dry-run] " if dry_run else "🗑️  "
    parts = [
        f"{head}prune (cutoff: {cutoff_date} *이전* 데이터)",
        f"  sessions:           {targets['session_rows']:>4} rows",
        f"  observations:       {targets['observation_rows']:>4} rows",
        f"  session 디렉토리:    {len(targets['session_dirs']):>4} 개",
        f"  tool_output 디렉토리: {len(targets['tool_output_dirs']):>4} 개",
        f"  telemetry 파일:      {len(targets['telemetry_files']):>4} 개",
        f"  applied 드래프트:    {len(targets['applied_drafts']):>4} 개",
        f"  discarded 드래프트:  {len(targets['discarded_drafts']):>4} 개",
    ]
    return "\n".join(parts)


def cmd_prune(days: int, confirmed: bool) -> int:
    if days < 1:
        print("⚠️  --older-than 값은 1 이상이어야 합니다.")
        return 1
    if not _ensure_db():
        return 1
    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_date = cutoff_dt.strftime("%Y-%m-%d")
    targets = _collect_prune_targets(cutoff_date)
    total = (targets["session_rows"] + len(targets["telemetry_files"])
             + len(targets["applied_drafts"]) + len(targets["discarded_drafts"]))
    print(_format_prune_summary(targets, cutoff_date, dry_run=not confirmed))
    if total == 0:
        print("\n삭제할 데이터가 없습니다.")
        return 0
    if not confirmed:
        print(
            f"\n--confirm 플래그 없이는 *삭제하지 않습니다* (dry-run). "
            f"실제 삭제: prune --older-than {days} --confirm"
        )
        return 0
    # 실제 삭제.
    for d in targets["session_dirs"]:
        shutil.rmtree(d, ignore_errors=True)
    for d in targets["tool_output_dirs"]:
        shutil.rmtree(d, ignore_errors=True)
    for f in targets["telemetry_files"] + targets["applied_drafts"] + targets["discarded_drafts"]:
        try:
            f.unlink()
        except OSError as e:
            print(f"⚠️  unlink 실패: {f.name} — {e}", file=sys.stderr)
    if targets["sessions"]:
        sids = [s for s, _ in targets["sessions"]]
        placeholders = ",".join("?" * len(sids))
        with _connect() as conn:
            conn.execute(f"DELETE FROM observations WHERE session_id IN ({placeholders})", sids)
            conn.execute(f"DELETE FROM sessions WHERE session_id IN ({placeholders})", sids)
            conn.commit()
    print(f"\n✅ prune 완료. (cutoff: {cutoff_date})")
    return 0


# ---------------------------- CHANGELOG.md draft ----------------------------

def _find_pending_drafts() -> list[Path]:
    if not DRAFTS_DIR.exists():
        return []
    return sorted(p for p in DRAFTS_DIR.glob("*.md") if p.is_file())


def _draft_for_session(session_id: str) -> Path | None:
    if not DRAFTS_DIR.exists():
        return None
    matches = sorted(DRAFTS_DIR.glob(f"*_{session_id}.md"))
    return matches[-1] if matches else None


def _extract_draft_row(text: str) -> str | None:
    """draft .md의 ``` block 안에 있는 markdown table row를 추출."""
    m = DRAFT_ROW_RE.search(text)
    if not m:
        return None
    return m.group(1).strip()


def _find_change_history_table(lines: list[str]) -> tuple[int, int] | None:
    """changelog 파일의 "변경 이력" 섹션 표 범위 (header_idx, last_row_idx) 반환.

    "변경 이력" 키워드를 포함한 heading/strong 다음에 등장하는 첫 markdown 표를 찾는다.
    """
    anchor = -1
    for i, line in enumerate(lines):
        if "변경 이력" in line and (line.startswith("#") or line.startswith("**")):
            anchor = i
            break
    if anchor < 0:
        return None
    # find first table after anchor
    i = anchor + 1
    while i < len(lines):
        if (
            ROW_LINE_RE.match(lines[i])
            and i + 1 < len(lines)
            and SEP_LINE_RE.match(lines[i + 1])
        ):
            header_idx = i
            j = i + 2
            last_row_idx = j - 1
            while j < len(lines) and ROW_LINE_RE.match(lines[j]) and not SEP_LINE_RE.match(lines[j]):
                last_row_idx = j
                j += 1
            return header_idx, last_row_idx
        i += 1
    return None


def cmd_claudemd_list() -> int:
    drafts = _find_pending_drafts()
    if not drafts:
        print("📝 미적용 CHANGELOG.md draft 0건.")
        return 0
    print(f"📝 미적용 CHANGELOG.md draft {len(drafts)}건:")
    for p in drafts:
        # filename: {date}_{sid}.md
        stem = p.stem
        date, _, sid = stem.partition("_")
        size = p.stat().st_size
        print(f"  · {date} {sid}  ({size}B)  apply: /cm-claudemd-apply {sid}")
    print()
    print("폐기: /cm-claudemd-discard [<sid>]   (인자 없으면 모두 폐기)")
    return 0


def _sanitize_reason(parts: list[str]) -> str:
    """사용자 입력 사유를 markdown table 안전 형태로 정규화.

    - 다중 인자 → 공백 join
    - 줄바꿈 → 공백 (table row가 1줄을 넘지 않도록)
    - `|` → `\\|` (table 컬럼 구분 깨짐 방지)
    - strip 후 빈 문자열이면 "" 반환 (호출 측이 placeholder 유지로 분기)
    """
    raw = " ".join(parts).strip()
    if not raw:
        return ""
    return raw.replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def cmd_claudemd_apply(session_id: str, reason_parts: list[str]) -> int:
    draft = _draft_for_session(session_id)
    if not draft:
        print(f"⚠️  draft 미발견: session_id={session_id}")
        print(f"   확인: ls {DRAFTS_DIR.relative_to(REPO_ROOT)}")
        return 1
    text = draft.read_text(encoding="utf-8")
    row = _extract_draft_row(text)
    if not row:
        print(f"⚠️  draft에서 표 행을 찾지 못함: {draft.relative_to(REPO_ROOT)}")
        return 1
    if not CHANGELOG_MD.exists():
        print(f"⚠️  CHANGELOG.md 없음: {CHANGELOG_MD.relative_to(REPO_ROOT)}")
        return 1

    reason = _sanitize_reason(reason_parts)
    reason_applied = False
    if reason:
        if DRAFT_REASON_PLACEHOLDER in row:
            row = row.replace(DRAFT_REASON_PLACEHOLDER, reason)
            reason_applied = True
        else:
            print(f"⚠️  draft row에 placeholder가 없어 사유 인자 무시 (사용자 직접 편집 필요)")

    changelog_text = CHANGELOG_MD.read_text(encoding="utf-8")
    lines = changelog_text.splitlines()
    span = _find_change_history_table(lines)
    if not span:
        print("⚠️  CHANGELOG.md에서 '변경 이력' 표를 찾지 못함.")
        return 1
    _, last_row_idx = span
    new_lines = lines[: last_row_idx + 1] + [row] + lines[last_row_idx + 1 :]
    new_text = "\n".join(new_lines)
    if changelog_text.endswith("\n"):
        new_text += "\n"
    CHANGELOG_MD.write_text(new_text, encoding="utf-8")

    DRAFTS_APPLIED.mkdir(parents=True, exist_ok=True)
    dest = DRAFTS_APPLIED / draft.name
    draft.replace(dest)

    print(f"✅ CHANGELOG.md '변경 이력' 표에 행 추가됨.")
    print(f"   삽입 위치: line {last_row_idx + 2}")
    print(f"   row: {row[:120]}{'…' if len(row) > 120 else ''}")
    print(f"   draft 이동: {dest.relative_to(REPO_ROOT)}")
    print()
    if reason_applied:
        print(f"✅ 사유 컬럼이 인자로 치환됐습니다: {reason[:80]}{'…' if len(reason) > 80 else ''}")
    else:
        print("⚠️  사유 컬럼이 placeholder인 채로 추가됐습니다 — CHANGELOG.md를 직접 편집해 사유를 채우거나,")
        print("    다음 apply 때 '/cm-claudemd-apply <sid> <사유 텍스트>' 형식으로 인자를 넘기세요.")
    return 0


def cmd_claudemd_discard(session_id: str | None) -> int:
    DRAFTS_DISCARDED.mkdir(parents=True, exist_ok=True)
    targets: list[Path]
    if session_id:
        d = _draft_for_session(session_id)
        if not d:
            print(f"⚠️  draft 미발견: session_id={session_id}")
            return 1
        targets = [d]
    else:
        targets = _find_pending_drafts()
    if not targets:
        print("폐기할 draft 없음.")
        return 0
    for d in targets:
        dest = DRAFTS_DISCARDED / d.name
        d.replace(dest)
        print(f"🗑️  {d.name} → {dest.relative_to(REPO_ROOT)}")
    return 0


# ---------------------------- main ----------------------------

def main() -> int:
    parser = argparse.ArgumentParser(prog="cm")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    p_sessions = sub.add_parser("sessions"); p_sessions.add_argument("--limit", type=int, default=30)
    p_reset = sub.add_parser("reset"); p_reset.add_argument("--confirm", action="store_true")
    p_prune = sub.add_parser("prune")
    p_prune.add_argument("--older-than", type=int, default=PRUNE_DEFAULT_DAYS,
                         help=f"N일 *이전* 데이터를 prune (default: {PRUNE_DEFAULT_DAYS})")
    p_prune.add_argument("--confirm", action="store_true",
                         help="실제 삭제 (생략 시 dry-run으로 영향 미리보기만)")
    sub.add_parser("claudemd-list")
    p_apply = sub.add_parser("claudemd-apply")
    p_apply.add_argument("session_id")
    p_apply.add_argument("reason", nargs="*", help="optional 사유 텍스트 (생략 시 placeholder 유지)")
    p_discard = sub.add_parser("claudemd-discard"); p_discard.add_argument("session_id", nargs="?", default=None)

    args = parser.parse_args()
    if args.cmd == "status":              return cmd_status()
    if args.cmd == "sessions":            return cmd_sessions(args.limit)
    if args.cmd == "reset":               return cmd_reset(args.confirm)
    if args.cmd == "prune":               return cmd_prune(getattr(args, "older_than"), args.confirm)
    if args.cmd == "claudemd-list":       return cmd_claudemd_list()
    if args.cmd == "claudemd-apply":      return cmd_claudemd_apply(args.session_id, args.reason)
    if args.cmd == "claudemd-discard":    return cmd_claudemd_discard(args.session_id)
    return 2


if __name__ == "__main__":
    sys.exit(main())
