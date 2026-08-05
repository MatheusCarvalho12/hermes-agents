---
name: hermes-multi-profile-ops
description: "Manage Hermes profiles, kanban, MCPs, SOUL.md per profile."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [hermes, profiles, kanban, mcp, skills, orchestration]
    related_skills: [hermes-administration, hermes-agent]
---

# Hermes Multi-Profile Ops

Operação do time multi-perfil do usuário: **default = orquestrador** + frontend-developer, backend-developer, database-developer, designer. Complementa a skill `hermes-administration` (comandos oficiais); esta carrega o fluxo validado e as armadilhas reais. Snapshot do time em `references/team-inventory.md`.

## Quando usar
- Criar/gerenciar perfis do time; instalar skill ou MCP em perfil específico
- Montar/editar SOUL.md de perfis (estrutura + gatilhos de skill)
- Orquestração via kanban (delegar, paralelismo, diagnósticos)
- Skill não instala, MCP sem tools, worker não roda

## Criar perfil
```bash
hermes profile create <nome> --clone --description "papel (usado pelo kanban p/ rotear)"
```
- `--clone` copia config/.env/SOUL/skills do default (herda modelo, mem0, desativações) — ⚠️ copia o `skills/` INTEIRO: todo perfil clonado nasce com ~75-90 skills e precisa de trim (ver seção "Limpeza de skills por perfil")
- `--description` NÃO é enfeite: o orquestrador/kanban roteia a task por ele
- SEMPRE mostrar o plano e confirmar com o usuário antes de criar perfil ou escrever SOUL.md

## Instalar skill em perfil específico
```bash
hermes -p <perfil> skills install <identifier> -y
```
⚠️ **Esquecer `-p` instala no DEFAULT** (erro real cometido com http-api).

Identifiers que funcionam:
- skills.sh: `skills-sh/owner/repo/path`
- clawhub: `clawhub/nome` — nome puro falha com "No exact match"
- GitHub: `owner/repo/path`; ou URL direta de SKILL.md (repo com SKILL.md na raiz): `hermes skills install <raw-url> --name <nome>`

Armadilhas:
- Preferir a flag `-y`; `echo y |` às vezes é consumido por prompt anterior → "Installation cancelled"
- O scanner skills-guard BLOQUEIA skill community: veredito `caution` → reinstalar com `--force -y`; veredito `dangerous` = BLOQUEIO DURO (nem `--force -y` passa — ex: docker do bobmatnyc com 25 findings) → procurar FONTE ALTERNATIVA da mesma skill (`mindrally/skills/docker` instalou limpo). Output: "Decision: BLOCKED" (grep por `Blocked`/`Installed:`, não por `Error`)
- Algumas skills não são indexadas pelo nome esperado (ex: "frontend-ui" da Anthropic não existe; a oficial é `frontend-design`). Listar o repo: `curl -s https://api.github.com/repos/<owner>/<repo>/contents/<dir> | grep '"name"'`
- Instalações do hub com 2+ arquivos (SKILL.md + references/) — conferir com `hermes -p <perfil> skills list`

## MCP por perfil
```bash
hermes -p <perfil> mcp add <nome> --env KEY=VAL --command npx --args ...
```
- `--env` ANTES de `--command` (`--args` precisa ser o último)
- Prompt "Enable all N tools?" → `echo y |` funciona aqui
- Sem a chave via `--env`, o server conecta mas "reported no tools" (ex: morph sem MORPH_API_KEY) — sempre passar a chave
- Chaves também no `.env` do perfil (backup antes: `cp .env .env.bak-$(date +%Y%m%d)`)
- Tools de MCP só carregam em **sessão nova** do perfil
- Morph warpgrep aparece como tool `codebase_search` (+ github_codebase_search, edit_file, reflex_*)

## RTK (Rust Token Killer) — ferramenta de sistema, vale p/ todos os perfis
```bash
brew install rtk
rtk init --agent hermes                                      # plugin rtk-rewrite no HERMES_HOME atual
HERMES_HOME=~/.hermes/profiles/<nome> rtk init --agent hermes  # replicar por perfil
```
- Plugin `rtk-rewrite` (hook `pre_tool_call`) reescreve comandos de terminal (git status → rtk git status), comprime output
- Pré-requisito do warpgrep (Morph): ripgrep instalado

