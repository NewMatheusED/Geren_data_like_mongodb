class User:
    def __init__(self, user_id, role):
        self.user_id = user_id
        self.role = role


class UserFactory:
    @staticmethod
    def create_user(user_id, role):
        role = role.lower()
        if role in ["manipulador", "consumidor"]:
            return User(user_id, role)
        raise ValueError(
            "Role inválida. Permitido apenas 'manipulador' ou 'consumidor'."
        )
