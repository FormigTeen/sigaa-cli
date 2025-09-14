from pathlib import Path
from typing import Optional

import rich_click as click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from .sigaa import Sigaa
from .types import  Institution
from .accounts.ufba import SigaaAccountUFBA
from .resources.file import SigaaFile


@click.group()
def cli() -> None:
    """CLI para interagir com o SIGAA."""
    pass


@cli.command("programs", help="Lista de Cursos (UFBA)")
@click.option("--provider", required=False)
@click.option("--user", required=False)
@click.option("--password", required=False)
def programs(provider: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None) -> None:
    sigaa = Sigaa(institution=provider)
    try:
        sigaa.login(user, password)
        sigaa.get_programs()
    finally:
        sigaa.close()


@cli.command("sections", help="Lista de Cursos (UFBA)")
@click.option("--provider", required=False)
@click.option("--user", required=False)
@click.option("--password", required=False)
def sections(provider: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None) -> None:
    sigaa = Sigaa(institution=provider)
    try:
        sigaa.login(user, password)
        sigaa.get_sections()
    finally:
        sigaa.close()

@cli.command("account", help="Mostra o nome do usuário)")
@click.option("--provider", required=False)
@click.option("--user", required=False)
@click.option("--password", required=False)
def get_account(provider: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None) -> None:
    sigaa = Sigaa(institution=provider)
    try:
        sigaa.login(user, password)
        account = sigaa.get_account()
        console = Console()

        grid = Table.grid(padding=(0, 2))
        grid.add_column(style="bold cyan", justify="right", no_wrap=True)
        grid.add_column()
        grid.add_row("Matrícula", account.registration or "-")
        grid.add_row("Nome", account.name or "-")
        grid.add_row("Curso", account.program or "-")
        grid.add_row("Email", account.email or "-")
        grid.add_row("Imagem de Perfil", account.profile_picture_url or "-")

        panel = Panel(
            grid,
            title=f"Conta | {account.name or 'Usuário'}",
            title_align="left",
            border_style="green",
            box=box.ROUNDED,
        )

        console.print(panel)
    finally:
        sigaa.close()


@cli.command("active-courses", help="Lista disciplinas ativas do discente")
@click.option("--provider", required=False)
@click.option("--user", required=False)
@click.option("--password", required=False)
def active_courses(provider: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None) -> None:
    sigaa = Sigaa(institution=provider)
    try:
        sigaa.login(user, password)
        courses = sigaa.get_active_courses()

        console = Console()
        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=box.SIMPLE_HEAVY,
            show_lines=False,
            title="Disciplinas Ativas",
            title_style="bold magenta",
        )

        table.add_column("Code", style="bold", no_wrap=True)
        table.add_column("Name")
        table.add_column("Location", style="dim")
        table.add_column("Time", style="dim", no_wrap=True)
        table.add_column("Term", no_wrap=True)

        for c in courses:
            table.add_row(c.code, c.name, c.table_location or "-", '|'.join(c.time_codes) or "-", c.term or "-")

        console.print(table)
    finally:
        sigaa.close()

def main() -> None:
    cli(prog_name="sigaa-api")


if __name__ == "__main__":
    main()
