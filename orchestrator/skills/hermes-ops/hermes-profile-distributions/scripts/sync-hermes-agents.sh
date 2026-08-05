#!/bin/bash
# Wrapper do sync-hermes-agents.py — usa o python do venv do Hermes (tem yaml).
# Silencioso se não houver mudanças (watchdog pattern); faz commit+push+tag quando há.
# Cron: cronjob action=create no_agent=true script=sync-hermes-agents.sh schedule="every 2h"
exec /Users/amaterei/.hermes/hermes-agent/venv/bin/python /Users/amaterei/.hermes/scripts/sync-hermes-agents.py "$@"
