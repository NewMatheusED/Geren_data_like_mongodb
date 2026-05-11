import os

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    from app.core import database

    monkeypatch.setattr(database.MongoStyleDatabase, "_instances", {})

    def patched_new(cls, file_path="app/data/banco.json"):
        redirected = os.path.join(str(tmp_path), file_path)
        with cls._lock:
            if redirected not in cls._instances:
                instance = object.__new__(cls)
                instance.file_path = redirected
                instance._ensure_file_exists()
                cls._instances[redirected] = instance
        return cls._instances[redirected]

    monkeypatch.setattr(database.MongoStyleDatabase, "__new__", patched_new)

    yield
