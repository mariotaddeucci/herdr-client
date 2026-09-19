# herdr-client

Clientes Python síncrono e assíncrono para a API de Unix socket do
[herdr](https://github.com/ogulcancelik/herdr). O pacote implementa o protocolo canônico
newline-delimited JSON sem dependências de runtime.

## Requisitos

- Python 3.13 ou superior
- `uv`
- Uma instância do herdr expondo o Unix socket

## Instalação

Para usar a versão publicada:

```bash
python -m pip install herdr-client
```

Ou com `uv`:

```bash
uv add herdr-client
```

Para desenvolvimento, instale o ambiente do repositório:

```bash
uv sync
```

O ambiente virtual, as dependências de desenvolvimento e o lockfile são gerenciados pelo
`uv`. O pacote não possui dependências de runtime.

## Imports

Os dois clientes podem ser importados diretamente pelo pacote principal:

```python
from herdr_client import AsyncHerdrClient, HerdrClient
```

Ou pelos subpacotes correspondentes:

```python
from herdr_client.async_client import AsyncHerdrClient
from herdr_client.sync import HerdrClient
```

## Uso síncrono

```python
from herdr_client import HerdrClient


client = HerdrClient()
print(client.ping())
print(client.workspace_list())
client.pane_send_input("w64e95948145ed1-1", text="pytest -q", keys=["Enter"])
```

## Uso assíncrono

```python
import asyncio

from herdr_client import AsyncHerdrClient


async def main() -> None:
    client = AsyncHerdrClient()

    print(await client.ping())
    print(await client.workspace_list())
    await client.pane_send_input("w64e95948145ed1-1", text="pytest -q", keys=["Enter"])


asyncio.run(main())
```

Os métodos de `HerdrClient` são síncronos. Os métodos de `AsyncHerdrClient` são
assíncronos e devem ser usados com `await`.

## Tipos

O pacote inclui `py.typed` e modelos `TypedDict` derivados do schema oficial. Os retornos
dos wrappers continuam sendo dicionários comuns, então o acesso por índice permanece
disponível:

```python
from herdr_client import HerdrClient, PongResult


result: PongResult = HerdrClient().ping()
print(result["version"])
```

`request()` possui overloads precisos quando o nome do método é literal e retorna um
`JsonObject` no fallback dinâmico. Os tipos compartilhados, como `ReadSource`, `OutputMatch`
e `EventSubscription`, estão disponíveis em `herdr_client` e `herdr_client.types`.

## Socket

Sem `socket_path` explícito, ambos os clientes seguem esta ordem:

1. `session="name"` no construtor
2. `HERDR_SOCKET_PATH`
3. `HERDR_SESSION=name`
4. `$HOME/.config/herdr/herdr.sock`

Sessões nomeadas usam `$HOME/.config/herdr/sessions/<name>/herdr.sock`.

```python
from pathlib import Path

from herdr_client import AsyncHerdrClient, HerdrClient


sync_client = HerdrClient(socket_path=Path("/run/user/1000/herdr.sock"))
async_client = AsyncHerdrClient(session="docs")
```

## Eventos

O cliente síncrono usa context manager e iterator:

```python
from herdr_client import HerdrClient


with HerdrClient().subscribe([{"type": "workspace.created"}]) as subscription:
    print(subscription.ack)
    for event in subscription.events():
        print(event)
```

O cliente assíncrono usa async context manager e async generator:

```python
import asyncio

from herdr_client import AsyncHerdrClient


async def watch_events() -> None:
    async with AsyncHerdrClient().subscribe(
        [{"type": "workspace.created"}]
    ) as subscription:
        print(subscription.ack)
        async for event in subscription.events():
            print(event)


asyncio.run(watch_events())
```

`Subscription.close()` e `AsyncSubscription.aclose()` são idempotentes.

## API

Os dois clientes oferecem a mesma superfície de operações:

- `request(method, params)`
- `ping()`
- `workspace_list()`
- `tab_list(workspace_id=None)`
- `pane_list(workspace_id=None)`
- `pane_send_text(pane_id, text)`
- `pane_send_keys(pane_id, keys)`
- `pane_send_input(pane_id, text="", keys=None)`
- `pane_read(pane_id, source="recent", lines=80, strip_ansi=True, format=None)`
- `pane_wait_for_output(...)`
- `subscribe(subscriptions)`

Métodos não reconhecidos pela API canônica geram `HerdrClientError`. Respostas de erro do
herdr geram `HerdrApiError`, que expõe os atributos `code` e `message`.

## Cobertura da API

O registro segue o schema oficial do herdr com protocolo `22` e contém 103 métodos JSON. Todos
os métodos oficiais JSON podem ser enviados pelo `request()` bruto. Os 10 métodos de conveniência
implementados são `ping`, `workspace_list`, `tab_list`, `pane_list`, `pane_send_text`,
`pane_send_keys`, `pane_send_input`, `pane_read`, `pane_wait_for_output` e `subscribe`.

Os demais métodos oficiais possuem stubs nomeados nos clientes sync e async e levantam
`NotImplementedError`, identificando o método e o schema correspondente. Use `request()`
quando precisar chamar um método ainda sem wrapper. Os metadados estão disponíveis por meio
de `METHOD_SCHEMAS`, `CANONICAL_METHODS`, `SCHEMA_PROTOCOL` e `SCHEMA_VERSION`.

`pane.graphics.stream` permanece separado porque usa framing híbrido: request JSON inicial,
headers JSON e bytes crus. Ele ainda levanta `NotImplementedError`.

O import legado `herdr_client.client` continua disponível para `AsyncHerdrClient`.

## Desenvolvimento

As configurações de `pytest`, `pytest-cov`, `ruff` e `pyrefly` ficam centralizadas no
`pyproject.toml`. O pre-commit executa verificações de estrutura, segredos, segurança,
formatação, lint e tipos antes de cada commit. A execução dos testes gera o relatório de
linhas não cobertas e exige no mínimo 90% de cobertura.

```bash
uv run pre-commit install
uv run pre-commit run --all-files
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyrefly check
uv build
PYTHONPATH=src uv run python tools/fetch_schema.py --check
PYTHONPATH=src uv run python tools/generate_models.py --check
PYTHONPATH=src uv run python tools/generate_stubs.py --check
```

### Integração com Herdr

Os testes live ficam em `tests/integration` e não rodam por padrão. Eles exigem um
socket explícito para evitar que a suíte use a sessão padrão por acidente:

```bash
HERDR_INTEGRATION_SOCKET="$HOME/.config/herdr/sessions/pytest/herdr.sock" \
  uv run pytest --run-integration -m integration --no-cov
```

Se o socket não estiver configurado, não existir ou não responder ao `ping`, as
fixtures marcam os testes live como `skipped` em vez de falhar a suíte.

As fixtures criam workspaces, tabs, panes e repositórios Git temporários dentro do
diretório da sessão do pytest e removem somente os recursos que criaram. Os comandos
enviados aos panes são limitados a `printf`, `pwd` e `true`; métodos de agentes,
integrações, plugins executáveis e operações globais ficam fora da fase geral.

O fluxo de agente é uma fase opt-in separada. Ele exige o executável local `opencode` e
usa somente o modelo gratuito `opencode/big-pickle`:

```bash
HERDR_INTEGRATION_SOCKET="$HOME/.config/herdr/sessions/pytest/herdr.sock" \
  uv run pytest --run-integration --run-agent-integration -m agent_integration --no-cov
```

Execute esse comando dentro de um contexto Herdr autorizado. O teste cria um workspace
isolado, inicia o OpenCode por `agent.start`, valida `agent.list`, `agent.get`,
`agent.read`, `agent.prompt` e `agent.wait`, e fecha o workspace ao terminar.

### Publicação

O workflow de publicação roda somente para tags que começam com `v` e exige que a tag
corresponda à versão em `pyproject.toml`. Depois de configurar o Trusted Publisher do
projeto `herdr-client` no PyPI e o ambiente `pypi` no GitHub, publique uma versão com:

```bash
git tag v0.2.0
git push origin v0.2.0
```

## Licença

Apache License 2.0.
