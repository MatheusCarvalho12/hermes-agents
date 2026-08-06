# Verificação de fluxo assíncrono (outbox → PgQueuer) — validado 2026-08-06

Padrão do orquestrador para VERIFICAR de ponta a ponta um endpoint de import assíncrono
(202 Accepted + operation durável + worker em background), sem deploy e sem derrubar
outras sessões. Contexto real: módulo de documentos do flowmex-core (`runtime/queue.py`).

## Regras de ouro
- **Uvicorn NÃO processa fila** — o app só aceita a operation (202). Sem worker dedicado,
  o import fica `accepted` para sempre. Isso NÃO é bug do app.
- **NUNCA chame `run(drain)` em loop**: `PgQueuer.run()` seta `self.shutdown` no `finally`
  (pgqueuer 0.26) → a 1ª chamada processa os jobs existentes, as seguintes são NO-OP
  silencioso. Sintoma: worker vivo (loop de ticks rodando), jobs novos ficam `queued`
  para sempre, drain retorna em 0.1s vazio, e o dequeue DIRETO acha o job.
- Worker correto: `run(mode=continuous)` UMA vez (loop infinito do pgqueuer) + relay do
  outbox (`relay_once()` a cada ~1s) em task separada via `asyncio.gather`.

## Setup de banco isolado (zero risco para outras sessões)
```bash
docker exec flowmex-pg createdb -U flowmex flowmex_docs
export FLOWMEX_DATABASE_URL='postgresql+asyncpg://flowmex:flowmex@localhost:5432/flowmex_docs'
# CONFERIR antes: printenv FLOWMEX_DATABASE_URL — shell pode ter env var poluída
# de outra sessão (env var > .env) → app e scripts veem bancos diferentes.
```
Schemas antes do alembic (senão `schema "runtime" does not exist`):
`CREATE SCHEMA IF NOT EXISTS runtime/companies/processos/documentos`, depois
`alembic upgrade head`. Tabelas do PgQueuer (tabela `public.pgqueuer`):
```bash
env -u PYTHONPATH .venv/bin/pgq --pg-dsn 'postgresql://flowmex:flowmex@localhost:5432/flowmex_docs' install
# NÃO existe --dsn (uso: --pg-dsn / env PGDSN); user do sistema se faltar URL
```

## Mini-worker validado (script de verificação)
```python
import asyncio
from pgqueuer.domain.types import QueueExecutionMode
from flowmex_core.database import session_factory
from flowmex_core.main import company_handlers, document_handlers
from flowmex_core.runtime.queue import OutboxRelay, QueueWorker, WorkerMode

async def relay_loop(relay: OutboxRelay) -> None:
    while True:
        await relay.relay_once()
        await asyncio.sleep(1)

async def main() -> None:
    w = QueueWorker({**company_handlers, **document_handlers},
                    mode=WorkerMode.PRODUCTION, session_factory=session_factory)
    await w.start()
    relay = OutboxRelay(session_factory, w.publisher)  # publisher é PROPRIEDADE, não chamável
    await asyncio.gather(relay_loop(relay), w.run(mode=QueueExecutionMode.continuous))

asyncio.run(main())
```
Rodar com `env -u PYTHONPATH .venv/bin/python` (PYTHONPATH do hermes contamina pydantic_core).

## Medição e critério
- Smoke: POST import (202) → poll `GET .../imports/{id}` até `completed`. Import de
  poucos arquivos pequenos completa em ~1s com worker contínuo.
- Atraso de MINUTOS ou `accepted` eterno = worker preso (drain em loop) ou sem worker.
- Poll com janela curta (20s) pode terminar antes do worker processar → re-checar via
  curl/banco antes de declarar falha.

## Diagnóstico rápido (tabelas: runtime.outbox, runtime.operations, public.pgqueuer)
| Sintoma | Causa |
|---|---|
| outbox `pending` > 0 | relay não roda (sem worker ou loop errado) |
| outbox `published` + job `queued` + worker vivo | drain em loop (shutdown setado) — trocar para continuous |
| operation existe sem outbox | `accept_import` não commitou (atômico: operation+outbox juntos) — olhar o adapter |
| app 404 em linha que existe no banco | env var aponta para outro banco (`printenv FLOWMEX_DATABASE_URL`) |
| job `queued` com `execute_after` no passado e dequeue manual acha | worker loop morto; drain manual direto (`qm.queries.dequeue`) isola worker vs query |

## Achado para produção (virou task)
O composition root expõe os handlers mas NÃO tem o runner de worker contínuo — sem ele,
o import async fica parado em produção. Criar task de backend: entry point do worker
(continuous + relay) + instrução de subida no README.
