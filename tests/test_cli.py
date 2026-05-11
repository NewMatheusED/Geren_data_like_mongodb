import pytest

from cli import cli


def create_user(runner, nome, role):
    result = runner.invoke(cli, ["users", "create", "--nome", nome, "--role", role])
    assert result.exit_code == 0, result.output
    return result


def insert_doc(runner, user_num: int, fields: dict):
    args = ["data", "insert", "-u", str(user_num)]
    for k, v in fields.items():
        args += ["--field", f"{k}={v}"]
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.output
    return result


class TestHelp:
    def test_root_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "users" in result.output
        assert "data" in result.output
        assert "logs" in result.output

    def test_users_help(self, runner):
        result = runner.invoke(cli, ["users", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "create" in result.output

    def test_data_help(self, runner):
        result = runner.invoke(cli, ["data", "--help"])
        assert result.exit_code == 0
        assert "insert" in result.output
        assert "list" in result.output
        assert "update" in result.output
        assert "delete" in result.output

    def test_data_insert_help(self, runner):
        result = runner.invoke(cli, ["data", "insert", "--help"])
        assert result.exit_code == 0
        assert "-u" in result.output
        assert "--field" in result.output

    def test_logs_help(self, runner):
        result = runner.invoke(cli, ["logs", "--help"])
        assert result.exit_code == 0
        assert "-u" in result.output


class TestUsers:
    def test_create_manipulador_success(self, runner):
        result = runner.invoke(
            cli, ["users", "create", "--nome", "Matheus", "--role", "manipulador"]
        )
        assert result.exit_code == 0
        assert "✔" in result.output
        assert "Matheus" in result.output

    def test_create_consumidor_success(self, runner):
        result = runner.invoke(
            cli, ["users", "create", "--nome", "João", "--role", "consumidor"]
        )
        assert result.exit_code == 0
        assert "✔" in result.output
        assert "João" in result.output

    def test_create_prints_user_id(self, runner):
        result = runner.invoke(
            cli, ["users", "create", "--nome", "Alice", "--role", "manipulador"]
        )
        assert result.exit_code == 0
        assert "ID:" in result.output

    def test_create_invalid_role_rejected(self, runner):
        result = runner.invoke(
            cli, ["users", "create", "--nome", "Hacker", "--role", "admin"]
        )
        assert result.exit_code != 0

    def test_create_missing_nome_rejected(self, runner):
        result = runner.invoke(cli, ["users", "create", "--role", "manipulador"])
        assert result.exit_code != 0

    def test_create_missing_role_rejected(self, runner):
        result = runner.invoke(cli, ["users", "create", "--nome", "Alguem"])
        assert result.exit_code != 0

    def test_list_shows_all_users(self, runner):
        create_user(runner, "Alice", "manipulador")
        create_user(runner, "Bob", "consumidor")
        result = runner.invoke(cli, ["users", "list"])
        assert result.exit_code == 0
        assert "Alice" in result.output
        assert "Bob" in result.output

    def test_list_shows_sequential_numbers(self, runner):
        create_user(runner, "Alice", "manipulador")
        create_user(runner, "Bob", "consumidor")
        result = runner.invoke(cli, ["users", "list"])
        assert "1" in result.output
        assert "2" in result.output

    def test_list_shows_roles(self, runner):
        create_user(runner, "Alice", "manipulador")
        create_user(runner, "Bob", "consumidor")
        result = runner.invoke(cli, ["users", "list"])
        assert "manipulador" in result.output
        assert "consumidor" in result.output

    def test_list_empty_shows_message(self, runner):
        result = runner.invoke(cli, ["users", "list"])
        assert result.exit_code == 0
        assert "Nenhum usuário cadastrado" in result.output


class TestData:
    @pytest.fixture(autouse=True)
    def setup_users(self, runner):
        """Cria um manipulador (#1) e um consumidor (#2) antes de cada teste."""
        create_user(runner, "Manipulador", "manipulador")
        create_user(runner, "Consumidor", "consumidor")

    def test_insert_manipulador_success(self, runner):
        result = runner.invoke(
            cli,
            [
                "data",
                "insert",
                "-u",
                "1",
                "--field",
                "titulo=Doc Teste",
                "--field",
                "valor=42",
            ],
        )
        assert result.exit_code == 0
        assert "✔" in result.output
        assert "ID:" in result.output

    def test_insert_consumidor_denied(self, runner):
        result = runner.invoke(
            cli, ["data", "insert", "-u", "2", "--field", "titulo=Proibido"]
        )
        assert result.exit_code == 1
        assert "✘" in result.output
        assert "Acesso Negado" in result.output

    def test_insert_missing_user_rejected(self, runner):
        result = runner.invoke(cli, ["data", "insert", "--field", "titulo=Sem user"])
        assert result.exit_code != 0

    def test_insert_missing_field_rejected(self, runner):
        result = runner.invoke(cli, ["data", "insert", "-u", "1"])
        assert result.exit_code != 0

    def test_insert_invalid_user_number(self, runner):
        result = runner.invoke(
            cli, ["data", "insert", "-u", "99", "--field", "titulo=Test"]
        )
        assert result.exit_code == 1
        assert "✘" in result.output
        assert "99" in result.output

    def test_list_manipulador_sees_docs(self, runner):
        insert_doc(runner, 1, {"titulo": "Doc A", "categoria": "tech"})
        result = runner.invoke(cli, ["data", "list", "-u", "1"])
        assert result.exit_code == 0
        assert "Doc A" in result.output

    def test_list_consumidor_can_read(self, runner):
        insert_doc(runner, 1, {"titulo": "Doc A"})
        result = runner.invoke(cli, ["data", "list", "-u", "2"])
        assert result.exit_code == 0
        assert "Doc A" in result.output

    def test_list_with_query_filter_returns_match(self, runner):
        insert_doc(runner, 1, {"titulo": "Python", "categoria": "tecnologia"})
        insert_doc(runner, 1, {"titulo": "Receita", "categoria": "culinaria"})
        result = runner.invoke(
            cli, ["data", "list", "-u", "1", "--query", "categoria=tecnologia"]
        )
        assert result.exit_code == 0
        assert "Python" in result.output
        assert "Receita" not in result.output

    def test_list_with_query_filter_regex(self, runner):
        insert_doc(runner, 1, {"titulo": "Python Avançado", "categoria": "tech"})
        insert_doc(runner, 1, {"titulo": "Python Básico", "categoria": "tech"})
        insert_doc(runner, 1, {"titulo": "Java", "categoria": "tech"})
        result = runner.invoke(
            cli, ["data", "list", "-u", "1", "--query", "titulo=Python"]
        )
        assert result.exit_code == 0
        assert "Python Avançado" in result.output
        assert "Python Básico" in result.output
        assert "Java" not in result.output

    def test_list_empty_shows_message(self, runner):
        result = runner.invoke(cli, ["data", "list", "-u", "1"])
        assert result.exit_code == 0
        assert "Nenhum documento encontrado" in result.output

    def test_list_invalid_user_number(self, runner):
        result = runner.invoke(cli, ["data", "list", "-u", "99"])
        assert result.exit_code == 1
        assert "✘" in result.output

    def test_update_manipulador_success(self, runner):
        insert_doc(runner, 1, {"titulo": "Original"})
        result = runner.invoke(
            cli,
            ["data", "update", "-u", "1", "-d", "1", "--field", "titulo=Atualizado"],
        )
        assert result.exit_code == 0
        assert "✔" in result.output
        assert "1" in result.output

    def test_update_reflects_in_list(self, runner):
        insert_doc(runner, 1, {"titulo": "Original"})
        runner.invoke(
            cli,
            ["data", "update", "-u", "1", "-d", "1", "--field", "titulo=Atualizado"],
        )
        result = runner.invoke(cli, ["data", "list", "-u", "1"])
        assert "Atualizado" in result.output
        assert "Original" not in result.output

    def test_update_consumidor_denied(self, runner):
        insert_doc(runner, 1, {"titulo": "Original"})
        result = runner.invoke(
            cli, ["data", "update", "-u", "2", "-d", "1", "--field", "titulo=Proibido"]
        )
        assert result.exit_code == 1
        assert "Acesso Negado" in result.output

    def test_update_invalid_doc_number(self, runner):
        result = runner.invoke(
            cli, ["data", "update", "-u", "1", "-d", "99", "--field", "titulo=X"]
        )
        assert result.exit_code == 1
        assert "✘" in result.output

    def test_delete_manipulador_success(self, runner):
        insert_doc(runner, 1, {"titulo": "Para Deletar"})
        result = runner.invoke(cli, ["data", "delete", "-u", "1", "-d", "1"])
        assert result.exit_code == 0
        assert "✔" in result.output

    def test_delete_removes_from_list(self, runner):
        insert_doc(runner, 1, {"titulo": "Para Deletar"})
        runner.invoke(cli, ["data", "delete", "-u", "1", "-d", "1"])
        result = runner.invoke(cli, ["data", "list", "-u", "1"])
        assert "Para Deletar" not in result.output

    def test_delete_consumidor_denied(self, runner):
        insert_doc(runner, 1, {"titulo": "Protegido"})
        result = runner.invoke(cli, ["data", "delete", "-u", "2", "-d", "1"])
        assert result.exit_code == 1
        assert "Acesso Negado" in result.output

    def test_delete_invalid_doc_number(self, runner):
        result = runner.invoke(cli, ["data", "delete", "-u", "1", "-d", "99"])
        assert result.exit_code == 1
        assert "✘" in result.output

    def test_delete_many_removes_matching_docs(self, runner):
        insert_doc(runner, 1, {"titulo": "Tech 1", "categoria": "tech"})
        insert_doc(runner, 1, {"titulo": "Tech 2", "categoria": "tech"})
        insert_doc(runner, 1, {"titulo": "Outro", "categoria": "outro"})
        result = runner.invoke(
            cli, ["data", "delete-many", "-u", "1", "--query", "categoria=tech"]
        )
        assert result.exit_code == 0
        assert "2 documento(s) deletado(s)" in result.output

    def test_delete_many_preserves_non_matching(self, runner):
        insert_doc(runner, 1, {"titulo": "Tech", "categoria": "tech"})
        insert_doc(runner, 1, {"titulo": "Outro", "categoria": "outro"})
        runner.invoke(
            cli, ["data", "delete-many", "-u", "1", "--query", "categoria=tech"]
        )
        result = runner.invoke(cli, ["data", "list", "-u", "1"])
        assert "Outro" in result.output
        assert "Tech" not in result.output

    def test_delete_many_consumidor_denied(self, runner):
        insert_doc(runner, 1, {"titulo": "Tech", "categoria": "tech"})
        result = runner.invoke(
            cli, ["data", "delete-many", "-u", "2", "--query", "categoria=tech"]
        )
        assert result.exit_code == 1
        assert "Acesso Negado" in result.output

    def test_delete_many_missing_query_rejected(self, runner):
        result = runner.invoke(cli, ["data", "delete-many", "-u", "1"])
        assert result.exit_code != 0


class TestLogs:
    @pytest.fixture(autouse=True)
    def setup_users(self, runner):
        create_user(runner, "Manipulador", "manipulador")
        create_user(runner, "Consumidor", "consumidor")

    def test_logs_show_register_action(self, runner):
        result = runner.invoke(cli, ["logs", "-u", "1"])
        assert result.exit_code == 0
        assert "register" in result.output
        assert "success" in result.output

    def test_logs_show_insert_success(self, runner):
        insert_doc(runner, 1, {"titulo": "Doc"})
        result = runner.invoke(cli, ["logs", "-u", "1"])
        assert "insert" in result.output
        assert "success" in result.output

    def test_logs_show_denied_action(self, runner):
        runner.invoke(cli, ["data", "insert", "-u", "2", "--field", "titulo=X"])
        result = runner.invoke(cli, ["logs", "-u", "2"])
        assert result.exit_code == 0
        assert "insert" in result.output
        assert "denied" in result.output

    def test_logs_show_read_success(self, runner):
        insert_doc(runner, 1, {"titulo": "Doc"})
        runner.invoke(cli, ["data", "list", "-u", "1"])
        result = runner.invoke(cli, ["logs", "-u", "1"])
        assert "read" in result.output

    def test_logs_show_delete_many(self, runner):
        insert_doc(runner, 1, {"titulo": "Doc", "categoria": "tech"})
        runner.invoke(
            cli, ["data", "delete-many", "-u", "1", "--query", "categoria=tech"]
        )
        result = runner.invoke(cli, ["logs", "-u", "1"])
        assert "delete_many" in result.output

    def test_logs_invalid_user_number(self, runner):
        result = runner.invoke(cli, ["logs", "-u", "99"])
        assert result.exit_code == 1
        assert "✘" in result.output

    def test_logs_empty_shows_message(self, runner):
        result = runner.invoke(cli, ["logs", "-u", "1"])
        assert result.exit_code == 0
        assert "register" in result.output


class TestResolver:
    def test_get_user_id_returns_valid_uuid(self, runner):
        create_user(runner, "Alice", "manipulador")
        from app.core.resolver import CLIResolver

        user_id = CLIResolver.get_user_id(1)
        assert isinstance(user_id, str)
        assert len(user_id) == 36

    def test_get_user_id_out_of_range(self, runner):
        create_user(runner, "Alice", "manipulador")
        from app.core.resolver import CLIResolver

        with pytest.raises(IndexError, match="Usuário #99"):
            CLIResolver.get_user_id(99)

    def test_get_user_id_zero_invalid(self, runner):
        create_user(runner, "Alice", "manipulador")
        from app.core.resolver import CLIResolver

        with pytest.raises(IndexError):
            CLIResolver.get_user_id(0)

    def test_get_doc_id_returns_valid_uuid(self, runner):
        create_user(runner, "Alice", "manipulador")
        insert_doc(runner, 1, {"titulo": "Doc"})
        from app.core.resolver import CLIResolver

        doc_id = CLIResolver.get_doc_id(1)
        assert isinstance(doc_id, str)
        assert len(doc_id) == 36

    def test_get_doc_id_out_of_range(self, runner):
        from app.core.resolver import CLIResolver

        with pytest.raises(IndexError, match="Documento #99"):
            CLIResolver.get_doc_id(99)

    def test_get_second_user_id_is_different(self, runner):
        create_user(runner, "Alice", "manipulador")
        create_user(runner, "Bob", "consumidor")
        from app.core.resolver import CLIResolver

        id1 = CLIResolver.get_user_id(1)
        id2 = CLIResolver.get_user_id(2)
        assert id1 != id2
