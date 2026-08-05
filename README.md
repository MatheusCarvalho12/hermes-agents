# 🤖 Hermes Agents — Time Multi-Perfil

Distribuições oficiais dos meus agentes [Hermes](https://hermes-agent.nousresearch.com) (Nous Research), prontas pra restaurar em qualquer máquina com **um comando**.

> Backup de configuração → **nunca** contém memórias, sessões, `.env`, `auth.json` nem chaves de API. O installer do Hermes exclui isso automaticamente (ver [docs oficiais](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions)).

## 🧑‍💻 Quem são os agentes

| Perfil | Pasta | Papel |
|---|---|---|
| 🎛️ Orquestrador | `orchestrator/` | Gerencia o time via kanban, decide quem faz o quê, delega e administra o Hermes |
| 🎨 Frontend | `frontend-developer/` | React, shadcn/ui, performance/Lighthouse, a11y, UI pt-BR |
| ⚙️ Backend | `backend-developer/` | FastAPI, SQLAlchemy/Alembic, pytest, APIs REST, segurança |
| 🗄️ Database | `database-developer/` | Postgres, SQL, modelagem, migrações, otimização |
| 🎯 Designer | `designer/` | Design system, branding, tokens, Figma, direção visual |

## 🚀 Restaurar em outra máquina (2 passos)

```bash
# 1. Clone o repo
git clone https://github.com/MatheusCarvalho12/hermes-agents.git
cd hermes-agents

# 2. Instale cada agente que quiser (um comando por perfil)
hermes profile install ./orchestrator --alias
hermes profile install ./frontend-developer --alias
hermes profile install ./backend-developer --alias
hermes profile install ./database-developer --alias
hermes profile install ./designer --alias
```

Pronto — cada perfil vira um comando (`frontend-developer chat`, `backend-developer chat`, ...). Suas memórias/sessões ficam vazias por design; as chaves de API você preenche no `.env` de cada perfil (o installer gera `.env.EXAMPLE`).

## 🔄 Atualizar (puxar mudanças sem perder dados)

```bash
git pull
hermes profile update orchestrator
hermes profile update frontend-developer
# ...
```

## 🛡️ O que vai / o que não vai

**Incluído** (por design do distribution): `SOUL.md`, `config.yaml` (sanitizado), `skills/` ativas, `plugins/`, `cron/` (se houver), `mcp.json`.

**Excluído SEMPRE**: `.env`, `auth.json`, `memories/`, `sessions/`, `logs/`, `state.db*`, caches, `plans/`, `home/`, `workspace/` — o `.gitignore` + o installer garantem isso nos dois lados.

## 📦 Detalhes por agente

- **Orquestrador**: time completo + kanban ativo; roteia tarefas pelo `--description` de cada perfil. Regras de ouro: Context7 sempre, git com squash + cleanup de branch pós-merge, código em inglês, UI em pt-BR humanizada.
- **Frontend**: componentização total, design system do designer manda, testes com Playwright headless.
- **Backend**: DRY/SOLID, testes de verdade (build + stack real + endpoints), sem mock quando o back existe.
- **Database**: schema com migrações (Alembic), queries otimizadas, Postgres real nos testes.
- **Designer**: dono do design system e tokens; telas novas com direção visual viram task pai do frontend.

## 📜 Licença

MIT — uso pessoal/estudo. Feito com [Hermes Agent](https://github.com/NousResearch/hermes-agent).
