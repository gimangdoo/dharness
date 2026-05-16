"""Validate harness cross-reference chain — dangling agent/skill/reference detection.

LLM-free. Plugin-bundled deterministic check.

Usage:
    py plugins/harness/scripts/validate/chain.py [--json] [--strict]
"""

from __future__ import annotations

import fnmatch
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
DESCRIPTION_LINE_PATTERN = re.compile(r"^\s*description\s*:\s*(.+)$", re.MULTILINE)
MCP_TOOL_PATTERN = re.compile(r"mcp__([\w-]+)__[\w-]+")
MCP_SERVER_LINE_PATTERN = re.compile(r"^\s*-\s+([\w-]+)\s*:\s*$", re.MULTILINE)

# Q11 — trigger-keyword-catalog.md 단일 출처. signal_id → [keywords]
# 본 catalog는 plugin 합성 결과를 검증 — derived `.claude/agents|skills/*.md`의 description이
# *최소 1 signal*을 hit해야 trigger 명확성 확보. catalog 갱신 시 본 dict도 동기.
_TRIGGER_SIGNAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "S1": ("분석", "검토", "리서치", "요약", "조회", "검색", "탐색", "탐사", "진단", "감사", "점검",
           "analyze", "review", "research", "summarize", "query", "search", "explore", "audit", "inspect", "investigate"),
    "S2": ("생성", "작성", "편집", "수정", "커밋", "마이그레이션", "배포", "적용", "등록", "갱신",
           "create", "write", "edit", "modify", "commit", "migrate", "deploy", "apply", "register", "update"),
    "S3": ("웹", "외부 API", "스크래핑", "크롤링", "fetch", "페이지", "URL",
           "web", "external API", "scrape", "crawl", "search engine", "HTTP"),
    "S4": ("DB", "데이터베이스", "쿼리", "스키마", "테이블", "인덱스", "JOIN",
           "database", "schema", "migration", "table", "index", "SQL"),
    "S5": ("PR", "issue", "리뷰", "CI", "CD", "릴리즈", "브랜치", "머지", "워크플로우",
           "release", "branch", "merge", "pipeline", "workflow"),
    "S6": ("단계별", "추론", "사고 과정", "장기 메모리", "시간", "타임존", "KG", "지식 그래프",
           "step-by-step", "reasoning", "chain-of-thought", "long-term memory", "timezone", "knowledge graph"),
    "S7": ("모델", "학습", "평가", "하이퍼파라미터", "실험 추적", "inference", "feature", "dataset", "라벨", "분류", "회귀", "추천",
           "model", "training", "evaluation", "hyperparameter", "experiment tracking", "classification", "regression", "recommendation"),
    "S8": ("Kubernetes", "k8s", "Terraform", "SRE", "oncall", "롤백", "helm", "IaC", "observability",
           "infrastructure", "monitoring", "rollback"),
    "S9": ("iOS", "Android", "Swift", "Kotlin", "Flutter", "React Native", "Xcode", "Gradle", "emulator",
           "IPA", "APK", "모바일", "mobile"),
    "S10": ("ETL", "ELT", "data pipeline", "Airflow", "dbt", "Spark", "data warehouse", "data lake", "ingestion", "lineage", "DAG",
            "스키마 변환"),
}


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


def _has_glob(s: str) -> bool:
    return any(ch in s for ch in "*?[")


def _single_star_overlap(a: str, b: str) -> bool:
    """단일 `*` glob 두 개의 교집합 비공집합 여부 결정적 판정.

    A = prefix_A + '*' + suffix_A, B = prefix_B + '*' + suffix_B 일 때
    겹치는 문자열 존재 조건:
      (1) 한 prefix가 다른 prefix의 시작
      (2) 한 suffix가 다른 suffix의 끝
      (3) 결합 prefix + 결합 suffix가 서로 겹치지 않음 (길이 sufficient)
    """
    if a.count("*") != 1 or b.count("*") != 1:
        return False
    if "?" in a or "?" in b or "[" in a or "[" in b:
        return False
    pa, sa = a.split("*", 1)
    pb, sb = b.split("*", 1)
    if not (pa.startswith(pb) or pb.startswith(pa)):
        return False
    if not (sa.endswith(sb) or sb.endswith(sa)):
        return False
    # 결합 prefix·suffix 길이 합이 한 패턴 길이 -1 (자리 '*') 이하여야 매칭 가능
    long_prefix = pa if len(pa) >= len(pb) else pb
    long_suffix = sa if len(sa) >= len(sb) else sb
    # 결합 string의 prefix와 suffix가 겹치면 (overlap 영역) — 그래도 일치 가능
    return True


