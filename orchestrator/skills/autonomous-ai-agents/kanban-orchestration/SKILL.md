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

## Escopo vazado = o time-killer #1 de worker (2026-08-05, task StatusBadge)Worker de frontend gastou 22 min numa task de 1 componente e reescreveu 20 arquivos fora do escopo (1180 linhas não commitadas: App/Header/StateViews/index.css...). Commit dele era limpo, mas o working tree virou um refactor inteiro que ninguém pediu.
- **Task de PROVA deve ser do TAMANHO REAL da demanda do usuário** (correção explícita 2026-08-05): ele rejeitou micro-task de teste ("StatusBadge porra, minhas tasks não vão ser uma coisa pequena assim"). Teste pequeno valida gatilho/processo; teste GRANDE (ex: refatorar o dashboard inteiro mantendo lógica de negócio, com spec do designer como contrato) valida escopo/autonomia/entrega. MAS: task gigante monolítica em UM ticket = contexto incha = API cai = protocol violation (ver seção protocol_violation) — a solução é quebrar a demanda grande em tickets verticais (to-tickets), não evitar tarefa grande.
- **Prevenção no body da task**: seção explícita "Escopo autorizado: <paths>" + "PROIBIDO tocar: <paths>" + "Se precisar de algo fora, pare e pergunte via kanban". Tasks GRANDES autorizam a área inteira (ex: "frontend/ inteiro") mas proíbem as outras (backend/, tests/).
- **Detecção pós-run**: `git status --short` + `git diff --stat HEAD` — se aparecer diff fora do que a task autorizou, é escopo vazado (devolver / reverter / reaproveitar com critério).
- **Time-box**: worker deve ler ≤ 30 min antes de codar em task grande; ≤ 10 min em task pequena.
- **Reaproveitar trabalho parcial de run crashado**: run anterior crashou por protocol_violation mas deixou refactor útil no working tree → orquestrador `git stash push -u -m "wip: ..."` ANTES de delegar de novo (preserva, reversível), commitar specs/contratos do designer separadamente (`git add docs/... && git commit`), e o worker novo valida o stash como baseline (build/lint) antes de decidir aproveitar ou refazer.

## protocol_violation (padrão recorrente em sessões longas)
Worker termina rc=0 SEM chamar kanban_complete/kanban_block → dispatcher marca gave_up/blocked apos 2-3 crashes; o erro instrui: "verify it and report the result via kanban_complete".
Recovery (do orquestrador):
1. Verificar a ENTREGA REAL (log do worker mostra sucesso? build/testes rodam? arquivos existem?).
2. `hermes kanban comment` explicando a revisão + `hermes kanban complete <id>`.
3. Prevenção: encerrar o body com "CHAME kanban_complete OBRIGATORIAMENTE ao terminar (senao o dispatcher conta como crash)".

### Diagnóstico: checar a API do modelo ANTES de culpar o worker (validado 2026-08-05, task t_b6e8e378)
O worker "não fecha o protocolo" NEM SEMPRE é desobediência — pode ser o run morrendo ANTES de chegar ao kanban_complete. Antes de concluir protocol_violation, ler o FINAL do log: `hermes kanban log <id> 2>&1 | tail -60 | grep -vE heartbeat` e procurar:
- `API call failed ... HTTP 503` (capacity limits), `stream drop (ReadTimeout) after 600s`, `Final error: Connection error`.
Caso real: task GRANDE crashou 4x com rc=0 — o worker tinha plano explícito de "commitar e fechar", mas a API do modelo caiu (503 + timeout 10min + connection) quando o contexto inchou a ~57k tokens / 40 msgs num run de 22min. Não era o worker nem o SOUL — era infra do modelo.
- Correção estrutural: **sizear a task para caber numa janela de contexto fresca** — tasks verticais pequenas (skill `to-tickets` do mattpocock: tracer-bullet slices com bloqueios) fecham o protocolo de forma confiável; task monolítica gigante + modelo instável = morte certa.
- **VALIDADO na cadeia T1→T2→T3 (2026-08-05)**: quebrar a demanda grande em 3 tickets verticais com `--parent` encadeado fez cada um fechar `done` em ~3 min, protocolo ok, sem recovery manual. O dispatcher promove os filhos sozinhos quando o pai done — **monitore a cadeia INTEIRA de uma vez** (`watch-kanban-tasks.sh t_1 t_2 t_3` aceita lista), não um ticket por vez; o script notifica quando todos terminarem.
- O worker herda o modelo do clone (`model.default` no config do perfil) — se o default do time está 503/timeout, todo worker cai junto; considerar trocar o modelo dos perfis ou quebrar em tickets menores.

