"""
Encrypted SQLite storage handler for digital-fasting-companion.

Uses AES-256-GCM via the cryptography library for field-level encryption
of sensitive behavioral data. Schema is initialized from config/schema.sql.

In production, this can be swapped with SQLCipher for full database-level
encryption, but the current approach ensures data is unreadable without
the encryption key using only pure-Python dependencies.
"""

import hashlib
import json
import logging
import os
import sqlite3
import threading
import uuid
from base64 import b64encode, b64decode
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)


class LocalDB:
    """
    AES-256-GCM encrypted SQLite database handler.

    Sensitive columns are encrypted before storage and decrypted on read.
    Non-sensitive metadata (timestamps, IDs) remains in plaintext for indexing.
    """

    def __init__(self, db_path: str, encryption_key: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        key_material = hashlib.sha256(encryption_key.encode("utf-8")).digest()
        self._cipher = AESGCM(key_material)

        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()

    def _encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self._cipher.encrypt(nonce, plaintext.encode("utf-8"), None)
        return b64encode(nonce + ciphertext).decode("ascii")

    def _decrypt(self, ciphertext: str) -> str:
        raw = b64decode(ciphertext.encode("ascii"))
        nonce, data = raw[:12], raw[12:]
        return self._cipher.decrypt(nonce, data, None).decode("utf-8")

    def connect(self) -> None:
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        logger.info("Connected to database: %s", self.db_path)

    def disconnect(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Disconnected from database")

    def init_schema(self, schema_path: str = "config/schema.sql") -> None:
        schema_file = Path(schema_path)
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        with open(schema_file, "r", encoding="utf-8") as f:
            sql = f.read()
        with self._lock:
            self._conn.executescript(sql)
            self._conn.commit()
        logger.info("Database schema initialized from %s", schema_path)

    # ── usage_sessions ────────────────────────────────────────────

    def insert_session(
        self,
        app_name: str,
        category: str,
        start_time: int,
        duration_seconds: int = 0,
        end_time: Optional[int] = None,
    ) -> str:
        session_id = uuid.uuid4().hex[:16]
        encrypted_app = self._encrypt(app_name)
        with self._lock:
            self._conn.execute(
                """INSERT INTO usage_sessions
                   (session_id, app_name, category, start_time, end_time, duration_seconds)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, encrypted_app, category, start_time, end_time or start_time + duration_seconds, duration_seconds),
            )
            self._conn.commit()
        return session_id

    def end_session(self, session_id: str) -> None:
        import time
        now = int(time.time())
        with self._lock:
            row = self._conn.execute(
                "SELECT start_time FROM usage_sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if row:
                duration = now - row["start_time"]
                self._conn.execute(
                    "UPDATE usage_sessions SET end_time = ?, duration_seconds = ? WHERE session_id = ?",
                    (now, duration, session_id),
                )
                self._conn.commit()

    def get_sessions(self, category: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        query = "SELECT * FROM usage_sessions"
        params: tuple = ()
        if category:
            query += " WHERE category = ?"
            params = (category,)
        query += " ORDER BY start_time DESC LIMIT ?"
        params = params + (limit,)
        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            try:
                d["app_name"] = self._decrypt(d["app_name"])
            except Exception:
                pass
            results.append(d)
        return results

    def get_category_today_minutes(self, category: str) -> int:
        import time
        today_start = int(time.time()) - (int(time.time()) % 86400)
        with self._lock:
            row = self._conn.execute(
                """SELECT COALESCE(SUM(duration_seconds), 0) AS total
                   FROM usage_sessions
                   WHERE category = ? AND start_time >= ?""",
                (category, today_start),
            ).fetchone()
        return row["total"] // 60 if row else 0

    # ── fatigue_events ────────────────────────────────────────────

    def insert_fatigue_event(
        self,
        event_type: str,
        fatigue_score: float,
        session_id: Optional[str] = None,
        trigger_category: Optional[str] = None,
    ) -> str:
        import time
        event_id = uuid.uuid4().hex[:16]
        now = int(time.time())
        with self._lock:
            self._conn.execute(
                """INSERT INTO fatigue_events
                   (event_id, event_type, fatigue_score, session_id, trigger_category, trigger_time)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (event_id, event_type, fatigue_score, session_id, trigger_category, now),
            )
            self._conn.commit()
        return event_id

    def resolve_fatigue_event(self, event_id: str, resolution_type: str) -> None:
        import time
        now = int(time.time())
        with self._lock:
            self._conn.execute(
                "UPDATE fatigue_events SET resolved_time = ?, resolution_type = ? WHERE event_id = ?",
                (now, resolution_type, event_id),
            )
            self._conn.commit()

    def get_recent_events(self, limit: int = 5) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM fatigue_events ORDER BY trigger_time DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    # ── challenges ─────────────────────────────────────────────────

    def insert_challenge(
        self,
        category: str,
        title: str,
        description: str,
        source: str,
        event_id: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> str:
        challenge_id = uuid.uuid4().hex[:16]
        encrypted_title = self._encrypt(title)
        encrypted_desc = self._encrypt(description)
        with self._lock:
            self._conn.execute(
                """INSERT INTO challenges
                   (challenge_id, event_id, category, title, description, source, prompt)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (challenge_id, event_id, category, encrypted_title, encrypted_desc, source, prompt),
            )
            self._conn.commit()
        return challenge_id

    def complete_challenge(self, challenge_id: str, rating: Optional[int] = None) -> None:
        import time
        now = int(time.time())
        with self._lock:
            self._conn.execute(
                "UPDATE challenges SET completed_at = ?, rating = ? WHERE challenge_id = ?",
                (now, rating, challenge_id),
            )
            self._conn.commit()

    def get_latest_challenge_category(self) -> Optional[str]:
        with self._lock:
            row = self._conn.execute(
                "SELECT category FROM challenges ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
        return row["category"] if row else None

    # ── recovery_log ───────────────────────────────────────────────

    def insert_recovery(
        self, event_id: str, challenge_id: Optional[str] = None
    ) -> None:
        import time
        now = int(time.time())
        with self._lock:
            self._conn.execute(
                """INSERT OR REPLACE INTO recovery_log (event_id, challenge_id, start_time)
                   VALUES (?, ?, ?)""",
                (event_id, challenge_id, now),
            )
            self._conn.commit()

    def complete_recovery(self, event_id: str, quality_score: Optional[float] = None) -> None:
        import time
        now = int(time.time())
        with self._lock:
            self._conn.execute(
                "UPDATE recovery_log SET end_time = ?, quality_score = ? WHERE event_id = ?",
                (now, quality_score, event_id),
            )
            self._conn.commit()

    # ── baseline ───────────────────────────────────────────────────

    def update_baseline_feature(self, feature_name: str, value: float, std_dev: float = 0):
        with self._lock:
            row = self._conn.execute(
                "SELECT sample_count FROM user_baseline WHERE feature_name = ?", (feature_name,)
            ).fetchone()
            if row:
                n = row["sample_count"] + 1
                self._conn.execute(
                    """UPDATE user_baseline
                       SET feature_value = ?, std_dev = ?, sample_count = ?
                       WHERE feature_name = ?""",
                    (value, std_dev, n, feature_name),
                )
            else:
                self._conn.execute(
                    """INSERT INTO user_baseline (feature_name, feature_value, std_dev, sample_count)
                       VALUES (?, ?, ?, 1)""",
                    (feature_name, value, std_dev),
                )
            self._conn.commit()

    def get_baseline(self) -> Dict[str, float]:
        with self._lock:
            rows = self._conn.execute("SELECT feature_name, feature_value FROM user_baseline").fetchall()
        return {r["feature_name"]: r["feature_value"] for r in rows}

    # ── settings ───────────────────────────────────────────────────

    def set_setting(self, key: str, value: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
            )
            self._conn.commit()

    def get_setting(self, key: str) -> Optional[str]:
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
        return row["value"] if row else None

    # ── export / delete ────────────────────────────────────────────

    def export_json(self, output_path: str) -> None:
        data = {
            "sessions": self.get_sessions(limit=10000),
            "fatigue_events": self.get_recent_events(limit=10000),
            "baseline": self.get_baseline(),
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info("Data exported to %s", output_path)

    def full_delete(self) -> None:
        with self._lock:
            tables = ["usage_sessions", "fatigue_events", "challenges", "recovery_log",
                       "user_baseline", "settings", "ml_checkpoints", "knowledge_crawl_log"]
            for table in tables:
                self._conn.execute(f"DELETE FROM {table}")
            self._conn.commit()
        logger.info("All data deleted from database")

    # ── context ────────────────────────────────────────────────────

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()


_db_instance: Optional[LocalDB] = None


def get_db() -> LocalDB:
    global _db_instance
    if _db_instance is None:
        from src.config.settings import get_settings
        s = get_settings()
        _db_instance = LocalDB(
            db_path=str(s.db_path_full),
            encryption_key=s.database.db_key or "default-dev-key-change-me",
        )
        _db_instance.connect()
        _db_instance.init_schema()
    return _db_instance
