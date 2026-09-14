# Typing Backlog

Checklist para tornar o client dinamico, simples de usar e fortemente tipado sem
dependencias de runtime. Cada mudanca de protocolo deve preservar a compatibilidade
de dicts e a equivalencia entre as APIs sync e async.

## Schema E Codegen

- [x] Fixar no repositorio o JSON Schema oficial do Herdr correspondente ao protocolo 22 e a versao suportada.
- [x] Criar geradores baseados apenas na biblioteca padrao para produzir modelos, `Literal` e declaracoes `.pyi`.
- [ ] Gerar automaticamente os overloads `request()` sync/async a partir do schema.
- [x] Gerar os modelos e `Literal` a partir do schema, sem inferir tipos completos dos nomes de campos em `METHOD_SCHEMAS`.
- [x] Adicionar verificacao que falhe quando os artefatos gerados estiverem desatualizados.
- [x] Preservar `SCHEMA_PROTOCOL`, `SCHEMA_VERSION`, a contagem de 103 metodos e os conjuntos de conveniencia/stubs quando o protocolo nao mudar.

## JSON E Envelopes

- [x] Substituir `JsonDict = dict[str, Any]` em `src/herdr_client/protocol.py` por aliases recursivos de JSON sem `Any`.
- [x] Definir tipos para escalares, arrays, objetos, mapas JSON e valores desconhecidos de forma compativel com `TypedDict`.
- [x] Criar `TypedDicts` para request envelopes, response envelopes, error envelopes e eventos.
- [x] Tipar `id`, `method`, `params`, `result`, `error` e os campos opcionais dos envelopes oficiais.
- [x] Alterar `_decode_json()` para nao expor o `Any` retornado por `json.loads()`.
- [x] Isolar e validar explicitamente toda fronteira nao tipada de desserializacao.
- [x] Tornar `_raise_for_error()` seguro para valores JSON desconhecidos sem indexacao nao validada.
- [x] Tornar `_response_result()` capaz de retornar somente objetos JSON validados.
- [ ] Criar validadores runtime para os formatos de resposta publicados antes de expor resultados tipados.
- [x] Permitir campos desconhecidos nas respostas para manter compatibilidade com evolucao do servidor.

## Modelos Do Protocolo

- [x] Gerar um `TypedDict` de parametros para cada metodo canonico, usando `Required` e `NotRequired` conforme o schema.
- [ ] Gerar um tipo de resultado para cada metodo canonico com seus campos, enums e unions discriminadas.
- [x] Criar `Literal` para nomes de metodos, tags de resultado, estados, direcoes, formatos e outros enums oficiais.
- [ ] Tipar `METHOD_SCHEMAS` com metadados suficientes para relacionar metodo, parametros e resultado.
- [x] Manter os modelos de wire como dicionarios, sem trocar a API publica por dataclasses ou validadores externos.
- [x] Modelar os eventos de subscription como unions de `TypedDict` discriminadas pelo campo `event`.

## Request E Clientes

- [x] Adicionar overloads `Literal` para `request()` sync em `src/herdr_client/sync/client.py`.
- [x] Adicionar overloads `Literal` para `request()` async em `src/herdr_client/async_client/client.py`.
- [x] Manter um overload generico para nomes dinamicos e parametros desconhecidos.
- [x] Fazer cada overload associar corretamente o tipo de parametros ao tipo de resultado.
- [x] Tipar os dez wrappers de conveniencia com modelos de request e resultado especificos.
- [x] Remover `JsonDict` dos parametros e retornos publicos dos wrappers sync.
- [x] Remover `JsonDict` dos parametros e retornos publicos dos wrappers async.
- [x] Compartilhar os mesmos modelos entre os clientes sync e async.
- [x] Verificar que nomes, defaults, envelopes, excecoes e retornos sync/async permanecem equivalentes.
- [x] Criar `Protocol` publico para a interface sync usada por mocks e dependency injection.
- [x] Criar `Protocol` publico equivalente para a interface async.
- [x] Nao usar `Protocol` como substituto das declaracoes estaticas dos clientes dinamicos concretos.

