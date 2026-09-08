# sparksDB

[![CI](https://github.com/JefersondaCruz/sparksDB/actions/workflows/ci.yml/badge.svg)](https://github.com/JefersondaCruz/sparksDB/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Cliente Postgres desktop básico, no estilo DBeaver: conectar num banco, navegar schemas/tabelas e rodar SQL com resultado em grid. Feito pra uso pessoal e local — sem login, sem múltiplos usuários.

## Stack

- [Tauri 2](https://tauri.app/) (shell nativo em Rust + webview do sistema, sem Node/Chromium empacotado)
- [Vue 3](https://vuejs.org/) + [Pinia](https://pinia.vuejs.org/) + [Tailwind CSS](https://tailwindcss.com/)
- [tokio-postgres](https://github.com/sfackler/rust-postgres) + [deadpool-postgres](https://github.com/bikeshedder/deadpool) (driver e pool Postgres, rodam só no backend Rust)
- [Monaco Editor](https://microsoft.github.io/monaco-editor/) para o editor SQL
- [keyring](https://github.com/hwchen/keyring-rs) para salvar conexões (a senha é criptografada usando o keychain do SO)

## Pré-requisitos

- Node.js 22 (o projeto foi criado e testado com essa versão via [nvm](https://github.com/nvm-sh/nvm))
- Rust estável (via [rustup](https://rustup.rs/)) e, no Linux, os pacotes de sistema: `libwebkit2gtk-4.1-dev`, `libssl-dev`, `libgtk-3-dev`, `librsvg2-dev`, `patchelf`, `libdbus-1-dev` (este último exigido pela feature `sync-secret-service` do `keyring`, que linka contra libdbus em tempo de build). Veja também o [guia de pré-requisitos do Tauri](https://tauri.app/start/prerequisites/) para outras plataformas.

```bash
nvm install 22
nvm use 22
```

## Rodando em desenvolvimento

```bash
npm install
npm run dev
```

Isso sobe o Vite em modo dev e abre a janela do Tauri (webview do sistema) com hot-reload do frontend.

## Build / empacotamento

```bash
npm run build:vite   # build de produção do frontend Vue em dist/
npm run build:linux  # tauri build: compila o backend Rust em release e gera AppImage + .deb em src-tauri/target/release/bundle/
```

## Como usar

1. **Conexões** (barra lateral): clique em "nova", preencha host/porta/database/usuário/senha, use "Testar" pra validar e "Salvar". A senha fica salva localmente criptografada (não sai da máquina).
2. Clique numa conexão salva pra conectar (bolinha fica verde quando conectado; clique de novo pra desconectar).
3. Com a conexão ativa, a árvore de **Schemas** aparece embaixo — clique num schema pra expandir e ver tabelas/views.
4. Clique numa tabela pra abrir uma aba com os **dados** (paginado) e a **estrutura** (colunas/tipos).
5. Clique em "+ Query" pra abrir uma aba de editor SQL. `Ctrl+Enter` ou o botão "Run" executa o texto do editor.

## Nota para quem já usava a versão Electron

Esta versão (Tauri/Rust) usa um diretório de configuração diferente da versão antiga (Electron), e o arquivo de conexões tem outro formato. Ou seja: as conexões salvas na versão anterior **não aparecem automaticamente** aqui — é preciso recriá-las na barra lateral. As senhas antigas também não dão pra migrar: ficavam criptografadas pelo `safeStorage` do Electron, que só o próprio Electron consegue ler. Nada foi apagado, o arquivo antigo continua onde estava (`~/.config/sparksDB/`), só não é mais lido.

## Estrutura do projeto

```
src-tauri/
  src/
    main.rs            # entrypoint do binário Tauri
    lib.rs             # registra os commands e o estado gerenciado
    state.rs           # estado compartilhado da aplicação
    store.rs           # persistência das conexões salvas (keyring para a senha)
    pool_manager.rs     # gerencia um deadpool-postgres::Pool por conexão ativa
    queries.rs          # helpers de introspecção (schemas/tabelas/colunas) e leitura de dados
    commands/
      connections.rs     # commands Tauri de CRUD/teste de conexões
      db.rs               # commands Tauri de conectar/desconectar/rodar query
src/
  api/
    sparksdb.js        # wrapper que chama os commands Tauri via invoke()
  components/          # ConnectionManager, SchemaTree, QueryTab, ResultsGrid, TableDataView
  stores/              # Pinia: connections.js, tabs.js
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
