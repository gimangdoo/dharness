"""Phase 1 patch (PC1~PC8) 회귀 테스트.

각 패치의 외관적 행동(WAL pragmas, migration marker, atomic write, sid regex,
hook crash telemetry, DROP COLUMN unsupported short-circuit)을 격리 검증한다.
"""

from __future__ import annotations

import io
import json
import sqlite3
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import _schema
from _test_fixtures import HookTestBase


class TestGetConnPragmas(HookTestBase):
    """PC1: _get_conn()이 WAL + busy_timeout + synchronous=NORMAL 적용."""

    def test_pragmas_applied(self):
        conn = _schema._get_conn()
        try:
            self.assertEqual(
                conn.execute("PRAGMA journal_mode").fetchone()[0].lower(),
                "wal",
            )
            self.assertEqual(
                conn.execute("PRAGMA busy_timeout").fetchone()[0],
                5000,
            )
            # synchronous=NORMAL == 1
            self.assertEqual(
                conn.execute("PRAGMA synchronous").fetchone()[0],
                1,
            )
        finally:
            conn.close()


class TestMigrationMarker(HookTestBase):
    """PC3·PC8: marker로 ensure_migrations short-circuit + version bump 일관성."""

    def test_marker_short_circuits_work(self):
        # marker가 있으면 ensure_migrations는 schema 조회조차 안 함.
        # 검증: observations 테이블을 의도적으로 망가뜨려도 ensure_migrations는 무사통과.
        conn = _schema._get_conn()
        try:
            conn.execute("DROP TABLE observations")
            conn.commit()
        finally:
            conn.close()

        _schema.MIGRATION_MARKER.parent.mkdir(parents=True, exist_ok=True)
        _schema.MIGRATION_MARKER.touch()

        conn = _schema._get_conn()
        try:
            # marker 없으면 PRAGMA table_info(observations) → empty → version 갱신 시도.
            # marker 있으면 0번째 줄에서 즉시 return.
            changed = _schema.ensure_migrations(conn)
        finally:
            conn.close()
        self.assertEqual(changed, [])

    def test_marker_created_on_fresh_db(self):
        # Setup이 만든 fresh DB는 user_version=0 + empty obs_cols 분기로 가야 함.
        # 사실 setUp의 executescript(DDL)이 테이블을 만들었으므로 obs_cols 채워짐 →
        # ADD COLUMN 분기 시도 + 성공. marker 생성 확인.
        self.assertFalse(_schema.MIGRATION_MARKER.exists())
        conn = _schema._get_conn()
        try:
            _schema.ensure_migrations(conn)
        finally:
            conn.close()
        self.assertTrue(_schema.MIGRATION_MARKER.exists())

    def test_marker_created_on_empty_db(self):
        # observations 테이블 자체가 없는 DB.
        empty_db = self.tmp_root / "_workspace" / "_memory" / "empty.db"
        empty_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(empty_db)
        try:
            changed = _schema.ensure_migrations(conn)
        finally:
            conn.close()
        self.assertEqual(changed, [])
        self.assertTrue(_schema.MIGRATION_MARKER.exists())

    def test_drop_column_unsupported_skips_bump(self):
        # SQLite < 3.35 mock — marker도 생성하지 않고 version도 bump 안 함.
        # 기존 dead 컬럼이 있는 DB를 시뮬레이션해야 분기 진입.
        conn = _schema._get_conn()
        try:
            # v1 상태 시뮬레이션 — dead 컬럼 추가 후 user_version=1.
            conn.execute("ALTER TABLE observations ADD COLUMN embedding TEXT")
            conn.execute("PRAGMA user_version = 1")
            conn.commit()
        finally:
            conn.close()

        with patch.object(_schema, "_SQLITE_SUPPORTS_DROP_COLUMN", False):
            conn = _schema._get_conn()
            try:
                stderr_buf = io.StringIO()
                with redirect_stderr(stderr_buf):
                    _schema.ensure_migrations(conn)
                version = conn.execute("PRAGMA user_version").fetchone()[0]
            finally:
                conn.close()

        self.assertEqual(version, 1)  # bump 보류
        self.assertFalse(_schema.MIGRATION_MARKER.exists())
        self.assertIn("DROP COLUMN", stderr_buf.getvalue())


