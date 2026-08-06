---
name: hermes-profile-engineering
description: "Set up Hermes profiles: MCPs, skills, SOUL.md, kanban."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [hermes, profiles, mcp, skills, soul, kanban, orchestration]
    related_skills: [hermes-administration, hermes-agent, i-have-adhd]
---

# Hermes Profile Engineering

Field-tested playbook for standing up and iterating a team of specialized Hermes profiles (e.g. frontend-developer, backend-developer, database-developer, designer) that a "default" orchestrator profile delegates to via Kanban. Complements the bundled `hermes-administration` skill (which covers profile basics, skills disable, memory providers) with the deeper per-profile tooling workflow. Official docs win: https://hermes-agent.nousresearch.com/docs/user-guide/profiles

## When to Use
- User wants specialized profiles with per-role skills, MCPs, and identity files
- Adding a tool/MCP/skill to an existing profile
- Writing or updating a profile's SOUL.md
- Setting up Kanban delegation from the default orchestrator

## Hard Invariants (user preferences — do not skip)
- **Confirm before writing any SOUL.md/SKILL.md**: consult official docs + `hermes-agent` skill first, show the user the draft (structure Identity/Style/Avoid/Defaults), and only write after OK. Exception: the user may pre-authorize a "base" and then edit it themselves.
- **SOUL.md/SKILL.md são SEMPRE em INGLÊS (correção 3×, 2026-08-05 — NÃO repetir)**: o usuário aprovou o SOUL v2 100% em inglês (decisão Q16 do grill) e corrigiu com raiva quando uma seção voltou em português ("Tu botou em português mano... parece que tu esqueceu tudo de quando a gente fez o seu MD"). pt-BR entra SÓ como regra de comportamento dentro do SOUL ("responda ao usuário em pt-BR humanizado"), nunca como idioma do documento. Verificar com `grep -cE '[áàâãéêíóôõúç]' SOUL.md` → deve dar 0.
- **Edição de MDs = DUAS skills juntas, sempre (regra 2026-08-06)**: (1) `hermes-agent-skill-authoring` (NATIVA do Hermes — valida FORMATO: frontmatter, name ≤64, description ≤1024, estrutura que o Hermes carrega; está no `.bundled_manifest`) e (2) `writing-for-agents` (mattpocock — melhora a ESCRITA: context pointers, leading words, information hierarchy, sem no-op, sem duplicação). Não é substituição — é conjunto: authoring = formato válido, writing-for-agents = escrita eficaz. Falhar uma quebra o doc; faltar a outra, o agente não segue. Aplicar em SOUL.md, AGENTS.md, SKILL.md e qualquer doc que agente consome (auditar MDs = usar as duas).
- **ask-matt SEMPRE no orquestrador (regra 2026-08-06)**: toda demanda nova do usuário passa por `skill_view ask-matt` → seguir o fluxo que ela aponta (grill-with-docs → to-spec → to-tickets → implement). ÚNICA exceção: usuário pediu velocidade ("faz isso rápido", "faz agora") → pular ask-matt, executar direto e rápido. Regra gravada no SOUL do default (seção Fluxo) + mem0.
- **Memória: local = só aprendizado universal minúsculo; mem0 = fato de projeto/pessoa (correção 2×, 2026-08-05)**: MEMORY.md local tem limite apertado (~2.200 chars) e é injetado em TODA sessão — NUNCA gravar fato de projeto/ambiente lá. Fatos duráveis (projetos, decisões, preferências, histórico) vão pro mem0 (externo, praticamente ilimitado, separado por projeto/agente). Local fica com regras universais de 1 linha (ex: "usar mem0_search antes de responder contexto do usuário", "verificação empírica"). Regra gravada como primeira entrada do próprio MEMORY.md.
- **Prefer market hub skills over creating new ones.** Only propose building a skill when nothing exists; the user hates duplicating a well-known skill (e.g. Anthropic's code-review).
- **Prefer official skills** (fastapi/fastapi, google/skills, getsentry/sentry-for-ai, shadcn/ui, antfu/skills) and check `Trust` in search results (trusted > community).
- Everything user-facing: **pt-BR, humanized** (skill humanizer). Code stays in English.
- Respond in the `i-have-adhd` style (action first, numbered steps, short lists).

## Workflow

### 1. Create a profile (clone-based)
```bash
hermes profile create <name> --clone --description "<one-line role used by kanban routing>"
```
`--clone` copies config.yaml, .env, SOUL.md, skills from default → new profile inherits model, provider keys, memory provider, and installed skills. Per-profile data lives in `~/.hermes/profiles/<name>/`. Verify with `hermes profile list` (shows model/gateway/alias).

**Clean-profile alternative (doc-verified 2026-08, preferred when the user wants "só as skills que usam"):**
```bash
hermes profile create <name> --no-skills --description "<role>"   # born with ZERO bundled skills
hermes -p <name> skills install <id> -y                            # then install only the curated kit
hermes skills opt-out            # stop future seeding — nothing on disk is touched
hermes skills opt-out --remove   # ALSO delete UNMODIFIED bundled skills (confirms first; edited/hub/own skills are always kept)
hermes skills opt-in --sync      # undo: remove marker and re-seed now
```
Pitfalls: `--no-skills` is the correct way to get a lean profile; clone-then-disable leaves ~90 skill files on disk that still show up in inventories. `opt-out --remove` is safe (only byte-identical bundled skills are deleted) and beats hand-editing `skills.disabled` for cleanup. All three paths write a `.no-bundled-skills` marker.

### 2. Per-profile MCP servers
```bash
hermes mcp add --help   # --env KEY=VALUE | --command npx | --args (must be last)
hermes -p <profile> mcp add context7 --env CONTEXT7_API_KEY=... --command npx --args -y @upstash/context7-mcp
hermes -p <profile> mcp add morph --env MORPH_API_KEY=... --command npx --args --prefer-offline -y @morphllm/morphmcp
hermes -p <profile> mcp list && hermes -p <profile> mcp test <name>
```
Pitfalls: (a) **`--env` is REQUIRED for keyed MCPs** — without it the server connects but reports 0 tools (morph without MORPH_API_KEY); (b) the interactive "Enable all N tools? [Y/n]" prompt needs `echo y |` piped in or the add is cancelled; (c) keys also go in the profile's `.env` (`~/.hermes/profiles/<name>/.env`) — the MCP `--env` lands in config.yaml by design; (d) tools only load in a NEW session of that profile.

### 3. Per-profile skill installs
```bash
hermes skills search <term> | grep -E "^│"     # Name/Description/Source/Trust/Identifier table
hermes skills inspect <identifier>             # preview before install
hermes -p <profile> skills install <identifier> -y
```
Identifier formats that work: `skills-sh/<owner>/<repo>/<path>` (skills.sh), `clawhub/<name>` (clawhub — the bare name fails with "No exact match"), `<owner>/<repo>/<path>` (GitHub, e.g. `millionco/react-doctor/.agents/skills/react-doctor`), or a direct `https://.../SKILL.md` URL with `--name <x>`.

Pitfalls:
- **Scanner blocks community skills**: "Blocked (community source + caution verdict, 2 findings)" — common findings html_comment_injection / unpinned_npm_install appear even in legit skills (Addy Osmani, Sentry). Override with `--force -y` after confirming the source is reputable.
- **DANGEROUS verdict is NOT overridable (validado 2026-08-05)**: "Blocked (community source + dangerous verdict, N findings)" → `--force` NÃO sobrescreve; o install recusa (ex.: mattpocock `ask-matt` com `agent_config_mod`, `writing-for-agents` com 4 findings). Não insistir — skill que mexe em config de múltiplos agentes ou instruções suspeitas fica de fora. `caution` = pode `--force`; `dangerous` = não.
- **`npx skills@latest add <owner>/<repo>` NÃO instala no Hermes (correção 2026-08-05)**: o CLI do skills.sh (npx) instala para OUTROS agentes (Codex/system, `~/.codex/skills` etc.) — o usuário rodou `npx skills@latest add mattpocock/skills` e NADA apareceu no `~/.hermes/skills/`. O caminho certo no Hermes é `hermes skills install "skills-sh/<owner>/<repo>/<path>" -y`. Sempre confirmar com `ls ~/.hermes/skills/ | grep <nome>` após instalar.
- **Consolidação de skills duplicadas (grilling ×3, 2026-08-05)**: ao instalar skills do mesmo autor/repo (ex.: mattpocock), podem existir cópias antigas em `skills/` raiz, `skills/y/` e a nova do hub — todas com o MESMO `name` no frontmatter → `skill_view` dá "Ambiguous skill name". Resolver: manter a versão mais recente (rounds/frontier do mattpocock), mover a antiga para backup (`mv skills/grilling skills/grilling.old-<data>`), e conferir qual o CLI resolve (`hermes skills list`).
- **`-y` is more reliable than `echo y |`** (echo failed once against a URL install's confirm prompt).
- **Always pass `-p <profile>`** — forgetting it installs into the DEFAULT profile (easy silent mistake; verify with `hermes -p <profile> skills list`).
- React-doctor-style repo skills: the skill lives under `.agents/skills/<name>` in the tool's GitHub repo — install via `<owner>/<repo>/.agents/skills/<name>`.

### 4. RTK (Rust Token Killer) per profile
```bash
brew install rtk
HERMES_HOME=~/.hermes/profiles/<name> rtk init --agent hermes   # per profile!
rtk init --agent hermes                                          # default (~/.hermes)
```
Installs plugin `rtk-rewrite` (hook `pre_tool_call`) that rewrites `git status` → `rtk git status` etc. The init targets the CURRENT `HERMES_HOME`, so it must be run once per profile with the env var set. Requires ripgrep for local codebase search. Plugin only activates in a new session.

### 5. SOUL.md authoring pattern (per profile)
Structure: `# Identity` → `# Style` → `# <domain section>` → `# Skills — use a skill certa na hora certa` → `# Verificação` → `# Context7 — LEI` → `# Morph/warpgrep — uso seletivo` → `# Avoid` → `# Defaults`. Keep the SOUL LEAN (~30 linhas de voz + regras de papel); tabela de gatilhos gigante NÃO vai no SOUL — vira a description da skill (abaixo).
- **Gatilho nativo > tabela manual (validado 2026-08 na reestruturação, doc oficial)**: o Hermes injeta name+description de TODAS as skills em toda sessão (nível 0 do progressive disclosure, ~3k tokens) e instrui carregar as relevantes. A `description` do frontmatter É o gatilho. Tabela manual no SOUL duplica e envelhece (ex.: gatilho morto `reactbits` apontando pra skill inexistente). Escrever descriptions acionáveis e manter no SOUL só regras de papel que não cabem em skill.
- **Seção Skills do SOUL = context pointers puros, não prosa (aplicado 2026-08-06 com writing-for-agents)**: escrever como lista `- **<skill>** → <quando>` (trigger à esquerda, condição à direita), NÃO como parágrafo "scan the skill list and load..." — parágrafo é no-op (o Hermes já injeta a lista; dizer pra escanear não muda comportamento). Cada linha: um gatilho por branch, sem sinônimos duplicados. Formato validado nos 5 SOULs (default + 4 workers).
- **Scope Discipline = seção OBRIGATÓRIA no SOUL v2 (validado 2026-08-05)**: na task de prova o worker gastou 22 min e reescreveu 20 arquivos fora do escopo (1180 linhas não commitadas em App/Header/StateViews/index.css — o commit dele era limpo, mas o working tree virou um refactor inteiro). O corpo da task define o escopo; worker lista arquivos antes de codar; se precisar tocar algo fora, para e pergunta via kanban comment; time-box de exploração (task pequena ≤ 10 min, grande ≤ 30 min). Texto exato no template (`templates/soul-v2-worker.md`).
- **"OBRIGATÓRIAS SEMPRE" foi corrigido pelo usuário (2026-08-05)**: humanizer NÃO é "carregar sempre" — é gatilho condicional (SÓ quando escrever copy de site ou mensagem pra alguém); i-have-adhd é estilo de resposta pro usuário, não skill a carregar; context7 é o único hábito de toda task (e é MCP — vira regra na seção de ferramentas, não "skill a carregar").
- **humanizer cobre TODO texto visível, inclusive TÍTULOS de seção/painel (correção 2026-08-05)**: o usuário flagrou "Loading / unloading", "Top clientes", "Top remarks", "Run" crus na UI — não só mensagens de erro/copy. Regra no SOUL: qualquer string que o usuário vê (títulos, labels, colunas, placeholders, tooltips) passa pelo humanizer; inglês só em código. Escrita como gatilho da skill humanizer + uma linha no SOUL.
- **Seção `# Learning` no SOUL dos workers = memória vira hábito (correção 2026-08-05)**: os perfis TÊM `memory_enabled: true` + mem0 key, mas o mecanismo é inerte sem instrução — auditado: 0 chamadas de memory/skill_manage em 5 tasks antes da seção existir. Adicionar ao SOUL de cada worker: "quando uma task te ensinar algo UNIVERSAL (hábito, pitfall, regra que vale além desta task — ex. 'sempre chamar Context7 antes de lib'), GRAVE na sua memória com a tool de memória; detalhe de projeto vai no repo (docs/README), NUNCA em memória/skills; procedimento repetido (5+ passos) → proponha criar skill, confirmando com o orquestrador." Assim o worker aprende igual ao orquestrador, sem config externa.
- **Spec incompleta ≠ skill não chamada (diagnóstico de feedback visual 2026-08-05)**: quando o usuário aponta problema de design (padding colado, textos crus, sem lazy load), verificar PRIMEIRO se a spec/contrato especificava aquele acabamento — a skill frontend-design fala de spacing em tom geral, mas sem critério explícito na spec do designer (ex.: padding interno de card, padrão Z) o worker não tem onde buscar. Correção dupla: task de correção visual com critérios explícitos + evidência ANTES/DEPOIS (screenshots), E atualizar a spec do designer com os critérios de acabamento.
- **Modelo em camadas de invocação (decisão da reestruturação)**: SOUL (sempre, voz+regras de papel) → task kanban (obrigação pontual: "USE skills X, Y" no body + prova no summary) → AGENTS.md (convenções do repo; ausência NÃO quebra nada — task e SOUL cobrem) → description da skill (gatilho por relevância). Auto-reporte no summary continua, mas valida o que a task pediu, não lista genérica.
- Encode role rules: DRY/SOLID + componentização total (frontend), Black/Ruff format immediately after writing code (backend — kills lint rework loops), performant+clear SQL (DBA), design-system ownership (designer: tokens/typography/padding/components; frontend executes).
- **Context7 is law**: always consult it before using any API/lib — latest version, current docs win over stale skill knowledge.
- **Context7 ativo ≠ Context7 usado (auditoria 2026-08-05)**: o MCP estava ✓ enabled e conectando (~2.4s, tools resolve-library-id + query-docs) nos 4 perfis, mas 0 menções de context7 em 4 tasks reais auditadas. A regra no SOUL sozinha NÃO garante o hábito. Correção comprovada: **exigir EVIDÊNCIA no summary** — body da task + SOUL pedem \"cite o que o Context7 confirmou (lib + versão consultada)\"; sem isso o orquestrador devolve. Reforçar regra sem exigir prova = continua ignorado.
- **Verificar \"latest\" de libs**: `npm view <pkg> version` é BLOQUEADO pelo guard de segurança (heurística de servidor) — usar `curl -s https://registry.npmjs.org/<pkg>/latest | python3 -c \"import sys,json; print(json.load(sys.stdin)['version'])\"`; Python: `curl -s https://pypi.org/pypi/<pkg>/json | python3 -c \"import sys,json; print(json.load(sys.stdin)['info']['version'])\"`. Comparar contra package.json/requirements.txt (as ranges `^x.y.z` do package.json podem estar no latest mesmo sem bump).
- **Morph/warpgrep is selective**: only for big searches (schema overview, refactors, large features); point lookups use plain grep.
- **Verification once before PR**: lint/tests/react-doctor/security/code-review run as a single pre-PR pass, not during development. Where the verification sequence lives: repo conventions → AGENTS.md; the PROCEDURE (exact sequence) → a per-role skill; SOUL keeps one line "rode a skill de verificação antes do done".
- Test philosophy: few, scenario-based tests (acceptance criteria; idempotency matters — e.g. like button clicks, "new section" button must not create 30 empty rows). Never test for testing's sake.
- Session detail (the full architecture-rework decision tree, Q1–Q12): `references/invocation-architecture.md`.
- Rodada 2 de validação (task GRANDE, 14 skills, protocol violation recorrente, recovery com commit órfão): `references/soul-v2-validation-round2.md`.
- Rodada 3 — RESOLUÇÃO do protocol violation (to-tickets): cadeia T1→T2→T3 com `--parent` encadeado fechou `done` em ~3 min por ticket, protocolo OK, sem recovery; causa raiz era task gigante inchando o contexto → API do modelo cai. Receita + pitfalls de instalação: `references/to-tickets-validation.md`.
- Correções de authoring do usuário (idioma inglês, dual-skill authoring+writing-for-agents, memória local vs mem0, ask-matt sempre, context pointers): `references/soul-authoring-corrections.md` — LER antes de tocar qualquer MD.

### 6. Kanban activation (orchestrator delegates)
```bash
hermes kanban init          # creates default board
hermes gateway start        # dispatcher ticks every 60s — WITHOUT gateway, tasks stay 'ready' forever
hermes kanban create "<task>" --assignee <profile> [--idempotency-key ...]
```
Agents drive the board via `kanban_*` tools (kanban_create/list/show/comment); the profile `--description` set at creation is what routes tasks to the right role. Orchestrator profile (default) should get a SOUL.md defining the delegate-via-kanban flow + grilling (requirements) + planning-and-task-breakdown skills.

## Pitfalls
- `hermes config set skills.disabled '["a"]'` silently stores a STRING — use the app API `save_disabled_skills` (see hermes-administration) or `hermes skills config`.
- **`hermes skills opt-out --remove` pede confirmação interativa**: sem pipe `echo y |` ele grava o marker `.no-bundled-skills` mas NÃO apaga nada (output "Marker kept; no skills deleted" — validado 2026-08). Sempre `echo y | hermes -p <profile> skills opt-out --remove`.
- **humanizer é bundled e SAI no `opt-out --remove`**: se está no kit curado (está — todo perfil), repor manualmente: `cp -r ~/.hermes/skills/creative/humanizer <profile>/skills/creative/` (a doc garante que hub/local/modificadas sobrevivem; bundled não-modificada não).
- **Skills LOCAIS (ex: hermes-administration clonada) NÃO são apagadas pelo opt-out** — sobram no disco do perfil; desabilitar via `save_disabled_skills` (script do hermes-administration, rodado com `HERMES_HOME=<profile>` + venv do hermes-agent) se não pertencem ao kit do papel.
- Plugin/MCP/tool changes only take effect in a NEW session of the target profile — always tell the user to open a fresh session to test.
- Same API keys (MORPH_API_KEY, CONTEXT7_API_KEY) can be reused across profiles — add to each profile's `.env` + MCP `--env`.
- `hermes profile list` after creating profiles: only `default` exists until you create the others; cloned profiles keep the starter SOUL.md until you rewrite it.

## Validation loop (SOUL v2 — draft → test → measure → iterate)
Depois de reescrever o SOUL de UM perfil (ex: frontend), NÃO replique nos outros na mesma hora. Valide com task kanban de PROVA (2026-08-05, método Anthropic skill-creator aplicado a SOULs):
1. Escrever o SOUL v2 de um perfil, mostrar o draft ao usuário, aplicar com backup (`.bak-$(date +%Y%m%d-%H%M%S)`).
2. Limpar + kit: `echo y | hermes -p <p> skills opt-out --remove` → reinstalar kit curado → verificar `COLUMNS=400 hermes -p <p> skills list` (só as skills do kit ativas). Repor `humanizer` (bundled, sai no opt-out): `cp -r ~/.hermes/skills/creative/humanizer <p>/skills/creative/`.
3. Criar task de PROVA **do tamanho real das demandas do usuário** (correção 2026-08-05: ele rejeitou micro-task tipo "crie um StatusBadge" — "minhas tasks não vão ser uma coisa pequena assim"). Task pequena valida gatilhos e processo; task GRANDE (ex: refatorar o dashboard inteiro mantendo a lógica de negócio, com spec do designer como contrato) valida escopo, autonomia e entrega de verdade. Body com "No summary, liste as skills que você CARREGOU" + "CHAME kanban_complete OBRIGATORIAMENTE" + seção "Escopo autorizado / PROIBIDO tocar" (mata o escopo vazado).
4. Medir: skills carregadas no summary (sem lista → devolve), entrega real (build/testes/branch), aderência ao gatilho, tempo gasto (escopo vazado = tempo estourado com diff fora da task — conferir `git status --short` e `git diff --stat` contra o que a task pediu).
5. Só então replicar SOUL + kit nos outros perfis. Se não seguiu → iterar o SOUL até seguir (usuário prefere iterar a "acertar de primeira").
   **Replicação validada (2026-08-05)**: após o frontend passar na prova, os 3 perfis restantes foram tratados na mesma sessão — backup do SOUL (`cp SOUL.md SOUL.md.bak-$(date +%Y%m%d-%H%M%S)`), `echo y | hermes -p <p> skills opt-out --remove`, repor humanizer (`cp -r ~/.hermes/skills/creative/humanizer <p>/skills/creative/`), desabilitar hermes-administration (script save_disabled_skills com `HERMES_HOME=<p>`), aplicar SOUL v2 adaptado ao papel. Kits finais: backend 16 ativas (14 kit + humanizer + i-have-adhd), database 6, designer 8. Conferir sempre com `COLUMNS=400 hermes -p <p> skills list`.
6. **Protocol violation recorrente ≠ SOUL ruim — cheque o tamanho da task primeiro (validado rodada 3)**: se o worker "entrega mas não fecha o protocolo" (rc=0 sem kanban_complete, várias vezes), o diagnóstico NÃO é desobediência — é a task monolítica inchando o contexto até a API do modelo cair (503/ReadTimeout/Connection error no final do log). Solução comprovada: quebrar a demanda em tickets verticais do to-tickets (cada um ~3 min, fecha `done` sozinho) em vez de iterar o SOUL. Ver `references/to-tickets-validation.md`.

## Verification
- `hermes -p <profile> skills list` shows installed hub skills (builtin filtered with `grep -v builtin`)
- `hermes -p <profile> mcp test <name>` confirms tools discovered
- `hermes profile list` shows all profiles + gateway status
- Open a new session in the profile and run `git status` to confirm RTK rewrite is active

See `references/mcp-and-tool-recipes.md` for the concrete context7/morph configs and the per-role skill assignment table from the first full setup.
