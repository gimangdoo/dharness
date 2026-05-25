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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema import INTENT_REQUIRED  # noqa: E402  W3 doctrine 단일 출처

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# scripts/validate/chain.py → parents[4]가 repo root. __file__ 기반 통일 (structure.py/schema.py 정합).
# cwd 의존 시 derived install user가 sub-dir에서 호출하면 silent precondition_fail.
REPO_ROOT = Path(__file__).resolve().parents[4]
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
SETTINGS_FILES = [
    REPO_ROOT / ".claude" / "settings.json",
    REPO_ROOT / ".claude" / "settings.local.json",
]
# plugin.json은 chain.py 기준 상대경로 — derived install 시 plugin 외부 위치에서도 안전.
PLUGIN_JSON_FROM_SCRIPT = (
    Path(__file__).resolve().parent.parent.parent / ".claude-plugin" / "plugin.json"
)
INTENT_PROFILE = REPO_ROOT / "_workspace" / "_baseline" / "intent_profile.md"

# Plugin-internal check (self-host doctrine). harness plugin 단일 구조 가정.
PLUGIN_SKILL_MD = REPO_ROOT / "plugins" / "harness" / "skills" / "harness" / "SKILL.md"
PLUGIN_REFERENCES_DIR = REPO_ROOT / "plugins" / "harness" / "skills" / "harness" / "references"
PLUGIN_COMMANDS_DIR = REPO_ROOT / "plugins" / "harness" / "commands"

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
    names: set[str] = set()
    for p in SKILLS_DIR.iterdir():
        if not p.is_dir():
            continue
        # SKILL.md 대문자 고정 (Anthropic 명세). 변종(skill.md/Skill.md)은 structure.py가
        # 별도 FAIL로 알린다 — chain.py 5 downstream(name_uniqueness, description_overlap,
        # signal_coverage, reference_links, find_orchestrator)은 모두 case-sensitive glob
        # 사용 중이므로 본 함수도 case-sensitive 유지해 partial validation 회피.
        if (p / "SKILL.md").is_file():
            names.add(p.name)
    return names


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


EXTERNAL_INPUT_TOOLS = {
    "bash",
    "write",
    "edit",
    "multiedit",
    "notebookedit",
    "webfetch",
    "websearch",
    "powershell",
}
INJECTION_GUARD_PATTERN = re.compile(
    r"입력\s*신뢰\s*경계|프롬프트\s*인젝션|인젝션\s*방어|injection\s*guard|untrusted\s*input|prompt\s*injection",
    re.IGNORECASE,
)