## Kanban (orquestração)
```bash
hermes kanban init
hermes kanban create "título" --assignee <perfil>
hermes kanban list / show <id> / watch
```
- Dispatcher roda no GATEWAY (`kanban.dispatch_in_gateway: true`, tick 60s). Sem gateway, task fica "ready" para sempre. Checar com `hermes gateway status`
- Ciclo: ready → claimed → spawned (worker = processo do perfil) → heartbeat → done
- **Teste de fumaça**: criar task trivial e `hermes kanban show <id>` até done (~25s) antes de confiar no pipeline
- PARALELISMO: `max_in_progress_per_profile: null` = sem limite (N workers do mesmo perfil em paralelo); `auto_decompose: true` quebra feature grande em tasks menores (3/tick) — o usuário espera decomposição + paralelismo máximos
- Workspaces `scratch` são EFÊMEROS (deletados ao completar) — usar `--workspace dir:/abs` ou `worktree:` para preservar output
- ⚠️ `--priority` é INT (ex: `--priority 10`), NÃO string — `--priority high` falha com `invalid int value` e a task NÃO é criada (erro vai pro stderr; some fácil se suprimir). A flag `--json` existe no help do create mas não foi validada na prática — capturar ID pelo stdout é o caminho robusto
- Capturar ID da task: a linha `Created t_XXXX (ready, assignee=...)` sai na STDOUT; o aviso "No gateway is running" vai pra STDERR e pode ser FALSO-NEGATIVO (gateway vivo via launchd — conferir `hermes gateway status`/`ps` antes de achar que o dispatcher morreu). Padrão validado:
  ```bash
  ID=$(hermes kanban create "título" --assignee <perfil> --body "$(cat /tmp/body.md)" 2>/dev/null | grep -o 't_[a-f0-9]*' | head -1)
  ```
- Bodies longos com acentos/caracteres especiais (ç, ÷, aspas): gravar o body num arquivo e passar `--body "$(cat /tmp/body.md)"` — evita quebra de quoting em cascata e permite reuso
- Dependência entre tasks: `--parent <id>` no create (child só dispara quando o parent termina — criar na ordem: parents primeiro, capturar IDs, depois children). Alternativa posterior: `hermes kanban link <parent> <child>`. **`--parent` é REPETÍVEL**: `--parent A --parent B` → child só roda quando TODOS os parents fecharem — use para serializar workers que editam o MESMO arquivo (ex: backend corrige a query e frontend aplica polish no mesmo `generate_dashboard.py`; sem isso, conflito garantido de edição paralela)
- Feature com dados reais desconhecidos (ex: colunas JSONB de uma fonte nova): a primeira task é DESCOBERTA/mapeamento que entrega um doc (`docs/*.md` com colunas reais + cálculo validado); as tasks de código ficam `--parent` dela — nunca chutar antes de ver os dados
- **Checklist de conformidade antes de fechar**: re-ler o TEXTO ORIGINAL da demanda e conferir requisito por requisito (o usuário pede "ve se ta adequado a tudo do texto"). Gap real: worker usou tonelagem PLANEJADA onde a demanda dizia "toneladas movimentadas" (realizado) — o doc até documentava a dúvida ("confirmar com o negócio") e seguiu com o valor errado. Quando o texto mandar algo e a implementação divergir, abrir task de correção, não aceitar o "documentado e segue"
- Para paralelizar DB + backend no mesmo repo (`--workspace dir:/abs`): o orquestrador define o CONTRATO (nomes de tabelas/colunas/arquivos) no corpo das tasks — cada worker mexe só nos arquivos da sua task, sem pisar no outro
- Usuário acompanha workers pelo KANBAN (dashboard/`kanban watch`/comentários), NÃO pelas seções dos perfis no desktop (sessões de worker são curtas/efêmeras; cada perfil tem HERMES_HOME próprio). Se o usuário reclamar que não vê as sessões no desktop, explicar isso e apontar o kanban — não é bug. Diagnóstico real (2026-08): a sidebar do app mostra SÓ sessões criadas na UI (source desktop) — com perfil trocado no seletor ela exibe "No sessions yet" mesmo com trabalho feito; os workers headless gravam request_dumps em `~/.hermes/profiles/<p>/sessions/` e o app não os indexa. Para PROVAR atividade/entregas de um perfil: `hermes -p <perfil> sessions list` (títulos tipo "work kanban task t_xxx", última atividade) e `sessions stats` (Total sessions/messages); e o transcript das ações: `kanban log <id>` (comandos reais) + `kanban show <id>` (heartbeats/summary).
- **Workers são Hermes nativos, NÃO Codex/CLIs externos**: cada task vira um processo `hermes -p <perfil> kanban run <task>` que carrega as skills DO PRÓPRIO PERFIL (SOUL com gatilhos força o uso — logs mostram skill_view no início de cada task). Se o usuário perguntar "estão codando com codex?", responder que não: as skills `codex`/`claude-code`/`opencode` são fluxo ALTERNATIVO de delegação externa, não o padrão do kanban. Inventário confirmado de skills por perfil: `references/team-inventory.md`

