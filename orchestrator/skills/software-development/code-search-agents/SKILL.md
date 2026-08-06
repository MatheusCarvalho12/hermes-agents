---
name: code-search-agents
description: "Use when user asks for morph/warpgrep or deep code search."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [code-search, warpgrep, morph, sdk, ripgrep]
    related_skills: [codebase-inspection]
---

# Code Search Agents

Buscar código com subagentes de busca (Morph WarpGrep) e alternativas locais. O usuário do flowmex pede "morph com warpgrep" para varrer o código; a ferramenta é um SDK Node (não CLI global) e a API tem armadilhas validadas.

## Quando usar
- Usuário pede "usa o morph com warpgrep" / "varre cada centímetro do código"
- Precisa de busca semântica (perguntas em linguagem natural sobre o codebase)
- Varredura exaustiva de um repo antes de mexer no código

## Fluxo validado (2026-08-06)
1. `npm install @morphllm/morphsdk` em diretório próprio (ex: `/tmp/morph-wg`) — NÃO tem binário global; é library ESM.
2. Script `.mjs`:
   ```javascript
   import { WarpGrepClient } from '@morphllm/morphsdk/tools/warp-grep';
   const client = new WarpGrepClient({ morphApiKey: process.env.MORPH_API_KEY });
   const result = await client.execute({ query: '...', repoRoot: '/abs/path' });
   // result.contexts: [{ file, content }]  — NUNCA result.files
   ```
3. Rodar: `MORPH_API_KEY='sk-...' node script.mjs`.

## Pitfalls validados
- **Resposta vem em `result.contexts`** (array de `{file, content}`), NÃO `result.files` como o README do pacote mostra — ler `result.files` retorna "(no files returned)" silenciosamente. Printar `result.success` e `result.contexts` sempre.
- **API key é formato `sk-...`** (morphllm.com/dashboard/api-keys). Outros formatos (ex: `sub_...`) → `401 invalid_api_key`. Confirmar com curl: `curl -s https://api.morphllm.com/v1/models -H "Authorization: Bearer <key>"`.
- **Keys podem vir rotuladas errado**: nesta sessão o usuário entregou a key do NopeCHA achando que era do Morph. Antes de assumir, validar contra o serviço certo (Morph: 401/200 em /v1/models; NopeCHA: `GET https://api.nopecha.com/status`).
- **Resultados podem ser rasos**: WarpGrep retornou só composition roots (main.py, api/) nas queries amplas. Para "cada centímetro", combinar com leitura direta (read_file/search_files) — o subagente complementa, não substitui.
- Sem SDK instalado ou sem key válida: usar `search_files`/`rg` locais (mesma capacidade para grep determinístico) e avisar o usuário do que faltou.

## Suporte
- `references/morph-warpgrep.md` — setup completo, script de exemplo, saída real de erro 401 e do shape `contexts`.
