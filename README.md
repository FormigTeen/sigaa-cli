# SIGAA CLI

Ferramenta de linha de comando para interagir com o SIGAA (foco inicial: UFBA), construída sobre Playwright. Oferece comandos para autenticação, consulta de conta, listagem de cursos/disciplinas ativas e mais.

- Python: >= 3.9
- Navegação: Playwright (Chromium headless)
- Tipagem: Mypy (opcional; modo estrito configurado)

Observação: O pacote Python interno foi renomeado para `sigaa_cli`.

## Instalação

1) Crie e ative um ambiente virtual (recomendado):

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows (PowerShell)
```

2) Instale em modo desenvolvimento (opcionalmente com extras):

```bash
pip install -e .[dev]
```

3) Instale o navegador do Playwright (uma vez por ambiente):

```bash
python -m playwright install chromium
```

Após instalado, o comando de entrada é `sigaa-cli` (ou `sigaa_cli`).

## Configuração

Você pode passar `--provider`, `--user` e `--password` por linha de comando ou definir via variáveis de ambiente/`.env`.

- `SIGAA_CLI_DEFAULT_PROVIDER`: Provedor padrão (ex.: `UFBA`).
- `SIGAA_CLI_USER`: Usuário para login.
- `SIGAA_CLI_PASSWORD`: Senha para login.
- `SIGAA_CLI_DATA_PATH`: Pasta base para dados/cache (padrão: `/tmp/sigaa`).

Arquivo `.env` é carregado automaticamente (se presente) via `python-dotenv`.

## Comandos

Todos os comandos suportam as opções comuns quando aplicável:

- `--provider`: Provedor/instituição (ex.: `UFBA`).
- `--user`: Usuário para autenticação.
- `--password`: Senha para autenticação.

Comandos disponíveis:

- `programs`: Lista cursos/graduações (UFBA)
  - Ex.: `sigaa-cli programs --provider UFBA --user ... --password ...`
- `courses`: Lista disciplinas (UFBA)
  - Ex.: `sigaa-cli courses --provider UFBA --user ... --password ...`
- `sections`: Lista turmas/seções (UFBA)
  - Ex.: `sigaa-cli sections --provider UFBA --user ... --password ...`
- `account`: Mostra informações da conta do usuário autenticado
  - Ex.: `sigaa-cli account --provider UFBA --user ... --password ...`
- `active-courses`: Lista as disciplinas ativas do discente
  - Ex.: `sigaa-cli active-courses --provider UFBA --user ... --password ...`

Alguns comandos aceitam `--no-cache` para ignorar cache local.

## Exemplos rápidos

Listar disciplinas ativas:

```bash
sigaa-cli active-courses --provider UFBA --user USUARIO --password SENHA
```

Exibir dados da conta:

```bash
sigaa-cli account --provider UFBA --user USUARIO --password SENHA
```

Listar cursos/graduações (programs):

```bash
sigaa-cli programs --provider UFBA --user USUARIO --password SENHA --no-cache
```

## Uso Programático (opcional)

O pacote interno para uso como biblioteca é `sigaa_cli`. Exemplos:

```python
from sigaa_cli import Sigaa, Institution

sigaa = Sigaa(institution=Institution.UFBA, url="https://sigaa.ufba.br")
try:
    sigaa.login("USUARIO", "SENHA")
    print(sigaa.get_name())
finally:
    sigaa.close()
```

## Como Contribuir

- Abra issues descrevendo bugs ou novas funcionalidades.
- Faça um fork e crie branches temáticas.
- Mantenha mudanças focadas e com descrição clara no PR.
- Siga o padrão dos módulos existentes e mantenha tipagem quando possível.

Checklist local:

```bash
pip install -e .[dev]
python -m playwright install chromium
mypy src/sigaa_cli
```

## Desenvolvimento

- Tipagem (mypy, modo estrito):

```bash
mypy src/sigaa_cli
```

- Tarefas via Poe the Poet:

```bash
poe typecheck  # alias: poe mypy
```

Estrutura principal do código:

- `sigaa_cli/sigaa.py`: Classe de alto nível `Sigaa` (browser + sessão + parser + login).
- `sigaa_cli/accounts/ufba.py`: Conta UFBA (vínculos, cursos, atividades, perfil).
- `sigaa_cli/courses/*`: Modelos e navegação de turma.
- `sigaa_cli/resources/file.py`: Download via Playwright.
- `sigaa_cli/search/teacher.py`: Busca pública de docentes.

## Notas e Limitações

- Suporte atual focado em UFBA; outras instituições podem variar o fluxo e layout.
- Requer instalação do Chromium via Playwright para execução dos comandos que navegam no SIGAA.
