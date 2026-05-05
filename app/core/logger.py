from datetime import datetime, timezone

from .database import MongoStyleDatabase


class UserLogger:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.db = MongoStyleDatabase(f"app/data/logs/{user_id}.json")

    def log(self, action: str, status: str, **kwargs):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "status": status,
            **kwargs,
        }
        self.db.insert(entry)

    def read(self):
        return self.db.read()
