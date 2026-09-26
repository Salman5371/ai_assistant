"""Private SQLite memory with one-time, transactional legacy text import."""
from contextlib import contextmanager
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_FILE = BASE_DIR / "memory.txt"


def database_path():
    return Path(os.environ.get("ASSISTANT_MEMORY_DB", str(BASE_DIR / "data" / "memory.sqlite3"))).expanduser()


class MemoryStore:
    def __init__(self, path=None, legacy_path=None):
        self.path = Path(path) if path is not None else database_path()
        self.legacy_path = Path(legacy_path) if legacy_path is not None else MEMORY_FILE

    @contextmanager
    def _connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY, content TEXT NOT NULL, created_at TEXT NOT NULL, source TEXT NOT NULL)")
                connection.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                imported = connection.execute("SELECT value FROM metadata WHERE key = 'legacy_import_v1'").fetchone()
                if imported is None:
                    # The old file is preserved as a backup. Unknown original times
                    # are represented by the import timestamp, not invented dates.
                    lines = self.legacy_path.read_text(encoding="utf-8-sig").splitlines() if self.legacy_path.exists() else []
                    timestamp = datetime.now(timezone.utc).isoformat()
                    connection.executemany("INSERT INTO memories(content, created_at, source) VALUES (?, ?, ?)",
                        [(line.strip(), timestamp, "legacy_import") for line in lines if line.strip()])
                    connection.execute("INSERT INTO metadata(key, value) VALUES ('legacy_import_v1', ?)", (timestamp,))
                yield connection
        finally:
            connection.close()

    def add(self, text):
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Memory must be nonempty text")
        with self._connect() as connection:
            cursor = connection.execute("INSERT INTO memories(content, created_at, source) VALUES (?, ?, ?)",
                (text.strip(), datetime.now(timezone.utc).isoformat(), "user"))
            return cursor.lastrowid

    def list(self):
        with self._connect() as connection:
            return [dict(row) for row in connection.execute("SELECT id, content, created_at, source FROM memories ORDER BY id")]

    def clear(self):
        with self._connect() as connection:
            connection.execute("DELETE FROM memories")


def save_memory(text):
    MemoryStore().add(text)
    return "I have saved that in memory."


def read_memory():
    records = MemoryStore().list()
    return "\n".join(record["content"] for record in records) if records else "I don't remember anything yet."


def clear_memory():
    MemoryStore().clear()
    return "Memory has been cleared."