### Monitorar SEM polling (usuário corrigiu explicitamente: "esses sleep é a forma mais eficiente???")
NUNCA ficar em loop `sleep N; kanban list` esperando task fechar. Usar monitor async:
```bash
# scripts/watch-task.sh <id1> [id2 ...] — espera as tasks saírem de running/ready e sai
# rodar com terminal(background=true, notify_on_complete=true) → o orquestrador é avisado NA HORA EXATA
```
Fluxo: dispara o monitor em background → responde ao usuário com o estado atual → quando a notificação chega, verifica artefatos e reporta. Zero turnos gastos em polling.

### protocol_violation / gave_up (worker "crashou" sem completar)
Sintoma: worker sai rc=0 mas sem chamar kanban_complete/block → dispatcher conta como crash; após ~2-3 violações dá `gave_up` e a task fica blocked. **O trabalho pode ter sido feito mesmo assim** (ex: HTML gerado, código escrito antes do crash).
Recuperação:
1. Verificar artefatos reais (arquivos modificados, output gerado, grep no HTML) — se o trabalho existe e está bom, `kanban complete` manual (o erro do dispatcher instrui: "verify it and report the result via kanban_complete")
2. Se faltou só o passo final, `kanban comment` com instrução EXPLÍCITA "AO TERMINAR, CHAME kanban_complete OBRIGATORIAMENTE" + `kanban unblock` + `kanban promote` (promote só aceita todo/blocked — se já está ready, o dispatcher pega sozinho)
3. Causa raiz comum: sessão longa onde o modelo "esquece" o call terminal — instruir o passo final no comment reduz recorrência

### review-required auto-block (comportamento bom, não é erro)
Workers com SOUL "verificação única" se auto-bloqueiam com `blocked {reason: 'review-required: ...'}` após entregar (nada commitado, pedindo revisão). Fluxo do orquestrador: ler artefatos reais (diff/sql/html) → `kanban comment` aprovando → `kanban complete` → a task filha é promovida sozinha. Nunca refazer o trabalho.

### Pré-requisitos de ambiente ANTES de delegar (economiza minutos de worker)
Workers perdem muito tempo caçando conexão quando o repo não tem `.env`/credenciais (ex: datalake sem `.env`, DATABASE_URL ausente → o worker fica sondando `.env` de OUTROS projetos). Antes de criar tasks que dependem de DB/API:
1. Conferir se `.env`/credenciais existem no repo; se não, pedir a connection string ao usuário e criar o `.env` (chmod 600; `.gitignore` geralmente já cobre)
2. Testar a conexão uma vez (select 1) antes de disparar os workers
3. Deixar `kanban comment` na task com o jeito de conectar (ex: `export $(cat .env | xargs)`)

## SOUL.md de perfis — convenções do usuário (obrigatório)
Estrutura: Identity / Style / Código / Skills (gatilhos) / Verificação / Context7 / Morph / Ferramentas / Avoid / Defaults. Template em `templates/soul-md-triggers.md`.

