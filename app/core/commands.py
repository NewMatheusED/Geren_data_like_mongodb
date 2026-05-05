from abc import ABC, abstractmethod
from typing import Any

from .database import MongoStyleDatabase
from .factory import UserFactory
from .logger import UserLogger
from .proxy import DatabaseProxy


class Command(ABC):
    @abstractmethod
    def execute(self) -> Any:
        pass


class InsertCommand(Command):
    def __init__(self, user_id, data):
        self.proxy = DatabaseProxy()
        self.user_id = user_id
        self.data = data

    def execute(self):
        return self.proxy.insert(self.user_id, self.data)


class ReadCommand(Command):
    def __init__(self, user_id, query=None):
        self.proxy = DatabaseProxy()
        self.user_id = user_id
        self.query = query

    def execute(self):
        return self.proxy.read(self.user_id, self.query)


class UpdateCommand(Command):
    def __init__(self, user_id, doc_id, data):
        self.proxy = DatabaseProxy()
        self.user_id = user_id
        self.doc_id = doc_id
        self.data = data

    def execute(self):
        return self.proxy.update(self.user_id, self.doc_id, self.data)


class DeleteCommand(Command):
    def __init__(self, user_id, doc_id):
        self.proxy = DatabaseProxy()
        self.user_id = user_id
        self.doc_id = doc_id

    def execute(self):
        return self.proxy.delete(self.user_id, self.doc_id)


class ReadAllUsersCommand(Command):
    def __init__(self):
        self.proxy = DatabaseProxy()

    def execute(self):
        return self.proxy.read_all_users()


class RegisterUserCommand(Command):
    def __init__(self, nome, role):
        self.nome = nome
        self.role = role
        self.users_db = MongoStyleDatabase("app/data/users.json")

    def execute(self):
        UserFactory.create_user("temp_id", self.role)

        user_data = {"nome": self.nome, "role": self.role.lower()}
        user_id = self.users_db.insert(user_data)
        UserLogger(user_id).log("register", "success", nome=self.nome, role=self.role)
        return user_id


class ReadLogCommand(Command):
    def __init__(self, user_id):
        self.proxy = DatabaseProxy()
        self.user_id = user_id

    def execute(self):
        return self.proxy.read_log(self.user_id)