class TestAtomicSessionIdWrite(HookTestBase):
    """PC2: write_session_id가 tmp+os.replace로 atomic."""

    def test_no_tmp_leftover(self):
        _schema.write_session_id("abc123")
        self.assertEqual(_schema.SESSION_ID_FILE.read_text(encoding="utf-8"), "abc123")
        tmp = _schema.SESSION_ID_FILE.with_suffix(".tmp")
        self.assertFalse(tmp.exists())

    def test_overwrite_atomic(self):
        _schema.write_session_id("first1")
        _schema.write_session_id("second")
        self.assertEqual(_schema.SESSION_ID_FILE.read_text(encoding="utf-8"), "second")


class TestSidTraversalGuard(HookTestBase):
    """PC4: cm_commands._draft_for_session sid 검증 + traversal block."""

    def _draft_for_session(self, sid):
        cm = self.hooks["cm_commands"]
        return cm._draft_for_session(sid)

    def test_rejects_traversal(self):
        self.assertIsNone(self._draft_for_session("../etc/passwd"))

    def test_rejects_wildcard(self):
        self.assertIsNone(self._draft_for_session("*"))

    def test_rejects_separators(self):
        self.assertIsNone(self._draft_for_session("a/b"))
        self.assertIsNone(self._draft_for_session("a\\b"))

    def test_rejects_too_short(self):
        self.assertIsNone(self._draft_for_session("abc"))

    def test_rejects_too_long(self):
        self.assertIsNone(self._draft_for_session("a" * 33))

    def test_accepts_valid_sid_with_existing_draft(self):
        _schema.DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        draft = _schema.DRAFTS_DIR / "2026-05-27_abc123.md"
        draft.write_text("placeholder", encoding="utf-8")
        found = self._draft_for_session("abc123")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "2026-05-27_abc123.md")


class TestHookCrashTelemetry(HookTestBase):
    """PC5: post_tool_use main()이 uncaught 예외를 hook_crash로 telemetry append + exit 0."""

    def test_crash_emits_telemetry_returns_zero(self):
        ptu = self.hooks["post_tool_use"]
        with patch.object(ptu, "_main_impl", side_effect=RuntimeError("boom")):
            with redirect_stderr(io.StringIO()):
                rc = ptu.main()
        self.assertEqual(rc, 0)

        # telemetry에 hook_crash 라인 존재.
        files = list(_schema.TELEMETRY_DIR.glob("*.jsonl"))
        self.assertTrue(files, "telemetry file 생성 안 됨")
        events = []
        for f in files:
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(json.loads(line))
        crash = [e for e in events if e.get("type") == "hook_crash"]
        self.assertEqual(len(crash), 1)
        self.assertEqual(crash[0]["handler"], "post_tool_use.py")
        self.assertIn("RuntimeError", crash[0]["error"])
        self.assertIn("boom", crash[0]["error"])

    def test_clean_run_no_crash_event(self):
        # 정상 경로 — payload empty, session_id 미설정 → 즉시 return 0.
        ptu = self.hooks["post_tool_use"]
        with patch("sys.stdin", io.StringIO("{}")):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                rc = ptu.main()
        self.assertEqual(rc, 0)
        files = list(_schema.TELEMETRY_DIR.glob("*.jsonl"))
        for f in files:
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    evt = json.loads(line)
                    self.assertNotEqual(evt.get("type"), "hook_crash")


class TestSessionIdCollisionEscalation(HookTestBase):
    """PC2 보조: session_start의 INSERT OR IGNORE hex_len 에스컬레이션 유지 검증."""

    def test_escalates_on_collision(self):
        # 6자 hex 영역을 직접 채워 충돌 강제 — uuid.uuid4()가 동일 hex prefix 만들 확률은
        # 사실상 0이므로 monkeypatch로 첫 호출만 충돌 trigger.
        ss = self.hooks["session_start"]
        # 미리 6자 sid 한 개 점유.
        self.insert_session("aaaaaa", date="2026-05-27", started_at="2026-05-27T00:00:00Z")

        original_uuid = ss.uuid.uuid4
        call_count = {"n": 0}

        class _FakeUUID:
            def __init__(self, hex):
                self.hex = hex

        def fake_uuid4():
            call_count["n"] += 1
            if call_count["n"] == 1:
                return _FakeUUID("aaaaaa" + "0" * 26)  # hex[:6] == 'aaaaaa' → 충돌
            return original_uuid()

        with patch.object(ss.uuid, "uuid4", side_effect=fake_uuid4):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                with patch("sys.stdin", io.StringIO("{}")):
                    rc = ss.main()

        self.assertEqual(rc, 0)
        # 충돌 1번 + escalation 1번 = uuid4 최소 2회 호출.
        self.assertGreaterEqual(call_count["n"], 2)


if __name__ == "__main__":
    unittest.main()
