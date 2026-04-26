from flask import Blueprint, jsonify, request

from app.core.commands import (
    DeleteCommand,
    InsertCommand,
    ReadCommand,
    RegisterUserCommand,
    UpdateCommand,
)
from app.core.database import MongoStyleDatabase

api_bp = Blueprint("api", __name__)


def get_user_id_from_headers():
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise PermissionError("Header 'X-User-ID' é obrigatório.")
    return user_id


# usuarios
@api_bp.route("/users", methods=["POST"])
def register_user():
    data = request.json
    role = data.get("role", "").lower()
    name = data.get("nome")

    try:
        command = RegisterUserCommand(name, role)
        user_id = command.execute()
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    return jsonify({"message": "Usuário criado com sucesso", "user_id": user_id}), 201


@api_bp.route("/users", methods=["GET"])
def list_users():
    users_db = MongoStyleDatabase("app/data/users.json")
    users = users_db.read()
    return jsonify(users), 200


# dados
@api_bp.route("/data", methods=["POST"])
def create_data():
    try:
        user_id = get_user_id_from_headers()
        data = request.json
        command = InsertCommand(user_id, data)
        doc_id = command.execute()
        return jsonify({"message": "Documento inserido", "id": doc_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 403


@api_bp.route("/data", methods=["GET"])
def read_data():
    try:
        user_id = get_user_id_from_headers()
        query = request.args.to_dict() if request.args else None
        command = ReadCommand(user_id, query)
        result = command.execute()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 403


@api_bp.route("/data/<doc_id>", methods=["PUT"])
def update_data(doc_id):
    try:
        user_id = get_user_id_from_headers()
        data = request.json
        command = UpdateCommand(user_id, doc_id, data)
        success = command.execute()
        if success:
            return jsonify({"message": "Documento atualizado"}), 200
        return jsonify({"error": "Documento não encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 403


@api_bp.route("/data/<doc_id>", methods=["DELETE"])
def delete_data(doc_id):
    try:
        user_id = get_user_id_from_headers()
        command = DeleteCommand(user_id, doc_id)
        success = command.execute()
        if success:
            return jsonify({"message": "Documento deletado"}), 200
        return jsonify({"error": "Documento não encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 403
