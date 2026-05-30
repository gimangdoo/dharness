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
from schema import (  # noqa: E402  W3·I2 doctrine 단일 출처
    INTENT_REQUIRED,
    INTENT_REQUIRED_USER_CONFIRMED,
)

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
PLUGIN_README = REPO_ROOT / "plugins" / "harness" / "README.md"

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
# S15 doctrine (2026-05-28): chain_doc_sync.py:check_trigger_catalog_python_sync가 본 dict ↔
# trigger-keyword-catalog.md §1 표 sync 결정적 검증 — catalog가 단일 출처(doctrine S11) 이므로
# 본 dict는 catalog 키워드 superset 또는 equal (catalog → code 누락 시 FAIL).
_TRIGGER_SIGNAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "S1": ("분석", "검토", "리서치", "요약", "조회", "검색", "탐색", "탐사", "진단", "감사", "점검",
           "analyze", "review", "research", "summarize", "query", "search", "explore", "audit", "inspect", "investigate"),
    "S2": ("생성", "작성", "편집", "수정", "커밋", "마이그레이션", "배포", "적용", "등록", "갱신",
           "create", "write", "edit", "modify", "commit", "migrate", "deploy", "apply", "register", "update"),
    "S3": ("웹", "외부 API", "스크래핑", "크롤링", "검색 엔진", "fetch", "페이지", "URL",
           "web", "external API", "scrape", "crawl", "search engine", "page", "HTTP"),
    "S4": ("DB", "데이터베이스", "쿼리", "스키마", "마이그레이션", "테이블", "인덱스", "JOIN",
           "database", "query", "schema", "migration", "table", "index", "SQL"),
    "S5": ("PR", "issue", "리뷰", "CI", "CD", "릴리즈", "브랜치", "머지", "커밋 그래프", "워크플로우",
           "review", "release", "branch", "merge", "pipeline", "workflow"),
    "S6": ("단계별", "추론", "사고 과정", "장기 메모리", "시간", "타임존", "KG", "지식 그래프",
           "step-by-step", "reasoning", "chain-of-thought", "long-term memory", "time", "timezone", "knowledge graph"),
    "S7": ("모델", "학습", "평가", "하이퍼파라미터", "실험 추적", "inference", "feature", "dataset", "라벨", "분류", "회귀", "추천",
           "model", "training", "evaluation", "hyperparameter", "experiment tracking", "label", "classification", "regression", "recommendation"),
    "S8": ("배포", "CI/CD", "인프라", "모니터링", "Kubernetes", "k8s", "Terraform", "SRE", "oncall", "롤백", "helm", "IaC", "observability",
           "deploy", "infrastructure", "monitoring", "rollback"),
    "S9": ("iOS", "Android", "Swift", "Kotlin", "Flutter", "React Native", "Xcode", "Gradle", "emulator", "build",
           "IPA", "APK", "모바일", "mobile"),
    "S10": ("ETL", "ELT", "data pipeline", "Airflow", "dbt", "Spark", "스키마 변환", "data warehouse", "data lake", "ingestion", "lineage", "DAG",
            "schema transform"),
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


def _normalize_perm_token(tok: str) -> str:
    """permission/tool 토큰을 비교용 base name으로 정규화.

    `Bash(rm:*)` → `bash`, `mcp__github__create_issue` → `mcp__github__create_issue`.
    소문자화 + 첫 `(`까지의 prefix만 추출.
    """
    base = tok.split("(", 1)[0].strip()
    return base.lower()


def check_agent_tools_vs_settings(valid_perms: set[str]) -> list[str]:
    errors: list[str] = []
    if not AGENTS_DIR.exists():
        return errors

    norm_perms = {_normalize_perm_token(p) for p in valid_perms}

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
            base = _normalize_perm_token(tool)
            if base in {"read", "write", "edit", "glob", "grep", "bash", "powershell"}:
                continue
            if base.startswith("websearch") or base.startswith("webfetch"):
                continue
            if not norm_perms:
                continue
            if base not in norm_perms:
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

    A = pa + '*' + sa, B = pb + '*' + sb일 때 동일 S에 매칭되려면:
      - S가 양쪽 prefix 시작 (한 prefix는 다른 prefix를 포함하는 시작이어야 함)
      - S가 양쪽 suffix 끝 (한 suffix는 다른 suffix를 포함하는 끝이어야 함)
      - lp + ls가 단일 S에서 충돌하지 않음 (`*` ≥ 0 char이므로 |S| ≥ |lp|+|ls| 항상 가능)
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


