# TODO

## Projeto e tooling

- [x] Criar `pyproject.toml` como fonte central de configuração do projeto.
- [x] Configurar Python `3.13+` em `requires-python`.
- [x] Configurar o build do pacote com Hatchling.
- [x] Configurar o layout `src/herdr_client`.
- [x] Gerenciar ambiente, dependências e comandos exclusivamente com `uv`.
- [x] Adicionar e versionar `uv.lock`.
- [x] Adicionar `pytest` e `pytest-asyncio` como dependências de desenvolvimento.
- [x] Adicionar `ruff` como ferramenta de lint e formatação.
- [x] Adicionar `pyrefly` para análise estática e tipagem.
- [x] Centralizar no `pyproject.toml` as configurações do `pytest`, `ruff` e `pyrefly`.
- [x] Manter zero dependências de runtime, usando `asyncio` da biblioteca padrão.

## Transporte assíncrono

- [x] Implementar conexão com Unix domain socket usando `asyncio.open_unix_connection`.
- [x] Implementar timeout configurável para conexão, escrita e leitura.
- [x] Implementar envio e leitura de envelopes JSON newline-delimited.
- [x] Fechar corretamente `StreamReader` e `StreamWriter` em sucesso, erro e cancelamento.
- [x] Preservar a resolução de socket por `session`, `HERDR_SOCKET_PATH`, `HERDR_SESSION` e caminho padrão.

## Cliente

- [x] Implementar `AsyncHerdrClient` como cliente assíncrono explícito.
- [x] Implementar `async request(...)` com validação dos métodos canônicos.
- [x] Implementar `async ping()`.
- [x] Implementar `async workspace_list()`.
- [x] Implementar `async tab_list(...)`.
- [x] Implementar `async pane_list(...)`.
- [x] Implementar `async pane_send_text(...)`.
- [x] Implementar `async pane_send_keys(...)`.
- [x] Implementar `async pane_send_input(...)`.
- [x] Implementar `async pane_read(...)`.
- [x] Implementar `async pane_wait_for_output(...)`.
- [x] Preservar os envelopes e formatos de parâmetros do cliente original.
- [x] Exportar `AsyncHerdrClient`, as exceções e as funções de resolução de socket no pacote público.

## Subscription de eventos

- [x] Implementar subscription como async context manager.
- [x] Expor o acknowledgement da subscription por meio de `ack`.
- [x] Implementar `aclose()` idempotente.
- [x] Implementar `events()` como async generator.
- [x] Tratar EOF, erros retornados pela API, timeout e cancelamento sem deixar recursos abertos.

## Exceções

- [x] Preservar `HerdrClientError` para erros locais de transporte e validação.
- [x] Preservar `HerdrApiError` para envelopes de erro retornados pelo herdr.
- [x] Manter disponíveis `code` e `message` em `HerdrApiError`.

## Testes

- [x] Criar fixture de servidor Unix socket assíncrono para os testes.
- [x] Testar round-trip de requests e respostas.
- [x] Testar construção correta dos envelopes e parâmetros.
- [x] Testar respostas de erro da API.
- [x] Testar rejeição de métodos não canônicos.
- [x] Testar resolução de socket e precedência das variáveis de ambiente.
- [x] Testar subscription, acknowledgement e múltiplos eventos.
- [x] Testar socket fechado antes da resposta.
- [x] Testar timeout e cancelamento.
- [x] Testar fechamento de recursos após sucesso e exceções.

## Documentação e verificação

- [x] Atualizar `README.md` com instalação usando `uv`.
- [x] Documentar exemplos com `await` e `async with`.
- [x] Documentar a resolução de socket e o tratamento de erros.
- [x] Executar `uv run pytest`.
- [x] Executar `uv run ruff check .`.
- [x] Executar `uv run ruff format --check .`.
- [x] Executar `uv run pyrefly check`.
- [x] Corrigir falhas encontradas pelas verificações.

## Upgrade sync e async

- [x] Extrair tipos, métodos canônicos e parsing de envelopes para `protocol.py`.
- [x] Criar o subpacote `herdr_client.sync`.
- [x] Criar o subpacote `herdr_client.async_client`.
- [x] Implementar `HerdrClient` síncrono com a mesma superfície do cliente assíncrono.
- [x] Implementar `Subscription` síncrona com `with`, `for` e `close()`.
- [x] Mover `AsyncHerdrClient` e `AsyncSubscription` para `async_client`.
- [x] Exportar `HerdrClient` e `AsyncHerdrClient` pelo pacote principal.
- [x] Preservar o import legado `herdr_client.client` por meio de um shim.
- [x] Adicionar testes equivalentes para as APIs sync e async.
- [x] Testar imports pelo pacote principal e pelos dois subpacotes.
- [x] Atualizar README com exemplos sync e async.
- [x] Atualizar a versão do pacote para `0.2.0`.
- [x] Executar `uv lock` e atualizar `uv.lock`.
- [x] Executar `uv run pytest`.
- [x] Executar `uv run ruff check .`.
- [x] Executar `uv run ruff format --check .`.
- [x] Executar `uv run pyrefly check`.
- [x] Executar `uv build`.

## Auditoria da API Herdr 0.9.0

- [x] Atualizar `CANONICAL_METHODS` para os 103 métodos do schema oficial, protocolo 22.
- [x] Remover `agent.send` e adicionar `agent.send_keys`.
- [x] Adicionar metadados de schema, campos obrigatórios e propriedades opcionais.
- [x] Permitir todos os métodos oficiais por meio de `request()`.
- [x] Adicionar stubs sync e async para métodos oficiais sem wrapper.
- [x] Fazer os stubs levantarem `NotImplementedError` com método e schema identificados.
- [x] Manter `pane.graphics.stream` separado por usar framing híbrido.
- [x] Adicionar o parâmetro `format` ao wrapper `pane_read`.
- [x] Manter `HerdrClientError` para métodos desconhecidos ou inválidos.
- [x] Adicionar testes para contagem, registro, metadados e stubs.
- [x] Documentar a cobertura da API e as limitações atuais.
