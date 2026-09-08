# sparksDB

[![CI](https://github.com/JefersondaCruz/sparksDB/actions/workflows/ci.yml/badge.svg)](https://github.com/JefersondaCruz/sparksDB/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Cliente Postgres desktop básico, no estilo DBeaver: conectar num banco, navegar schemas/tabelas e rodar SQL com resultado em grid. Feito pra uso pessoal e local — sem login, sem múltiplos usuários.

## Stack

- [Electron](https://www.electronjs.org/) + [electron-vite](https://electron-vite.org/) (scaffold com hot-reload)
- [Vue 3](https://vuejs.org/) + [Pinia](https://pinia.vuejs.org/) + [Tailwind CSS](https://tailwindcss.com/)
- [pg](https://node-postgres.com/) (driver Postgres, roda só no processo main)
- [Monaco Editor](https://microsoft.github.io/monaco-editor/) para o editor SQL
- [electron-store](https://github.com/sindresorhus/electron-store) + `safeStorage` do Electron para salvar conexões (a senha é criptografada usando o keychain do SO)

## Pré-requisitos

- Node.js 22 (o projeto foi criado e testado com essa versão via [nvm](https://github.com/nvm-sh/nvm))

```bash
nvm install 22
nvm use 22
```

## Rodando em desenvolvimento

```bash
npm install
npm run dev
```

Isso sobe o Vite em modo dev e abre a janela do Electron com hot-reload. Se o download automático do binário do Electron falhar durante o `npm install` (comum em redes restritas), rode manualmente:

```bash
node node_modules/electron/install.js
```

## Build / empacotamento

```bash
npm run build        # gera main/preload/renderer em out/
npm run build:linux  # gera AppImage + .deb em dist/ via electron-builder
```

## Como usar

1. **Conexões** (barra lateral): clique em "nova", preencha host/porta/database/usuário/senha, use "Testar" pra validar e "Salvar". A senha fica salva localmente criptografada (não sai da máquina).
2. Clique numa conexão salva pra conectar (bolinha fica verde quando conectado; clique de novo pra desconectar).
3. Com a conexão ativa, a árvore de **Schemas** aparece embaixo — clique num schema pra expandir e ver tabelas/views.
4. Clique numa tabela pra abrir uma aba com os **dados** (paginado) e a **estrutura** (colunas/tipos).
5. Clique em "+ Query" pra abrir uma aba de editor SQL. `Ctrl+Enter` ou o botão "Run" executa o texto do editor.

## Estrutura do projeto

```
src/
  main/            # processo principal do Electron (Node) - único lugar que fala com Postgres
    db/
      store.js         # persistência das conexões salvas (electron-store + safeStorage)
      pool-manager.js  # gerencia um pg.Pool por conexão ativa
      queries.js       # helpers de introspecção (schemas/tabelas/colunas) e leitura de dados
    index.js         # cria a janela e registra os handlers IPC
  preload/
    index.js         # expõe uma API restrita (window.sparksdb) pro renderer via contextBridge
  renderer/
    src/
      components/    # ConnectionManager, SchemaTree, QueryTab, ResultsGrid, TableDataView
      stores/        # Pinia: connections.js, tabs.js
```

## Escopo (o que não tem, de propósito)

Só Postgres, uso local single-user. Não tem: diagrama ER, export/import CSV, histórico de queries, autocomplete avançado de SQL, controle explícito de transação entre execuções de "Run", múltiplos usuários/autenticação. Se algum desses fizer falta, dá pra adicionar depois.

## Contribuindo

Contribuições são bem-vindas! Veja o [guia de contribuição](CONTRIBUTING.md)
para o fluxo de PR e como o projeto é mantido.

## Licença

[MIT](LICENSE)
