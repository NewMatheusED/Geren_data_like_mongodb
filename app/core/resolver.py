from .database import MongoStyleDatabase


class CLIResolver:
    @staticmethod
    def get_user_id(num: int) -> str:
        users = MongoStyleDatabase("app/data/users.json").read()
        if num < 1 or num > len(users):
            raise IndexError(
                f"Usuário #{num} não encontrado. "
                f"Use 'python cli.py users list' para ver os disponíveis."
            )
        return users[num - 1]["_id"]

    @staticmethod
    def get_doc_id(num: int) -> str:
        docs = MongoStyleDatabase("app/data/banco.json").read()
        if num < 1 or num > len(docs):
            raise IndexError(
                f"Documento #{num} não encontrado. "
                f"Use 'python cli.py data list -u <num>' para ver os disponíveis."
            )
        return docs[num - 1]["_id"]