_RUNTIME_GATE_START = "<!-- RUNTIME-GATE:start -->"
_RUNTIME_GATE_END = "<!-- RUNTIME-GATE:end -->"


def check_runtime_gate_block() -> list[str]:
    """S17 doctrine — derived 오케스트레이터에 Runtime Gate 블록 마커 정합 (2026-05-30 runtime 기초).

    dharness가 합성하는 오케스트레이터는 런타임 의사결정 스캐폴드(규모분류/plan분해/산출물생성)를
    `<!-- RUNTIME-GATE:start -->` … `<!-- RUNTIME-GATE:end -->` 1쌍으로 박제해야 한다.
    단일 출처: references/runtime-execution.md §1. plugin-only repo(derived 오케스트레이터 부재)는
    silent skip — dharness 자체는 빌드타임 팩토리라 게이트를 보유하지 않는다.
    """
    errors: list[str] = []
    orch = find_orchestrator()
    if not orch:
        return errors
    try:
        text = orch.read_text(encoding="utf-8-sig")
    except OSError:
        return errors
    rel = orch.relative_to(REPO_ROOT)
    n_start = text.count(_RUNTIME_GATE_START)
    n_end = text.count(_RUNTIME_GATE_END)
    if n_start == 0 or n_end == 0:
        errors.append(
            f"{rel}: Runtime Gate 블록 마커 부재 "
            f"(`{_RUNTIME_GATE_START}`…`{_RUNTIME_GATE_END}`) — S17 (runtime-execution.md §1)"
        )
        return errors
    if n_start != 1 or n_end != 1:
        errors.append(f"{rel}: Runtime Gate 마커 쌍이 정확히 1쌍이 아님 — S17")
        return errors
    si = text.find(_RUNTIME_GATE_START)
    ei = text.find(_RUNTIME_GATE_END)
    if si > ei:
        errors.append(f"{rel}: Runtime Gate 마커 순서 역전 (start가 end보다 뒤) — S17")
        return errors
    block = text[si:ei + len(_RUNTIME_GATE_END)]
    missing = [g for g in ("G1", "G2", "G3") if g not in block]
    if missing:
        errors.append(
            f"{rel}: Runtime Gate 스캐폴드 불완전 — 게이트 식별자 {missing} 누락 "
            f"(G1 규모분류/G2 plan/G3 산출물, runtime-execution.md §1) — S17"
        )
    return errors


_WIKI_CANDIDATE_FIXTURE = PLUGIN_REFERENCES_DIR / "fixtures" / "wiki_candidate_example"
_WIKI_CANDIDATE_FM_FIELDS = (
    "name", "description", "skill_kind", "candidate_version",
    "gap_source", "static_tier", "llm_judge_tier", "mc_tier", "promoted_to",
)


