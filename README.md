# My Hermes Agents — Minha Harness Multi-Agente

![License](https://img.shields.io/badge/license-MIT-blue) ![Release](https://img.shields.io/github/v/release/MatheusCarvalho12/my-hermes-agents) ![Agentes](https://img.shields.io/badge/agentes-5-orange) ![Skills](https://img.shields.io/badge/skills-95-green)

> **Minha harness pessoal** construída com [Hermes Agent](https://hermes-agent.nousresearch.com) (Nous Research) — o time de agentes que eu sempre quis: cada perfil com papel, skills e memória próprios, orquestrados por mim. Restaurável em qualquer máquina com um comando.
>
> **Backup de configuração** — nunca contém memórias, sessões, `.env`, `auth.json` nem chaves de API (o installer do Hermes exclui isso por design).

## 👥 O time

| Agente | Papel | Skills ativas |
|---|---|---|
| ![orchestrator](https://img.shields.io/badge/-orchestrator-326CE5?logo=kubernetes&logoColor=white) | Orquestrador — gerencia o time via Kanban, decide quem faz o quê, delega e administra o Hermes. | 45 |
| ![frontend-developer](https://img.shields.io/badge/-frontend--developer-61DAFB?logo=react&logoColor=white) | Frontend — React, shadcn/ui, performance/Lighthouse, a11y e UI pt-BR humanizada. | 23 |
| ![backend-developer](https://img.shields.io/badge/-backend--developer-009688?logo=fastapi&logoColor=white) | Backend — FastAPI, SQLAlchemy/Alembic, pytest, APIs REST e segurança. | 15 |
| ![database-developer](https://img.shields.io/badge/-database--developer-4169E1?logo=postgresql&logoColor=white) | Database — Postgres, SQL, modelagem, migrações e otimização. | 5 |
| ![designer](https://img.shields.io/badge/-designer-F24E1E?logo=figma&logoColor=white) | Designer — design system, branding, tokens, Figma e direção visual. | 7 |

*Última atualização: 06/08/2026 — 5 agentes, 95 skills ativas no total.*

## 💾 Restaurar em outra máquina

```bash
git clone https://github.com/MatheusCarvalho12/my-hermes-agents.git
cd my-hermes-agents
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

## 🧩 Skills por agente

### ![orchestrator](https://img.shields.io/badge/-orchestrator-326CE5?logo=kubernetes&logoColor=white)

`agent-browser` | `alembic-migrations` | `api-integration-research` | `ask-matt` | `captcha-solver-integrations` | `captcha-solving` | `code-review` | `code-search-agents` | `codebase-design` | `database-migrations` | `diagnosing-bugs` | `domain-modeling` | `github-readme-badges` | `grill-me` | `grill-with-docs` | `grilling` | `handoff` | `hermes-administration` | `hermes-multi-profile-iteration` | `hermes-multi-profile-ops` | `hermes-profile-distributions` | `hermes-profile-engineering` | `hermes-profile-fleets` | `hermes-team-operations` | `i-have-adhd` | `implement` | `improve-codebase-architecture` | `kanban-orchestration` | `morph-warpgrep` | `onepassword-integration` | `planning-and-task-breakdown` | `portais-receita-brasil` | `prototype` | `resolving-merge-conflicts` | `saas-integration-research` | `tdd` | `teach` | `to-questionnaire` | `to-spec` | `to-tickets` | `triage` | `wait-what` | `wayfinder` | `wizard` | `writing-for-agents`

### ![frontend-developer](https://img.shields.io/badge/-frontend--developer-61DAFB?logo=react&logoColor=white)

`accessibility` | `agent-browser` | `chrome-devtools` | `code-review` | `docker` | `frontend-design` | `humanizer` | `i-have-adhd` | `lighthouse` | `performance` | `playwright` | `r3f-animation` | `react-doctor` | `react-testing-library` | `responsive-design` | `scroll` | `security-review` | `sentry-react-sdk` | `shadcn` | `spline-interactive` | `test-review` | `view-transitions` | `vitest`

### ![backend-developer](https://img.shields.io/badge/-backend--developer-009688?logo=fastapi&logoColor=white)

`api-design-principles` | `api-testing` | `code-review` | `fastapi` | `http-api` | `humanizer` | `i-have-adhd` | `pytest` | `ruff` | `security-review` | `sentry-fix-issues` | `sentry-python-sdk` | `sentry-sdk-setup` | `sqlalchemy-alembic-expert-best-practices-code-review` | `test-review`

### ![database-developer](https://img.shields.io/badge/-database--developer-4169E1?logo=postgresql&logoColor=white)

`bigquery-basics` | `humanizer` | `i-have-adhd` | `postgres-best-practices` | `sql`

### ![designer](https://img.shields.io/badge/-designer-F24E1E?logo=figma&logoColor=white)

`Design System` | `design-principles` | `design-tokens` | `figma` | `humanizer` | `i-have-adhd` | `typography`

## 🙏 Thanks

To [@teknium1](https://github.com/teknium1) and the whole [Nous Research](https://nousresearch.com/) team — thank you for building **Hermes Agent**.

I tried a lot of AI tools before this one. I could never get my agents to work the way I wanted — the skills, the memory, the whole setup always felt like fighting the tool instead of using it. Hermes was the first framework that actually let me build the multi-agent team I had in mind, and it just *works*. This repo is the proof.

## 📜 Licença

MIT — uso pessoal/estudo. Feito com [Hermes Agent](https://github.com/NousResearch/hermes-agent).
