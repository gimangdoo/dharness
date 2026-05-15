"""Validate harness structure — frontmatter + required sections + YAML parsing.

LLM-free. Plugin-bundled deterministic check.

Usage:
    py plugins/harness/scripts/validate/structure.py [--json]

Exit codes:
    0 — all checks passed
    1 — at least one check failed (with --strict)
    2 — preconditions missing (.claude/ not found)
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
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"

AGENT_REQUIRED_SECTIONS = [
    r"핵심\s*역할|core\s*role",
    r"작업\s*원칙|work(ing)?\s*princip(le|al)",
    r"입력.*출력|input.*output",
    r"에러\s*핸들링|error\s*handling",
    r"협업|collaboration",
    r"팀\s*통신|team\s*communication",
]

SKILL_REQUIRED_SECTIONS = [
    r"워크플로우|workflow",
]

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict | None, str | None]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, "frontmatter 미존재"
    body = m.group(1)
    fields: dict = {}
    for line in body.splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        fields[k.strip()] = v.strip().strip('"').strip("'")
    return fields, None


def check_agent_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as e:
        return [f"{path}: read failed — {e}"]

    fm, err = parse_frontmatter(text)
    if err:
        errors.append(f"{path.name}: {err}")
        return errors

    if not fm.get("name"):
        errors.append(f"{path.name}: frontmatter `name:` 누락")
    if not fm.get("description"):
        errors.append(f"{path.name}: frontmatter `description:` 누락")

    m = FRONTMATTER_RE.match(text)
    body = text[m.end():] if m else text
    for section_re in AGENT_REQUIRED_SECTIONS:
        if not re.search(section_re, body, re.IGNORECASE):
            errors.append(f"{path.name}: 필수 섹션 누락 (pattern: `{section_re}`)")

    return errors


def check_skill_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as e:
        return [f"{path}: read failed — {e}"]

    fm, err = parse_frontmatter(text)
    if err:
        errors.append(f"{path.relative_to(SKILLS_DIR)}: {err}")
        return errors

    if not fm.get("name"):
        errors.append(f"{path.relative_to(SKILLS_DIR)}: frontmatter `name:` 누락")
    if not fm.get("description"):
        errors.append(f"{path.relative_to(SKILLS_DIR)}: frontmatter `description:` 누락")

    m = FRONTMATTER_RE.match(text)
    body = text[m.end():] if m else text
    for section_re in SKILL_REQUIRED_SECTIONS:
        if not re.search(section_re, body, re.IGNORECASE):
            errors.append(f"{path.relative_to(SKILLS_DIR)}: 필수 섹션 누락 (pattern: `{section_re}`)")

    return errors


def find_orchestrator() -> Path | None:
    if not SKILLS_DIR.exists():
        return None
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        if "orchestrator" in skill_dir.name.lower():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                return skill_md
    if CLAUDE_MD.exists():
        text = CLAUDE_MD.read_text(encoding="utf-8-sig")
        m = re.search(r"`\.claude/skills/([^/]+)/SKILL\.md`", text)
        if m:
            candidate = SKILLS_DIR / m.group(1) / "SKILL.md"
            if candidate.exists():
                return candidate
    return None


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    strict = "--strict" in argv

    if not (REPO_ROOT / ".claude").exists():
        msg = ".claude/ 디렉토리 미존재 — harness 미생성"
        if as_json:
            print(json.dumps({"status": "precondition_fail", "error": msg}, ensure_ascii=False))
        else:
            print(f"❌ {msg}")
        return 2

    errors: list[str] = []
    agents_count = 0
    skills_count = 0

    if AGENTS_DIR.exists():
        for agent_path in AGENTS_DIR.glob("*.md"):
            agents_count += 1
            errors.extend(check_agent_file(agent_path))

    if SKILLS_DIR.exists():
        for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
            skills_count += 1
            errors.extend(check_skill_file(skill_md))

    orch = find_orchestrator()
    if orch is None and skills_count > 0:
        errors.append("오케스트레이터 스킬 식별 실패 (CLAUDE.md 포인터 또는 `.claude/skills/*-orchestrator/` 미존재)")

    status = "PASS" if not errors else "FAIL"
    report = {
        "section": "structure",
        "status": status,
        "agents_count": agents_count,
        "skills_count": skills_count,
        "orchestrator": str(orch.relative_to(REPO_ROOT)) if orch else None,
        "errors": errors,
    }

    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        icon = "✅" if status == "PASS" else "❌"
        print(f"{icon} §1 structure: {status} ({agents_count} agents / {skills_count} skills, {len(errors)} errors)")
        for e in errors:
            print(f"  - {e}")

    return 1 if (strict and errors) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
