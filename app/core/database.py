import json
import os
import threading
import uuid


class MongoStyleDatabase:
    _instances = {}
    _lock = threading.Lock()
    file_path: str

    def __new__(cls, file_path="app/data/banco.json"):
        with cls._lock:
            if file_path not in cls._instances:
                instance = super(MongoStyleDatabase, cls).__new__(cls)
                instance.file_path = file_path
                instance._ensure_file_exists()
                cls._instances[file_path] = instance
        return cls._instances[file_path]

    def _ensure_file_exists(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read_file(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_file(self, data):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def insert(self, data):
        with self._lock:
            db_data = self._read_file()
            doc_id = str(uuid.uuid4())
            data["_id"] = doc_id
            db_data.append(data)
            self._write_file(db_data)
            return doc_id

    def read(self):
        with self._lock:
            return self._read_file()

    def update(self, doc_id, new_data):
        with self._lock:
            db_data = self._read_file()
            for i, doc in enumerate(db_data):
                if doc.get("_id") == doc_id:
                    db_data[i] = {**doc, **new_data, "_id": doc_id}
                    self._write_file(db_data)
                    return True
            return False

    def delete(self, doc_id):
        with self._lock:
            db_data = self._read_file()
            new_db_data = [doc for doc in db_data if doc.get("_id") != doc_id]
            if len(db_data) != len(new_db_data):
                self._write_file(new_db_data)
                return True
            return False

    def delete_many(self, doc_ids: list):
        with self._lock:
            db_data = self._read_file()
            ids_set = set(doc_ids)
            new_db_data = [doc for doc in db_data if doc.get("_id") not in ids_set]
            deleted_count = len(db_data) - len(new_db_data)
            if deleted_count > 0:
                self._write_file(new_db_data)
            return deleted_count