def check_wiki_candidate_schema() -> list[str]:
    """S18 doctrine — wiki bridge Emit candidate contract 정합 (2026-05-30 runtime wiki 다리).

    dharness가 합성 reusable skill을 로컬 harness wiki `candidates/<name>-v<N>/`로 Emit 할 때의
    contract(SKILL.md frontmatter + eval-results.json + changelog.md)를 결정적 강제(M5 schema gate).
    fixture-anchored — canonical 산출물 `fixtures/wiki_candidate_example/`를 검증하며 실제 Emit
    candidate도 동일 gate를 통과해야 한다. 단일 출처: references/wiki-bridge.md.
    fixture 부재(외부 install·미동봉)는 silent skip.
    """
    errors: list[str] = []
    base = _WIKI_CANDIDATE_FIXTURE
    if not base.is_dir():
        return errors
    rel = base.relative_to(REPO_ROOT)
    skill_md = base / "SKILL.md"
    eval_json = base / "eval-results.json"
    changelog = base / "changelog.md"
    for f in (skill_md, eval_json, changelog):
        if not f.is_file():
            errors.append(f"{rel}: wiki candidate 필수 파일 부재 `{f.name}` — S18 (wiki-bridge.md §1)")
    if errors:
        return errors
    # SKILL.md frontmatter 필수 필드 (wiki-bridge.md §1-a)
    try:
        fm = _extract_frontmatter_block(skill_md.read_text(encoding="utf-8-sig")) or ""
    except OSError:
        return errors
    skill_ver: int | None = None
    for field in _WIKI_CANDIDATE_FM_FIELDS:
        m = re.search(rf"^\s*{field}\s*:\s*(.+)$", fm, re.MULTILINE)
        if not m:
            errors.append(
                f"{rel}/SKILL.md: candidate frontmatter 필수 필드 `{field}` 누락 — S18 (wiki-bridge.md §1-a)"
            )
            continue
        val = _strip_quotes(m.group(1).strip())
        if field == "skill_kind" and val == "internal-capability":
            errors.append(
                f"{rel}/SKILL.md: candidate `skill_kind: internal-capability` 금지 (wiki rule 3-a) — S18"
            )
        if field == "candidate_version":
            if not val.isdigit():
                errors.append(f"{rel}/SKILL.md: `candidate_version`은 정수여야 함 (got `{val}`) — S18")
            else:
                skill_ver = int(val)
    # eval-results.json shape (wiki-bridge.md §1-b)
    try:
        data = json.loads(eval_json.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{rel}/eval-results.json: 유효 JSON 아님 ({exc}) — S18 (wiki-bridge.md §1-b)")
        return errors
    for key in ("candidate_slug", "candidate_version", "gap_source", "evals", "promotion"):
        if key not in data:
            errors.append(f"{rel}/eval-results.json: 필수 키 `{key}` 누락 — S18 (wiki-bridge.md §1-b)")
    evals = data.get("evals")
    if isinstance(evals, dict):
        for tier in ("static", "llm_judge", "monte_carlo"):
            if tier not in evals:
                errors.append(f"{rel}/eval-results.json: `evals.{tier}` 누락 — S18")
    elif "evals" in data:
        errors.append(f"{rel}/eval-results.json: `evals`는 object여야 함 — S18")
    json_ver = data.get("candidate_version")
    if not isinstance(json_ver, int):
        errors.append(f"{rel}/eval-results.json: `candidate_version`은 정수여야 함 (got {json_ver!r}) — S18")
    elif skill_ver is not None and json_ver != skill_ver:
        errors.append(
            f"{rel}: candidate_version 불일치 — SKILL.md {skill_ver} ≠ eval-results.json {json_ver} "
            f"(M5 cross-field) — S18"
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
        # description: 라인의 들여쓰기 (보통 0). block은 이보다 깊은 들여쓰기 라인 누적.
        desc_indent = len(line) - len(line.lstrip(" "))
        raw = m.group(1).strip()
        # YAML block scalar — 다음 들여쓰기 라인들 join
        if raw in ("|", ">", "|-", ">-", "|+", ">+"):
            collected: list[str] = []
            block_indent: int | None = None
            for sub in lines[i + 1:]:
                if not sub.strip():
                    collected.append("")
                    continue
                sub_indent = len(sub) - len(sub.lstrip(" "))
                # block의 indent는 첫 content 라인이 결정. 이후 라인이 더 얕으면 block 종료.
                if block_indent is None:
                    if sub_indent <= desc_indent:
                        break
                    block_indent = sub_indent
                elif sub_indent <= desc_indent:
                    break
                collected.append(sub[block_indent:] if sub_indent >= block_indent else sub.strip())
            # trailing empty lines strip (folded/literal 양쪽 동일 처리)
            while collected and not collected[-1].strip():
                collected.pop()
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


_ALLOWED_AGENT_MODELS = {"opus", "sonnet", "haiku"}


def check_agent_model_field() -> list[str]:
    """frontmatter `model:` 필드 박제 + enum 검증 (Q2 doctrine, permission-profiles-synthesis.md §5-1-c).

    필드 부재 + 허용 외 값(`opus`/`sonnet`/`haiku` 외) 모두 FAIL.
    quoted 값(`"opus"`, `'opus'`)도 같은 enum으로 정규화.
    """
    errors: list[str] = []
    if not AGENTS_DIR.exists():
        return errors
    pattern = re.compile(r"^\s*model\s*:\s*['\"]?([\w-]+)['\"]?\s*$", re.MULTILINE)
    for path in AGENTS_DIR.glob("*.md"):
        rel = str(path.relative_to(REPO_ROOT))
        try:
            text = path.read_text(encoding="utf-8-sig")
        except OSError:
            continue
        fm = _extract_frontmatter_block(text)
        if not fm:
            continue
        m = pattern.search(fm)
        if not m:
            errors.append(
                f"{rel}: frontmatter `model:` 필드 누락 (Q2 doctrine — opus/sonnet/haiku 명시 필수)"
            )
            continue
        value = m.group(1).lower()
        if value not in _ALLOWED_AGENT_MODELS:
            errors.append(
                f"{rel}: frontmatter `model: {value}` 허용 외 값 — "
                f"opus/sonnet/haiku 중 하나여야 함 (permission-profiles-synthesis.md §5-1-c)"
            )
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


def _classify_external_tool(token: str) -> str | None:
    """tool token → external surface category. external이면 category 반환, 아니면 None.

    A1 fix (audit2 2026-05-27): `mcp__*` 도구는 분류 누락 (이전 코드는 `split("__", 1)[0]` →
    literal `"mcp"` → EXTERNAL_INPUT_TOOLS 미매칭 → mcp surface 보유 에이전트가 가드 절 없어도
    PASS 되는 silent bypass. mcp prefix 검출 분기 명시화.
    """
    norm = token.strip().lower()
    if norm.startswith("mcp__"):
        return "mcp"
    head = norm.split("(", 1)[0].split("__", 1)[0]
    if head in EXTERNAL_INPUT_TOOLS:
        return head
    return None
INJECTION_GUARD_PATTERN = re.compile(
    r"입력\s*신뢰\s*경계|프롬프트\s*인젝션|인젝션\s*방어|injection\s*guard|untrusted\s*input|prompt\s*injection",
    re.IGNORECASE,
)
# PD4 — 가드 절 본문 semantic 검증. 절 anchor 이후 본문에서 distinct keyword ≥2 매칭 요구.
# 단순 boilerplate 복붙 차단 (heading만 박제 + 빈 본문 회피).
_INJECTION_SEMANTIC_KEYWORDS = (
    re.compile(r"untrusted", re.IGNORECASE),
    re.compile(r"injection", re.IGNORECASE),
    re.compile(r"프롬프트"),
    re.compile(r"sanitize", re.IGNORECASE),
    re.compile(r"validate", re.IGNORECASE),
    re.compile(r"신뢰\s*경계"),
    re.compile(r"검증"),
)
# 가드 절 본문 추출 — anchor 매치 위치 이후 다음 heading (`##` 또는 `---`) 또는 ~800 char까지.
_NEXT_HEADING_RE = re.compile(r"^\s*##\s|^\s*---\s*$", re.MULTILINE)


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
            held = sorted({c for c in (_classify_external_tool(t) for t in tools) if c})
            if not held:
                continue
            surface = ", ".join(held)
        else:
            # `tools:` 필드 부재 = 전체 도구 상속 (Bash/Write 포함) — 인젝션 표면 존재
            surface = "tools: 필드 부재 → 전체 도구 상속"
        body = text.split("---", 2)[-1] if text.lstrip().startswith("---") else text
        anchor = INJECTION_GUARD_PATTERN.search(body)
        if not anchor:
            errors.append(
                f"{rel}: 외부 입력·부작용 도구 보유({surface})하나 본문 인젝션 방어 절 부재 "
                f"— '입력 신뢰 경계' 섹션 박제 필수 (N-C-1 doctrine)"
            )
            continue
        # PD4 semantic gate — anchor 이후 가드 절 본문에서 distinct keyword ≥2 매칭.
        rest = body[anchor.end():]
        next_h = _NEXT_HEADING_RE.search(rest)
        section_body = rest[: next_h.start()] if next_h else rest[:800]
        matched = sum(1 for kw in _INJECTION_SEMANTIC_KEYWORDS if kw.search(section_body))
        if matched < 2:
            errors.append(
                f"{rel}: 외부 입력·부작용 도구 보유({surface}) 가드 절 박제됐으나 본문 semantic 키워드 부족 "
                f"(matched={matched}, 요구 ≥2 of untrusted/injection/프롬프트/sanitize/validate/신뢰 경계/검증) "
                f"— boilerplate 복붙 의심 (PD4)"
            )
    return errors


# Korean stopword set — dharness 도메인 공통 어휘. trigger 충돌 신호 아님 (PA11).
# 8 stopword에서 추출된 2-gram이 description 유사도를 부풀려 false positive 양산.
_KO_STOPWORDS: frozenset[str] = frozenset({
    "에이전트", "스킬", "검증", "관리", "도구", "하네스", "오케스트", "프로젝트",
})


def _build_ko_stopword_bigrams(words: frozenset[str]) -> frozenset[str]:
    bigrams: set[str] = set()
    for w in words:
        if len(w) == 2:
            bigrams.add(w)
        else:
            for k in range(len(w) - 1):
                bigrams.add(w[k:k + 2])
    return frozenset(bigrams)


_KO_STOPWORD_BIGRAMS: frozenset[str] = _build_ko_stopword_bigrams(_KO_STOPWORDS)


def _tokenize_description(desc: str) -> set[str]:
    """description에서 trigger 키워드 후보 토큰화.

    영문/숫자: word 단위 (소문자 정규화).
    한글: 2-gram character n-gram만 사용 — Korean은 word boundary가 의미와 어긋나
    (`데이터` ↔ `데이터베이스`처럼 substring 관계 흔함), word 단위는 검출 불가.
    n-gram 토큰은 `kg2:` prefix로 영문 word 토큰과 namespace 분리.
    한글 stopword set의 2-gram은 제외 (PA11 — 도메인 공통 어휘 false positive 차단).
    """
    tokens: set[str] = set()
    for w in re.findall(r"[A-Za-z][A-Za-z0-9_-]+", desc):
        if len(w) >= 2:
            tokens.add(w.lower())
    for block in re.findall(r"[가-힣]{2,}", desc):
        for k in range(len(block) - 1):
            bg = block[k:k + 2]
            if bg in _KO_STOPWORD_BIGRAMS:
                continue
            tokens.add(f"kg2:{bg}")
    return tokens


def check_skill_description_overlap(threshold: float = 0.65) -> list[str]:
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
                kw_l = kw.lower()
                # ASCII 키워드는 word boundary 필요 — `inspect` ≠ `inspector`.
                # 한글은 word boundary 효력 없음 — substring 매칭 + min len 3 (1~2자 noise 차단).
                if re.search(r"[A-Za-z]", kw_l):
                    if re.search(rf"\b{re.escape(kw_l)}\b", desc_lower):
                        hit_signals.append(signal_id)
                        break
                else:
                    if len(kw_l) >= 3 and kw_l in desc_lower:
                        hit_signals.append(signal_id)
                        break
        if not hit_signals:
            errors.append(
                f"{rel}: description이 trigger-keyword-catalog 10 signal 어느 것도 hit 안 함 (Q11 signal coverage 0) — 트리거 약함"
            )
    return errors


# W3 doctrine (phase-entry-gates.md:§Phase 2). 5필드 모두 사용자 raw 답변으로
# meta.user_confirmed_fields 등록 필수. brownfield 자동 추론도 사용자 확인 답변
# 받아야 user_confirmed_fields 등록 — inferred_fields 등록만으로 doctrine 불충족.
# 정본은 schema.py:INTENT_REQUIRED_USER_CONFIRMED — 본 alias로 의도 명시.
# 2026-05-28 audit2 PA8: INTENT_REQUIRED 6필드로 격상되며 meta.dharness_version은
# LLM 박제 (I2 doctrine), 사용자 raw 답변 불요 → alias는 USER_CONFIRMED 5만 포함.
_INTENT_USER_CONFIRMED_REQUIRED = tuple(INTENT_REQUIRED_USER_CONFIRMED)


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


# R6 self-host (chain_registry.py로 fn 분할, sub-cycle ζ) — path constant는 chain.py 잔류:
# chain_doc_sync.py/chain_registry.py에서 chain._DOCTRINE_REGISTRY 참조 + test_chain monkey-patch 호환.
_DOCTRINE_REGISTRY = PLUGIN_REFERENCES_DIR / "doctrine-registry.md"
_VALIDATE_DIR = Path(__file__).resolve().parent


# chain_intent.py 분할 (2026-05-25):
#   - W9 4 fn (cycle 6+ MVP)
#   - W3 2 fn + helper (sub-cycle α 흡수)
# main()에서 호출 시 chain_intent module에서 re-export — backward compat 위해 import.
from chain_intent import (  # noqa: E402
    check_intent_profile_brownfield_inferred,
    check_intent_profile_greenfield_locked_in,
    check_intent_profile_grilling_log,
    check_intent_profile_project_type,
    check_intent_profile_version,
    check_intent_required_doc_sync,
    check_required_user_confirmed_fields,
)
from chain_version import check_dharness_version_drift  # noqa: E402
from chain_doc_sync import (  # noqa: E402
    check_command_count_sync,
    check_output_checklist_count_sync,
    check_phase_count_sync,
    check_trigger_catalog_python_sync,
)


from chain_advisor import check_advisor_handoff_adapter_consistency  # noqa: E402
from chain_registry import (  # noqa: E402
    check_doctrine_registry_fn_refs,
    check_doctrine_registry_inverse_index,
)


def find_orchestrator() -> Path | None:
    if not SKILLS_DIR.exists():
        return None
    # FS iteration 순서는 비결정적 — sorted()로 박제. 다중 orchestrator-named 디렉토리가 있어도 결정적 첫 매치.
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
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


def _parse_only_flag(argv: list[str]) -> set[str] | None:
    """--only <name>[,<name>...] flag 파싱. 미지정 시 None (전체 실행)."""
    for i, a in enumerate(argv):
        if a == "--only" and i + 1 < len(argv):
            return {n.strip() for n in argv[i + 1].split(",") if n.strip()}
        if a.startswith("--only="):
            return {n.strip() for n in a.split("=", 1)[1].split(",") if n.strip()}
    return None


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    strict = "--strict" in argv
    only = _parse_only_flag(argv)

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

    # check 이름 → callable 매핑. `--only <name>` flag 미지정 시 전체 실행.
    checks: list[tuple[str, callable]] = [
        ("check_orchestrator_dangling", lambda: find_dangling_in_orchestrator(
            find_orchestrator(), valid_agents, valid_skills) if find_orchestrator() else []),
        ("check_agent_tools_vs_settings", lambda: check_agent_tools_vs_settings(valid_perms)),
        ("check_agent_name_uniqueness", check_agent_name_uniqueness),
        ("check_agent_write_path_overlap", check_agent_write_path_overlap),
        ("check_orchestrator_agent_coverage", check_orchestrator_agent_coverage),
        ("check_runtime_gate_block", check_runtime_gate_block),
        ("check_wiki_candidate_schema", check_wiki_candidate_schema),
        ("check_skill_name_uniqueness", check_skill_name_uniqueness),
        ("check_reference_links", check_reference_links),
        ("check_plugin_internal_references", check_plugin_internal_references),
        ("check_agent_tools_mcp_consistency", check_agent_tools_mcp_consistency),
        ("check_agent_model_field", check_agent_model_field),
        ("check_agent_injection_guard", check_agent_injection_guard),
        ("check_skill_description_overlap", check_skill_description_overlap),
        ("check_skill_signal_coverage", check_skill_signal_coverage),
        ("check_intent_profile_grilling_log", check_intent_profile_grilling_log),
        ("check_required_user_confirmed_fields", check_required_user_confirmed_fields),
        ("check_doctrine_registry_fn_refs", check_doctrine_registry_fn_refs),
        ("check_doctrine_registry_inverse_index", check_doctrine_registry_inverse_index),
        ("check_intent_required_doc_sync", check_intent_required_doc_sync),
        ("check_output_checklist_count_sync", check_output_checklist_count_sync),
        ("check_command_count_sync", check_command_count_sync),
        ("check_trigger_catalog_python_sync", check_trigger_catalog_python_sync),
        ("check_phase_count_sync", check_phase_count_sync),
        ("check_intent_profile_version", check_intent_profile_version),
        ("check_intent_profile_project_type", check_intent_profile_project_type),
        ("check_intent_profile_brownfield_inferred", check_intent_profile_brownfield_inferred),
        ("check_intent_profile_greenfield_locked_in", check_intent_profile_greenfield_locked_in),
        ("check_advisor_handoff_adapter_consistency", check_advisor_handoff_adapter_consistency),
    ]
    known = {name for name, _ in checks}
    if only:
        unknown = only - known
        if unknown:
            msg = f"unknown check name(s): {sorted(unknown)} — known: {sorted(known)}"
            if as_json:
                print(json.dumps({"status": "precondition_fail", "error": msg}, ensure_ascii=False))
            else:
                print(f"❌ {msg}")
            return 2

    orch = find_orchestrator()
    errors: list[str] = []
    for name, fn in checks:
        if only and name not in only:
            continue
        errors.extend(fn())

    version_drift = check_dharness_version_drift() if not only else {"message": None}

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
