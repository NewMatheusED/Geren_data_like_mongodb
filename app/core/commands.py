from abc import ABC, abstractmethod
from typing import Any

from .database import MongoStyleDatabase
from .factory import UserFactory
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


class RegisterUserCommand(Command):
    def __init__(self, nome, role):
        self.nome = nome
        self.role = role
        self.users_db = MongoStyleDatabase("app/data/users.json")

    def execute(self):
        UserFactory.create_user("temp_id", self.role)

        user_data = {"nome": self.nome, "role": self.role.lower()}
        return self.users_db.insert(user_data)