def _paths_overlap(a: str, b: str) -> bool:
    """두 writes: path가 동일 파일을 가리킬 가능성 검출.

    literal vs literal: exact match.
    literal vs glob: fnmatch(literal, glob).
    glob vs glob: 양방향 fnmatch + single-* 분석 (`a/*x.md` ∩ `a/x*.md` 같은 케이스).
    """
    if a == b:
        return True
    a_glob, b_glob = _has_glob(a), _has_glob(b)
    if not a_glob and not b_glob:
        return False
    if a_glob and not b_glob:
        return fnmatch.fnmatch(b, a)
    if b_glob and not a_glob:
        return fnmatch.fnmatch(a, b)
    if fnmatch.fnmatch(a, b) or fnmatch.fnmatch(b, a):
        return True
    return _single_star_overlap(a, b)


def check_agent_write_path_overlap() -> list[str]:
    """agents/*.md frontmatter `writes:` 경로 충돌 검출 (A7 doctrine, 2026-05-15).

    frontmatter 내부에 `writes: [path1, path2]` 필드 박제 시 각 path를 owner agent에 매핑.
    exact match + glob intersection 양쪽 검사 — literal-vs-glob 교차 차단.
    """
    errors: list[str] = []
    if not AGENTS_DIR.exists():
        return errors
    agent_paths: list[tuple[str, list[str]]] = []
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
        agent_paths.append((rel, paths))

    # exact match
    by_path: dict[str, list[str]] = {}
    for rel, paths in agent_paths:
        for p in paths:
            by_path.setdefault(p, []).append(rel)
    for p, owners in by_path.items():
        if len(owners) > 1:
            errors.append(
                f"write path `{p}` per-agent exclusivity 위반 — {', '.join(owners)} (A7 doctrine)"
            )

    # glob intersection (pairwise cross-agent, exact pairs already flagged above)
    seen: set[tuple[str, str, str, str]] = set()
    for i in range(len(agent_paths)):
        rel_a, paths_a = agent_paths[i]
        for j in range(i + 1, len(agent_paths)):
            rel_b, paths_b = agent_paths[j]
            for pa in paths_a:
                for pb in paths_b:
                    if pa == pb:
                        continue
                    if not _paths_overlap(pa, pb):
                        continue
                    key = (rel_a, rel_b, *sorted([pa, pb]))
                    if key in seen:
                        continue
                    seen.add(key)
                    errors.append(
                        f"write paths `{pa}` ∩ `{pb}` glob 교집합 — {rel_a}, {rel_b} (A7 glob intersection)"
                    )
    return errors


