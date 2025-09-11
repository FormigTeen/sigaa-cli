# SIGAA API (Python)

Port em Python do projeto sigaa-api com foco inicial em UFBA, usando httpx + selectolax para navegação/crawling e Mypy para tipagem.

- Python: >= 3.9
- HTTP: httpx (cliente) + selectolax (parser)
- Tipagem: Mypy (opcional, modo estrito configurado)

## Funcionalidades

- Login (UFBA) com validação de credenciais.
- Conta (UFBA):
  - Listar vínculos ativos/inativos e trocar vínculo por matrícula.
  - Obter nome e e-mails do usuário.
  - Obter matrícula (Registration) ativa do discente.
  - Obter URL e baixar foto de perfil.
  - Listar cursos/turmas do discente.
  - Listar atividades do portal do discente.
- Cursos:
  - Abrir turma por título, listar e baixar arquivos anexos (heurística).
- Busca pública:
  - Buscar docentes, listar resultados (nome, departamento, URL da página e foto), extrair e-mail e baixar foto do docente.

Observação: Suporte atual: UFBA.

### Status de Funcionalidades (Testes & Desenvolvimento)

| Funcionalidade                             | Status | Exemplo de comando                                                                                                    |
|--------------------------------------------| --- |-----------------------------------------------------------------------------------------------------------------------|
| Login (implícito nos comandos)             | ✅ | `sigaa-api account-name --provider UFBA --user USUARIO --password SENHA`                                              |
| Get Account                                | ✅ | `sigaa-api account --provider UFBA --user USUARIO --password SENHA`                                               |
| Listar vínculos (ativos/inativos)          | ⏳ |                                                                                                                       |
| Listar e-mails do usuário                  | ⏳ |                                                                                                                       |
| Trocar vínculo por matrícula               | ⏳ |                                                                                                                       |
| Listar cursos/turmas do discente           | ⏳ |                                                                                                                       |
| Listar atividades do portal do discente    | ⏳ |                                                                                                                       |
| Download de arquivo por URL (autenticado)  | ⏳ |                                                                                                                       |
| Busca de docentes (pública)                | ⏳ |                                                                                                                       |
| Abrir turma por título                     | ⏳ |                                                                                                                       |
| Listar/baixar arquivos da turma            | ⏳ |                                                                                                                       |
| Ver faltas e notas das turmas              | ⏳ |                                                                                                                       |
| Ver notícias publicadas nas turmas         | ⏳ |                                                                                                                       |
| Ver membros da turma (alunos/professores)  | ⏳ |                                                                                                                       |
| Ver foto de colegas e professores          | ⏳ |                                                                                                                       |
| Buscar docentes por campus                 | ⏳ |                                                                                                                       |
| Planos de ensino, atendimento, referências | ⏳ |                                                                                                                       |
| Alterar senha da conta                     | ⏳ |                                                                                                                       |
| Download de arquivos de todas as turmas    | ⏳ |                                                                                                                       |

Notas:
- As quatro primeiras entradas foram testadas manualmente (Login, Get Name, Get Matricula, Get Profile Image). As demais estão implementadas ou planejadas, mas ainda não validadas end‑to‑end nesta branch.
- “Abrir turma por título” e “Listar/baixar arquivos da turma” estão presentes na API programática e na documentação, mas os comandos de CLI específicos ainda não foram adicionados nesta branch.

## Instalação

1) Crie e ative um ambiente virtual (recomendado):

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows
```

2) Instale o pacote (modo desenvolvimento) e dependências de dev (opcional):

```bash
pip install -e .[dev]
```

3) (Opcional) Checar tipagem com Mypy:

```bash
mypy src/sigaa_api
```

## Uso via CLI

Após instalado, o comando de entrada é `sigaa-api` (ou `python -m sigaa_api`). Todos os comandos aceitam `--url` (URL base do SIGAA, ex.: `https://sigaa.ufba.br`), `--user` e `--password` quando exigem autenticação.

### Busca de docentes (pública)

```bash
sigaa-api search-teacher --url https://sigaa.ufba.br \
  --user SEU_USUARIO --password SUA_SENHA \
  --name "Nome do Docente" \
  --download-photo-dir ./fotos  # opcional
```

Saída: lista com nome, departamento e URL. Se `--download-photo-dir` for informado e houver foto, baixa a imagem.

### Conta (UFBA)

- Vínculos:

```bash
sigaa-api account-bonds --url https://sigaa.ufba.br \
  --user SEU_USUARIO --password SUA_SENHA
```

- Trocar vínculo por matrícula:

