---
name: kanban-orchestration
description: "Orquestrar time via kanban: tasks, monitor, recovery."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [kanban, orchestration, multi-profile, delegation, merge]
    related_skills: [hermes-multi-profile-ops, github-pr-workflow, i-have-adhd]
---

# Kanban Orchestration

Fluxo operacional do ORQUESTRADOR sobre o kanban do Hermes, validado em entrega real multi-perfil (repo datalake-mega, 10 tasks, 2 demandas). Complementa a skill `hermes-multi-profile-ops` (do usuário: gestão de perfis/SOUL/skills + inventário do time); esta carrega o padrão de orquestração: criar tasks, dependências, monitoramento async, recovery de crash e merge.

## Quando usar
- Delegar features para os perfis via kanban (backend/frontend/database/designer)
- Acompanhar N workers em paralelo sem gastar turnos com polling
- Task de worker que crashou no protocolo ou se auto-bloqueou pedindo revisão

## Fluxo (resumo)
1. Entender demanda → quebrar em tasks ENXUTAS (título + o que + criterio de pronto). Feature ambígua: no maximo 1 pergunta.
2. Criar tasks: `--workspace "dir:<abs-repo>"` (scratch é efêmero e some ao completar), `--priority <int>`, `--parent <id>` repetível para dependências.
3. DEFINIR CONTRATO nos bodies (schema SQL, shape JSON da API, nomes de tabela) → database/backend/frontend rodam em PARALELO sem pisar um no outro.
4. Monitorar com script background + `notify_on_complete=true` — NUNCA polling com sleep (usuario corrigiu explicitamente: quer notificação na hora exata).
5. Quando fechar: VERIFICAR entrega real (arquivos existem, build/testes rodam, log mostra sucesso) — nunca confiar em self-report.
6. Revisar auto-blocks, completar, rodar verificacao unica pre-PR (pytest + ruff + review), commit, PR, merge squash + limpeza de branch.

## Pitfalls reais do CLI kanban
- `--priority` é INT (10/5), nao string: `--priority high` → `invalid int value` (erro vai pro stderr — nao suprimir stderr ao debugar).
- `create` NÃO tem flag `--json`: capturar o ID no stdout com `grep -o 't_[a-f0-9]*'` (output "Created t_XXXX").
- Warning "No gateway is running" no create pode ser FALSO ALARME com gateway vivo — conferir `hermes gateway status` + `ps aux | grep gateway` antes de agir.
- `--body` com caracteres especiais/acentos: gravar em arquivo e usar `--body "$(cat /tmp/body.md)"` — evita quoting quebrado.
- Workspace `dir:` compartilha o MESMO diretório físico: tasks que editam o MESMO arquivo DEVEM ser serializadas (filha com `--parent` dos dois) — senao conflito garantido.
- Dispatcher tick ~60s: task ready → running em ~1 min.

## protocol_violation (padrão recorrente em sessões longas)
Worker termina rc=0 SEM chamar kanban_complete/kanban_block → dispatcher marca gave_up/blocked apos 2-3 crashes; o erro instrui: "verify it and report the result via kanban_complete".
Recovery (do orquestrador):
1. Verificar a ENTREGA REAL (log do worker mostra sucesso? build/testes rodam? arquivos existem?).
2. `hermes kanban comment` explicando a revisão + `hermes kanban complete <id>`.
3. Prevenção: encerrar o body com "CHAME kanban_complete OBRIGATORIAMENTE ao terminar (senao o dispatcher conta como crash)".

## Auto-block review-required
Workers com "NÃO commitar" no body se auto-bloqueiam com `kind: needs_input` (review-required) quando terminam. Orquestrador: revisa artefatos (diff/arquivos), comenta aprovacao, `kanban complete` → libera tasks filhas.

## Verificação pré-PR (orquestrador)
- pytest + `ruff check . --fix`; atenção: ruff --fix altera arquivos FORA da task (ex: camadas antigas) — conferir `git diff` antes de commitar.
- Worker pode deletar docs/specs sem querer → `git checkout -- <arquivo>`.
- Mudanças pendentes que escaparam do commit → branch de hotfix + cherry-pick + PR rapido pos-merge.
- Merge: `gh pr merge <n> --squash --delete-branch`; limpar branches locais (`git branch -D`), remota residual (`git fetch --prune`), sincronizar main (`git reset --hard origin/main` apos squash).
- Verificar que ASSETS usados pelo codigo entram no commit (ex: logos de dashboard) — git status mostra untracked que o `git add` de lista nao pegou.

## Tasks que leem banco
- ANTES de delegar: confirmar que o `.env`/DATABASE_URL existe no repo (senao workers improvisam conexao — podem demorar ou falhar).
- Rodar python de projeto no Mac do usuario: `env -u PYTHONPATH` (o shell herda o site-packages do venv do hermes-agent py3.11 e contamina imports).
- Sessoes dos workers NÃO aparecem na sidebar do desktop (perfis separados, headless) — usuario acompanha via kanban list/show/log; explicar isso sem repetir.

## Scripts
- `scripts/watch-kanban-tasks.sh` — espera uma lista de tasks ficarem done/blocked e notifica; rodar com `terminal(background=true, notify_on_complete=true)` e continuar o trabalho (0 polling).
- **O script imprime o BOARD INTEIRO no final** ("TODAS AS TASKS TERMINARAM: ..."), não só as monitoradas — ao ler o output, grep pela task alvo (`grep t_1fde025e`) em vez de se assustar com tasks antigas done na lista (observado 2026-08-05).
- **Verificação pós-done com `kanban show <id>`**: o campo "Latest summary" do `hermes kanban show` traz o auto-reporte do worker (incluindo lista de skills carregadas, se o body pediu). Para validar SOUL/processo: conferir summary + re-rodar testes/build (`npm test -- --run`, `npx tsc --noEmit`, `npm run build`) — self-report nunca é prova.
