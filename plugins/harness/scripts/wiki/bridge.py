"""wiki bridge 실행 헬퍼 — M1 Emit / M4 Feedback 기계적 I/O (P5, self-host 전용).

산문 지시(SKILL.md 7-7 Emit / 5-0 Feedback)를 재사용 코드로 박제한다. 사용자 gate는
LLM 레이어에 유지 — 본 모듈은 gate 통과 후 호출되는 *기계적 I/O*(write/glob/dedup/
telemetry)만 수행한다. 콘텐츠 저작(SKILL 본문 등)은 호출자(LLM)가 한다.

단일 출처 doctrine: references/wiki-bridge.md (§1 Emit contract·§2 Feedback·§4 안전).
presence-gated: candidates_dir 부재 시 skip telemetry 1줄 + no-op (wiki repo 미오염).
self-host 전용 — derived 런타임 주입 0 (RUNTIME-FEATURES-PLAN P5, 2026-06-03 결정).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# scripts/wiki/bridge.py → parents[4]가 repo root (chain.py REPO_ROOT 정합).
REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_TELEMETRY_DIR = REPO_ROOT / "_workspace" / "_telemetry"

# 공유 candidate contract 검증 단일 출처 — validate/ dir를 path에 올려 dir-on-path import
# (트리 관행 정합·포터블). 절대 `plugins.` 패키지 import 회피 → 외부 install 위치서도 무손상 (L11-2 fix).
_VALIDATE_DIR = REPO_ROOT / "plugins" / "harness" / "scripts" / "validate"
if str(_VALIDATE_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATE_DIR))
from schema import validate_candidate_contract  # noqa: E402

# dedup 임계 — wiki rule 2-a(75% 중복 Emit 금지) *상속*. 정본=<wiki>/.../WIKI-SCHEMA §11 rule 2.
# dharness 독립 숫자 fork 아님 — 미러. wiki 측 변경 시 본 상수 추종 (wiki-bridge.md §4).
_DEDUP_THRESHOLD = 0.75


# ─────────────────────────────────────────────────────────────────────────────
# telemetry
# ─────────────────────────────────────────────────────────────────────────────
def _emit_telemetry(event: dict, telemetry_dir: Path | None = None) -> None:
    """append-only JSONL 1줄 (runtime-telemetry.md §1 형식). 절대 삭제·수정 금지.

    write 실패는 삼킨다(stderr만) — telemetry는 비-load-bearing 관측 side effect라,
    실패가 candidate write 같은 load-bearing 결과를 오염시키면 안 된다 (L08-005 fix).
    """
    tdir = telemetry_dir or _DEFAULT_TELEMETRY_DIR
    now = datetime.now(timezone.utc)
    row = {"ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"), **event}
    try:
        tdir.mkdir(parents=True, exist_ok=True)
        fpath = tdir / f"{now.strftime('%Y-%m-%d')}.jsonl"
        with fpath.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"[wiki-bridge] telemetry write 실패 (관측성만 손실): {exc}", file=sys.stderr)


def _emit_skip(milestone: str, reason: str, session_id: str,
               telemetry_dir: Path | None = None, **extra) -> None:
    """wiki_bridge_skipped — milestone(emit/pull) + reason(target-absent/not-reusable/dedup-hit)."""
    _emit_telemetry(
        {"type": "wiki_bridge_skipped", "session_id": session_id,
         "milestone": milestone, "reason": reason, **extra},
        telemetry_dir,
    )


def note_skip(milestone: str, reason: str, session_id: str = "self-host",
              telemetry_dir: Path | None = None, **extra) -> None:
    """LLM 레이어 공개 skip 로깅 — emit_candidate를 *호출하지 않는* 분기(특히 합성 skill을
    재사용 가치 없다고 판단해 Emit 안 하는 reason=not-reusable)도 추적 신호를 남긴다.

    wiki-bridge.md §0 observability 보장("wiki 미설정 vs 설정됐으나 skip" 구분) 충족 (L08-002 fix).
    SKILL 7-7이 비-Emit 결정 시 본 fn 호출을 지시한다.
    """
    _emit_skip(milestone, reason, session_id, telemetry_dir, **extra)


# ─────────────────────────────────────────────────────────────────────────────
# dedup (advisory — hard-block 아님, wiki-bridge.md §4 inflation guard)
# ─────────────────────────────────────────────────────────────────────────────
def _norm_triggers(triggers) -> set[str]:
    return {t.strip().lower() for t in (triggers or []) if t and t.strip()}


def _dedup_check(triggers, existing_triggers, threshold: float = _DEDUP_THRESHOLD) -> dict:
    """트리거 구 집합 Jaccard overlap. 반환 {overlap, conflict} — bool 아님(advisory).

    existing_triggers = {slug: [trigger,...]}. 최대 overlap slug를 conflict로 보고.
    """
    cur = _norm_triggers(triggers)
    if not cur or not existing_triggers:
        return {"overlap": 0.0, "conflict": None}
    best_overlap, best_slug = 0.0, None
    for slug, ex in existing_triggers.items():
        other = _norm_triggers(ex)
        if not other:
            continue
        inter = len(cur & other)
        union = len(cur | other)
        jac = inter / union if union else 0.0
        if jac > best_overlap:
            best_overlap, best_slug = jac, slug
    return {"overlap": round(best_overlap, 4),
            "conflict": best_slug if best_overlap >= threshold else None}


# ─────────────────────────────────────────────────────────────────────────────
# candidate 검증 (write 후 자가검증 — 실패 시 abort, wiki repo 미오염)
# ─────────────────────────────────────────────────────────────────────────────
def _validate_candidate_dir(cand_dir: Path) -> list[str]:
    """emit한 candidate가 M5 contract(wiki-bridge.md §1)를 만족하는지 — schema 단일 출처 위임.

    `schema.validate_candidate_contract`를 chain.py:check_wiki_candidate_schema와 공유 (fork 차단).
    """
    return validate_candidate_contract(cand_dir)


# ─────────────────────────────────────────────────────────────────────────────
# changelog 렌더 (append-only 표, wiki-bridge.md §1-c)
# ─────────────────────────────────────────────────────────────────────────────
def _render_changelog(slug: str, version: int, rows) -> str:
    head = (
        f"# `{slug}-v{version}` — Candidate changelog\n\n"
        "> Append-only. 1행 per evolution event. "
        "promote 시 본 history는 `pages/tools/<name>/evolution.md` Version timeline 절로 hoist.\n\n"
        "| 일자 | event | 본문 |\n|---|---|---|\n"
    )
    body = "".join(f"| {d} | {e} | {b} |\n" for d, e, b in rows)
    return head + body


def _append_changelog_rows(changelog: Path, rows) -> None:
    text = changelog.read_text(encoding="utf-8-sig").rstrip("\n")
    extra = "".join(f"| {d} | {e} | {b} |\n" for d, e, b in rows)
    changelog.write_text(text + "\n" + extra, encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# M1 Emit
# ─────────────────────────────────────────────────────────────────────────────
def emit_candidate(candidates_dir: Path, slug: str, version: int,
                   skill_md: str, eval_results: dict, changelog_rows,
                   *, triggers=None, existing_triggers=None, session_id: str = "self-host",
                   threshold: float = _DEDUP_THRESHOLD,
                   telemetry_dir: Path | None = None) -> dict:
    """reusable skill을 wiki `candidates/<slug>-v<N>/`로 Emit (gate 통과 후 호출).

    반환 status:
      skipped     — presence-gate(target-absent) 부재, no-op
      soft_block  — dedup overlap≥threshold (advisory — 호출자가 사용자에 재확인)
      invalid     — write 후 자가검증 FAIL → 롤백(생성분), wiki 미오염
      exists      — 동일 slug-vN 존재 → changelog append만 (멱등)
      emitted     — 신규 박제 성공
    """
    candidates_dir = Path(candidates_dir)
    # 1. presence-gate
    if not candidates_dir.is_dir():
        _emit_skip("emit", "target-absent", session_id, telemetry_dir, slug=slug)
        return {"status": "skipped", "reason": "target-absent"}

    # 2. dedup (advisory soft-block — hard-block 아님)
    dd = _dedup_check(triggers, existing_triggers, threshold)
    if dd["conflict"]:
        _emit_skip("emit", "dedup-hit", session_id, telemetry_dir,
                   slug=slug, overlap=dd["overlap"], conflict=dd["conflict"])
        return {"status": "soft_block", "dedup": dd}

    cand_dir = candidates_dir / f"{slug}-v{version}"

    # 3. 멱등 — 이미 존재하면 changelog append만, SKILL/eval 미덮어씀
    if cand_dir.is_dir():
        if changelog_rows:
            _append_changelog_rows(cand_dir / "changelog.md", changelog_rows)
        _emit_telemetry({"type": "wiki_bridge_emit", "session_id": session_id,
                         "slug": slug, "outcome": "partial", "note": "exists-appended"},
                        telemetry_dir)
        return {"status": "exists", "path": str(cand_dir)}

    # 4. write
    cand_dir.mkdir(parents=True)
    (cand_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
    (cand_dir / "eval-results.json").write_text(
        json.dumps(eval_results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (cand_dir / "changelog.md").write_text(
        _render_changelog(slug, version, changelog_rows), encoding="utf-8")

    # 5. 자가검증 — FAIL 시 telemetry 먼저(롤백이 실패해도 추적 보장) → 롤백 guard (L08-003/004 fix)
    errors = _validate_candidate_dir(cand_dir)
    if errors:
        _emit_telemetry({"type": "wiki_bridge_emit", "session_id": session_id,
                         "slug": slug, "outcome": "failure",
                         "n_errors": len(errors), "errors": errors[:6]}, telemetry_dir)
        residual = None
        try:
            for f in cand_dir.iterdir():
                f.unlink()
            cand_dir.rmdir()
        except OSError as exc:
            residual = str(cand_dir)
            _emit_skip("emit", "rollback-failed", session_id, telemetry_dir,
                       slug=slug, residual=residual, error=str(exc)[:100])
        return {"status": "invalid", "errors": errors, "residual": residual}

    _emit_telemetry({"type": "wiki_bridge_emit", "session_id": session_id,
                     "slug": slug, "outcome": "success"}, telemetry_dir)
    return {"status": "emitted", "path": str(cand_dir)}


# ─────────────────────────────────────────────────────────────────────────────
# M4 Feedback
# ─────────────────────────────────────────────────────────────────────────────
def pull_promoted(candidates_dir: Path, *, session_id: str = "self-host",
                  telemetry_dir: Path | None = None) -> list[dict]:
    """promoted candidate 조회 — 3 tier 전부 PASS + promotion.verdict 박제 시만 (wiki-bridge.md §2).

    반환 [{slug, version, promoted_to, verdict}, ...]. presence-gate 부재 시 [] + skip telemetry.
    """
    candidates_dir = Path(candidates_dir)
    if not candidates_dir.is_dir():
        _emit_skip("pull", "target-absent", session_id, telemetry_dir)
        return []

    promoted: list[dict] = []
    for eval_json in sorted(candidates_dir.glob("*/eval-results.json")):
        try:
            data = json.loads(eval_json.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        evals = data.get("evals") or {}
        tiers_pass = all(
            isinstance(evals.get(t), dict) and evals[t].get("status") == "PASS"
            for t in ("static", "llm_judge", "monte_carlo")
        )
        promo = data.get("promotion") or {}
        if tiers_pass and promo.get("verdict"):
            promoted.append({
                "slug": data.get("candidate_slug"),
                "version": data.get("candidate_version"),
                "promoted_to": promo.get("promoted_to"),
                "verdict": promo.get("verdict"),
            })

    _emit_telemetry({"type": "wiki_bridge_pull", "session_id": session_id,
                     "n_promoted": len(promoted)}, telemetry_dir)
    return promoted
