# 🤖 Hermes Agents — Time Multi-Perfil

> Distribuições oficiais dos meus agentes [Hermes](https://hermes-agent.nousresearch.com) (Nous Research) — restauração em qualquer máquina com um comando.
>
> **Backup de configuração** — nunca contém memórias, sessões, `.env`, `auth.json` nem chaves de API (o installer do Hermes exclui isso por design).

## 🧑‍💻 O time

| | Agente | Papel | Skills ativas |
|---|---|---|---|
| 🎛️ | `orchestrator` | Orquestrador — gerencia o time via Kanban, decide quem faz o quê, delega e administra o Hermes. | 9 |
| 🎨 | `frontend-developer` | Frontend — React, shadcn/ui, performance/Lighthouse, a11y e UI pt-BR humanizada. | 22 |
| ⚙️ | `backend-developer` | Backend — FastAPI, SQLAlchemy/Alembic, pytest, APIs REST e segurança. | 14 |
| 🗄️ | `database-developer` | Database — Postgres, SQL, modelagem, migrações e otimização. | 4 |
| 🎯 | `designer` | Designer — design system, branding, tokens, Figma e direção visual. | 6 |

*Última atualização: 05/08/2026 — 5 agentes, 55 skills ativas no total.*

## 🚀 Restaurar em outra máquina

```bash
git clone https://github.com/MatheusCarvalho12/hermes-agents.git
cd hermes-agents
hermes profile install ./orchestrator --alias
hermes profile install ./frontend-developer --alias
hermes profile install ./backend-developer --alias
hermes profile install ./database-developer --alias
hermes profile install ./designer --alias
```

Suas memórias/sessões nascem vazias por design; chaves de API você preenche no `.env` de cada perfil (o installer gera `.env.EXAMPLE`).

## 🔄 Atualizar (sem perder dados)

```bash
git pull
hermes profile update orchestrator frontend-developer backend-developer database-developer designer
```

## 🛡️ O que vai / o que não vai

**Incluído:** `SOUL.md`, `config.yaml` (sanitizado), `skills/` ativas, `plugins/`, `cron/`, `mcp.json`.

**Excluído SEMPRE:** `.env`, `auth.json`, `memories/`, `sessions/`, `logs/`, `state.db*`, caches — garantido pelo `.gitignore` + installer nos dois lados.

## 📦 Skills por agente

### 🎛️ orchestrator

`agent-browser` | `grilling` | `hermes-administration` | `hermes-multi-profile-ops` | `hermes-profile-distributions` | `hermes-profile-engineering` | `hermes-profile-fleets` | `i-have-adhd` | `planning-and-task-breakdown`

### 🎨 frontend-developer

`accessibility` | `agent-browser` | `chrome-devtools` | `code-review` | `docker` | `frontend-design` | `i-have-adhd` | `lighthouse` | `performance` | `playwright` | `r3f-animation` | `react-doctor` | `react-testing-library` | `responsive-design` | `scroll` | `security-review` | `sentry-react-sdk` | `shadcn` | `spline-interactive` | `test-review` | `view-transitions` | `vitest`

### ⚙️ backend-developer

`api-design-principles` | `api-testing` | `code-review` | `fastapi` | `http-api` | `i-have-adhd` | `pytest` | `ruff` | `security-review` | `sentry-fix-issues` | `sentry-python-sdk` | `sentry-sdk-setup` | `sqlalchemy-alembic-expert-best-practices-code-review` | `test-review`

### 🗄️ database-developer

`bigquery-basics` | `i-have-adhd` | `postgres-best-practices` | `sql`

### 🎯 designer

`Design System` | `design-principles` | `design-tokens` | `figma` | `i-have-adhd` | `typography`

## 📜 Licença

MIT — uso pessoal/estudo. Feito com [Hermes Agent](https://github.com/NousResearch/hermes-agent).
