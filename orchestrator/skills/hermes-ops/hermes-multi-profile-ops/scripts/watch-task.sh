#!/bin/bash
# watch-task.sh — monitor async de tasks do kanban (SEM polling do orquestrador).
#
# Uso: watch-task.sh <task_id> [task_id ...]
# Espera cada task sair de running/ready/todo (ou seja, ficar done OU blocked) e sai.
# O orquestrador deve rodar via terminal(background=true, notify_on_complete=true):
#   -> quando o script sai, o Hermes notifica NA HORA EXATA — zero turnos de sleep-polling.
#
# Pitfall tratado: task ARQUIVADA some do `kanban list` e o estado fica vazio — sem
# contador de ausências o monitor esperaria PARA SEMPRE (aconteceu de verdade: arquivar
# uma task obsoleta travou o monitor antigo). Task ausente por 3 checagens consecutivas
# é tratada como terminal ("ausente/arquivada").
#
# Saída: lista final do kanban + estado de cada task monitorada.
# Exit code: 0 se todas terminaram done/ausente; 1 se alguma terminou blocked (para chamar atenção).

TASKS=("$@")
if [ ${#TASKS[@]} -eq 0 ]; then
  echo "uso: watch-task.sh <task_id> [task_id ...]" >&2
  exit 2
fi

declare -A MISSING
for t in "${TASKS[@]}"; do MISSING["$t"]=0; done

while true; do
  all_terminal=1
  for t in "${TASKS[@]}"; do
    line=$(hermes kanban list 2>&1 | grep "$t")
    state=$(echo "$line" | grep -oE '\b(done|blocked)\b' | head -1)
    if [ -n "$state" ]; then
      MISSING["$t"]=0
    else
      MISSING["$t"]=$((MISSING["$t"] + 1))
      if [ "${MISSING[$t]}" -lt 3 ]; then
        all_terminal=0
      fi
    fi
  done
  if [ "$all_terminal" = "1" ]; then
    break
  fi
  sleep 15
done

echo "=== KANBAN FINAL ==="
hermes kanban list
echo "=== ESTADOS ==="
any_blocked=0
for t in "${TASKS[@]}"; do
  line=$(hermes kanban list 2>&1 | grep "$t")
  state=$(echo "$line" | grep -oE '\b(done|blocked)\b' | head -1)
  if [ -z "$state" ]; then state="ausente (provavelmente arquivada)"; fi
  echo "$t -> $state"
  if [ "$state" = "blocked" ]; then any_blocked=1; fi
done
exit $any_blocked