```bash
sigaa-api account-switch-bond --url https://sigaa.ufba.br \
  --user SEU_USUARIO --password SUA_SENHA \
  --registration 2023XXXXX
```

- Nome e e-mails:

```bash
sigaa-api account-name   --url https://sigaa.ufba.br --user ... --password ...
sigaa-api account-emails --url https://sigaa.ufba.br --user ... --password ...
```

- Foto de perfil (exibir URL e opcionalmente baixar):

```bash
sigaa-api account-profile-picture --url https://sigaa.ufba.br \
  --user ... --password ... \
  --download-dir ./fotos  # opcional
```

### Cursos do discente (UFBA)

- Listar cursos/turmas:

```bash
sigaa-api student-courses --url https://sigaa.ufba.br \
  --user ... --password ...
```

- Listar atividades do portal:

```bash
sigaa-api student-activities --url https://sigaa.ufba.br \
  --user ... --password ...
```

- Listar e baixar arquivos de uma turma (por título):

```bash
sigaa-api course-list-files --url https://sigaa.ufba.br \
  --user ... --password ... \
  --course-title "Algoritmos I"

sigaa-api course-download-files --url https://sigaa.ufba.br \
  --user ... --password ... \
  --course-title "Algoritmos I" --dest ./downloads
```

### Download direto por URL

Baixa um arquivo acessível com a sessão autenticada.

```bash
sigaa-api download-file --url https://sigaa.ufba.br \
  --user ... --password ... \
  --file-url https://sigaa.ufba.br/sigaa/.../arquivo.pdf \
  --dest ./downloads
```

## Uso Programático (Python)

### Uso rápido (alto nível `Sigaa`)

Os métodos abaixo seguem o mesmo padrão de cache usados em `get_name` e `get_email`, e agora incluem matrícula (Registration) e URL da foto de perfil.

```python
from sigaa_api import Sigaa, Institution

sigaa = Sigaa(institution=Institution.UFBA, url="https://sigaa.ufba.br")
try:
    sigaa.login("USUARIO", "SENHA")

    # Perfil do usuário (alto nível)
    print(sigaa.get_name())                 # Nome
    print(sigaa.get_email())                # Email
    print(sigaa.get_registration())         # Registration (Matrícula ativa)
    print(sigaa.get_profile_picture_url())  # URL da foto de perfil
finally:
    sigaa.close()
```

```python
from pathlib import Path
from sigaa_api import Sigaa, Institution

sigaa = Sigaa(institution=Institution.UFBA, url="https://sigaa.ufba.br")
try:
    account = sigaa.login("USUARIO", "SENHA")

    # Vínculos (API de conta UFBA)
    active = account.get_active_bonds()
    inactive = account.get_inactive_bonds()
    account.switch_bond_by_registration("2023XXXXX")

    # Cursos e atividades
    courses = account.get_courses()
    activities = account.get_activities()

    # Arquivos de uma turma por título
    cs = account.open_course_by_title("Algoritmos I")
    files = cs.list_files()
    saved = cs.download_files(Path("./downloads"))
finally:
    sigaa.close()
```

## Limitações e Notas

- Instituições suportadas nos recursos de conta: UFBA. Outras instituições podem apresentar variações de layout/fluxo, e serão adicionadas conforme demanda.
- A listagem de arquivos usa heurística sobre a página da turma; se sua instância SIGAA possuir seções específicas (ex.: "Materiais", "Conteúdo"), podemos refinar os seletores.
- As operações agora usam HTTP direto; não há navegador para visualizar.

## Desenvolvimento

- Formatação e tipagem:

```bash
mypy src/sigaa_api
```

- Usando Poe the Poet (tarefas):

```bash
# já incluso em extras de desenvolvimento
pip install -e .[dev]

# checagem de tipos
poe typecheck
# ou alias
poe mypy
```

- Estrutura principal do código:
  - `sigaa_api/sigaa.py`: Classe de alto nível `Sigaa` (browser + sessão + parser + login).
  - `sigaa_api/login.py`: Login UFBA.
  - `sigaa_api/accounts/ufba.py`: Conta UFBA (vínculos, cursos, atividades, perfil).
  - `sigaa_api/courses/*`: Modelos e navegação de turma.
  - `sigaa_api/resources/file.py`: Download via cliente HTTP (`httpx`).
  - `sigaa_api/search/teacher.py`: Busca pública de docentes (JSF) via `httpx`.

## Roadmap

- Adicionar suporte a outras instituições (quando necessário).
- Parser específico por tipo de recurso (materiais, notícias, fóruns etc.).
- Melhorar detecção de links de arquivos e navegação dentro da turma (JSF form actions).
