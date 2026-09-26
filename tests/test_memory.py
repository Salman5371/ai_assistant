import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from ai import memory


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.legacy = self.path / "memory.txt"
        self.store = memory.MemoryStore(self.path / "memory.sqlite3", self.legacy)

    def test_legacy_import_once_and_preserve_backup(self):
        self.legacy.write_text("Original Case!\nSecond memory\n", encoding="utf-8")
        first = self.store.list()
        self.assertEqual(len(first), 2)
        self.assertEqual(first[0]["source"], "legacy_import")
        self.assertTrue(first[0]["created_at"].endswith("+00:00"))
        self.assertEqual(self.store.list(), first)
        self.assertIn("Original Case!", self.legacy.read_text())
        self.store.clear()
        self.assertEqual(self.store.list(), [])

    def test_parameterized_storage_and_empty_validation(self):
        text = "Robert'); DROP TABLE memories;--"
        self.store.add(text)
        self.assertEqual(self.store.list()[0]["content"], text)
        self.assertEqual(self.store.list()[0]["source"], "user")
        with self.assertRaises(ValueError):
            self.store.add(" ")

    def test_existing_commands_use_sqlite(self):
        with patch.dict("os.environ", {"ASSISTANT_MEMORY_DB": str(self.store.path)}), patch.object(memory, "MEMORY_FILE", self.legacy):
            self.assertIn("don't remember", memory.read_memory())
            memory.save_memory("Meet Alice at 5:30!")
            self.assertEqual(memory.read_memory(), "Meet Alice at 5:30!")
            memory.clear_memory()
            self.assertIn("don't remember", memory.read_memory())

    def test_bad_legacy_file_rolls_back_marker(self):
        self.legacy.write_bytes(b"\xff")
        with self.assertRaises(UnicodeDecodeError):
            self.store.list()
        self.legacy.write_text("Recovered", encoding="utf-8")
        self.assertEqual(len(self.store.list()), 1)

    def test_separate_connections_persist(self):
        self.store.add("one")
        other = memory.MemoryStore(self.store.path, self.legacy)
        other.add("two")
        self.assertEqual([row["content"] for row in self.store.list()], ["one", "two"])
