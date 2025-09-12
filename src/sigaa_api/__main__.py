from pathlib import Path
from typing import Optional

import rich_click as click
from rich.console import Console
from rich.table import Table

from .sigaa import Sigaa
from .types import  Institution
from .accounts.ufba import SigaaAccountUFBA
from .resources.file import SigaaFile


console = Console()


@click.group()
def cli() -> None:
    """CLI para interagir com o SIGAA."""
    # Configurações adicionais do rich-click podem ser feitas via variáveis
    # de ambiente ou no arquivo principal do app, se necessário.
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
        console.print(f"[bold]Encontrados {len(results)} docentes[/bold]")
        for r in results:
            console.print(f"- [cyan]{r.name}[/cyan] | {r.department} | {r.page_url}")
            if download_photo_dir and r.profile_picture_url and r.download_profile_picture:
                dest = r.download_profile_picture(download_photo_dir, None)
                console.print(f"  [green]Foto salva em:[/green] {dest}")
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
        console.print("[bold]Ativos:[/bold]")
        for b in active:
            console.print(f"- {b}")
        console.print("[bold]Inativos:[/bold]")
        for b in inactive:
            console.print(f"- {b}")
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
        console.print(f"[bold]Matrícula:[/bold] {account.registration}")
        console.print(f"[bold]Nome:[/bold] {account.name}")
        console.print(f"[bold]Curso:[/bold] {account.program}")
        console.print(f"[bold]Email:[/bold] {account.email}")
        console.print(f"[bold]Imagem de Perfil:[/bold] {account.profile_picture_url}")
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
        courses = sigaa.get_active_courses()

        table = Table(title="Disciplinas Ativas", header_style="bold magenta")
        table.add_column("Code", style="cyan", no_wrap=True)
        table.add_column("Name", style="white")
        table.add_column("Location", style="white")
        table.add_column("Time", style="white")
        table.add_column("Term", style="white")

        for c in courses:
            table.add_row(str(c.code), str(c.name), str(c.location), str(c.time_code), str(c.term))

        console.print(table)
    finally:
        sigaa.close()

@cli.command("download-file", help="Baixa arquivo por URL absoluta (UFBA)")
@click.option("--url", required=True, help="URL base do SIGAA (ex.: https://sigaa.ufba.br)")
@click.option("--user", required=True)
@click.option("--password", required=True)
@click.option("--file-url", required=True, help="URL completa do arquivo a baixar")
@click.option("--dest", required=True, type=click.Path(path_type=Path, file_okay=False, dir_okay=True), help="Diretório destino")
def download_file(url: str, user: str, password: str, file_url: str, dest: Path) -> None:
    sigaa = Sigaa(institution=Institution.UFBA, url=url)
    try:
        sigaa.login(user, password)
        f = SigaaFile(sigaa._browser)  # uso interno controlado
        dest_path = f.download_get(file_url, dest)
        console.print(dest_path)
    finally:
        sigaa.close()


@cli.command("account-switch-bond", help="Troca vínculo ativo por matrícula (UFBA)")
@click.option("--url", required=True)
@click.option("--user", required=True)
@click.option("--password", required=True)
@click.option("--registration", required=True, help="Matrícula do vínculo discente para ativar")
def account_switch_bond(url: str, user: str, password: str, registration: str) -> None:
    sigaa = Sigaa(institution=Institution.UFBA, url=url)
    try:
        acc = sigaa.login(user, password)
        if not isinstance(acc, SigaaAccountUFBA):
            raise click.ClickException("Instituição não suportada neste comando.")
        acc.switch_bond_by_registration(registration)
        console.print("[green]Vínculo alterado (se disponível).[/green]")
    finally:
        sigaa.close()


@cli.command("student-courses", help="Lista cursos/turmas do discente (UFBA)")
@click.option("--url", required=True)
@click.option("--user", required=True)
@click.option("--password", required=True)
def student_courses(url: str, user: str, password: str) -> None:
    sigaa = Sigaa(institution=Institution.UFBA, url=url)
    try:
        acc = sigaa.login(user, password)
        if not isinstance(acc, SigaaAccountUFBA):
            raise click.ClickException("Instituição não suportada neste comando.")
        courses = list(acc.get_courses())
        table = Table(title="Cursos/Turmas", header_style="bold magenta")
        table.add_column("Title", style="white")
        table.add_column("Code", style="cyan", no_wrap=True)
        table.add_column("Period", style="white")
        table.add_column("Students", style="white", justify="right")
        for c in courses:
            table.add_row(str(c.title), str(c.code), str(c.period), str(c.number_of_students))
        console.print(table)
    finally:
        sigaa.close()


@cli.command("student-activities", help="Lista atividades do portal (UFBA)")
@click.option("--url", required=True)
@click.option("--user", required=True)
@click.option("--password", required=True)
def student_activities(url: str, user: str, password: str) -> None:
    sigaa = Sigaa(institution=Institution.UFBA, url=url)
    try:
        acc = sigaa.login(user, password)
        if not isinstance(acc, SigaaAccountUFBA):
            raise click.ClickException("Instituição não suportada neste comando.")
        for a in acc.get_activities():
            status = "[green]OK[/green]" if a.done else "[yellow]PEND[/yellow]"
            console.print(f"- [{a.date:%d/%m/%Y %H:%M}] {status} {a.type}: {a.title} ({a.course_title})")
    finally:
        sigaa.close()

def main() -> None:
    cli(prog_name="sigaa-api")


if __name__ == "__main__":
    main()
