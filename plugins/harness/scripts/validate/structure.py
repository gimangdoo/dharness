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

# scripts/validate/structure.py → parents[4]가 repo root (plugins/harness/scripts/validate/ 위).
# cwd 의존 시 derived install user가 sub-dir에서 호출하면 silent precondition_fail —
# __file__ 기반으로 통일 (chain.py / _schema.py 동일 패턴).
REPO_ROOT = Path(__file__).resolve().parents[4]
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
_CODE_FENCE_RE = re.compile(r"```.*?(?:\n|$).*?(?:```|\Z)", re.DOTALL)


def _strip_code_fences(text: str) -> str:
    """fenced code block을 제거 — section 매칭이 코드 예시 안의 가짜 heading을 잡지 않도록 (PV6)."""
    return _CODE_FENCE_RE.sub("", text)


try:
    import yaml as _yaml  # PyYAML
except ImportError:
    _yaml = None


def parse_frontmatter(text: str) -> tuple[dict | None, str | None]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, "frontmatter 미존재"
    body = m.group(1)
    if _yaml is not None:
        try:
            data = _yaml.safe_load(body)
        except _yaml.YAMLError as e:
            return None, f"frontmatter YAML 파싱 실패 — {e}"
        if not isinstance(data, dict):
            return None, "frontmatter 최상위가 mapping이 아님"
        # legacy 호환: 모든 값 stringify (이전 단순 split이 string만 반환)
        return {k: (v if isinstance(v, str) else str(v) if v is not None else "") for k, v in data.items()}, None
    # PyYAML 미설치 fallback — PV7 패턴 확장 (PA14): block scalar `|`/`>` 다중 라인 누적 +
    # 다음 top-level key 또는 dedent 시 종료. flow scalar는 기존 단순 split 유지.
    fields: dict = {}
    lines = body.splitlines()
    i = 0
    block_re = re.compile(r"^([A-Za-z0-9_.-]+)\s*:\s*([|>])[-+]?\s*$")
    flow_re = re.compile(r"^([A-Za-z0-9_.-]+)\s*:(.*)$")
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        bm = block_re.match(line)
        if bm and indent == 0:
            key, indicator = bm.group(1), bm.group(2)
            i += 1
            buf: list[str] = []
            base_indent: int | None = None
            while i < len(lines):
                sub = lines[i]
                sub_stripped = sub.lstrip()
                sub_indent = len(sub) - len(sub_stripped)
                if not sub_stripped:
                    buf.append("")
                    i += 1
                    continue
                if sub_indent == 0:
                    break
                if base_indent is None:
                    base_indent = sub_indent
                if sub_indent < base_indent:
                    break
                buf.append(sub[base_indent:])
                i += 1
            joined = ("\n".join(buf) if indicator == "|" else " ".join(s.strip() for s in buf if s.strip()))
            fields[key] = joined
            continue
        fm_line = flow_re.match(line) if indent == 0 else None
        if fm_line:
            key, val = fm_line.group(1), fm_line.group(2)
            fields[key] = val.strip().strip('"').strip("'")
        i += 1
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
    scanned = _strip_code_fences(body)
    for section_re in AGENT_REQUIRED_SECTIONS:
        if not re.search(section_re, scanned, re.IGNORECASE):
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
    if not body.strip():
        errors.append(
            f"{path.relative_to(SKILLS_DIR)}: SKILL.md 본문 부재 — frontmatter만 존재 (빈 스킬, dangling 참조 유발)"
        )
        return errors
    scanned = _strip_code_fences(body)
    for section_re in SKILL_REQUIRED_SECTIONS:
        if not re.search(section_re, scanned, re.IGNORECASE):
            errors.append(f"{path.relative_to(SKILLS_DIR)}: 필수 섹션 누락 (pattern: `{section_re}`)")

    return errors


def check_skills_dir() -> tuple[int, list[str]]:
    """skill 디렉토리 순회 — SKILL.md 미존재(빈 디렉토리) 검출 + 파일별 본문 검증.

    `SKILLS_DIR.glob("*/SKILL.md")`는 SKILL.md 없는 디렉토리를 통째로 누락한다.
    빈 스킬 디렉토리는 오케스트레이터 스킬 참조의 dangling 원인이므로 디렉토리 단위로 순회한다.
    """
    errors: list[str] = []
    count = 0
    if not SKILLS_DIR.exists():
        return count, errors
    for skill_dir in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        # host-agnostic: 케이스 민감 FS에서도 변종 검출하려면 .exists() 대신 실제 파일명 비교
        skill_files = [
            p for p in skill_dir.iterdir() if p.is_file() and p.name.lower() == "skill.md"
        ]
        if not skill_files:
            errors.append(
                f"{skill_dir.name}/: SKILL.md 미존재 — 빈 스킬 디렉토리 (dangling 스킬 참조 유발)"
            )
            continue
        actual = next((p for p in skill_files if p.name == "SKILL.md"), skill_files[0])
        if actual.name != "SKILL.md":
            errors.append(
                f"{skill_dir.name}/{actual.name}: 파일명 대소문자 위반 — `SKILL.md` (대문자) 필수"
            )
        count += 1
        errors.extend(check_skill_file(actual))
    return count, errors


def find_orchestrator() -> Path | None:
    if not SKILLS_DIR.exists():
        return None
    # FS iteration 비결정 — sorted() 박제 (chain.py find_orchestrator 정합).
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
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

    skills_count, skill_errors = check_skills_dir()
    errors.extend(skill_errors)

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
