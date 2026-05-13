import shlex
import sys

import click

from app.core.commands import (
    DeleteCommand,
    DeleteManyCommand,
    InsertCommand,
    ReadCommand,
    ReadLogCommand,
    RegisterUserCommand,
    UpdateCommand,
)
from app.core.database import MongoStyleDatabase
from app.core.resolver import CLIResolver


def parse_pairs(pairs: tuple, label: str) -> dict:
    """Converte ('chave=valor', ...) em {'chave': 'valor'}."""
    result = {}
    for pair in pairs:
        if "=" not in pair:
            raise click.UsageError(
                f"{label} inválido: '{pair}'. Use o formato chave=valor"
            )
        key, _, value = pair.partition("=")
        result[key.strip()] = value.strip()
    return result


def ok(msg: str):
    click.echo(click.style("  ✔ ", fg="green", bold=True) + msg)


def err(msg: str):
    click.echo(click.style("  ✘ ", fg="red", bold=True) + msg, err=True)


def section(title: str):
    bar = "─" * len(title)
    click.echo(click.style(f"\n  {title}", fg="cyan", bold=True))
    click.echo(click.style(f"  {bar}", fg="cyan"))


@click.group()
def cli():
    """
    \b
    Use --help em qualquer subcomando para mais detalhes.

    \b
    Exemplos rápidos:
      python cli.py users list
      python cli.py users create --nome "Matheus" --role manipulador
      python cli.py data list -u 1
      python cli.py data insert -u 1 --field titulo=Doc --field valor=42
      python cli.py data update -u 1 -d 2 --field titulo=Novo
      python cli.py data delete -u 1 -d 2
      python cli.py data delete-many -u 1 --query categoria=tecnologia
      python cli.py logs -u 1
    """
    pass


@cli.group()
def users():
    """Gerenciar usuários (criar, listar)."""
    pass


@users.command("list")
def users_list():
    """Lista todos os usuários com seus números de referência."""
    all_users = MongoStyleDatabase("app/data/users.json").read()

    if not all_users:
        click.echo(click.style("\n  Nenhum usuário cadastrado.", fg="yellow"))
        return

    section("USUÁRIOS")
    click.echo(f"  {'#':<5} {'Nome':<22} {'Role':<14}")
    click.echo(f"  {'─' * 5} {'─' * 22} {'─' * 14}")

    for i, user in enumerate(all_users, start=1):
        role = user.get("role", "")
        role_str = click.style(
            f"{role:<14}", fg="green" if role == "manipulador" else "yellow"
        )
        click.echo(f"  {i:<5} {user.get('nome', ''):<22} {role_str}")

    click.echo()


@users.command("create")
@click.option("--nome", required=True, help="Nome do usuário")
@click.option(
    "--role",
    required=True,
    type=click.Choice(["manipulador", "consumidor"], case_sensitive=False),
    help="Role: manipulador (leitura + escrita) | consumidor (só leitura)",
)
def users_create(nome, role):
    """Cria um novo usuário."""
    try:
        command = RegisterUserCommand(nome, role)
        user_id = command.execute()
        ok(f"Usuário '{nome}' criado com sucesso!")
        click.echo(f"     ID: {click.style(user_id, fg='cyan')}")
        click.echo()
    except ValueError as e:
        err(str(e))
        sys.exit(1)


@cli.group()
def data():
    """Gerenciar documentos (inserir, ler, atualizar, deletar)."""
    pass


@data.command("list")
@click.option(
    "-u",
    required=True,
    type=int,
    metavar="NUM",
    help="Número do usuário  →  veja: users list",
)
@click.option(
    "--query",
    multiple=True,
    metavar="CHAVE=VALOR",
    help="Filtro regex. Ex: --query categoria=tech",
)
def data_list(u, query):
    """Lista documentos. Combine --query para filtrar por regex."""
    try:
        user_id = CLIResolver.get_user_id(u)
        parsed_query = parse_pairs(query, "--query") if query else None
        docs = ReadCommand(user_id, parsed_query).execute()

        if not docs:
            click.echo(click.style("\n  Nenhum documento encontrado.", fg="yellow"))
            return

        keys = []
        for doc in docs:
            for k in doc:
                if k != "_id" and k not in keys:
                    keys.append(k)

        col = 18
        section(f"DOCUMENTOS  (usuário #{u})")
        header = f"  {'#':<5} " + " ".join(f"{k:<{col}}" for k in keys) + "  ID"
        click.echo(header)
        click.echo(
            f"  {'─' * 5} " + " ".join("─" * col for _ in keys) + f"  {'─' * 36}"
        )

        for i, doc in enumerate(docs, start=1):
            values = " ".join(f"{str(doc.get(k, '')):<{col}}" for k in keys)
            click.echo(f"  {i:<5} {values}  {doc.get('_id', '')}")

        click.echo()
    except (IndexError, PermissionError) as e:
        err(str(e))
        sys.exit(1)


@data.command("insert")
@click.option("-u", required=True, type=int, metavar="NUM", help="Número do usuário")
@click.option(
    "--field",
    multiple=True,
    required=True,
    metavar="CHAVE=VALOR",
    help="Campo do documento. Ex: --field titulo=Doc --field valor=42",
)
def data_insert(u, field):
    """Insere um novo documento."""
    try:
        user_id = CLIResolver.get_user_id(u)
        data_dict = parse_pairs(field, "--field")
        doc_id = InsertCommand(user_id, data_dict).execute()
        ok("Documento inserido com sucesso!")
        click.echo(f"     ID: {click.style(doc_id, fg='cyan')}")
        click.echo()
    except (IndexError, PermissionError) as e:
        err(str(e))
        sys.exit(1)


