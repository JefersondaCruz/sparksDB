# Política de Segurança

## Reportando uma vulnerabilidade

Se você encontrar uma vulnerabilidade de segurança no sparksDB (por exemplo,
algo relacionado a como credenciais de conexão são armazenadas/criptografadas,
ou execução de SQL), por favor **não abra uma issue pública**.

Reporte de forma privada usando a aba [Security > Report a
vulnerability](../../security/advisories/new) deste repositório no GitHub.
Isso cria um relatório visível só para o mantenedor até que o problema seja
corrigido.

Vou tentar responder o mais rápido possível, avaliar o impacto e lançar uma
correção antes de divulgar publicamente os detalhes.

## Escopo

Este é um projeto de uso pessoal/local (sem servidor remoto, sem
multiusuário). O modelo de ameaça principal é: proteção das credenciais de
conexão salvas localmente e do processo que executa SQL arbitrário contra o
banco configurado pelo próprio usuário.