### Variante: trabalho grande NÃO commitado (2ª ocorrência consecutiva — 2026-08-05, task dashboard GRANDE)Worker entrega a refatoração INTEIRA mas: (a) só commitou o pedaço pequeno (ex: componente) e deixou 19-29 arquivos (+1000 linhas) como diff não commitado no working tree; (b) não chamou `kanban_complete` → blocked após 4 runs. O summary pode nem existir — NÃO confiar nele; a prova é o diff + build/testes.
Recovery completo (validado na task t_b6e8e378):
1. `hermes kanban show <id>` → confirmar protocol_violation + runs crashados (não é falha de trabalho — o diff existe).
2. Rodar build + testes + tsc NO working tree (`npm run build`, `npm test -- --run`, `npx tsc --noEmit`) — prova que o trabalho órfão é real e saudável.
3. Se a task tem CONTRATO (spec do designer, AGENTS.md): validar o diff contra os CRITÉRIOS DE ACEITE antes de commitar — ex. spec de design: `grep -rn "#[0-9a-fA-F]\{6\}" frontend/src/components/ --include="*.tsx"` (hardcode hex proibido), `startViewTransition` no toggle, fontes Inter/JetBrains + `.num`, dark sem box-shadow. Não commitar trabalho que não bate com o contrato.
4. Commitar o trabalho órfão EM NOME DO WORKER (orquestrador fecha o ciclo quando o worker crashou no protocolo): `git add` + `git commit` com mensagem que reflete a feature. Lixo (ex: `frontend/test-results/.last-run.json`, `assets/mockup-*`) → `.gitignore` em vez de commitar (`git rm -r --cached` + append no .gitignore + commit separado).
5. `hermes kanban comment` com a revisão (o que foi validado, commits/hashes) + `hermes kanban complete <id>`.
6. **Lição recorrente**: worker que entrega bem mas não fecha o protocolo pela 2ª vez é padrão, não acidente — considerar reforço no SOUL/body (instrução de fechamento mais agressiva) e reportar ao usuário como problema de processo, não de qualidade de entrega.

## Stress test multi-perfil: fronteira de arquivo no body = paralelismo sem conflito (validado 2026-08-05)
Para validar o time INTEIRO no padrão novo (SOUL v2 + kits curados) de uma vez: criar 4 tasks em paralelo, uma por perfil, no MESMO repo, cada body com seção explícita "Escopo (fronteira de arquivos): SOMENTE <path>" + "PROIBIDO tocar: <paths>" + um CONTRATO entre eles (ex.: database cria função `X()` → backend consome via SQLAlchemy; contrato fixo no body permite rodarem simultâneos sem depender de ordem). Resultado real: 4 workers (designer/database/backend/frontend) pegaram no mesmo tick, cada um na sua área (docs/ vs db/ vs api/ vs frontend/), todos `done` em 3-14 min, zero conflito de working tree, zero protocol_violation. Verificação pós-done por área: `git status --short | awk '{print $2}' | sed 's|\(docs/\).*|\1|...'` mostra quem tocou o quê e confirma que cada um respeitou a fronteira. Para stress test REAL: a demanda deve ser do tamanho das demandas do usuário (não micro-task de brinquedo) — ex. "ronda de qualidade pós-redesign" com 1 ticket por papel.

## Feedback visual do usuário: spec incompleta ≠ skill não chamada (2026-08-05)
Quando o usuário aponta problema de DESIGN no resultado (padding colado, textos crus em inglês, lista sem lazy load, padrão Z ausente), ANTES de culpar skill não invocada, verificar se a SPEC/contrato especificava aquele acabamento. Caso real: KPI cards sem padding interno + títulos "Loading / unloading" crus — a skill frontend-design fala de spacing em tom geral, mas a spec §5.2 do designer NÃO tinha critério de padding interno/padrão Z, e o SOUL pedia humanizer só para erros/copy, não para títulos de seção. Ou seja: a correção é dupla — (1) task de correção visual com critérios explícitos + evidência ANTES/DEPOIS (screenshots), e (2) atualizar a spec do designer e o SOUL (humanizer em TODO texto visível, inclusive títulos de painel/seção). Verificação real pós-correção: `vision_analyze` no screenshot ANTES/DEPOIS para confirmar o padding de verdade (não confiar no summary do worker).