def check_orchestrator_agent_coverage() -> list[str]:
    """모든 .claude/agents/*.md는 orchestrator SKILL.md/CLAUDE.md에서 참조 필수 (Q1 cardinality).

    M9 Phase 5 게이트의 정량 보강 — agent 파일은 존재하나 orchestrator가 미참조하면
    dead agent로 간주하고 FAIL. inline 대안 검토 doctrine 강제.
    """
    errors: list[str] = []
    if not AGENTS_DIR.exists():
        return errors
    orch = find_orchestrator()
    if not orch:
        return errors
    try:
        text = orch.read_text(encoding="utf-8-sig")
    except OSError:
        return errors
    referenced: set[str] = set()
    for m in AGENT_REF_PATTERN.finditer(text):
        referenced.add(m.group(1))
    for path in AGENTS_DIR.glob("*.md"):
        stem = path.stem
        if stem in referenced:
            continue
        try:
            atext = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        nm = AGENT_NAME_PATTERN.search(atext)
        if nm and nm.group(1) in referenced:
            continue
        errors.append(
            f".claude/agents/{stem}.md — orchestrator {orch.relative_to(REPO_ROOT)} 미참조 (Q1 cardinality: dead agent / inline 대안 미검토)"
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


def _extract_frontmatter_block(text: str) -> str | None:
    m = FRONTMATTER_RE.match(text)
    return m.group(1) if m else None


def _extract_description(text: str) -> str | None:
    """frontmatter `description:` 추출 — inline / quoted / YAML block scalar (`|` `>`) 지원."""
    fm = _extract_frontmatter_block(text)
    if not fm:
        return None
    lines = fm.splitlines()
    for i, line in enumerate(lines):
        m = DESCRIPTION_LINE_PATTERN.match(line)
        if not m:
            continue
        raw = m.group(1).strip()
        # YAML block scalar — 다음 들여쓰기 라인들 join
        if raw in ("|", ">", "|-", ">-", "|+", ">+"):
            collected: list[str] = []
            for sub in lines[i + 1:]:
                if not sub.strip():
                    continue
                if re.match(r"^\s+", sub) and not re.match(r"^\S", sub):
                    collected.append(sub.strip())
                    continue
                if re.match(r"^\S", sub):
                    break
            sep = "\n" if raw.startswith("|") else " "
            return sep.join(collected) if collected else None
        # quoted 또는 plain inline
        if raw.startswith('"') and raw.endswith('"'):
            raw = raw[1:-1]
        elif raw.startswith("'") and raw.endswith("'"):
            raw = raw[1:-1]
        return raw
    return None


def _extract_mcp_servers(text: str) -> set[str]:
    """frontmatter mcpServers: list-of-dicts에서 서버 이름 집합 추출."""
    fm = _extract_frontmatter_block(text)
    if not fm:
        return set()
    if "mcpServers" not in fm:
        return set()
    # mcpServers: 라인 이후만 스캔 — 본문 다른 list 키와 오인 방지
    idx = fm.index("mcpServers")
    after = fm[idx:]
    return {m.group(1) for m in MCP_SERVER_LINE_PATTERN.finditer(after)}


def _extract_tools_list(fm: str) -> list[str]:
    """frontmatter `tools:` 필드를 inline 또는 multi-line YAML list 양쪽 지원으로 파싱."""
    m = TOOLS_LINE_PATTERN.search(fm)
    if not m:
        return []
    inline = m.group(1).strip()
    tools: list[str] = []
    if inline:
        # inline 형태: tools: [a, b, c] 또는 tools: a
        for t in re.split(r"[,\[\]]", inline):
            t = t.strip().strip("'\"")
            if t:
                tools.append(t)
    # multi-line YAML list: `tools:` 라인 뒤의 `  - item` 줄 수집
    lines = fm.splitlines()
    in_tools = False
    for line in lines:
        if re.match(r"^\s*tools\s*:\s*", line):
            in_tools = True
            continue
        if in_tools:
            # YAML list item or 들여쓰기 있는 내용
            li = re.match(r"^\s+-\s+(.+)$", line)
            if li:
                t = li.group(1).strip().strip("'\"")
                if t:
                    tools.append(t)
                continue
            # 들여쓰기 0 + 새 키 = tools 블록 종료
            if re.match(r"^\S", line):
                in_tools = False
    return tools


def check_agent_tools_mcp_consistency() -> list[str]:
    """frontmatter `tools:` allowlist의 `mcp__<server>__<tool>` 항목 ↔ `mcpServers:` 정의 정합 (Q12).

    silent skip 위험 차단: tools:에 mcp 도구 박제했으나 mcpServers: 정의 누락 시 도구 미노출.
    """
    errors: list[str] = []
    if not AGENTS_DIR.exists():
        return errors
    for path in AGENTS_DIR.glob("*.md"):
        rel = str(path.relative_to(REPO_ROOT))
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        fm = _extract_frontmatter_block(text)
        if not fm:
            continue
        tools = _extract_tools_list(fm)
        if not tools:
            continue
        declared_servers = _extract_mcp_servers(text)
        referenced_servers: set[str] = set()
        for tool in tools:
            mm = MCP_TOOL_PATTERN.match(tool)
            if mm:
                referenced_servers.add(mm.group(1))
        missing = referenced_servers - declared_servers
        for server in sorted(missing):
            errors.append(
                f"{rel}: `tools:` references mcp__{server}__* but `mcpServers:` 미선언 — silent skip 위험 (Q12)"
            )
    return errors


def check_agent_model_field() -> list[str]:
    """frontmatter `model:` 필드 박제 확인 (Q2 doctrine, permission-profiles.md §5-1-c)."""
    errors: list[str] = []
    if not AGENTS_DIR.exists():
        return errors
    for path in AGENTS_DIR.glob("*.md"):
        rel = str(path.relative_to(REPO_ROOT))
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        fm = _extract_frontmatter_block(text)
        if not fm:
            continue
        if not re.search(r"^\s*model\s*:\s*\S+", fm, re.MULTILINE):
            errors.append(f"{rel}: frontmatter `model:` 필드 누락 (Q2 doctrine — opus/sonnet 명시 필수)")
    return errors


def _tokenize_description(desc: str) -> set[str]:
    """description에서 trigger 키워드 후보 토큰화 — 한글/영문 단어 단위."""
    # 한글 음절 연속 + 영문 단어 + 숫자 — 기호·공백 분리
    tokens = re.findall(r"[가-힣]+|[A-Za-z][A-Za-z0-9_-]+", desc)
    return {t.lower() for t in tokens if len(t) >= 2}


def check_skill_description_overlap(threshold: float = 0.5) -> list[str]:
    """skill description 트리거 키워드 *pairwise* Jaccard 유사도 검출 (Q5).

    threshold 초과 쌍은 트리거 충돌 가능성 — Phase 8-4 should-NOT regression 사전 감지.
    """
    errors: list[str] = []
    if not SKILLS_DIR.exists():
        return errors
    desc_by_skill: list[tuple[str, set[str]]] = []
    for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
        try:
            text = skill_md.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        desc = _extract_description(text)
        if not desc:
            continue
        tokens = _tokenize_description(desc)
        if len(tokens) < 3:
            continue
        desc_by_skill.append((str(skill_md.relative_to(REPO_ROOT)), tokens))
    for i in range(len(desc_by_skill)):
        rel_a, toks_a = desc_by_skill[i]
        for j in range(i + 1, len(desc_by_skill)):
            rel_b, toks_b = desc_by_skill[j]
            inter = toks_a & toks_b
            union = toks_a | toks_b
            if not union:
                continue
            jaccard = len(inter) / len(union)
            if jaccard >= threshold:
                sample = ", ".join(sorted(inter)[:5])
                errors.append(
                    f"skill description overlap — {rel_a} ↔ {rel_b} (Jaccard {jaccard:.2f} ≥ {threshold}, 공통: {sample}) — Q5 트리거 충돌 위험"
                )
    return errors


def check_skill_signal_coverage() -> list[str]:
    """skill description이 trigger-keyword-catalog.md 10 signal 중 *최소 1*을 hit해야 함 (Q11).

    miss 시 자연어 트리거 약함 → Phase 8-4 should-trigger regression 위험.
    """
    errors: list[str] = []
    if not SKILLS_DIR.exists():
        return errors
    for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
        try:
            text = skill_md.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        desc = _extract_description(text)
        if not desc:
            continue
        rel = str(skill_md.relative_to(REPO_ROOT))
        desc_lower = desc.lower()
        hit_signals: list[str] = []
        for signal_id, keywords in _TRIGGER_SIGNAL_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in desc_lower:
                    hit_signals.append(signal_id)
                    break
        if not hit_signals:
            errors.append(
                f"{rel}: description이 trigger-keyword-catalog 10 signal 어느 것도 hit 안 함 (Q11 signal coverage 0) — 트리거 약함"
            )
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
    errors.extend(check_orchestrator_agent_coverage())
    errors.extend(check_skill_name_uniqueness())
    errors.extend(check_reference_links())
    errors.extend(check_agent_tools_mcp_consistency())
    errors.extend(check_agent_model_field())
    errors.extend(check_skill_description_overlap())
    errors.extend(check_skill_signal_coverage())

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
