# sparksDB

[![CI](https://github.com/JefersondaCruz/sparksDB/actions/workflows/ci.yml/badge.svg)](https://github.com/JefersondaCruz/sparksDB/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Cliente Postgres desktop básico, no estilo DBeaver: conectar num banco, navegar schemas/tabelas e rodar SQL com resultado em grid. Feito pra uso pessoal e local — sem login, sem múltiplos usuários.

## Stack

- [pywebview](https://pywebview.flowrl.com/) (janela nativa com o webview do sistema — WebKitGTK no Linux — e ponte JS ↔ Python)
- [Vue 3](https://vuejs.org/) + [Pinia](https://pinia.vuejs.org/) + [Tailwind CSS](https://tailwindcss.com/)
- [psycopg 3](https://www.psycopg.org/psycopg3/) + [psycopg_pool](https://www.psycopg.org/psycopg3/docs/advanced/pool.html) (driver e pool Postgres, rodam só no backend Python)
- [Monaco Editor](https://microsoft.github.io/monaco-editor/) para o editor SQL
- [keyring](https://github.com/jaraco/keyring) para salvar conexões (a senha fica no keychain do SO)

## Instalando (só pra usar)

Baixe o `sparksDB-<versão>-x86_64.AppImage` (artefato `sparksdb-appimage` do último build na aba Actions) e:

```bash
chmod +x sparksDB-*-x86_64.AppImage
./sparksDB-*-x86_64.AppImage
```

Não precisa de sudo nem de instalar nada: roda no Ubuntu Desktop 24.04 ou mais novo, usando o Python e o WebKit que já vêm no sistema.

## Pré-requisitos (pra desenvolver)

- Ubuntu Desktop 24.04+ (o Python 3 e o WebKitGTK já vêm instalados)
- Node.js 22 (o projeto foi criado e testado com essa versão via [nvm](https://github.com/nvm-sh/nvm))

```bash
nvm install 22
nvm use 22
```

Não precisa de sudo: o `npm run setup` cria um ambiente Python isolado em `.venv/`, dentro do projeto.

## Rodando em desenvolvimento

```bash
npm install
npm run setup   # uma vez: cria .venv/ com as dependências Python
npm run dev
```

O `npm run dev` sobe o Vite em modo dev e abre a janela do pywebview apontando pra ele, com hot-reload do frontend. Mudanças no backend Python pedem reiniciar o `npm run dev`.

### Testes do backend

Os testes que falam com Postgres precisam de um banco descartável:

```bash
docker run -d --rm --name sparksdb-test-pg -p 55432:5432 -e POSTGRES_PASSWORD=postgres postgres:16
export SPARKSDB_TEST_DSN="host=127.0.0.1 port=55432 dbname=postgres user=postgres password=postgres"
npm run test:backend
```

Sem `SPARKSDB_TEST_DSN`, esses testes são pulados.

## Build / empacotamento

```bash
npm run build:appimage   # build do frontend + gera build/sparksDB-<versão>-x86_64.AppImage
```

O AppImage leva dentro o app e as dependências Python (psycopg com a própria libpq, pywebview, keyring), com as partes compiladas para Python 3.12, 3.13 e 3.14. Ele usa o `python3`, o GTK e o WebKitGTK do sistema. Pra suportar um Python mais novo, adicione a versão em `PYTHON_VERSIONS` no `scripts/build-appimage.sh`.

## Como usar

1. **Conexões** (barra lateral): clique em "nova", preencha host/porta/database/usuário/senha, use "Testar" pra validar e "Salvar". A senha fica salva localmente criptografada (não sai da máquina).
2. Clique numa conexão salva pra conectar (bolinha fica verde quando conectado; clique de novo pra desconectar).
3. Com a conexão ativa, a árvore de **Schemas** aparece embaixo — clique num schema pra expandir e ver tabelas/views.
4. Clique numa tabela pra abrir uma aba com os **dados** (paginado) e a **estrutura** (colunas/tipos).
5. Clique em "+ Query" pra abrir uma aba de editor SQL. `Ctrl+Enter` ou o botão "Run" executa o texto do editor.

## Nota para quem já usava a versão Electron

Desde a versão Tauri, o sparksDB usa um diretório de configuração diferente da versão antiga (Electron), e o arquivo de conexões tem outro formato. Ou seja: as conexões salvas na versão anterior **não aparecem automaticamente** aqui — é preciso recriá-las na barra lateral. As senhas antigas também não dão pra migrar: ficavam criptografadas pelo `safeStorage` do Electron, que só o próprio Electron consegue ler. Nada foi apagado, o arquivo antigo continua onde estava (`~/.config/sparksDB/`), só não é mais lido.

Já quem vem da versão Tauri não perde nada: o backend Python lê o mesmo diretório de configuração e o mesmo keyring, então as conexões e queries salvas continuam aparecendo.

## Estrutura do projeto

```
backend/
  pyproject.toml       # dependências e config do pytest
  sparksdb/
    __main__.py        # entrypoint: cria a janela do pywebview (dev ou dist/)
    api.py             # métodos expostos ao frontend via window.pywebview.api
    paths.py           # diretório de config e leitura/escrita de JSON
    store.py           # conexões salvas (senha no keyring, fallback em arquivo)
    saved_queries.py   # queries salvas por conexão
    pool_manager.py    # um psycopg_pool por conexão ativa + execução de SQL
    queries.py         # introspecção (schemas/tabelas/colunas) e leitura de dados
  tests/               # pytest
scripts/
  setup-dev.sh         # cria .venv/ sem sudo
  build-appimage.sh    # gera o AppImage
src/
  api/
    sparksdb.js        # wrapper que chama o backend via window.pywebview.api
  components/          # ConnectionManager, SchemaTree, QueryTab, ResultsGrid, TableDataView, SavedQueries
  stores/              # Pinia: connections.js, tabs.js, savedQueries.js
  App.vue
  main.js
```

## Escopo (o que não tem, de propósito)

Só Postgres, uso local single-user. Não tem: conexão via SSL/TLS (o campo existe no formulário, mas marcar SSL devolve um erro explícito em vez de conectar sem criptografia), diagrama ER, export/import CSV, histórico de queries, autocomplete avançado de SQL, controle explícito de transação entre execuções de "Run", múltiplos usuários/autenticação. Se algum desses fizer falta, dá pra adicionar depois.

## Contribuindo

Contribuições são bem-vindas! Veja o [guia de contribuição](CONTRIBUTING.md)
para o fluxo de PR e como o projeto é mantido.

## Licença

[MIT](LICENSE)