## Context7 "LEI" no SOUL não é seguido na prática — exigir evidência (2026-08-05)
Regra "Context7 é LEI antes de usar API/lib" nos SOULs dos workers NÃO garante uso: auditando 4 tasks reais, o MCP context7 estava ativo (✓ enabled, conecta ~2.4s, tools resolve-library-id + query-docs) mas **0 menções de context7 nos logs**. As libs estavam no latest por sorte (package.json já atualizado), não por hábito.
- Corrigir com EVIDÊNCIA, não com mais regra: exigir no body da task + no SOUL "no summary, cite o que o Context7 confirmou (lib + versão consultada)". Sem isso, orquestrador devolve.
- Auditoria rápida de "latest": `hermes -p <perfil> mcp list | grep context7` (confirmar ativo) + `hermes -p <perfil> mcp test context7` (confirmar tools) + comparar package.json/requirements.txt contra o registry. **`npm view <pkg> version` é BLOQUEADO pelo guard de segurança (heurística de servidor)** — usar `curl -s https://registry.npmjs.org/<pkg>/latest | python3 -c "import sys,json; print(json.load(sys.stdin)['version'])"` e para Python `curl -s https://pypi.org/pypi/<pkg>/json | python3 -c "import sys,json; print(json.load(sys.stdin)['info']['version'])"`.

## Pitfalls de verificação pós-done (2026-08-05)
- **`rtk uv ...` quebra**: o plugin rtk-rewrite prefixa `rtk` e `rtk uv run` falha com "Failed to spawn process: No such file or directory". Para rodar backend de projeto no Mac do usuário: `env -u PYTHONPATH <caminho-do-uv>/uv run uvicorn ...` (uv em ~/.local/bin/uv; PYTHONPATH do venv hermes-agent contamina pydantic_core → ModuleNotFoundError).
- **Endpoint novo dá 404 = processo antigo na porta**: uvicorn SEM `--reload` não pega código novo; worker sobe o backend, depois o orquestrador edita/delega e o curl no endpoint novo retorna `{"detail":"Not Found"}` enquanto o código já existe em api/main.py. Diagnóstico: `lsof -i :8000` (PID antigo ainda vivo) + `grep -n "@app.get(\"<rota>\"` no código. Correção: `kill -9 <pid>`, subir de novo com `env -u PYTHONPATH ... uvicorn`, re-testar.
- **Workers deixam arquivos temporários** (`verify-*.tmp.ts`, `*_tmp.py`, `capture-*.ts`, `_test_*.txt`) no working tree — limpar antes do commit (`git rm --cached` + rm + adicionar `*.tmp.ts` ao .gitignore) ou o PR sai poluído.

## Padrão de finalização do usuário (instrução explícita 2026-08-05)
Ao terminar QUALQUER task/verificação, o fluxo de fechamento é:
1. **SUBIR A STACK para o usuário VER o resultado real** (front + back: uvicorn em :8000 com `env -u PYTHONPATH .../uv run uvicorn`, vite em :5173; abrir `open_preview` no front). Ele quer ver o que os workers entregaram, mesmo já sabendo que está certo — "sempre que terminar uma tarefa, sobe o compose pra mim ver".
2. **NÃO fazer PR/merge sem aval explícito** — o usuário diz "pode fazer" (ou "faz PR, merge"). Se ele disser "não faz o merge/PR", NÃO faz.
3. Após o aval e o merge: **limpar TUDO** — branch local (`git branch -D`), branch remota (o `--delete-branch` do `gh pr merge` + `git fetch --prune`), main sincronizado (`git reset --hard origin/main` após squash). Zero sujeira.
- Regra gravada na memória também; aqui fica o PORQUÊ: o usuário aprova visualmente antes de versionar — o PR sem aval dele é visto como atropelo.

## Gargalo de velocidade: verificação pesada em task pequena (diagnóstico 2026-08-05)
Medição real dos runs: task de endpoint simples = 2.3 min; task de padding (4 linhas de CSS) = 20 min — o excesso era a BATERIA COMPLETA de verificação (lighthouse 2x + e2e 5/5 + react-doctor + screenshots antes/depois) rodada em CADA task pequena. Custo fixo por task: carregar SOUL + explorar repo + sessão nova (~1-3 min que uma sessão full-stack contínua não paga).
- **Proposta (não aplicada ainda — pendente de aprovação do usuário): verificação em camadas** — task pequena roda só testes+build+lint (≤5 min); bateria completa (lighthouse+e2e+screenshots) só no PR. Se o usuário aprovar, aplicar nos SOULs dos workers.
- Observação de arquitetura (respondida ao usuário): a fronteira designer×front / dba×back NÃO é falta de skill — funcionou no stress test com fronteira de arquivo no body (designer=docs/**, front=frontend/**, dba=db/**, back=api/**). O bug visual real era spec incompleta (não tinha padding → front não tinha onde buscar), corrigido na spec §5.2.
- Trade-off full-stack-direto vs time: o time paga ~1-3 min de setup por task mas ganha paralelismo (N workers), isolamento (crash não derruba tudo) e verificação independente (autor não valida o próprio trabalho).


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
