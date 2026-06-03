"""Validate harness baseline schema — required fields + inferred_fields source citation.

LLM-free. Plugin-bundled deterministic check.

Usage:
    py plugins/harness/scripts/validate/schema.py [--json] [--strict]
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except ImportError:
    yaml = None  # type: ignore
    _HAS_YAML = False

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# scripts/validate/schema.py → parents[4]가 repo root. __file__ 기반 통일 (structure.py 정합).
REPO_ROOT = Path(__file__).resolve().parents[4]
BASELINE_DIR = REPO_ROOT / "_workspace" / "_baseline"

PROJECT_PROFILE = BASELINE_DIR / "project_profile.md"
INTENT_PROFILE = BASELINE_DIR / "intent_profile.md"

PROJECT_REQUIRED = ["stack", "architecture", "convention", "maturity", "pain_points"]
# W3 doctrine — Phase 2 사용자 raw 답변 강제 5필드. chain_intent.py:check_required_user_confirmed_fields가 본 list로 prefix 매칭.
INTENT_REQUIRED_USER_CONFIRMED = [
    "constraints.tech_stack",
    "constraints.team.size",
    "constraints.timeline.horizon",
    "architecture.deployment_target",
    "quality.test_rigor",
]
# I2 doctrine — LLM이 합성 시점 plugin version 자동 박제 (사용자 raw 답변 불요). 2026-05-28 audit2 PA8 격상.
INTENT_REQUIRED_LLM_STAMPED = [
    "meta.dharness_version",
]
# 전체 필수 6필드 superset — schema.py existence check + chain_intent.py:check_intent_required_doc_sync 정본.
INTENT_REQUIRED = INTENT_REQUIRED_USER_CONFIRMED + INTENT_REQUIRED_LLM_STAMPED

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def extract_yaml_body(text: str) -> str:
    m = FRONTMATTER_RE.match(text)
    if m:
        return m.group(1)
    code_m = re.search(r"```ya?ml\s*\n(.*?)```", text, re.DOTALL)
    if code_m:
        return code_m.group(1)
    return text


def _has_dotted_field_yaml(yaml_text: str, parts: list[str]) -> bool:
    """PyYAML 위임 경로 — yaml.safe_load 후 nested dict/list walk.

    list 요소는 dotted path 분기점에서 *임의 원소 hit*면 True (inferred_fields 같은
    `- field: X` 구조 등의 array containment 패턴 수용).
    """
    if not _HAS_YAML:
        return False
    try:
        root = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return False
    if root is None:
        return False

    def walk(node: object, path: list[str]) -> bool:
        if not path:
            return node is not None
        head, *rest = path
        if isinstance(node, dict):
            if head in node:
                return walk(node[head], rest)
            return False
        if isinstance(node, list):
            return any(walk(item, [head, *rest]) for item in node)
        return False

    return walk(root, parts)


def _has_dotted_field_manual(yaml_text: str, parts: list[str]) -> bool:
    """Regex/indent 기반 fallback — PyYAML 부재 또는 parse 실패 시."""
    stack: list[tuple[int, str]] = []
    key_re = re.compile(r"([A-Za-z0-9_.-]+)\s*:")
    for raw in yaml_text.splitlines():
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        body = stripped[1:].lstrip() if stripped.startswith("-") else stripped
        m = key_re.match(body)
        if not m:
            continue
        key = m.group(1)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        path = [k for _, k in stack] + [key]
        if path == parts:
            return True
        stack.append((indent, key))
    return False


def has_dotted_field(yaml_text: str, dotted: str) -> bool:
    """dotted path 존재 여부. PyYAML 위임 우선, 실패/부재 시 manual fallback (PA13)."""
    parts = dotted.split(".")
    if _HAS_YAML:
        try:
            if _has_dotted_field_yaml(yaml_text, parts):
                return True
        except Exception:
            pass
    return _has_dotted_field_manual(yaml_text, parts)


def find_inferred_fields_without_source(yaml_text: str) -> list[str]:
    missing: list[str] = []
    in_inferred_block = False
    current_field: str | None = None
    current_indent = 0
    found_source = False

    for raw_line in yaml_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if stripped.startswith("inferred_fields:") or stripped.startswith("- field:"):
            if stripped.startswith("- field:"):
                if current_field and not found_source:
                    missing.append(current_field)
                m = re.search(r"-\s*field:\s*(\S+)", stripped)
                current_field = m.group(1) if m else "?"
                found_source = False
                in_inferred_block = True
                current_indent = indent
            else:
                in_inferred_block = True
                current_indent = indent
            continue

        if in_inferred_block:
            if stripped.startswith("source:"):
                found_source = True
            if indent <= current_indent and stripped and not stripped.startswith("-"):
                if current_field and not found_source:
                    missing.append(current_field)
                in_inferred_block = False
                current_field = None
                found_source = False

    if current_field and not found_source:
        missing.append(current_field)

    return missing


# ── wiki bridge candidate contract (S18 단일 출처) ──
# chain.py:check_wiki_candidate_schema(fixture) + scripts/wiki/bridge.py 양쪽이 본 모듈에 위임.
# 필드/로직 fork 차단 (L11-3·L11-5 coupling fix, 2026-06-03).
WIKI_CANDIDATE_FM_FIELDS = (
    "name", "description", "skill_kind", "candidate_version",
    "gap_source", "static_tier", "llm_judge_tier", "mc_tier", "promoted_to",
)


def validate_candidate_contract(cand_dir: Path) -> list[str]:
    """wiki bridge Emit candidate contract(wiki-bridge.md §1) 결정적 검증 — 단일 출처.

    3파일 존재 + SKILL.md frontmatter 필수 9필드 + skill_kind!=internal-capability +
    candidate_version 정수 + eval-results.json shape + cross-field version 정합.
    """
    errors: list[str] = []
    skill_md = cand_dir / "SKILL.md"
    eval_json = cand_dir / "eval-results.json"
    changelog = cand_dir / "changelog.md"
    for f in (skill_md, eval_json, changelog):
        if not f.is_file():
            errors.append(f"필수 파일 부재 `{f.name}` (wiki-bridge.md §1)")
    if errors:
        return errors

    fm_m = FRONTMATTER_RE.match(skill_md.read_text(encoding="utf-8-sig"))
    fm = fm_m.group(1) if fm_m else ""
    skill_ver: int | None = None
    for field in WIKI_CANDIDATE_FM_FIELDS:
        m = re.search(rf"^\s*{field}\s*:\s*(.+)$", fm, re.MULTILINE)
        if not m:
            errors.append(f"SKILL.md frontmatter 필수 필드 `{field}` 누락 (§1-a)")
            continue
        val = m.group(1).strip().strip("\"'")
        if field == "skill_kind" and val == "internal-capability":
            errors.append("SKILL.md `skill_kind: internal-capability` 금지 (wiki rule 3-a)")
        if field == "candidate_version":
            if not val.isdigit():
                errors.append(f"SKILL.md `candidate_version` 정수 아님 (got `{val}`)")
            else:
                skill_ver = int(val)

    try:
        data = json.loads(eval_json.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"eval-results.json 유효 JSON 아님 ({exc}) (§1-b)")
        return errors
    for key in ("candidate_slug", "candidate_version", "gap_source", "evals", "promotion"):
        if key not in data:
            errors.append(f"eval-results.json 필수 키 `{key}` 누락 (§1-b)")
    evals = data.get("evals")
    if isinstance(evals, dict):
        for tier in ("static", "llm_judge", "monte_carlo"):
            if tier not in evals:
                errors.append(f"eval-results.json `evals.{tier}` 누락")
    elif "evals" in data:
        errors.append("eval-results.json `evals` object 아님")
    json_ver = data.get("candidate_version")
    if not isinstance(json_ver, int):
        errors.append(f"eval-results.json `candidate_version` 정수 아님 (got {json_ver!r})")
    elif skill_ver is not None and json_ver != skill_ver:
        errors.append(f"candidate_version 불일치 — SKILL.md {skill_ver} ≠ eval-results.json {json_ver}")
    return errors


def check_baseline_file(path: Path, required_fields: list[str], label: str) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        errors.append(f"{label}: 파일 미존재 — `{path.relative_to(REPO_ROOT)}`")
        return errors

    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as e:
        errors.append(f"{label}: read failed — {e}")
        return errors

    yaml_body = extract_yaml_body(text)

    for field in required_fields:
        if not has_dotted_field(yaml_body, field):
            errors.append(f"{label}: 필수 필드 누락 — `{field}`")

    missing_source = find_inferred_fields_without_source(yaml_body)
    for field in missing_source:
        errors.append(f"{label}: inferred_fields `{field}` source 인용 누락 (P6-4 doctrine 위반)")

    return errors


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    strict = "--strict" in argv

    if not BASELINE_DIR.exists():
        msg = "_workspace/_baseline/ 미존재 — Phase 1·2 미실행"
        if as_json:
            print(json.dumps({"status": "precondition_fail", "error": msg}, ensure_ascii=False))
        else:
            print(f"❌ {msg}")
        return 2

    errors: list[str] = []
    errors.extend(check_baseline_file(PROJECT_PROFILE, PROJECT_REQUIRED, "project_profile.md"))
    errors.extend(check_baseline_file(INTENT_PROFILE, INTENT_REQUIRED, "intent_profile.md"))

    status = "PASS" if not errors else "FAIL"
    report = {
        "section": "schema",
        "status": status,
        "project_required_count": len(PROJECT_REQUIRED),
        "intent_required_count": len(INTENT_REQUIRED),
        "errors": errors,
    }

    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        icon = "✅" if status == "PASS" else "❌"
        print(f"{icon} §2 schema: {status} ({len(PROJECT_REQUIRED)}+{len(INTENT_REQUIRED)} required fields, {len(errors)} errors)")
        for e in errors:
            print(f"  - {e}")

    return 1 if (strict and errors) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
