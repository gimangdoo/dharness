"""hook 테스트 공통 fixture — tmp_root 기반 path patching + DB·디렉토리 격리.

3 hook (session_start/post_tool_use/session_end) + cm_commands는 import 시점에
_schema.REPO_ROOT / DB_PATH 등을 자기 모듈로 binding 한다. 단순 patch.object로는
이미 binding 된 값을 잡지 못하므로, _schema 모듈 attr을 tmp 경로로 재설정 후
hook 모듈을 importlib.reload 한다 (재import 시 patched 값 다시 가져옴).

사용:
    class MyTest(HookTestBase):
        def test_x(self):
            # self.tmp_root, self.db_path 등 사용 가능
            ...
"""

from __future__ import annotations

import importlib
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _schema  # noqa: E402


HOOK_MODULES = ("session_start", "post_tool_use", "session_end", "cm_commands")


def _apply_tmp_paths(tmp_root: Path) -> None:
    """_schema 모듈의 path 상수를 tmp_root 기반으로 재설정."""
    _schema.REPO_ROOT = tmp_root
    _schema.MEMORY_ROOT = tmp_root / "_workspace" / "_memory"
    _schema.DB_PATH = _schema.MEMORY_ROOT / "observations" / "observations.db"
    _schema.TELEMETRY_DIR = tmp_root / "_workspace" / "_telemetry"
    _schema.TOOL_OUTPUTS = tmp_root / "_workspace" / "_tool_outputs"
    _schema.DRAFTS_DIR = tmp_root / "_workspace" / "_drafts"
    _schema.DRAFTS_APPLIED = _schema.DRAFTS_DIR / "applied"
    _schema.DRAFTS_DISCARDED = _schema.DRAFTS_DIR / "discarded"
    _schema.SESSION_ID_FILE = _schema.MEMORY_ROOT / ".current_session"
    _schema.CLAUDE_MD = tmp_root / "CLAUDE.md"
    _schema.CHANGELOG_MD = tmp_root / "CHANGELOG.md"
    _schema.LAST_ADAPT_FILE = _schema.TELEMETRY_DIR / "_last_adapt"


def _reload_hooks() -> dict:
    """hook 모듈을 재import해 patched _schema 값으로 binding 갱신."""
    loaded: dict = {}
    for name in HOOK_MODULES:
        if name in sys.modules:
            loaded[name] = importlib.reload(sys.modules[name])
        else:
            loaded[name] = importlib.import_module(name)
    return loaded


class HookTestBase(unittest.TestCase):
    """tmp_root + DB 부트스트랩 + hook 모듈 reload 자동화 base class."""

    _ORIG_PATHS: dict = {}

    @classmethod
    def setUpClass(cls):
        # 원래 _schema 값 백업 (모든 테스트 종료 후 복원).
        cls._ORIG_PATHS = {
            attr: getattr(_schema, attr)
            for attr in (
                "REPO_ROOT", "MEMORY_ROOT", "DB_PATH", "TELEMETRY_DIR",
                "TOOL_OUTPUTS", "DRAFTS_DIR", "DRAFTS_APPLIED", "DRAFTS_DISCARDED",
                "SESSION_ID_FILE", "CLAUDE_MD", "CHANGELOG_MD", "LAST_ADAPT_FILE",
            )
        }

    @classmethod
    def tearDownClass(cls):
        for attr, val in cls._ORIG_PATHS.items():
            setattr(_schema, attr, val)
        _reload_hooks()

    def setUp(self):
        # Windows: SQLite 핸들이 잔존할 수 있어 ignore_cleanup_errors 필요.
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.tmp_root = Path(self._tmp.name)
        _apply_tmp_paths(self.tmp_root)
        # DB 부트스트랩 (각 테스트 fresh). sqlite3 `with`는 commit/rollback만 처리
        # — close는 명시적이어야 Windows file lock 회피 가능.
        _schema.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(_schema.DB_PATH)
        try:
            conn.executescript(_schema.DDL)
        finally:
            conn.close()
        _schema.MEMORY_ROOT.mkdir(parents=True, exist_ok=True)
        _schema.TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
        _schema.DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        self.hooks = _reload_hooks()

    def tearDown(self):
        import gc
        gc.collect()  # 누수된 sqlite Connection finalize 유도 (Windows file lock 회피).
        self._tmp.cleanup()

    # ----- helpers -----

    def write_session_id(self, sid: str) -> None:
        _schema.SESSION_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
        _schema.SESSION_ID_FILE.write_text(sid, encoding="utf-8")

    def insert_session(self, sid: str, started_at: str = "2026-05-23T00:00:00Z",
                       date: str = "2026-05-23", ended_at: str | None = None) -> None:
        conn = sqlite3.connect(_schema.DB_PATH)
        try:
            conn.execute(
                "INSERT INTO sessions (session_id, date, started_at, ended_at, project) "
                "VALUES (?, ?, ?, ?, 'test')",
                (sid, date, started_at, ended_at),
            )
            conn.commit()
        finally:
            conn.close()

    def insert_observation(self, sid: str, category: str,
                           artifact_kind: str = "skill",
                           content: str = "Edit plugins/harness/skills/harness/SKILL.md",
                           date: str = "2026-05-23") -> None:
        import json as _json
        import uuid as _uuid
        conn = sqlite3.connect(_schema.DB_PATH)
        try:
            conn.execute(
                "INSERT INTO observations "
                "(id, session_id, date, section, content, tags, created_at, category, artifact_kind) "
                "VALUES (?, ?, ?, 'dharness_event', ?, ?, '2026-05-23T00:00:00Z', ?, ?)",
                (f"{sid}-{_uuid.uuid4().hex[:8]}", sid, date, content, _json.dumps([]), category, artifact_kind),
            )
            conn.commit()
        finally:
            conn.close()
