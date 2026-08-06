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

**Fix de verdade**: pré-criar o schema no `env.py` ANTES de `run_migrations`, com commit explícito:

```python
async with connectable.connect() as connection:
    await connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {VERSION_TABLE_SCHEMA}"))
    await connection.commit()  # OBRIGATÓRIO — ver Pitfall 3
    await connection.run_sync(do_run_migrations)
```

Sem o `commit()`, o fix fica PIOR que o bug original (ver Pitfall 3). Registrar como bug/task e validar com o critério de pronto da seção "Regras gerais" (drop + upgrade + persistência real).

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

## Pitfall 3 — ROLLBACK SILENCIOSO: migrations "rodam" (exit 0) mas nada persiste

**Sintoma**: `alembic upgrade head` imprime `Running upgrade -> ...` para TODAS as migrations, exit 0, mas o banco fica vazio — nem schemas, nem version table. `alembic current` imprime só as INFO de setup, sem revisão nenhuma.

**Causa**: `connection.execute()` no SQLAlchemy 2.0 **abre transação implícita**. Se o env.py executa algo (ex: o `CREATE SCHEMA IF NOT EXISTS` do fix do Pitfall 1) antes de `connection.run_sync(do_run_migrations)`, o Alembic vê uma transação externa e **não commita**; ao sair do `async with connectable.connect()`, o close faz ROLLBACK de tudo. As migrations executam dentro da transação (por isso "Running upgrade" + exit 0) e somem no fim.

**Prova empírica** (não teorizar — replicar o env.py num script):
```python
async with eng.connect() as conn:
    await conn.execute(text("CREATE SCHEMA IF NOT EXISTS runtime"))
    # SEM commit: schema não persiste ([])  → rollback silencioso
    # COM  commit: schema persiste (True)
```

**Detecção rápida**: depois do upgrade, conferir persistência REAL — `SELECT schema_name FROM information_schema.schemata ...` e `SELECT version_num FROM <schema>.alembic_version`. "Running upgrade + exit 0" NUNCA é prova. Alembic dizendo sucesso + banco vazio = rollback silencioso (ou pipeline mascarando erro, Pitfall 4).

## Pitfall 4 — pipeline `| grep | head` mascara FAILED e o exit code

`alembic upgrade head 2>&1 | grep -E "Running upgrade|ERROR" | head -8`:
- grep não captura a linha `FAILED: ...` (não contém "ERROR") → parece sucesso
- o exit code do pipeline é o do `head`/`grep` (0), nunca o do alembic

Ao validar migrations, rodar SEM filtro e olhar o tail completo. Um "upgrade bem-sucedido" com banco vazio pode ser um FAILED filtrado pelo grep.

## Pitfall 5 — teste de integração falha no SETUP com `schema "X" does not exist`

**Sintoma**: `pytest` de store/application falha no setup com `asyncpg.exceptions.InvalidSchemaNameError: schema "documentos" does not exist`, enquanto o resto da suíte passa (18 passed / 9 errors, validado 2026-08-06 na branch feat/documentos).

**Causa**: fixtures que criam tabelas via `Base.metadata.create_all` NÃO criam o schema — o schema nasce da migration Alembic. Em banco que nunca rodou `alembic upgrade head` daquela branch, o `create_all` falha. Não é defeito do fixture em si — é estado do banco (funciona quando o schema já existe de uma migration anterior).

**Resolução** (ordem): rodar `env -u PYTHONPATH .venv/bin/alembic upgrade head` e re-testar (18 pass/9 err → 27/27). Para testes novos, o fixture deve ser independente da migration: `CREATE SCHEMA IF NOT EXISTS <schema>` antes do `create_all` — assim a suíte roda em banco dropado.

## Pitfall 6 — banco novo sem tabelas do PgQueuer: `pgq install` falha em silêncio

**Sintoma**: worker do runtime morre no startup com `RuntimeError: The required table 'pgqueuer' is missing. Please run 'pgq install'` — mesmo depois de `alembic upgrade head` OK. O alembic cria os schemas de negócio (runtime/companies/...) mas NÃO as tabelas do PgQueuer (`public.pgqueuer`, `pgqueuer_log`, `pgqueuer_statistics`, `pgqueuer_schedules` + TYPE `pgqueuer_status`).

**Causa**: o CLI `pgq install` (e `python -m pgqueuer.cli install --pg-dsn ...`) pode sair exit 0 **sem criar nada** (falha silenciosa — validado 2026-08-06, pgqueuer no venv do worktree). O `.venv/bin/pgq` pode também estar com binário quebrado ("No such file or directory" mesmo existindo) — preferir `python -m pgqueuer.cli`.

**Resolução rápida** (quando um banco irmão do mesmo repo já tem as tabelas — ex: outro worktree com worker rodando):
```bash
CID=$(docker ps -q -f publish=5432 | head -1)
docker exec $CID sh -c "pg_dump -U flowmex -d <banco_irmao> -n public --schema-only" \
  | grep -v '^\\restrict' \
  | docker exec -i $CID psql -U flowmex -d <banco_novo>
```
- `-n public` pega só o schema public (no flowmex só há as tabelas pgqueuer lá); erros de "schema already exists"/"sequence already exists" são benignos.
- **`grep -v '^\restrict'` é OBRIGATÓRIO**: pg_dump 17+ emite `\restrict <token>` no início do dump; sem remover, o psql falha com "relation does not exist" nas dependências.
- `pg_dump -t 'public.pgqueuer*' --schema-only` NÃO basta — o TYPE `pgqueuer_status` fica de fora e o restore quebra.

**Verificação**: `SELECT tablename FROM pg_tables WHERE schemaname='public'` deve listar as 4 tabelas; o worker sobe com seu log de início.

## Regras gerais
- **NUNCA dropar schema/tabela antes de conferir contagens** — banco local de dev vazio é resetável; banco com dados não.
- `alembic stamp` para "mentir" o estado só quando o schema atual bate com a revisão alvo — caso contrário, drop + upgrade limpo.
- Rodar migrations de projeto Python no Mac do usuário: `env -u PYTHONPATH .venv/bin/alembic ...` (PYTHONPATH do venv hermes-agent contamina).
- Após `upgrade head` em banco limpo, a prova é a suíte: `pytest` sem ERRORs de setup.
- Verificação automática pronta: `scripts/verify_clean_upgrade.sh` (drop schemas → upgrade head → checa persistência real → pytest). Rodar sempre que o critério de pronto envolver migrations; também serve de critério de aceite em tasks.

## References
- `references/rollback-silencioso-alembic.md` — caso real completo (sintomas, árvore de diagnóstico, prova empírica, fix).
