import json
import os
import tempfile

from src.data_manager import DataManager


def test_data_manager_add_and_export(tmp_path, monkeypatch):
    # временная папка для данных
    data_file = tmp_path / "conversations.json"
    monkeypatch.chdir(tmp_path)

    dm = DataManager()
    # убедимся, что использует data/conversations.json
    assert os.path.basename(dm.data_file) == "conversations.json"

    dm.add_message("u1", "user", "user", "hello")
    dm.add_message("u1", "user", "assistant", "hi")

    stats = dm.get_statistics()
    assert stats["total_users"] == 1
    assert stats["total_sessions"] == 1
    assert stats["total_messages"] == 2

    exported = json.loads(dm.export_all_history())
    assert exported["total_users"] == 1
    assert "users" in exported


def test_data_manager_clear(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    dm = DataManager()
    dm.add_message("u1", "user", "user", "hello")
    dm.clear_user_history("u1")
    hist = dm.get_user_history("u1")
    assert hist is not None
    assert hist["sessions"] == []
