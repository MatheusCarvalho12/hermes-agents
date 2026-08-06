#!/bin/bash
# Espera tasks do kanban terminarem (done/blocked/gave_up/crashed) e notifica o orquestrador.
# Uso: ./watch-kanban-tasks.sh t_abc123 t_def456 [t_ghi789 ...]
# Rode com terminal(background=true, notify_on_complete=true) e SIGA TRABALHANDO
# — a notificacao chega na hora exata em que a ultima task fechar (0 polling no turno).
# NUNCA use loops de sleep no turno do orquestrador: usuario corrigiu esse padrao.
# Estados terminais: done | blocked | gave_up | crashed (timed_out aparece como crashed/gave_up).
# Se a task sair do board (archived), o list nao a mostra -> tambem conta como terminal.

TASKS="$@"
if [ -z "$TASKS" ]; then
  echo "uso: $0 <task-id> [task-id...]"
  exit 1
fi

while true; do
  pending=0
  for t in $TASKS; do
    line=$(hermes kanban list 2>&1 | grep "$t")
    if [ -z "$line" ]; then
      # task sumiu do board (archived/deleted) -> terminal
      continue
    fi
    state=$(echo "$line" | grep -oE '\b(done|blocked|gave_up|crashed)\b' | head -1)
    [ -z "$state" ] && pending=$((pending + 1))
  done
  if [ "$pending" -eq 0 ]; then
    echo "TODAS AS TASKS TERMINARAM:"
    hermes kanban list
    break
  fi
  sleep 15
done