@data.command("update")
@click.option("-u", required=True, type=int, metavar="NUM", help="Número do usuário")
@click.option(
    "-d",
    required=True,
    type=int,
    metavar="NUM",
    help="Número do documento  →  veja: data list -u <num>",
)
@click.option(
    "--field",
    multiple=True,
    required=True,
    metavar="CHAVE=VALOR",
    help="Campo a atualizar. Ex: --field titulo=Novo",
)
def data_update(u, d, field):
    """Atualiza campos de um documento existente."""
    try:
        user_id = CLIResolver.get_user_id(u)
        doc_id = CLIResolver.get_doc_id(d)
        data_dict = parse_pairs(field, "--field")
        success = UpdateCommand(user_id, doc_id, data_dict).execute()
        if success:
            ok(f"Documento #{d} atualizado com sucesso!")
        else:
            err(f"Documento #{d} não encontrado no banco.")
        click.echo()
    except (IndexError, PermissionError) as e:
        err(str(e))
        sys.exit(1)


@data.command("delete")
@click.option("-u", required=True, type=int, metavar="NUM", help="Número do usuário")
@click.option("-d", required=True, type=int, metavar="NUM", help="Número do documento")
def data_delete(u, d):
    """Deleta um documento pelo número."""
    try:
        user_id = CLIResolver.get_user_id(u)
        doc_id = CLIResolver.get_doc_id(d)
        success = DeleteCommand(user_id, doc_id).execute()
        if success:
            ok(f"Documento #{d} deletado.")
        else:
            err(f"Documento #{d} não encontrado no banco.")
        click.echo()
    except (IndexError, PermissionError) as e:
        err(str(e))
        sys.exit(1)


@data.command("delete-many")
@click.option("-u", required=True, type=int, metavar="NUM", help="Número do usuário")
@click.option(
    "--query",
    multiple=True,
    required=True,
    metavar="CHAVE=VALOR",
    help="Filtro regex. Ex: --query categoria=tech",
)
def data_delete_many(u, query):
    """Deleta todos os documentos que casarem com o filtro regex."""
    try:
        user_id = CLIResolver.get_user_id(u)
        parsed_query = parse_pairs(query, "--query")
        count = DeleteManyCommand(user_id, parsed_query).execute()
        ok(f"{count} documento(s) deletado(s).")
        click.echo()
    except (IndexError, PermissionError) as e:
        err(str(e))
        sys.exit(1)


@cli.command("logs")
@click.option("-u", required=True, type=int, metavar="NUM", help="Número do usuário")
def logs(u):
    """Exibe o histórico completo de ações de um usuário."""
    try:
        user_id = CLIResolver.get_user_id(u)
        entries = ReadLogCommand(user_id).execute()

        if not entries:
            click.echo(click.style("\n  Nenhum log encontrado.", fg="yellow"))
            return

        section(f"LOGS  (usuário #{u})")
        click.echo(f"  {'#':<5} {'Timestamp':<28} {'Ação':<14} {'Status':<10} Detalhes")
        click.echo(f"  {'─' * 5} {'─' * 28} {'─' * 14} {'─' * 10} {'─' * 36}")

        skip_keys = {"timestamp", "action", "status", "_id"}
        for i, entry in enumerate(entries, start=1):
            status = entry.get("status", "")
            status_colored = (
                click.style(f"{status:<10}", fg="green")
                if status == "success"
                else click.style(f"{status:<10}", fg="red")
            )
            details = ", ".join(
                f"{k}={v}" for k, v in entry.items() if k not in skip_keys
            )
            ts = entry.get("timestamp", "")[:26]
            click.echo(
                f"  {i:<5} {ts:<28} {entry.get('action', ''):<14} {status_colored} {details}"
            )

        click.echo()
    except (IndexError, Exception) as e:
        err(str(e))
        sys.exit(1)


def repl():
    click.echo(
        click.style("\n  ╔══════════════════════════════╗", fg="cyan", bold=True)
    )
    click.echo(click.style("  ║          🗄  MongoDB          ║", fg="cyan", bold=True))
    click.echo(click.style("  ╚══════════════════════════════╝", fg="cyan", bold=True))
    click.echo(
        click.style("  Digite '--help' para ver os comandos.", fg="bright_black")
    )
    click.echo(click.style("  Digite 'exit' ou 'quit' para sair.\n", fg="bright_black"))

    while True:
        try:
            line = input(click.style("db> ", fg="cyan", bold=True))
            line = line.strip()

            if not line:
                continue

            if line.lower() in ("exit", "quit"):
                click.echo(click.style("\n  Até logo! 👋\n", fg="cyan"))
                break

            try:
                args = shlex.split(line)
            except ValueError as e:
                err(f"Erro ao parsear comando: {e}")
                continue

            try:
                cli.main(args, standalone_mode=False)
            except click.exceptions.UsageError as e:
                err(str(e))
            except click.exceptions.Exit:
                pass
            except SystemExit:
                pass
            except Exception as e:
                err(f"Erro inesperado: {e}")

        except (KeyboardInterrupt, EOFError):
            click.echo()
            click.echo(click.style("\n  Até logo!\n", fg="cyan"))
            break


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Modo normal: python cli.py users list ...
        cli()
    else:
        # Modo interativo: python cli.py
        repl()
