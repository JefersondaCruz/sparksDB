# Instruções para o Claude neste projeto

## Git: commit e push sempre pelo usuário

Nunca rode `git commit` ou `git push` (ou qualquer ação que publique algo em
nome do usuário) diretamente. Prepare as mudanças e peça para o usuário
(Jeferson) executar o commit/push ele mesmo — inclusive quando for só passar
o comando pronto pra ele copiar/colar. O motivo: é um repositório open source
público, e o histórico do GitHub deve refletir que as ações (commits, pushes)
foram feitas por ele, não pelo assistente.

Se for necessário compor uma mensagem de commit, monte o texto e entregue o
comando completo pro usuário rodar — não execute via Bash.

## Idioma: branch e commit em inglês

Nomes de branch e a linha de assunto (título) do commit devem ser em
**inglês** (padrão de convenção comum em open source). A descrição/corpo do
commit (linhas depois do título, explicando o porquê) pode ser em
**português**. Documentação do projeto (README, CONTRIBUTING, etc.) continua
em português conforme já decidido.
