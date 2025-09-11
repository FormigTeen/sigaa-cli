from pathlib import Path
from typing import Optional

import click

from .sigaa import Sigaa, Institution
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


@cli.command("account-name", help="Mostra o nome do usuário (UFBA)")
@click.option("--url", required=True)
@click.option("--user", required=True)
@click.option("--password", required=True)
def account_name(url: str, user: str, password: str) -> None:
    sigaa = Sigaa(institution=Institution.UFBA, url=url)
    try:
        acc = sigaa.login(user, password)
        if not isinstance(acc, SigaaAccountUFBA):
            raise click.ClickException("Instituição não suportada neste comando.")
        click.echo(acc.get_name())
    finally:
        sigaa.close()


@cli.command("account-emails", help="Lista e-mails do usuário (UFBA)")
@click.option("--url", required=True)
@click.option("--user", required=True)
@click.option("--password", required=True)
def account_emails(url: str, user: str, password: str) -> None:
    sigaa = Sigaa(institution=Institution.UFBA, url=url)
    try:
        acc = sigaa.login(user, password)
        if not isinstance(acc, SigaaAccountUFBA):
            raise click.ClickException("Instituição não suportada neste comando.")
        for email in acc.get_emails():
            click.echo(email)
    finally:
        sigaa.close()


@cli.command("account-profile-picture", help="Mostra/baixa foto de perfil (UFBA)")
@click.option("--url", required=True)
@click.option("--user", required=True)
@click.option("--password", required=True)
@click.option("--download-dir", type=click.Path(path_type=Path, file_okay=False, dir_okay=True), default=None)
def account_profile_picture(url: str, user: str, password: str, download_dir: Optional[Path]) -> None:
    sigaa = Sigaa(institution=Institution.UFBA, url=url)
    try:
        acc = sigaa.login(user, password)
        if not isinstance(acc, SigaaAccountUFBA):
            raise click.ClickException("Instituição não suportada neste comando.")
        url = acc.get_profile_picture_url()
        click.echo(f"URL: {url}")
        if download_dir:
            dest = acc.download_profile_picture(download_dir)
            click.echo(f"Salvo em: {dest}")
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
        click.echo(dest_path)
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
        click.echo("Vínculo alterado (se disponível).")
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
        for c in acc.get_courses():
            click.echo(f"- {c.title} | código={c.code} | período={c.period} | alunos={c.number_of_students}")
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
            click.echo(f"- [{a.date:%d/%m/%Y %H:%M}] {'OK' if a.done else 'PEND'} {a.type}: {a.title} ({a.course_title})")
    finally:
        sigaa.close()


@cli.command("course-list-files", help="Lista arquivos (links de download) de um curso (UFBA)")
@click.option("--url", required=True)
@click.option("--user", required=True)
@click.option("--password", required=True)
@click.option("--course-title", required=True)
def course_list_files(url: str, user: str, password: str, course_title: str) -> None:
    sigaa = Sigaa(institution=Institution.UFBA, url=url)
    try:
        acc = sigaa.login(user, password)
        if not isinstance(acc, SigaaAccountUFBA):
            raise click.ClickException("Instituição não suportada neste comando.")
        cs = acc.open_course_by_title(course_title)
        for fl in cs.list_files():
            click.echo(f"- {fl.name} | {fl.url}")
    finally:
        sigaa.close()


@cli.command("course-download-files", help="Baixa arquivos do curso (UFBA)")
@click.option("--url", required=True)
@click.option("--user", required=True)
@click.option("--password", required=True)
@click.option("--course-title", required=True)
@click.option("--dest", required=True, type=click.Path(path_type=Path, file_okay=False, dir_okay=True))
def course_download_files(url: str, user: str, password: str, course_title: str, dest: Path) -> None:
    sigaa = Sigaa(institution=Institution.UFBA, url=url)
    try:
        acc = sigaa.login(user, password)
        if not isinstance(acc, SigaaAccountUFBA):
            raise click.ClickException("Instituição não suportada neste comando.")
        cs = acc.open_course_by_title(course_title)
        for p in cs.download_files(dest):
            click.echo(p)
    finally:
        sigaa.close()


def main() -> None:
    cli(prog_name="sigaa-api")


if __name__ == "__main__":
    main()
