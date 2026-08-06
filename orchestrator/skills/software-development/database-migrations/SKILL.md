---
name: database-migrations
description: "Use when alembic upgrade falha ou banco local esta orfao."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [alembic, migrations, postgres, sqlalchemy, troubleshooting]
    related_skills: [diagnosing-bugs]
---

# Database Migrations

Troubleshooting de migrations (alembic/sqlalchemy + Postgres): falha em banco limpo, banco órfão de revisão refeita, reset seguro. Ambos os pitfalls abaixo foram reproduzidos e resolvidos em 2026-08-06 (repo flowmex core).

## Pitfall 1 — `version_table_schema` aponta para schema criado só pela migration base

**Sintoma**: `alembic upgrade head` falha em banco limpo com:
```
asyncpg.exceptions.InvalidSchemaNameError: schema "runtime" does not exist
```
A tabela `alembic_version` é criada ANTES da primeira migration rodar. Se o env.py usa
`version_table_schema="runtime"` e o schema `runtime` só é criado pela migration base
(`CREATE SCHEMA IF NOT EXISTS runtime`), o alembic tenta criar `runtime.alembic_version`
antes do schema existir → erro em banco limpo. (Funciona por acaso quando o banco já tem
schemas de uma cadeia antiga.)

**Diagnóstico rápido**:
- `alembic current` e `alembic heads` (heads = head local; current falha se houver conflito)
- Version table pode viver em schema não-`public` — consultar `SELECT version_num FROM <schema>.alembic_version` (não assumir public).

**Workaround imediato** (sem editar código):
```sql
CREATE SCHEMA IF NOT EXISTS runtime;  -- nome do version_table_schema
```
depois `alembic upgrade head` (a migration base usa IF NOT EXISTS, não conflita).

**Fix de verdade**: pré-criar o schema no `env.py` (ex: `CREATE SCHEMA IF NOT EXISTS runtime`
na conexão antes de `run_migrations`) ou fora da migration base. Registrar como bug/task.

## Pitfall 2 — banco órfão: "Can't locate revision identified by 'XXXX'"

**Sintoma**: `alembic current`/`upgrade` falham com `Can't locate revision identified by 'abc123'`
e o head local (`alembic heads`) não inclui `abc123`.

**Causa**: as migrations foram REFEITAS (squash/refactor) no git depois que o banco local
já tinha sido migrado; `abc123` está gravado na version table mas não existe mais nos arquivos.

**Diagnóstico**:
1. `alembic heads` → head local
2. `SELECT version_num FROM <schema>.alembic_version` → revisão gravada no banco
3. Comparar: gravada ∉ arquivos = banco órfão

**Resolução — só depois de confirmar que o banco está VAZIO** (nunca dropar com dados):
```sql
-- contagens primeiro:
SELECT 't1', count(*) FROM schema.t1 UNION ALL ...;  -- todas = 0?
-- então:
DROP SCHEMA IF EXISTS runtime CASCADE;
DROP SCHEMA IF EXISTS companies CASCADE;   -- todos os schemas de negócio
-- e por fim:
env -u PYTHONPATH .venv/bin/alembic upgrade head
```

## Regras gerais
- **NUNCA dropar schema/tabela antes de conferir contagens** — banco local de dev vazio é resetável; banco com dados não.
- `alembic stamp` para "mentir" o estado só quando o schema atual bate com a revisão alvo — caso contrário, drop + upgrade limpo.
- Rodar migrations de projeto Python no Mac do usuário: `env -u PYTHONPATH .venv/bin/alembic ...` (PYTHONPATH do venv hermes-agent contamina).
- Após `upgrade head` em banco limpo, a prova é a suíte: `pytest` sem ERRORs de setup.
