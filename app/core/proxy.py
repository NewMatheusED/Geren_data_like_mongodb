from .database import MongoStyleDatabase
from .factory import UserFactory
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
        user = self._authenticate_user(user_id)
        self._check_permission(user, "insert")
        return self.db.insert(data)

    def read(self, user_id, query=None):
        user = self._authenticate_user(user_id)
        self._check_permission(user, "read")
        all_data = self.db.read()
        return RegexORM.find(all_data, query)

    def update(self, user_id, doc_id, data):
        user = self._authenticate_user(user_id)
        self._check_permission(user, "update")
        return self.db.update(doc_id, data)

    def delete(self, user_id, doc_id):
        user = self._authenticate_user(user_id)
        self._check_permission(user, "delete")
        return self.db.delete(doc_id)