## Metodos Dinamicos

- [x] Remover `Any` de `*args` e `**kwargs` nas factories de `src/herdr_client/stub_methods.py`.
- [x] Gerar declaracoes estaticas dos nomes instalados por `setattr` em `.pyi` ou em blocos `TYPE_CHECKING`.
- [x] Fazer as declaracoes estaticas dos 93 stubs e de `pane.graphics.stream` aparecerem no autocomplete e nos type checkers.
- [x] Representar os stubs nao implementados com assinaturas compativeis e retorno `Never`/`NoReturn` quando apropriado.
- [x] Preservar em runtime a geracao dinamica, `hasattr`, introspection e as mensagens atuais de `NotImplementedError`.
- [x] Adicionar teste que compare os metodos dinamicos em runtime com os metodos declarados estaticamente.

## Subscriptions E Transporte

- [x] Tipar filtros de subscription com `TypedDict` em `Subscription` e `AsyncSubscription`.
- [x] Criar tipos especificos para acknowledgement de subscription.
- [x] Fazer `Subscription.events()` retornar o tipo de evento tipado.
- [x] Fazer `AsyncSubscription.events()` retornar o mesmo modelo de evento em `AsyncIterator`.
- [x] Substituir `traceback: Any` por `TracebackType | None` nos context managers sync e async.
- [x] Tipar envelopes usados por `_send_envelope()`, `_read_json_line()` e seus equivalentes async.
- [x] Preservar a resolucao de socket, timeouts, cancelamento, fechamento e comportamento de excecoes.

## Testes E Tooling

- [ ] Remover `Any` desnecessario dos helpers tipados em `tests/test_client.py` e `tests/test_sync_client.py`.
- [x] Adicionar testes de contrato estatico com `assert_type` para wrappers, `request()` e subscriptions.
- [ ] Adicionar casos negativos para parametros ausentes, tipos incorretos, metodos invalidos e resultados invalidos.
- [ ] Garantir cobertura equivalente dos modelos e overloads nos testes sync e async.
- [x] Configurar Pyrefly para analisar `src`, o contrato em `tests` e arquivos `.pyi` relevantes.
- [ ] Habilitar gradualmente o preset `strict` do Pyrefly, usando baseline apenas durante a migracao.
- [ ] Adicionar uma meta de cobertura estrita de tipos e impedir novos `Any` na API publica.
- [x] Manter `ruff check .` e `ruff format --check .` sem excecoes para os artefatos gerados.
- [x] Manter zero dependencias externas de runtime ao implementar validacao e codegen.

## Distribuicao E Documentacao

- [x] Adicionar `src/herdr_client/py.typed` conforme a especificacao de distribuicao de tipos.
- [x] Garantir que `py.typed` e `.pyi` sejam incluidos pelo `uv build`.
- [x] Verificar o conteudo do wheel localmente, nao apenas o resultado do type checker no source tree.
- [x] Exportar os tipos publicos necessarios sem quebrar os imports existentes.
- [x] Documentar exemplos de uso simples com retorno tipado e acesso por indice de dict.
- [x] Documentar o fallback dinamico de `request()` e a perda intencional de precisao quando o nome do metodo nao e literal.

## Referencias

- [Herdr Socket API](https://herdr.dev/docs/socket-api/)
- [Python Typing Specification](https://typing.python.org/en/latest/spec/)
- [Protocols](https://typing.python.org/en/latest/spec/protocol.html)
- [TypedDict](https://typing.python.org/en/latest/spec/typeddict.html)
- [Overloads e Callables](https://typing.python.org/en/latest/spec/overload.html)
- [Distribuicao de informacao de tipos](https://typing.python.org/en/latest/spec/distributing.html)
- [Configuracao do Pyrefly](https://pyrefly.org/en/docs/configuration/)
