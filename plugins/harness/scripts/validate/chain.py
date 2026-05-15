"""Validate harness cross-reference chain — dangling agent/skill/reference detection.

LLM-free. Plugin-bundled deterministic check.

Usage:
    py plugins/harness/scripts/validate/chain.py [--json] [--strict]
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
SETTINGS_FILES = [
    REPO_ROOT / ".claude" / "settings.json",
    REPO_ROOT / ".claude" / "settings.local.json",
]

AGENT_NAME_PATTERN = re.compile(r"^\s*name\s*:\s*[\"']?([\w-]+)[\"']?\s*$", re.MULTILINE)
SKILL_DIR_PATTERN = re.compile(r"\.claude/skills/([\w-]+)")
AGENT_REF_PATTERN = re.compile(r"\.claude/agents/([\w-]+)\.md")
TOOLS_LINE_PATTERN = re.compile(r"^\s*tools\s*:\s*(.+)$", re.MULTILINE)
REFERENCE_LINK_PATTERN = re.compile(r"references/([\w/-]+\.md)")
WRITES_LINE_PATTERN = re.compile(r"^\s*writes\s*:\s*(.+)$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def collect_agents() -> set[str]:
    names: set[str] = set()
    if not AGENTS_DIR.exists():
        return names
    for path in AGENTS_DIR.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        m = AGENT_NAME_PATTERN.search(text)
        if m:
            names.add(m.group(1))
        names.add(path.stem)
    return names


def collect_skills() -> set[str]:
    if not SKILLS_DIR.exists():
        return set()
    return {p.name for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists()}


def collect_settings_permissions() -> set[str]:
    perms: set[str] = set()
    for path in SETTINGS_FILES:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        permissions = data.get("permissions", {})
        for bucket in ("allow", "ask", "deny"):
            for entry in permissions.get(bucket, []):
                if isinstance(entry, str):
                    perms.add(entry)
    return perms


def find_dangling_in_orchestrator(orch_path: Path, valid_agents: set[str], valid_skills: set[str]) -> list[str]:
    errors: list[str] = []
    try:
        text = orch_path.read_text(encoding="utf-8-sig")
    except OSError as e:
        return [f"{orch_path.name}: read failed — {e}"]

    for match in AGENT_REF_PATTERN.finditer(text):
        agent_name = match.group(1)
        if agent_name not in valid_agents:
            errors.append(f"{orch_path.relative_to(REPO_ROOT)}: dangling agent reference `{agent_name}`")

    for match in SKILL_DIR_PATTERN.finditer(text):
        skill_name = match.group(1)
        if skill_name not in valid_skills and skill_name != orch_path.parent.name:
            errors.append(f"{orch_path.relative_to(REPO_ROOT)}: dangling skill reference `{skill_name}`")

    return errors


def check_agent_tools_vs_settings(valid_perms: set[str]) -> list[str]:
    errors: list[str] = []
    if not AGENTS_DIR.exists():
        return errors

    for path in AGENTS_DIR.glob("*.md"):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        m = TOOLS_LINE_PATTERN.search(text)
        if not m:
            continue
        tools_raw = m.group(1).strip()
        tools = [t.strip().strip("'\"") for t in re.split(r"[,\[\]]", tools_raw) if t.strip()]
        for tool in tools:
            if tool.lower() in {"read", "write", "edit", "glob", "grep", "bash", "powershell"}:
                continue
            if tool.lower().startswith("websearch") or tool.lower().startswith("webfetch"):
                continue
            if not valid_perms:
                continue
            if not any(tool in perm or perm in tool for perm in valid_perms):
                errors.append(f"{path.name}: `tools:` entry `{tool}` — settings*.json permissions 미정합 (warning)")
    return errors


def check_agent_name_uniqueness() -> list[str]:
    """agents/*.md frontmatter `name:` slug + file stem 전역 유일성 검증."""
    errors: list[str] = []
    if not AGENTS_DIR.exists():
        return errors
    by_name: dict[str, list[str]] = {}
    by_stem: dict[str, list[str]] = {}
    for path in AGENTS_DIR.glob("*.md"):
        rel = str(path.relative_to(REPO_ROOT))
        by_stem.setdefault(path.stem, []).append(rel)
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        m = AGENT_NAME_PATTERN.search(text)
        if m:
            by_name.setdefault(m.group(1), []).append(rel)
    for name, paths in by_name.items():
        if len(paths) > 1:
            errors.append(f"agent `name: {name}` 중복 — {', '.join(paths)}")
    for stem, paths in by_stem.items():
        if len(paths) > 1:
            errors.append(f"agent 파일명 `{stem}.md` 중복 — {', '.join(paths)}")
    return errors


def check_agent_write_path_overlap() -> list[str]:
    """agents/*.md frontmatter `writes:` 경로 충돌 검출 (A7 doctrine, 2026-05-15).

    frontmatter 내부에 `writes: [path1, path2]` 필드 박제 시 각 path를 owner agent에 매핑.
    두 agent가 동일 path 박제 시 FAIL. exact string match 기준 — glob 교집합은 향후 확장.
    """
    errors: list[str] = []
    if not AGENTS_DIR.exists():
        return errors
    by_path: dict[str, list[str]] = {}
    for path in AGENTS_DIR.glob("*.md"):
        rel = str(path.relative_to(REPO_ROOT))
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        fm = FRONTMATTER_RE.match(text)
        if not fm:
            continue
        m = WRITES_LINE_PATTERN.search(fm.group(1))
        if not m:
            continue
        raw = m.group(1).strip()
        paths = [p.strip().strip("'\"") for p in re.split(r"[,\[\]]", raw) if p.strip()]
        for p in paths:
            by_path.setdefault(p, []).append(rel)
    for p, owners in by_path.items():
        if len(owners) > 1:
            errors.append(
                f"write path `{p}` per-agent exclusivity 위반 — {', '.join(owners)} (A7 doctrine)"
            )
    return errors


def check_skill_name_uniqueness() -> list[str]:
    """skills/*/SKILL.md frontmatter `name:` 전역 유일성 + 디렉토리명 정합 검증."""
    errors: list[str] = []
    if not SKILLS_DIR.exists():
        return errors
    by_name: dict[str, list[str]] = {}
    for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
        rel = str(skill_md.relative_to(REPO_ROOT))
        dir_name = skill_md.parent.name
        try:
            text = skill_md.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        m = AGENT_NAME_PATTERN.search(text)
        if not m:
            continue
        name = m.group(1)
        by_name.setdefault(name, []).append(rel)
        if name != dir_name:
            errors.append(
                f"{rel}: frontmatter `name: {name}` ≠ 디렉토리명 `{dir_name}` — Claude Code skill resolver mismatch"
            )
    for name, paths in by_name.items():
        if len(paths) > 1:
            errors.append(f"skill `name: {name}` 중복 — {', '.join(paths)}")
    return errors


def check_reference_links() -> list[str]:
    errors: list[str] = []
    if not SKILLS_DIR.exists():
        return errors

    for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
        try:
            text = skill_md.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        skill_dir = skill_md.parent
        for match in REFERENCE_LINK_PATTERN.finditer(text):
            rel_path = match.group(1)
            target = skill_dir / "references" / rel_path
            if not target.exists():
                errors.append(f"{skill_md.relative_to(REPO_ROOT)}: dangling reference `references/{rel_path}`")
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
    claude_md = REPO_ROOT / "CLAUDE.md"
    if claude_md.exists():
        text = claude_md.read_text(encoding="utf-8-sig")
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
        msg = ".claude/ 미존재 — harness 미생성"
        if as_json:
            print(json.dumps({"status": "precondition_fail", "error": msg}, ensure_ascii=False))
        else:
            print(f"❌ {msg}")
        return 2

    valid_agents = collect_agents()
    valid_skills = collect_skills()
    valid_perms = collect_settings_permissions()

    errors: list[str] = []
    orch = find_orchestrator()
    if orch:
        errors.extend(find_dangling_in_orchestrator(orch, valid_agents, valid_skills))

    errors.extend(check_agent_tools_vs_settings(valid_perms))
    errors.extend(check_agent_name_uniqueness())
    errors.extend(check_agent_write_path_overlap())
    errors.extend(check_skill_name_uniqueness())
    errors.extend(check_reference_links())

    status = "PASS" if not errors else "FAIL"
    report = {
        "section": "chain",
        "status": status,
        "agents_count": len(valid_agents),
        "skills_count": len(valid_skills),
        "orchestrator": str(orch.relative_to(REPO_ROOT)) if orch else None,
        "errors": errors,
    }

    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        icon = "✅" if status == "PASS" else "❌"
        print(f"{icon} §3 chain: {status} (dangling 0 check across {len(valid_agents)} agents / {len(valid_skills)} skills, {len(errors)} errors)")
        for e in errors:
            print(f"  - {e}")

    return 1 if (strict and errors) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
