# Morph WarpGrep — detalhes validados (2026-08-06)

## Setup (validado)
```bash
mkdir -p /tmp/morph-wg && cd /tmp/morph-wg
npm init -y >/dev/null 2>&1
npm install @morphllm/morphsdk        # ~segundos com cache; é ESM ("type": "module")
```
- NÃO existe binário global (`morph` command not found; package.json sem campo `bin`).
- Export válido: `@morphllm/morphsdk/tools/warp-grep` (também `/openai`, `/anthropic`, `/gemini`, `/vercel`, `/client`, `/harness`).
- API key: `morphllm.com/dashboard/api-keys`, formato `sk-...`.

## Script de exemplo (funcionou)
```javascript
// /tmp/morph-wg/wg.mjs
import { WarpGrepClient } from '@morphllm/morphsdk/tools/warp-grep';
const client = new WarpGrepClient({ morphApiKey: process.env.MORPH_API_KEY });
const result = await client.execute({
  query: 'Where is SiscargaHttpGateway defined and used',
  repoRoot: '/Users/amaterei/dev/flowmex/flowmex-platform/services/core',
});
console.log(JSON.stringify(result, null, 2));
```
```bash
MORPH_API_KEY='sk-...' node wg.mjs
```

## Shape da resposta (importante)
- Sucesso: `{ "success": true, "contexts": [ { "file": "/abs/path", "content": "..." } ] }`
- **O README do pacote mostra `result.files`** — desatualizado. Ler `result.files` dá `undefined` → "no files returned" SEM erro.
- Queries amplas retornaram apenas composition roots (ex: `main.py`, `api/app.py`, `api/companies.py`) — para varredura exaustiva, combinar com leitura direta dos módulos.

## Erro 401 (key errada ou formato errado)
```
[ERROR] [WarpGrep] model_call_error {"status":401,"error":"401 API key required...","latency_ms":257}
```
- Key `sub_...` (formato de subscription/NopeCHA) NÃO serve: `{"error":{"code":"invalid_api_key"}}`.
- Confirmação rápida: `curl -s https://api.morphllm.com/v1/models -H "Authorization: Bearer <key>"` → 200 vs 401.

## Lição de processo
O usuário pode rotular keys errado entre serviços (deu a NopeCHA `sub_...` como "morph", e a morph `sk-...` como "nopecha" no primeiro envio). Sempre validar a key contra o endpoint do serviço ANTES de assumir que funciona — e devolver a validação (ex: "NopeCHA /status: Active, credit X").
