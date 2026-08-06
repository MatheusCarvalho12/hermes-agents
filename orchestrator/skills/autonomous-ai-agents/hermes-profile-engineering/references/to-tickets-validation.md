# Validação SOUL v2 — rodada 3 (to-tickets, 2026-08-05)

A rodada 2 terminou com "protocol violation recorrente: worker entrega mas não fecha o
protocolo". A rodada 3 testou a hipótese de que a CAUSA é o tamanho da task (contexto
inchando → API do modelo cai → run morre antes do kanban_complete), não o worker.

## Setup testado
- Instaladas 16 skills do mattpocock via `hermes skills install "skills-sh/mattpocock/skills/engineering/<nome>" -y`
  (to-tickets, to-spec, triage, wayfinder, grill-with-docs, handoff, prototype, codebase-design,
  domain-modeling, tdd, code-review, diagnosing-bugs, improve-codebase-architecture,
  to-questionnaire, teach, wait-what). `ask-matt` e `writing-for-agents` BLOQUEADOS pelo scanner
  (veredito dangerous — `--force` NÃO sobrepõe dangerous, só caution).
- Demanda real quebrada com o método do to-tickets em 3 tracer-bullet vertical slices:

| Ticket | O que entrega | Blocked by |
|---|---|---|
| T1 (t_fcb974ec) | Subir stack real (backend+banco+front) + rodar os 3 specs e2e headless, relatório | None |
| T2 (t_9b9b0972) | Corrigir até e2e verde | T1 |
| T3 (t_be04ce91) | Lighthouse + checklist de aceite da spec §8 | T2 |

## O que funcionou (confirmado)
1. **Cada ticket fechou `done` em ~3 min** (T1: 3 min, T2: ~2 min), protocolo OK — sem recovery manual.
   Contraste com a task monolítica da rodada 2 (22 min, 4 runs, blocked).
2. **T1 foi a PRIMEIRA task que o worker fechou sozinho chamando kanban_complete** — evidência de que
   "não fecha o protocolo" era efeito do tamanho, não do worker.
3. **Cadeia automática**: `--parent` encadeado faz o dispatcher promover T2 quando T1 done, T3 quando T2 done.
4. **E2e real verificado**: 5/5 testes passaram (2 execuções consecutivas), screenshots em /tmp,
   backend :8000 e front :5173 respondendo, working tree limpo (nenhum arquivo fora do escopo).
5. **T1 reportou sem editar nada**: só subiu a stack, rodou os specs, e relatou com evidência — a
   "Scope Discipline" do SOUL v2 segurou o escopo num ticket que era só diagnóstico.
6. **Cadeia 3/3 fechou (2026-08-05)**: T3 (Lighthouse + checklist §8) também `done` — lighthouse real em
   build de produção: desktop dark 99/100/100/92, light 100/100/100/92, mobile 375 ≥94, LCP ≤1.05s,
   CLS ~0; checklist §8 da spec do designer 11/11 OK. T3 ainda achou e corrigiu 3 bugs reais de CSS
   (auto-referência `--border` → todas as bordas caíam para currentColor; radius de panels/KPIs; borda
   top âmbar do KPI featured que a utility `.border` comia) — prova que checklist de aceite contra o
   contrato valida de verdade, não é formalidade.
7. **Pós-cadeia**: PR do trabalho (merge squash `gh pr merge <n> --squash --delete-branch`), limpeza
   `git branch -D` local + `git fetch --prune` (limpou até branch morta antiga), main sincronizada —
   repo fica só com `origin/main`.

## Diagnóstico confirmado (o que resolve o "protocol violation")
- Ler o FINAL do log da task (`hermes kanban log <id> 2>&1 | tail -60 | grep -vE heartbeat`) procura:
  `API call failed ... HTTP 503`, `stream drop (ReadTimeout) after 600s`, `Final error: Connection error`.
- Task gigante → contexto ~57k tokens → API do modelo instável (deepseek-v4-flash deu 503/timeout) →
  run morre rc=0 sem complete → dispatcher marca protocol_violation. NÃO é o worker nem o SOUL.
- Correção estrutural = **sizear a task para caber numa janela de contexto fresca** (to-tickets).
- Todos os workers herdam o modelo do clone (`model.default` no config do perfil) — se o default
  do time está 503, todo worker cai junto.

## Receita (reutilizável)
1. `hermes skills install "skills-sh/mattpocock/skills/engineering/to-tickets" -y`
2. Quebrar a demanda em tickets: 1 arquivo de body por ticket (`/tmp/ticket-*.md`), formato do to-tickets
   (What to build / Blocked by / Status / acceptance criteria).
3. Criar encadeado: `T1=$(hermes kanban create ... )` → `T2=$(hermes kanban create ... --parent "$T1")` → ...
   Capturar IDs com `grep -oE 't_[a-f0-9]+'`.
4. Monitorar a CADEIA INTEIRA de uma vez: `watch-kanban-tasks.sh t_1 t_2 t_3` (aceita lista).
5. Verificar entrega real pós-done (build/testes/tsc) — nunca confiar só no summary.

## Scanner / instalação (pitfalls)
- `npx skills@latest add mattpocock/skills` NÃO instala no Hermes (vai pro Codex/system) — usar sempre
  `hermes skills install`.
- Veredito `dangerous` bloqueia SEM `--force` funcionar (ask-matt: agent_config_mod; writing-for-agents: 4 findings).
- Nome duplicado (ex: `grilling` em `~/.hermes/skills/grilling/` + `y/grilling/` + `y/grill-me/` stub) →
  `skill_view` dá "Ambiguous skill name". Consolidar: manter a versão rounds/frontier, mover a antiga
  para `<name>.old-YYYYMMDD` (backup, não delete), verificar com `COLUMNS=400 hermes skills list`.
