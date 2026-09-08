# Contribuindo com o sparksDB

Obrigado pelo interesse em contribuir! O sparksDB é um projeto pessoal, mas
aberto a contribuições da comunidade. Este documento explica como propor
mudanças.

## Antes de começar

Para mudanças pequenas (typos, bugs simples, ajustes de UI), pode abrir a PR
direto. Para mudanças maiores (nova feature, mudança de arquitetura), abra
uma [issue](../../issues/new/choose) primeiro descrevendo o que você quer
fazer, pra alinhar antes de codar.

## Fluxo de contribuição

1. Faça um fork do repositório.
2. Crie uma branch a partir da `main`, com nome em inglês: `git checkout -b fix-connection-timeout` (ou `feat-...`, `docs-...`).
3. Rode o projeto localmente (veja o [README](README.md#rodando-em-desenvolvimento)):
   ```bash
   npm install
   npm run dev
   ```
4. Faça suas mudanças. Mantenha o escopo da PR pequeno e focado em uma coisa só.
5. Confirme que o build passa: `npm run build`.
6. Abra um Pull Request contra a `main` descrevendo o que mudou e por quê.

## Como as PRs são revisadas e mergeadas

Este projeto tem um único mantenedor. Todas as PRs passam por revisão e o
merge é feito manualmente por ele — isso não é um julgamento sobre a
qualidade da contribuição, é só como o projeto é governado. Pode levar um
tempo até a revisão acontecer; issues e PRs não são esquecidas, só tem fila.

- A branch `main` é protegida: não é possível dar push direto nela.
- Todo merge passa por PR + checks de CI.
- Só o mantenedor tem permissão de merge.

## Estilo de código

Não tem linter configurado ainda, mas siga o padrão que já existe no
arquivo que você está mexendo (nomes em português no domínio da UI, código em
inglês/português misto como já está no projeto, componentes Vue com
`<script setup>`).

## Commits

O título (primeira linha) do commit deve ser em **inglês** (ex.: `fix: handle
connection timeout`). O corpo, explicando o porquê, pode ser em português.

## Reportando bugs

Abra uma issue usando o template de bug report, com passos pra reproduzir,
comportamento esperado vs. observado, e versão do SO/Node quando relevante.

## Dúvidas

Abra uma issue com a tag `question` ou comente em uma issue/PR existente.
