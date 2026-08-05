# Browser / e2e no Hermes — 3 caminhos e quando usar cada um

Mapa validado com o usuário (2026-08). O usuário usa **Side** (side.app) no Mac pra uso pessoal — bom pra ele, mas NÃO é engine do Hermes nem backend de teste (usa o perfil Chrome local dele; teste precisa de contexto isolado). Não tentar integrar Side nos workers.

## 1. Browser remoto (Browser Use — assinatura Nous)
- Tools `browser_navigate/click/snapshot/vision` do orquestrador.
- Roda Chrome em infra gerenciada pela Nous (**nuvem, não na máquina do usuário** — ele nunca vê nada abrir).
- Por baixo: Playwright dirigindo Chrome remoto headless.
- Uso: QA/inspeção do orquestrador, telas que precisam de "olhar ao vivo". Não é pra worker de build.

## 2. cua-driver local (computer_use / cua_browser_*)
- Roda NA máquina do usuário **em background, sem roubar cursor/foco**.
- Tem browser tipado com **profiles**: `isolated_new`, `isolated_named`, `existing_profile` (a "parada de perfil" que o usuário menciona).
- Uso: automação de desktop local, browser local controlado. NÃO usar para e2e massivo de workers.

## 3. Playwright CLI headless nos workers (O PADRÃO DE TESTE)
- `npx playwright test` — **sem janela, invisível, paralelo** (N workers ao mesmo tempo).
- ⚠️ O usuário REJEITA modo headed: "meu computador ficava mexendo", "não rodava 2 ao mesmo tempo" — headed abre Chrome na frente e rouba o computador. Headless resolve os dois.
- Regra travada no gatilho do SOUL do front: "SEMPRE headless, proibido modo headed/interativo".
- Skills: `playwright` (skills-sh/openai/skills/playwright, trusted) no front; `docker` (skills-sh/mindrally/skills/docker — o do bobmatnyc é BLOQUEADO por veredito dangerous) no front; `pytest` + `api-testing` no back.

## Garantia factual (usuário pediu): o browser_* NÃO roda na máquina dele
- `grep browser ~/.hermes/config.yaml` → `browser.cloud_provider: browser-use` — os tools `browser_*` do Hermes rodam na nuvem Nous. N workers em paralelo (3, 5, 8 fronts) NÃO conflitam com o uso pessoal do Mac dele. Quando ele diz "me garante que roda na remota", a resposta é a config, não promessa.

## 4. agent-browser (Vercel Labs) — CLI LOCAL com perfil persistente (login)
- **Roda LOCAL na máquina do usuário** (⚠️ o oposto do browser remoto). Instalação: `brew install agent-browser` + `agent-browser install` (baixa Chrome for Testing, ~180MB em `~/.agent-browser/browsers/`).
- Skills instaladas: `skills-sh/vercel-labs/agent-browser/agent-browser` no DEFAULT (orquestrador) e no frontend.
- Comandos core: `open <url>`, `snapshot` (árvore a11y com refs), `click @e2` / `fill @e3 "texto"`, `read [url]` (fetch agent-friendly, sem abrir Chrome — mais barato que browser remoto), `state save`, `close`.
- **Perfis persistentes (o que o usuário quer p/ login salvo)**: `--profile <nome>` (reusa Chrome com login), `--profile <path>` (estado completo), `--auto-connect` + `state save` (importa auth de uma sessão Chrome já logada), `--session <id> --restore` (cookies+localStorage), `--state <path>`. Cloud: `-p kernel` (Kernel, pago — usuário rejeita pago), `-p agentcore` (AWS).
- **Uso restrito (regra do usuário, travada no SOUL do orquestrador e do front)**: workers testam SEMPRE com browser remoto ou playwright headless — agent-browser local NUNCA para e2e em paralelo (daria o conflito que ele previu). agent-browser serve só pra tarefa PONTUAL do orquestrador: logar num site 1x e manter a sessão entre conversas.
- **Regra de senha (usuário insistiu que vai mandar)**: aceitar a senha 1x para logar e salvar a sessão no perfil; NUNCA gravar em memória (mem0/memory); avisar honestamente que fica no histórico da conversa; Google/2FA = o próprio usuário loga (ele faz questão). Ideal: usuário loga 1x no perfil persistente e nunca mais circula senha.

## Skills de browser do hub (instaladas nesta rodada — usuário pediu)
- `chrome-devtools` (`skills-sh/chromedevtools/chrome-devtools-mcp/chrome-devtools`, repo oficial do MCP) → instalada no FRONT: debug de UI (console, erros, a11y, profiler, React tree). O usuário considera importante.
- `agent-browser` (vercel-labs) → instalada no DEFAULT + FRONT (ver seção 4 acima).
- Avaliadas e NÃO adicionadas: `browser-use` (repo oficial — é o que a Nous usa por baixo, dispensa), `agentic-browser` (clawhub/inference.sh — lib concorrente).
- Conclusão revisada: playwright headless (workers) + browser remoto nativo (QA) + agent-browser local (login persistente pontual) + chrome-devtools (debug) cobrem o cenário.
