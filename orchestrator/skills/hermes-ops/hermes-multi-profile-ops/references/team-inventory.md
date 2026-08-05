# Time multi-perfil do usuário — inventário (snapshot 2026-08)

Snapshots mudam; re-verificar com `hermes profile list` / `hermes -p <perfil> skills list` / `hermes -p <perfil> mcp list` antes de confiar.

## Perfis
| Perfil | Papel | Stack |
|---|---|---|
| default | Orquestrador (delega via kanban) | tudo de gestão; SEM skills de código |
| frontend-developer | Executor React | React + TS + shadcn/ui + React Bits |
| backend-developer | APIs | FastAPI + Pydantic, padrão Black/Ruff |
| database-developer | Banco | Postgres, BigQuery |
| designer | Dono do design system | tokens/cores/tipografia/padding; gera imagens; frontend executa o que ele propõe |

Todos criados com `--clone` (herdam modelo deepseek-v4-flash, mem0, desativações de skills) e `--description` que o kanban usa p/ rotear.

## Skills do hub por perfil
| Perfil | Skills ativas (identifier abreviado) |
|---|---|
| frontend-developer | accessibility, code-review, frontend-design, lighthouse, performance, r3f-animation, react-doctor, react-testing-library, responsive-design, scroll, security-review, sentry-react-sdk, shadcn, spline-interactive, test-review (nm-pensive), view-transitions, vitest, playwright (e2e headless), docker (stack local), **chrome-devtools (debug UI)**, **agent-browser (perfil persistente)** + metodologia (spike, systematic-debugging, tdd) + humanizer, i-have-adhd |
| backend-developer | api-design-principles, code-review, fastapi, http-api, ruff, security-review, sentry-fix-issues, sentry-python-sdk, sentry-sdk-setup, sqlalchemy-alembic-expert-best-practices-code-review, test-review (nm-pensive), **pytest**, **api-testing** + metodologia (spike, systematic-debugging, tdd) + humanizer, i-have-adhd |
| database-developer | bigquery-basics, postgres-best-practices, **sql** + humanizer, i-have-adhd |
| designer | Design System, design-principles, design-tokens, figma, typography + claude-design, design-md, popular-web-designs, sketch + humanizer, i-have-adhd |
| default | grilling (mattpocock), planning-and-task-breakdown (addyosmani) + **agent-browser (browser com perfil persistente/logins)** + todo o bundle geral (faz-tudo/orquestrador) |

**Limpeza 2026-08**: perfis dev foram criados com `--clone` e herdaram o `skills/` inteiro do default (~75-90 skills cada). Desabilitei a herança que não pertence ao papel via `skills.disabled` por perfil (reversível; nada foi apagado do disco). Default fica intacto (é o faz-tudo). Backup dos config.yaml: `config.yaml.bak-*` em cada perfil.

Família Nm Pensive (clawhub) tem também `nm-pensive-api-review` e `nm-pensive-architecture-review` (não instaladas; ofertáveis ao backend).

## MCPs por perfil
| Perfil | MCP | Comando |
|---|---|---|
| frontend-developer | context7 | npx -y @upstash/context7-mcp (env CONTEXT7_API_KEY) |
| frontend-developer | morph | npx --prefer-offline -y @morphllm/morphmcp (env MORPH_API_KEY) — warpgrep = codebase_search |
| frontend-developer | shadcn | npx shadcn@latest mcp |
| frontend-developer | reactbits | npx reactbits-dev-mcp-server |
| backend-developer | context7 + morph | idem |
| database-developer | morph | idem |

## Ferramentas de sistema
- RTK (Rust Token Killer) — brew; plugin rtk-rewrite ativo nos 5 perfis (hook pre_tool_call)
- Gitleaks — brew (front + back; DBA não)
- React Doctor CLI — npx react-doctor@latest (skill instalada no front)
- WarpGrep requer ripgrep (instalado)

## Regras de ouro do usuário
1. Context7 = LEI (sempre; versão mais recente; doc atual vence)
2. Morph/warpgrep seletivo (só busca grande)
3. Verificação única pré-PR; formatação imediata (ruff)
4. Skills com gatilhos explícitos no SOUL.md
5. Código inglês / UI pt-BR humanizada / sem "Internal Server Error" cru
6. DRY/SOLID + componentização total + sem over-engineering
7. Filosofia de testes: poucos, por cenários/critérios de aceitação (ex: curtida idempotente; "Nova seção" não cria 30 seções vazias)
