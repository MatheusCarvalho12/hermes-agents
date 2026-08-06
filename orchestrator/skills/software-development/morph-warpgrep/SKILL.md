---
name: morph-warpgrep
description: "Use quando o usuário pedir morph/warpgrep pra buscar código."
---

# Morph SDK — WarpGrep (busca de código por agente)

O usuário (flowmex) usa o Morph WarpGrep como ferramenta de varredura de código ("usa o morph com warpgrep pra ver cada centímetro"). SDK Node/ESM — não é CLI.

## Setup
```bash
npm install @morphllm/morphsdk   # ESM, sem binário global — SDK programático
```
- API key: `morphllm.com/dashboard/api-keys`, formato **`sk-...`** obrigatório. Chaves `sub_...` (ex: key do NopeCHA) → `401 invalid_api_key`. Para instalar num dir temporário e rodar: `npm init -y && npm install @morphllm/morphsdk` em `/tmp/...`.

## Uso
```javascript
import { WarpGrepClient } from '@morphllm/morphsdk/tools/warp-grep';
const client = new WarpGrepClient({ morphApiKey: process.env.MORPH_API_KEY });
const result = await client.execute({ query: '...', repoRoot: '/abs/path' });
```

## Pitfalls reais (validados 2026-08-06)
1. **A resposta usa `contexts`, NÃO `files`** — o README mostra `result.files`, mas a API real retorna `{success, contexts: [{file, content}]}`. Iterar `result.contexts` — `result.files` vem vazio e parece "no files returned".
2. **Key precisa ser `sk-...`** — qualquer outro prefixo dá 401 `invalid_api_key`; não confundir com key do NopeCHA (`sub_...`).
3. **É um subagente LLM — resultados podem ser RASOS/genéricos**: 3 queries distintas retornaram o mesmo conjunto de arquivos (só composition root + api/), sem achar adapter/domain/tests. Não usar como fonte única: para varrer "cada centímetro", complementar com `search_files`/`read_file` local (determinístico). WarpGrep serve pra confirmar composition root/uso transversal; a leitura profunda é local.
4. Custa API (créditos do Morph) por query — não disparar em loop.

## Quando preferir local
Varredura completa e confiável = `search_files` (ripgrep) + `read_file`. WarpGrep = segundo olhar de agente sobre "onde X é usado", não a base da auditoria.
