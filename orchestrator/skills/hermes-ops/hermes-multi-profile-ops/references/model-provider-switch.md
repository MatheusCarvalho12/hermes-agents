# Troca de provider/modelo LLM em massa nos perfis (validado 2026-08: nous → deepseek direto)

Sessão real: os 4 perfis do time (backend-developer, database-developer, designer, frontend-developer) usavam DeepSeek via Nous Portal (`model.provider: nous`, `model.default: deepseek/deepseek-v4-flash-0731`) e foram trocados para a API DeepSeek direta — igual ao default (`model.provider: deepseek`, `model.default: deepseek-v4-flash`). Fluxo completo validado com teste real.

## Passos

1. Ler estado atual por perfil:
   ```bash
   hermes -p <perfil> config get model.provider
   hermes -p <perfil> config get model.default
   ```

2. Aplicar a troca por perfil:
   ```bash
   hermes -p <perfil> config set model.provider deepseek
   hermes -p <perfil> config set model.default deepseek-v4-flash
   ```
   (`hermes config set` respeita a flag `-p` e escreve no config.yaml do perfil — saída confirma o caminho.)

3. Chave de API é POR PERFIL: cada `~/.hermes/profiles/<p>/.env` precisa da chave do provider novo; NÃO herda do default. Copiar sem expor o segredo no output, checando antes para não duplicar:
   ```bash
   grep -q '^DEEPSEEK_API_KEY=' ~/.hermes/profiles/<p>/.env || \
     grep -E '^DEEPSEEK_API_KEY=' ~/.hermes/.env >> ~/.hermes/profiles/<p>/.env
   ```

4. Verificar configs de todos os perfis + smoke test REAL de um deles:
   ```bash
   hermes -p <perfil> chat -q "Responda apenas: OK"
   ```
   Resposta viva no stdout = chave + provider autenticados. Cuidado: o rodapé do output mostra só o resumo da sessão (Session/Duration/Messages) — a resposta vem antes, no quadro do Hermes; filtrar com `grep -vE '^(Session|Duration|Messages|hermes --resume|$)'` ou `head` para achá-la.

## Pitfalls

- ⚠️ **`HERMES_PROFILE=<nome>` env var NÃO seleciona o perfil para `hermes config get`** — no teste real, `HERMES_PROFILE=backend-developer hermes config get model.provider` retornou `deepseek` (valor do DEFAULT), enquanto `hermes -p backend-developer ...` retornou `nous` (valor correto do perfil). Usar SEMPRE a flag `-p <nome>` para qualquer comando por perfil (config, skills, mcp, chat).
- **Nome do modelo é específico do provider**: nous aceitava `deepseek/deepseek-v4-flash-0731` (formato `provider/modelo`, sufixo de data da versão); o provider deepseek direto espera `deepseek-v4-flash` puro. Ao trocar provider, NORMALIZAR a string do modelo — copiar a do default que já funciona no provider de destino.
- `reasoning_effort: max` e demais chaves de `model:` não são tocadas pelo provider set — conferir com `config get` depois (os 4 perfis já tinham `reasoning_effort: max` e seguiram com ele).
- Loop `for` inline com `$(...)` cai no bloqueio de parser do terminal do Hermes (hardline) — escrever script `.sh` e `bash script.sh`, ou chamadas separadas.
- A troca vale para sessões NOVAS dos perfis (config é lida no start).
