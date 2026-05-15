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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_ROOT = Path.cwd()
BASELINE_DIR = REPO_ROOT / "_workspace" / "_baseline"

PROJECT_PROFILE = BASELINE_DIR / "project_profile.md"
INTENT_PROFILE = BASELINE_DIR / "intent_profile.md"

PROJECT_REQUIRED = ["stack", "architecture", "convention", "maturity", "pain_points"]
INTENT_REQUIRED = [
    "constraints.tech_stack",
    "constraints.team.size",
    "constraints.timeline.horizon",
    "architecture.deployment_target",
    "quality.test_rigor",
]

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def extract_yaml_body(text: str) -> str:
    m = FRONTMATTER_RE.match(text)
    if m:
        return m.group(1)
    code_m = re.search(r"```ya?ml\s*\n(.*?)```", text, re.DOTALL)
    if code_m:
        return code_m.group(1)
    return text


def has_dotted_field(yaml_text: str, dotted: str) -> bool:
    parts = dotted.split(".")
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
