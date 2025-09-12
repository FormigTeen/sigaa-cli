from pathlib import Path
from typing import Optional

import click

from .sigaa import Sigaa
from .types import  Institution
from .accounts.ufba import SigaaAccountUFBA
from .resources.file import SigaaFile


@click.group()
def cli() -> None:
    """CLI para interagir com o SIGAA."""
    pass


@cli.command("search-teacher", help="Busca docentes por nome (UFBA)")
@click.option("--url", required=True, help="URL base do SIGAA (ex.: https://sigaa.ufba.br)")
@click.option("--user", required=True, help="Usuário")
@click.option("--password", required=True, help="Senha")
@click.option("--name", required=True, help="Nome do docente para busca")
@click.option(
    "--download-photo-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=None,
    help="Diretório para salvar a foto do perfil (opcional)",
)
def search_teacher(url: str, user: str, password: str, name: str, download_photo_dir: Optional[Path]) -> None:
    sigaa = Sigaa(institution=Institution.UFBA, url=url)
    try:
        sigaa.login(user, password)
        results = sigaa.search.teacher().search(name)
        click.echo(f"Encontrados {len(results)} docentes")
        for r in results:
            click.echo(f"- {r.name} | {r.department} | {r.page_url}")
            if download_photo_dir and r.profile_picture_url and r.download_profile_picture:
                dest = r.download_profile_picture(download_photo_dir, None)
                click.echo(f"  Foto salva em: {dest}")
    finally:
        sigaa.close()


@cli.command("account-bonds", help="Lista vínculos (UFBA)")
@click.option("--url", required=True)
@click.option("--user", required=True)
@click.option("--password", required=True)
def account_bonds(url: str, user: str, password: str) -> None:
    sigaa = Sigaa(institution=Institution.UFBA, url=url)
    try:
        acc = sigaa.login(user, password)
        if not isinstance(acc, SigaaAccountUFBA):
            raise click.ClickException("Instituição não suportada neste comando.")
        active = acc.get_active_bonds()
        inactive = acc.get_inactive_bonds()
        click.echo("Ativos:")
        for b in active:
            click.echo(f"- {b}")
        click.echo("Inativos:")
        for b in inactive:
            click.echo(f"- {b}")
    finally:
        sigaa.close()


@cli.command("account", help="Mostra o nome do usuário)")
@click.option("--provider", required=True)
@click.option("--user", required=True)
@click.option("--password", required=True)
def get_account(provider: str, user: str, password: str) -> None:
    sigaa = Sigaa(institution=provider)
    try:
        sigaa.login(user, password)
        account = sigaa.get_account()
        click.echo(f"Matrícula: {account.registration}")
        click.echo(f"Nome: {account.name}")
        click.echo(f"Curso: {account.program}")
        click.echo(f"Email: {account.email}")
        click.echo(f"Imagem de Perfil: {account.profile_picture_url}")
    finally:
        sigaa.close()


@cli.command("active-courses", help="Lista disciplinas ativas do discente")
@click.option("--provider", required=True)
@click.option("--user", required=True)
@click.option("--password", required=True)
def get_account(provider: str, user: str, password: str) -> None:
    sigaa = Sigaa(institution=provider)
    try:
        sigaa.login(user, password)
        courses = sigaa.get_active_courses/()
        headers = ["Code", "Name", "Location", "Time", "Term"]
        rows = [
            [c.code, c.name, c.location, c.time_code, c.term]
            for c in courses
        ]

        # Compute column widths
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                widths[i] = max(widths[i], len(str(cell)))

        def fmt_row(values: list[str]) -> str:
            return " | ".join(str(v).ljust(widths[i]) for i, v in enumerate(values))

        # Print table
        click.echo(fmt_row(headers))
        click.echo("-+-".join("-" * w for w in widths))
        for row in rows:
            click.echo(fmt_row([str(x) for x in row]))
    finally:
        sigaa.close()

def main() -> None:
    cli(prog_name="sigaa-api")


if __name__ == "__main__":
    main()
