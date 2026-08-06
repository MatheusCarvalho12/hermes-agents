---
name: alembic-migrations
description: "Alembic: rollback silencioso, schemas, verificacao real."
---

# Alembic Migrations — pitfalls e verificação

Aprendizados de 2026-08-06 (projeto flowmex-core, Postgres + asyncpg + alembic): dois bugs não-óbvios de setup de migrations que custaram ~40 min de diagnóstico.

## Pitfall 1 — ROLLBACK SILENCIOSO por transação implícita (o pior)

Sintoma: `alembic upgrade head` imprime `Running upgrade -> <rev>` para TODAS as migrations, sai com exit 0, e o banco fica VAZIO (nenhum schema, nenhuma version table). `alembic current` não mostra revisão; rodar de novo re-aplica do zero.

Causa: qualquer `connection.execute(...)` ANTES de `connection.run_sync(do_run_migrations)` (ex: `CREATE SCHEMA IF NOT EXISTS runtime` no env.py para a version table) **abre uma transação implícita** no SQLAlchemy. O Alembic vê transação externa ativa e NÃO commita no fim; ao sair do `async with connectable.connect()`, o close faz ROLLBACK de tudo.

Fix (no env.py, `run_async_migrations`):
```python
async with connectable.connect() as connection:
    await connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {VERSION_TABLE_SCHEMA}"))
    await connection.commit()  # ← OBRIGATÓRIO: encerra a transação implícita
    await connection.run_sync(do_run_migrations)
```

Diagnóstico rápido: replicar o env.py num script e verificar se o schema persiste após o close (sem commit → some; com commit → fica).

## Pitfall 2 — version_table_schema em schema criado pela migration base

Sintoma em banco limpo: `asyncpg.exceptions.InvalidSchemaNameError: schema "runtime" does not exist` — o Alembic cria a version table (version_table_schema="runtime") ANTES de rodar a migration base (que é quem cria o schema).

Fix: pré-criar o schema no env.py antes de `run_migrations` (com o commit do Pitfall 1). A migration base usa `CREATE SCHEMA IF NOT EXISTS` → idempotente em instalações existentes.

## Verificação REAL (nunca confiar no exit code)

O exit 0 do alembic NÃO prova que migrou. Prova de verdade:
```bash
# 1. banco 100% limpo
psql -c "DROP SCHEMA IF EXISTS runtime CASCADE; DROP SCHEMA IF EXISTS companies CASCADE; ..."
# 2. upgrade
alembic upgrade head
# 3. conferir PERSISTÊNCIA (não só o exit)
psql -tc "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN (...)"
psql -tc "SELECT version_num FROM <schema>.alembic_version"   # deve ser o head
# 4. suíte canônica
pytest -q
```
Grep com filtro (`alembic upgrade head 2>&1 | grep "Running upgrade"`) esconde o `FAILED:` final — rodar SEM filtro quando suspeitar.

## Pitfall 3 — DROP sem CASCADE em testes de integração

Testes que dropam tabelas no setup falham com `DependentObjectsStillExistError` quando outra tabela (ex: `documentos.folders` com FK para `processos.process_records`) depende delas — sintoma intermitente conforme o estado do banco (schema órfão de cadeia antiga de migrations). Fix: DROP ... CASCADE ou drop topológico (dependentes primeiro). Workaround imediato: `DROP SCHEMA IF EXISTS <schema_orfao> CASCADE`.

## Outros

- Migrations refeitas (squash) deixam bancos locais com revisões órfãs (`Can't locate revision identified by '<hash>'`) — banco local de dev sem dados: drop dos schemas + upgrade head do zero
- `env -u PYTHONPATH` ao rodar alembic/pytest de projeto (o shell herda o site-packages do venv do hermes-agent e contamina)