def check_agent_injection_guard() -> list[str]:
    """외부 입력·부작용 도구 보유 에이전트 ↔ 본문 인젝션 방어 절 정합 (N-C-1 doctrine).

    Bash/Write/Edit/MultiEdit/NotebookEdit/WebFetch/WebSearch/PowerShell 보유 OR `tools:` 필드
    부재(전체 도구 상속)면 인젝션 표면이 존재 — 본문에 '입력 신뢰 경계' 절 박제 필수.
    agent-design-patterns.md "입력 신뢰 경계" doctrine.
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
        if TOOLS_LINE_PATTERN.search(fm):
            tools = _extract_tools_list(fm)
            held = sorted(
                {t for t in tools if t.split("__", 1)[0].strip().lower() in EXTERNAL_INPUT_TOOLS}
            )
            if not held:
                continue
            surface = ", ".join(held)
        else:
            # `tools:` 필드 부재 = 전체 도구 상속 (Bash/Write 포함) — 인젝션 표면 존재
            surface = "tools: 필드 부재 → 전체 도구 상속"
        body = text.split("---", 2)[-1] if text.lstrip().startswith("---") else text
        if not INJECTION_GUARD_PATTERN.search(body):
            errors.append(
                f"{rel}: 외부 입력·부작용 도구 보유({surface})하나 본문 인젝션 방어 절 부재 "
                f"— '입력 신뢰 경계' 섹션 박제 필수 (N-C-1 doctrine)"
            )
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


_GRILLING_VALID_PHASES = ("0.5", "2", "5", "9")
_GRILLING_VALID_SOURCES = ("signals>=2", "section_3_1_direct", "section_3_2_estimate")
_GRILLING_REQUIRED_KEYS = ("phase", "field", "mode", "recommended", "recommended_source", "user_response")

# W3 doctrine (phase-entry-gates.md:§Phase 2). 5필드 모두 사용자 raw 답변으로
# meta.user_confirmed_fields 등록 필수. brownfield 자동 추론도 사용자 확인 답변
# 받아야 user_confirmed_fields 등록 — inferred_fields 등록만으로 doctrine 불충족.
# 정본은 schema.py:INTENT_REQUIRED — 본 alias로 의도 명시.
_INTENT_USER_CONFIRMED_REQUIRED = tuple(INTENT_REQUIRED)


def _extract_user_confirmed_fields(yaml_body: str) -> list[str] | None:
    """meta.user_confirmed_fields list 추출 — inline / indented / compact YAML 양쪽 지원.

    반환값 의미:
      None  — meta.user_confirmed_fields 필드 자체 박제 미존재
      list  — 박제 list (빈 list 포함). 원소는 dot-path string.

    `_extract_grilling_log_block` 패턴 재사용 — meta 블록 내부 list 키를 indent 기반 파싱.
    inline 형태 `user_confirmed_fields: []` / `user_confirmed_fields: [a, b]`도 지원.
    """
    lines = yaml_body.splitlines()
    in_meta = False
    meta_indent = -1
    in_list = False
    list_indent = -1
    items: list[str] = []
    for raw in lines:
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        if not in_meta:
            if stripped.startswith("meta:") and indent == 0:
                in_meta = True
                meta_indent = indent
            continue
        if in_meta and not in_list:
            if indent <= meta_indent:
                return None
            m = re.match(r"^user_confirmed_fields\s*:\s*(.*)$", stripped)
            if m:
                inline = m.group(1).strip()
                if inline.startswith("["):
                    # inline list. `[]` 빈 list 포함.
                    body = inline.strip().lstrip("[").rstrip("]")
                    return [_strip_quotes(t.strip()) for t in body.split(",") if t.strip()]
                if inline:
                    # 단일 scalar — list로 해석 안 함. doctrine 위반 케이스로 빈 list 반환.
                    return []
                in_list = True
                list_indent = indent
            continue
        if in_list:
            if stripped.startswith("- ") and indent > list_indent:
                items.append(_strip_quotes(stripped[2:].strip()))
                continue
            if indent <= list_indent and stripped:
                break
    if in_list:
        return items
    return None


def check_required_user_confirmed_fields() -> list[str]:
    """W3 doctrine — intent_profile.md meta.user_confirmed_fields가 INTENT_REQUIRED 5필드 전부 커버.

    prefix 매칭 — `constraints.tech_stack.locked_in` 등록은 `constraints.tech_stack` 커버.
    intent_profile.md 미존재 시 silent skip (schema.py가 별도 FAIL).
    meta.user_confirmed_fields 박제 자체 미존재 또는 빈 list → 5필드 모두 누락 FAIL.

    근거: phase-entry-gates.md §Phase 2 step 1 + Phase 0.5 anti-premature-judgment evidence #2.
    """
    errors: list[str] = []
    if not INTENT_PROFILE.exists():
        return errors
    try:
        text = INTENT_PROFILE.read_text(encoding="utf-8-sig")
    except OSError:
        return errors

    fm = FRONTMATTER_RE.search(text)
    body = fm.group(1) if fm else text

    confirmed = _extract_user_confirmed_fields(body)
    if confirmed is None:
        errors.append(
            "intent_profile.md meta.user_confirmed_fields 필드 박제 누락 — "
            "Phase 2 doctrine 위반 (W3, phase-entry-gates.md §Phase 2 step 1)"
        )
        confirmed = []

    for required in _INTENT_USER_CONFIRMED_REQUIRED:
        prefix = required + "."
        if not any(c == required or c.startswith(prefix) for c in confirmed):
            errors.append(
                f"intent_profile.md meta.user_confirmed_fields: 필수 필드 `{required}` 누락 — "
                f"사용자 raw 답변 미박제 (W3 anti-premature-judgment 강제)"
            )
    return errors


def check_intent_profile_grilling_log() -> list[str]:
    """meta.grilling_log[] doctrine 검증 (Phase B, 2026-05-19, grill-me 흡수).

    intent_profile.md frontmatter의 meta.grilling_log 박제 항목별로:
      - 필수 키 6개 (phase/field/mode/recommended/recommended_source/user_response) 존재
      - phase ∈ {"0.5","2","5","9"}, mode == "grilling"
      - recommended_source ∈ {"signals>=2","section_3_1_direct","section_3_2_estimate"}
        (디렉토리·파일 이름 단독 추천 — anti-premature-judgment doctrine 위반 차단)

    intent_profile.md 또는 meta.grilling_log 미박제 시 silent skip (옵션 필드).
    """
    errors: list[str] = []
    intent_path = REPO_ROOT / "_workspace" / "_baseline" / "intent_profile.md"
    if not intent_path.exists():
        return errors
    try:
        text = intent_path.read_text(encoding="utf-8-sig")
    except OSError:
        return errors

    fm = FRONTMATTER_RE.search(text)
    body = fm.group(1) if fm else text

    log_block = _extract_grilling_log_block(body)
    if log_block is None:
        return errors

    entries = _parse_grilling_entries(log_block)
    for idx, entry in enumerate(entries):
        missing = [k for k in _GRILLING_REQUIRED_KEYS if k not in entry]
        if missing:
            errors.append(
                f"intent_profile.md meta.grilling_log[{idx}]: 필수 키 누락 {missing} — grilling-loop.md §8 위반"
            )
            continue
        if entry["phase"] not in _GRILLING_VALID_PHASES:
            errors.append(
                f"intent_profile.md meta.grilling_log[{idx}].phase = `{entry['phase']}` 허용값 {_GRILLING_VALID_PHASES} 외"
            )
        if entry["mode"] != "grilling":
            errors.append(
                f"intent_profile.md meta.grilling_log[{idx}].mode = `{entry['mode']}` — 'grilling' 고정값"
            )
        if entry["recommended_source"] not in _GRILLING_VALID_SOURCES:
            errors.append(
                f"intent_profile.md meta.grilling_log[{idx}].recommended_source = `{entry['recommended_source']}` "
                f"— anti-premature-judgment doctrine 위반. 허용값 {_GRILLING_VALID_SOURCES}"
            )
    return errors


def _extract_dharness_version_from_baseline() -> str | None:
    if not INTENT_PROFILE.exists():
        return None
    try:
        text = INTENT_PROFILE.read_text(encoding="utf-8-sig")
    except OSError:
        return None
    fm = _extract_frontmatter_block(text)
    if not fm:
        return None
    m = re.search(
        r"^\s*dharness_version\s*:\s*['\"]?([^'\"\n]+?)['\"]?\s*$",
        fm,
        re.MULTILINE,
    )
    return m.group(1).strip() if m else None


def _read_current_plugin_version() -> str | None:
    try:
        data = json.loads(PLUGIN_JSON_FROM_SCRIPT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    v = data.get("version") if isinstance(data, dict) else None
    return v if isinstance(v, str) else None


def check_dharness_version_drift() -> dict[str, str | None]:
    """baseline `intent_profile.md` `meta.dharness_version` vs 현 plugin.json `version` 비교.

    schema 위반 아님 (옵션 필드) — *warning/info* 영역. doctrine drift refit 권고 1줄.
    `harness-validate`/`harness-status`가 본 결과를 사용자에게 노출.
    (2026-05-23 doctrine drift refit 인프라.)
    """
    baseline_v = _extract_dharness_version_from_baseline()
    current_v = _read_current_plugin_version()
    if baseline_v is None or current_v is None or baseline_v == current_v:
        return {"baseline": baseline_v, "current": current_v, "message": None}
    msg = (
        f"dharness plugin upgrade 감지 — baseline `{baseline_v}` → 현 `{current_v}`. "
        f"doctrine refit 권고: `/harness:harness-audit` + `/harness:harness-validate` "
        f"진단 후 발견 항목별 `/harness:harness-evolve`·`-add-skill`·`-remove`로 수정."
    )
    return {"baseline": baseline_v, "current": current_v, "message": msg}


def _extract_grilling_log_block(yaml_body: str) -> str | None:
    lines = yaml_body.splitlines()
    in_meta = False
    meta_indent = -1
    log_indent = -1
    in_log = False
    collected: list[str] = []
    for raw in lines:
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            if in_log:
                collected.append(raw)
            continue
        indent = len(line) - len(stripped)
        if not in_meta:
            if stripped.startswith("meta:") and indent == 0:
                in_meta = True
                meta_indent = indent
            continue
        if in_meta and not in_log:
            if indent <= meta_indent:
                return None
            if stripped.startswith("grilling_log:"):
                in_log = True
                log_indent = indent
            continue
        if in_log:
            # YAML compact block sequence form: list item at parent indent
            # (e.g. `grilling_log:` indent=2, `- phase` indent=2). Treat as
            # first list item rather than as a sibling key.
            if stripped.startswith("- ") and indent == log_indent:
                collected.append(raw)
                continue
            if indent <= log_indent and stripped:
                break
            collected.append(raw)
    return "\n".join(collected) if collected else None


def _parse_grilling_entries(block: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    key_value_re = re.compile(r"^([A-Za-z_]+)\s*:\s*(.*?)\s*$")
    for raw in block.splitlines():
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- "):
            if current is not None:
                entries.append(current)
            current = {}
            body = stripped[2:].strip()
            m = key_value_re.match(body)
            if m:
                current[m.group(1)] = _strip_quotes(m.group(2))
            continue
        if current is None:
            continue
        m = key_value_re.match(stripped)
        if m:
            current[m.group(1)] = _strip_quotes(m.group(2))
    if current is not None:
        entries.append(current)
    return entries


def _strip_quotes(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        return v[1:-1]
    return v


_CODE_FENCE_RE = re.compile(r"```.*?(?:\n|$).*?(?:```|\Z)", re.DOTALL)


def _strip_code_fences(text: str) -> str:
    """fenced code block (``` ... ```)을 빈 줄로 치환 — link scan false-positive 차단 (P4)."""
    return _CODE_FENCE_RE.sub("", text)


def check_reference_links() -> list[str]:
    errors: list[str] = []
    if not SKILLS_DIR.exists():
        return errors

    for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
        try:
            text = skill_md.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        scanned = _strip_code_fences(text)
        skill_dir = skill_md.parent
        for match in REFERENCE_LINK_PATTERN.finditer(scanned):
            rel_path = match.group(1)
            target = skill_dir / "references" / rel_path
            if not target.exists():
                errors.append(f"{skill_md.relative_to(REPO_ROOT)}: dangling reference `references/{rel_path}`")
    return errors


def check_plugin_internal_references() -> list[str]:
    """harness plugin 본체 내부 cross-reference 검증 (P2 self-host doctrine).

    검사 대상: `plugins/harness/skills/harness/SKILL.md` + `references/*.md` + `commands/*.md`.
    각 파일의 `references/<path>.md` 패턴이 `plugins/harness/skills/harness/references/` 하위에 실존하는지 확인.
    fence 안 예시는 `_strip_code_fences`로 건너뜀.
    """
    errors: list[str] = []
    if not PLUGIN_REFERENCES_DIR.exists():
        return errors

    targets: list[Path] = []
    if PLUGIN_SKILL_MD.exists():
        targets.append(PLUGIN_SKILL_MD)
    targets.extend(sorted(PLUGIN_REFERENCES_DIR.glob("*.md")))
    if PLUGIN_COMMANDS_DIR.exists():
        targets.extend(sorted(PLUGIN_COMMANDS_DIR.glob("*.md")))

    for path in targets:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        scanned = _strip_code_fences(text)
        for match in REFERENCE_LINK_PATTERN.finditer(scanned):
            rel_path = match.group(1)
            target = PLUGIN_REFERENCES_DIR / rel_path
            if not target.exists():
                errors.append(
                    f"{path.relative_to(REPO_ROOT)}: dangling plugin reference `references/{rel_path}`"
                )
    return errors


_DOCTRINE_REGISTRY = (
    PLUGIN_REFERENCES_DIR / "doctrine-registry.md"
)
_VALIDATE_DIR = Path(__file__).resolve().parent
# `chain.py:fn` / `structure.py:fn` / `schema.py:fn` — backtick 안 인용 패턴.
# 본 정규식은 단일 출처 doctrine-registry.md의 fn-name drift 영구 차단을 위함 (R6 doctrine).
_DOCTRINE_FN_REF_PATTERN = re.compile(
    r"`(chain|structure|schema)\.py:([A-Za-z_][A-Za-z0-9_]*)`"
)
_DEF_PATTERN = re.compile(r"^def\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
# 모듈-레벨 UPPERCASE 상수 (e.g. INTENT_REQUIRED) — registry가 fn 외 canonical symbol 인용 시 허용.
_CONST_PATTERN = re.compile(r"^([A-Z_][A-Z0-9_]*)\s*=", re.MULTILINE)


def _collect_module_fns(module_name: str) -> set[str]:
    path = _VALIDATE_DIR / f"{module_name}.py"
    if not path.exists():
        return set()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return set()
    return set(_DEF_PATTERN.findall(text)) | set(_CONST_PATTERN.findall(text))


def check_doctrine_registry_fn_refs() -> list[str]:
    """doctrine-registry.md의 `chain.py:<fn>`·`structure.py:<fn>`·`schema.py:<fn>` 인용 ↔
    실제 모듈 def 존재 정합 (R6 doctrine, 2026-05-24).

    drift 영구 차단: registry 인용이 실 fn명과 어긋나면 contributor가 잘못된 경로로
    정합 점검을 시도. registry는 단일 출처 색인이므로 결정적 검증 필수.
    """
    errors: list[str] = []
    if not _DOCTRINE_REGISTRY.exists():
        return errors
    try:
        text = _DOCTRINE_REGISTRY.read_text(encoding="utf-8-sig")
    except OSError:
        return errors
    scanned = _strip_code_fences(text)
    fn_cache: dict[str, set[str]] = {}
    seen: set[tuple[str, str]] = set()
    for module, fn in _DOCTRINE_FN_REF_PATTERN.findall(scanned):
        key = (module, fn)
        if key in seen:
            continue
        seen.add(key)
        if module not in fn_cache:
            fn_cache[module] = _collect_module_fns(module)
        if fn not in fn_cache[module]:
            errors.append(
                f"doctrine-registry.md: `{module}.py:{fn}` 인용 — 실제 fn 미존재 "
                f"(R6 doctrine drift)"
            )
    return errors


# §6 inverse index row: ``| `<module>.py` | <ids cell> |``
_INVERSE_MODULE_ROW_PATTERN = re.compile(
    r"^\|\s*`(chain|structure|schema)\.py`\s*\|\s*([^|]+)\|",
    re.MULTILINE,
)
# §1-5 doctrine row: ``| W1 | ... |`` — capture id + rest of line for module ref scan.
_DOCTRINE_ROW_LINE_PATTERN = re.compile(
    r"^\|\s*((?:W|R|S|P|I)\d+)\s*\|([^\n]*)$",
    re.MULTILINE,
)
_DOCTRINE_ID_TOKEN_PATTERN = re.compile(r"\b((?:W|R|S|P|I)\d+)\b")


def check_doctrine_registry_inverse_index() -> list[str]:
    """doctrine-registry.md §6 역색인 ↔ §1-5 doctrine id 매핑 정합 (R6 확장, 2026-05-24).

    §1-5 row가 `chain.py:<fn>` / `structure.py:<fn>` / `schema.py:<fn>`를 인용하면
    §6 inverse index의 해당 module 행에도 그 doctrine id가 등재돼 있어야 한다.
    contributor가 §6 색인 read만으로 doctrine ↔ module 매핑을 추적하므로 drift 차단.
    """
    errors: list[str] = []
    if not _DOCTRINE_REGISTRY.exists():
        return errors
    try:
        text = _DOCTRINE_REGISTRY.read_text(encoding="utf-8-sig")
    except OSError:
        return errors
    scanned = _strip_code_fences(text)

    inverse: dict[str, set[str]] = {}
    for module, ids_cell in _INVERSE_MODULE_ROW_PATTERN.findall(scanned):
        ids = set(_DOCTRINE_ID_TOKEN_PATTERN.findall(ids_cell))
        inverse.setdefault(module, set()).update(ids)

    reported: set[tuple[str, str]] = set()
    for match in _DOCTRINE_ROW_LINE_PATTERN.finditer(scanned):
        doctrine_id = match.group(1)
        row_body = match.group(2)
        for module, _fn in _DOCTRINE_FN_REF_PATTERN.findall(row_body):
            key = (doctrine_id, module)
            if key in reported:
                continue
            if module not in inverse:
                reported.add(key)
                errors.append(
                    f"doctrine-registry.md: §1-5 {doctrine_id} → `{module}.py:` "
                    f"인용 — §6 inverse index에 `{module}.py` 행 부재 (R6 확장)"
                )
                continue
            if doctrine_id not in inverse[module]:
                reported.add(key)
                errors.append(
                    f"doctrine-registry.md: §1-5 {doctrine_id} → `{module}.py:` "
                    f"인용 — §6 `{module}.py` 행에 {doctrine_id} 미등재 (R6 확장)"
                )
    return errors


# W3 doctrine doc sync — 5 필수 필드가 schema.py 정본과 동기인 doc 위치.
# 각 path는 PLUGIN_REFERENCES_DIR 또는 PLUGIN_SKILL_MD 기준 상대.
_INTENT_REQUIRED_DOC_TARGETS = (
    ("SKILL.md", lambda: PLUGIN_SKILL_MD),
    ("phase-entry-gates.md", lambda: PLUGIN_REFERENCES_DIR / "phase-entry-gates.md"),
    ("intent-profile-schema.md", lambda: PLUGIN_REFERENCES_DIR / "intent-profile-schema.md"),
)


def check_intent_required_doc_sync() -> list[str]:
    """W3 doctrine doc sync — schema.py:INTENT_REQUIRED 5필드가 본문 doc에 모두 박제 (2026-05-24).

    필드 list가 schema.py와 doc 5곳에 분산 hard-code된 drift 위험을 결정적으로 차단.
    각 doc 위치(SKILL.md / phase-entry-gates.md / intent-profile-schema.md)에 5필드 모두
    문자열 hit 보장. 1 필드라도 doc 누락 시 FAIL — schema 진화 시 doc 동기화 강제.
    """
    errors: list[str] = []
    for label, resolver in _INTENT_REQUIRED_DOC_TARGETS:
        path = resolver()
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        for field in INTENT_REQUIRED:
            if field not in text:
                errors.append(
                    f"{label}: schema.py:INTENT_REQUIRED 필드 `{field}` 박제 누락 "
                    f"— doc ↔ schema sync drift (W3 doc sync)"
                )
    return errors


# S13 박제 — output-checklist.md 본문 카운트 ↔ 인용 박제 정합 검증 대상 파일.
_OUTPUT_CHECKLIST_QUOTE_TARGETS = (
    ("SKILL.md", lambda: PLUGIN_SKILL_MD),
    ("harness-new.md", lambda: PLUGIN_COMMANDS_DIR / "harness-new.md"),
)
_OUTPUT_CHECKLIST_QUOTE_PATTERN = re.compile(r"must\s+(\d+)\s*/\s*should\s+(\d+)")
_OUTPUT_CHECKLIST_HEADER_PATTERN = re.compile(
    r"must\s*\(\s*(\d+)\s*\)\s*/\s*should\s*\(\s*(\d+)\s*\)"
)


def check_output_checklist_count_sync() -> list[str]:
    """S13 doctrine doc sync — output-checklist.md must/should 카운트 ↔ 인용 박제 정합 (2026-05-25).

    `output-checklist.md` 본문 ## 차단 (must) / ## 권장 (should) 섹션 `- [ ]` 항목 카운트가
    정본. 헤더 `must (N) / should (M)` 박제 + SKILL.md·harness-new.md 인용 박제 `must N / should M`
    토큰이 정본과 mismatch 시 FAIL. 체크리스트 항목 추가/삭제 시 cross-doc 동기 강제.
    """
    checklist = PLUGIN_REFERENCES_DIR / "output-checklist.md"
    if not checklist.exists():
        return []
    try:
        body = checklist.read_text(encoding="utf-8-sig")
    except OSError:
        return []

    must_count = 0
    should_count = 0
    current: str | None = None
    for raw in body.splitlines():
        stripped = raw.strip()
        if stripped.startswith("## "):
            header = stripped.lower()
            if "must" in header or "차단" in header:
                current = "must"
            elif "should" in header or "권장" in header:
                current = "should"
            else:
                current = None
            continue
        if current == "must" and stripped.startswith("- [ ]"):
            must_count += 1
        elif current == "should" and stripped.startswith("- [ ]"):
            should_count += 1

    errors: list[str] = []

    # output-checklist.md 헤더 `must (N) / should (M)` 정합.
    for m in _OUTPUT_CHECKLIST_HEADER_PATTERN.finditer(body):
        mu, sh = int(m.group(1)), int(m.group(2))
        if mu != must_count or sh != should_count:
            errors.append(
                f"output-checklist.md: 헤더 `must ({mu}) / should ({sh})` ↔ "
                f"본문 정본 `must {must_count} / should {should_count}` drift (S13)"
            )

    # 인용 박제 위치 — `must N / should M` 토큰.
    for label, resolver in _OUTPUT_CHECKLIST_QUOTE_TARGETS:
        path = resolver()
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        for m in _OUTPUT_CHECKLIST_QUOTE_PATTERN.finditer(text):
            mu, sh = int(m.group(1)), int(m.group(2))
            if mu != must_count or sh != should_count:
                errors.append(
                    f"{label}: 인용 박제 `must {mu} / should {sh}` ↔ "
                    f"output-checklist.md 정본 `must {must_count} / should {should_count}` "
                    f"drift (S13)"
                )
    return errors


_METHODOLOGY_ENUM = {
    "tdd", "bdd", "ddd", "spec-driven", "trunk-based",
    "kanban", "scrum", "shape-up", "xp", "none", "unknown",
}
_METHODOLOGY_SOURCE_ENUM = {"advisor", "user", "inferred", "none"}


def _strip_inline_comment(val: str) -> str:
    """YAML inline 주석(` #` 또는 `\\t#`) 제거. quoted scalar 내부 `#`은 보존."""
    v = val.strip()
    if not v:
        return v
    if v[0] in ('"', "'"):
        quote = v[0]
        end = v.find(quote, 1)
        if end != -1:
            return v[: end + 1]
        return v
    m = re.search(r"\s+#", v)
    if m:
        return v[: m.start()].rstrip()
    return v


def _extract_section_scalar(yaml_body: str, section: str, key: str) -> str | None:
    """frontmatter 본문에서 `section.key` scalar 값 추출. inline·indented 양쪽 지원.

    반환:
      None  — section 또는 key 박제 미존재
      str   — scalar 값 (quotes·inline 주석 제거). 빈 string 가능.
    """
    in_section = False
    section_indent = -1
    for raw in yaml_body.splitlines():
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        if not in_section:
            if stripped.startswith(f"{section}:") and indent == 0:
                in_section = True
                section_indent = indent
            continue
        if indent <= section_indent:
            return None
        m = re.match(rf"^{re.escape(key)}\s*:\s*(.*)$", stripped)
        if m:
            val = _strip_inline_comment(m.group(1))
            if val and not val.startswith("["):
                return _strip_quotes(val)
            return None
    return None


def _extract_section_list(yaml_body: str, section: str, key: str) -> list[str] | None:
    """frontmatter 본문에서 `section.key` list 값 추출. inline·dash 양쪽 지원.

    반환:
      None  — section 또는 key 박제 미존재
      list  — 박제 list (빈 list 포함). 원소 string.
    """
    in_section = False
    section_indent = -1
    in_list = False
    list_indent = -1
    items: list[str] = []
    for raw in yaml_body.splitlines():
        line = raw.rstrip()
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        if not in_section:
            if stripped.startswith(f"{section}:") and indent == 0:
                in_section = True
                section_indent = indent
            continue
        if not in_list:
            if indent <= section_indent:
                return None
            m = re.match(rf"^{re.escape(key)}\s*:\s*(.*)$", stripped)
            if m:
                inline = _strip_inline_comment(m.group(1))
                if inline.startswith("["):
                    body_in = inline.strip().lstrip("[").rstrip("]")
                    return [_strip_quotes(t.strip()) for t in body_in.split(",") if t.strip()]
                if inline:
                    return []
                in_list = True
                list_indent = indent
            continue
        if in_list:
            if stripped.startswith("- ") and indent > list_indent:
                items.append(_strip_quotes(_strip_inline_comment(stripped[2:])))
                continue
            if indent <= list_indent and stripped:
                break
    return items if in_list else None


def check_advisor_handoff_adapter_consistency() -> list[str]:
    """W8 v0.12.1 adapter doctrine — advisor handoff merge 후 intent_profile.md 정합 검증.

    검증 룰 (intent-profile-schema.md §8, 5건):
      1. methodology_source=advisor + methodology_matrix_row=null/미박제 → 모순
      2. methodology_source≠advisor + methodology_matrix_row 박제 → 모순
      3. methodology_source=advisor + meta.advisor_handoff_version 미박제 → 모순 (재현성 손실)
      4. meta.advisor_secondary_methodologies non-empty + methodology_source≠advisor → 모순
      5. methodology_source=advisor + methodology non-enum-or-non-lowercase → 모순 (adapter 변환 누락)
    추가: methodology 값 ∈ dharness enum 11 (또는 "unknown"), methodology_source ∈ enum 4.

    intent_profile.md 미존재 또는 workflow.methodology·methodology_source 양쪽 모두 미박제 시
    silent skip (Phase 2 미진입 또는 advisor 영역 미합성 — 검증 대상 아님).
    """
    errors: list[str] = []
    if not INTENT_PROFILE.exists():
        return errors
    try:
        text = INTENT_PROFILE.read_text(encoding="utf-8-sig")
    except OSError:
        return errors

    fm = FRONTMATTER_RE.search(text)
    body = fm.group(1) if fm else text

    methodology = _extract_section_scalar(body, "workflow", "methodology")
    source = _extract_section_scalar(body, "workflow", "methodology_source")
    matrix_row = _extract_section_scalar(body, "workflow", "methodology_matrix_row")
    handoff_version = _extract_section_scalar(body, "meta", "advisor_handoff_version")
    secondary = _extract_section_list(body, "meta", "advisor_secondary_methodologies") or []

    if source is None and methodology is None:
        return errors

    matrix_present = matrix_row is not None and matrix_row.lower() != "null"

    if methodology is not None and methodology not in _METHODOLOGY_ENUM:
        errors.append(
            f"intent_profile.md workflow.methodology=`{methodology}` — "
            f"dharness enum 11 외 (W8 adapter doctrine, intent-profile-schema.md §2)"
        )

    if source is not None and source not in _METHODOLOGY_SOURCE_ENUM:
        errors.append(
            f"intent_profile.md workflow.methodology_source=`{source}` — "
            f"enum 4(advisor/user/inferred/none) 외 (W8 adapter doctrine)"
        )

    if source == "advisor" and not matrix_present:
        errors.append(
            "intent_profile.md workflow.methodology_source=advisor + "
            "methodology_matrix_row 미박제 — §8 cross-field 룰 위반 (W8)"
        )

    if source not in (None, "advisor") and matrix_present:
        errors.append(
            f"intent_profile.md workflow.methodology_source=`{source}` + "
            f"methodology_matrix_row=`{matrix_row}` — 비-advisor source는 "
            "matrix_row 보유 금지 (W8 §8 cross-field 룰)"
        )

    if source == "advisor" and not handoff_version:
        errors.append(
            "intent_profile.md workflow.methodology_source=advisor + "
            "meta.advisor_handoff_version 미박제 — v0.12.1 adapter 룰 위반 "
            "(원본 source string 손실, 재현성 ↓, W8)"
        )

    if secondary and source != "advisor":
        errors.append(
            f"intent_profile.md meta.advisor_secondary_methodologies non-empty + "
            f"workflow.methodology_source=`{source or 'none'}` — secondary list는 "
            "advisor source 시만 박제 (v0.12.1 adapter 룰, W8)"
        )

    if source == "advisor" and methodology:
        if methodology != methodology.lower():
            errors.append(
                f"intent_profile.md workflow.methodology=`{methodology}` "
                f"(source=advisor) — lowercase 정규화 누락 "
                "(v0.12.1 adapter 변환 step 3 미실행, W8)"
            )

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
    errors.extend(check_plugin_internal_references())
    errors.extend(check_agent_tools_mcp_consistency())
    errors.extend(check_agent_model_field())
    errors.extend(check_agent_injection_guard())
    errors.extend(check_skill_description_overlap())
    errors.extend(check_skill_signal_coverage())
    errors.extend(check_intent_profile_grilling_log())
    errors.extend(check_required_user_confirmed_fields())
    errors.extend(check_doctrine_registry_fn_refs())
    errors.extend(check_doctrine_registry_inverse_index())
    errors.extend(check_intent_required_doc_sync())
    errors.extend(check_output_checklist_count_sync())
    errors.extend(check_advisor_handoff_adapter_consistency())

    version_drift = check_dharness_version_drift()

    status = "PASS" if not errors else "FAIL"
    report = {
        "section": "chain",
        "status": status,
        "agents_count": len(valid_agents),
        "skills_count": len(valid_skills),
        "orchestrator": str(orch.relative_to(REPO_ROOT)) if orch else None,
        "errors": errors,
        "version_drift": version_drift,
    }

    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        icon = "✅" if status == "PASS" else "❌"
        print(f"{icon} §3 chain: {status} (dangling 0 check across {len(valid_agents)} agents / {len(valid_skills)} skills, {len(errors)} errors)")
        for e in errors:
            print(f"  - {e}")
        if version_drift["message"]:
            print(f"ℹ️  {version_drift['message']}")

    return 1 if (strict and errors) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
