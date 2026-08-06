# Caso real: rollback silencioso do alembic (flowmex-core, 2026-08-06)

## Contexto
Bug original: `alembic upgrade head` falhava em banco limpo (`InvalidSchemaNameError: schema "runtime" does not exist` — Pitfall 1). Task de fix delegada ao backend-developer. O worker editou `migrations/env.py`:

```python
async with connectable.connect() as connection:
    await connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {VERSION_TABLE_SCHEMA}"))
    await connection.run_sync(do_run_migrations)
```

O worker crashou no protocolo (2x protocol_violation, rc=0 sem kanban_complete). Recovery do orquestrador: validar a entrega real com o critério de pronto da task.

## Sintomas observados (em ordem)
1. `alembic upgrade head` (com o fix do worker): "Running upgrade -> ..." x5, exit 0
2. `docker exec psql ... \dn` → banco com SÓ `public` — nada persistiu
3. `alembic current` → imprime só as 2 INFO de setup, SEM revisão (nenhuma linha de resultado)
4. Re-rodar `upgrade head` → "Running upgrade -> eeafe5b25dd2" DE NOVO (como se o banco nunca tivesse migrado — version table inexistente)
5. `pytest` → 17 errors de integração: `schema "runtime" does not exist`

## Árvore de diagnóstico (o que foi descartado)
- Banco errado? `lsof -i :5432` → só o Docker escuta; DSN do Settings idêntico ao do asyncpg que via o banco vazio → descartado
- `.env` com URL alternativa? Sem `.env` no repo; `env | grep FLOWMEX` → vazio → descartado
- FAILED mascarado por grep? O primeiro comando usava `| grep -E "Running upgrade|ERROR" | head -8` (Pitfall 4) — mas re-rodar SEM filtro também deu exit 0 → não era só isso
- **Causa raiz**: `connection.execute()` abre transação implícita no SQLAlchemy 2.0; o Alembic não commita dentro de transação externa; `async with connectable.connect()` faz rollback no close → TUDO revertido

## Prova empírica (script que replica o env.py)
```python
async with eng.connect() as conn:
    await conn.execute(text("CREATE SCHEMA IF NOT EXISTS runtime"))
    await conn.run_sync(lambda c: None)  # no-op no lugar do alembic
await eng.dispose()
# verificar persistência em conexão NOVA:
# SEM commit  -> schema não existe ([])   → confirma rollback silencioso
# COM commit  -> schema existe (True)     → confirma o fix
```

## Fix aplicado (1 linha + comentário)
```python
await connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {VERSION_TABLE_SCHEMA}"))
await connection.commit()  # sem isso: migrations rodam na transação implícita e o close reverte tudo
await connection.run_sync(do_run_migrations)
```

## Verificação final (critério de pronto da task)
1. `DROP SCHEMA ... CASCADE` (runtime, companies, processos, documentos) — banco 100% limpo
2. `alembic upgrade head` → exit 0
3. Persistência real: 3 schemas + `version_num = 391094211683` (head)
4. `pytest -q` → 122 passed, 6 skipped

## Lições
- A validação de entrega de worker NÃO pode ser só "rodou + pytest": pytest passa mesmo com o banco quebrado se os testes de integração não rodam (erram no setup). O critério de pronto da task (drop + upgrade + persistência + suíte) pegou o bug silencioso.
- Fix de migrations validado só depois de drop completo + verificação de persistência em conexão nova.
