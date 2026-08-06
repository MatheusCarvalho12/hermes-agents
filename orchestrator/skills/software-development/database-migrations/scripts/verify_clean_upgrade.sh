#!/bin/bash
# Prova de migrations em banco LIMPO (validado 2026-08-06, flowmex-core):
# drop schemas -> alembic upgrade head -> checar persistencia REAL -> pytest.
# "Running upgrade + exit 0" nunca prova nada; so a persistencia conta.
#
# Uso (env vars para adaptar ao projeto):
#   CORE_DIR="services/core" \
#   PG_PSQL="docker exec flowmex-pg psql -U flowmex -d flowmex -tAc" \
#   SCHEMAS="runtime companies processos" \
#   bash verify_clean_upgrade.sh
set -u
CORE_DIR="${CORE_DIR:-services/core}"
PG_PSQL="${PG_PSQL:-docker exec flowmex-pg psql -U flowmex -d flowmex -tAc}"
SCHEMAS="${SCHEMAS:-runtime companies processos}"

echo "== 1. drop schemas (banco de dev vazio = seguro; conferir contagens antes se houver duvida) =="
for s in $SCHEMAS; do
  $PG_PSQL "DROP SCHEMA IF EXISTS $s CASCADE" >/dev/null 2>&1 || true
done

echo "== 2. alembic upgrade head (SEM filtro — grep mascara FAILED) =="
(cd "$CORE_DIR" && env -u PYTHONPATH .venv/bin/alembic upgrade head) || { echo "FALHA: upgrade head"; exit 1; }

echo "== 3. persistencia REAL =="
IN=""
for s in $SCHEMAS; do IN="$IN'$s',"; done
IN="${IN%,}"
COUNT=$($PG_PSQL "SELECT count(*) FROM information_schema.schemata WHERE schema_name IN ($IN)")
echo "schemas esperados: $SCHEMAS | presentes: $COUNT"
VERSION=$($PG_PSQL "SELECT version_num FROM ${VERSION_SCHEMA:-runtime}.alembic_version" 2>/dev/null)
echo "version: $VERSION"
[ "$COUNT" = "$(echo "$SCHEMAS" | wc -w | tr -d ' ')" ] || { echo "FALHA: schemas nao persistiram (rollback silencioso?)"; exit 1; }
[ -n "$VERSION" ] || { echo "FALHA: version table vazia"; exit 1; }

echo "== 4. suite (testes de integracao precisam do banco) =="
(cd "$CORE_DIR" && env -u PYTHONPATH .venv/bin/python -m pytest -q 2>&1 | tail -1)
