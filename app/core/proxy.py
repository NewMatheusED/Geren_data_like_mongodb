from .database import MongoStyleDatabase
from .factory import UserFactory
from .logger import UserLogger
from .orm import RegexORM


class DatabaseProxy:
    def __init__(self):
        self.db = MongoStyleDatabase("app/data/banco.json")
        self.users_db = MongoStyleDatabase("app/data/users.json")

    def _authenticate_user(self, user_id):
        users = self.users_db.read()
        for u in users:
            if u.get("_id") == user_id:
                return UserFactory.create_user(user_id, u.get("role"))
        raise PermissionError("Usuário não encontrado ou não autenticado.")

    def _check_permission(self, user, action):
        if user.role == "manipulador":
            return True
        if user.role == "consumidor" and action == "read":
            return True
        raise PermissionError(
            f"Acesso Negado: '{user.role}' não pode executar '{action}'."
        )

    def insert(self, user_id, data):
        try:
            user = self._authenticate_user(user_id)
            self._check_permission(user, "insert")
            doc_id = self.db.insert(data)
            UserLogger(user_id).log("insert", "success", doc_id=doc_id)
            return doc_id
        except PermissionError as e:
            UserLogger(user_id).log("insert", "denied", reason=str(e))
            raise

    def read(self, user_id, query=None):
        try:
            user = self._authenticate_user(user_id)
            self._check_permission(user, "read")
            all_data = self.db.read()
            result = RegexORM.find(all_data, query)
            UserLogger(user_id).log("read", "success", query=query if query else "all")
            return result
        except PermissionError as e:
            UserLogger(user_id).log("read", "denied", reason=str(e))
            raise

    def update(self, user_id, doc_id, data):
        try:
            user = self._authenticate_user(user_id)
            self._check_permission(user, "update")
            result = self.db.update(doc_id, data)
            UserLogger(user_id).log("update", "success", doc_id=doc_id)
            return result
        except PermissionError as e:
            UserLogger(user_id).log("update", "denied", reason=str(e))
            raise

    def delete(self, user_id, doc_id):
        try:
            user = self._authenticate_user(user_id)
            self._check_permission(user, "delete")
            result = self.db.delete(doc_id)
            UserLogger(user_id).log("delete", "success", doc_id=doc_id)
            return result
        except PermissionError as e:
            UserLogger(user_id).log("delete", "denied", reason=str(e))
            raise

    def read_log(self, user_id):
        self._authenticate_user(user_id)
        return UserLogger(user_id).read()

    def read_all_users(self):
        return self.users_db.read()