1. **Seção "Skills — SEMPRE use a skill certa na hora certa"**: gatilho explícito por skill ("shadcn → sempre que criar componente de UI"). O usuário NÃO quer ter que mandar chamar skill — já teve agentes com skills instaladas que nunca chamavam
2. **Context7 = LEI**: consultar sempre antes de usar API/lib; versão mais recente, doc atual vence (mesmo que a skill diga o contrário)
3. **Morph seletivo**: só para busca grande (schema geral, refatoração, feature grande); pontual = grep
4. **Verificação UMA vez antes do PR** (não durante o dev): testes → lint/react-doctor → security/code review → gitleaks; formatação IMEDIATA (ruff format/check após escrever) para evitar retrabalho
5. Código em INGLÊS; mensagens de UI/erro em pt-BR humanizadas (skill humanizer); NUNCA "Internal Server Error" cru pro cliente
6. DRY/SOLID, componentização total (um botão em 2 telas = UM componente), sem over-engineering; gitleaks antes de commit
7. **Orquestrador (default)**: classificar rápido (pontual vs feature), opinião honesta (propor melhorias sem puxa-saquismo), tasks de kanban ENXUTAS (título + o que + critério de pronto), paralelizar ao máximo
8. Usuário: pt-BR, estilo i-have-adhd (ação primeiro, listas ≤5, sem preâmbulo)
9. **Teste de verdade** — proibido reportar "funcionou" sem EVIDÊNCIA: rodar build, subir a stack local via `docker compose` (front sobe o BACKEND REAL — mock só quando o back não existe; back sobe banco real), bater nos endpoints reais (curl/api-testing), `alembic upgrade head` sem erro, e2e no fluxo de usuário. Integração front↔back = task do ORQUESTRADOR (kanban link dependente entre tasks), NÃO "passam teste um pro outro". Regra gravada nos SOULs de front e back
10. **Playwright SEMPRE headless** (`npx playwright test`, sem janela) — usuário odeia modo headed: rouba o computador dele e não roda 2 em paralelo; headless roda invisível e paralelo (N workers). Regra travada no gatilho do SOUL do front. Escolha de ferramenta de browser/e2e: ver `references/browser-e2e-options.md`
11. **humanizer OBRIGATÓRIO em TODO texto user-facing** (copy do site, mensagens, erros — nunca "Internal Server Error"/"HTTP 400"/stacktrace cru); erro técnico vai só pra log/console/Sentry; pro usuário vai mensagem amigável pt-BR. Regra gravada nos SOULs de front E back

## Limpeza de skills por perfil (pós `--clone`)
`hermes profile create --clone` copia o `skills/` INTEIRO do perfil fonte (~75-90 skills) — todo perfil clonado nasce poluído e precisa de trim. Só desabilita (`skills.disabled`); nada é apagado do disco, é reversível.

Workflow validado (2026-08: 4 perfis dev, 327 → 53 ativas):
1. Backup: `cp ~/.hermes/profiles/<p>/config.yaml config.yaml.bak-$(date +%Y%m%d)`
2. Ler os nomes CANÔNICOS (o CLI trunca com "…" sem COLUMNS largo): `COLUMNS=400 hermes -p <p> skills list`
3. Rodar `scripts/trim-profile-skills.py <perfil> <keep...>` (usa `save_disabled_skills`, mesmo caminho do `hermes skills config`; sem args aplica a distribuição conhecida do time)
4. Validar: `COLUMNS=400 hermes -p <p> skills list --enabled-only`

Pitfalls:
- ⚠️ O nome no `skills.disabled` precisa ser o DISPLAY name do CLI, não o nome da pasta: `Design System` (display) ≠ `design-system` (pasta); `test-review` ≠ `nm-pensive-test-review`. O CLI é a fonte da verdade; `ls skills/` engana.
- ⚠️ Após desabilitar, conferir GATILHOS ÓRFÃOS no SOUL do perfil: skill citada na seção "Skills" que não está mais ativa (ex real: `nm-pensive-test-review` no SOUL do DBA, sem a skill instalada) — remove ou instala a skill, senão o agente fica esperando uma skill que não carrega.
- `hermes config set skills.disabled '[...]'` grava string e falha silencioso — só `save_disabled_skills` funciona (ver hermes-administration).
- Distribuição atual do time (o que fica em cada perfil): `references/team-inventory.md`.

## Pitfalls gerais
- Mudanças de config/tools/skills/MCP só valem em sessão nova do perfil
- `hermes config set skills.disabled` grava string e NÃO funciona — usar `save_disabled_skills` (ver hermes-administration)
- Confirmar com o usuário ANTES de escrever qualquer MD (SOUL.md/SKILL.md) — regra explícita dele; mostrar rascunho primeiro
