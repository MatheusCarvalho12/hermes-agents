# NopeCHA × hCaptcha (lições de 2026-08-06 contra o Siscarga real)

## Dois caminhos de API (token)

| | Endpoint | Payload extra | Custo |
|---|---|---|---|
| Adapter flowmex | `POST /v1/token/hcaptcha` | key, sitekey, url, useragent, cookie?, proxy?, data?{rqdata} | 10 créditos |
| Biblioteca `nopecha` 2.0.1 | `POST /token/` | key, **type: "hcaptcha"**, sitekey, url, **enterprise: false**, proxy, data?{rqdata} | 10 créditos |

- O comentário no adapter dizia que a lib responde "Invalid request" no `/token/` — **errado**: a lib funciona (testada; o erro do adapter foi provavelmente payload sem `type`/`enterprise`).
- **BUG da lib (async)**: `AsyncHTTPXAPIClient.solve_hcaptcha` monta GET com URL relativa (`/token/?key=...`) → httpx: "Request URL is missing an 'http://' or 'https://' protocol". **Usar `HTTPXAPIClient` (sync)** ou montar o payload manual.
- Auth: header `Authorization: Bearer <key>` (lib) ou `Basic <key>` (doc) ou `key` no body — os três aceitos.
- Recognition (desafio de imagem): formato NOVO 2026 em `references/nopecha-recognition-2026.md` (na skill captcha-solver-integrations) — a lib está desatualizada.

## Taxa de sucesso real contra o Siscarga (sitekey 15095c53-...)

- 2026-08-06: tokens gerados e **rejeitados silenciosamente** pelo portal (form re-renderizado, 0 registros); vários jobs nunca completaram
- Widget do Siscarga é **classic** (sem `data-rqdata` no HTML), mas **o tipo de desafio varia por sessão**: checkbox direto (classic), desafio de imagem `image_label_binary` (9 tiles), `image_label_area_select`, ou enterprise por config server-side — SEMPRE verificar o tipo antes de escolher o caminho
- **Rejeição é SILENCIOSA**: POST 200, form re-renderizado com campos, 0 registros — verificar isso antes de culpar o parser

## Padrão de retry que funciona

- Jobs NopeCHA variam muito (segundos a 30+ min, ou nunca): loop de 3-4 tentativas com novo job a cada falha, polling de até 600s (NOPECHA_MAX_POLLS=600 — 150 polls de 2.5 min matavam solves que completariam em 5-10 min)
- `GET /v1/timelines?n=...` mostra eventos do job (posted/worked/solved/collected) — útil para diagnosticar jobs presos
- Sem proxy residencial: solve lento/impossível; com proxy BR: solve em segundos nos dias bons

## Fallback 100% confiável (quando o solver falha)

Browser headed + clique manual do usuário no checkbox "Sou humano" → sessão autenticada dura minutos → extrair TUDO de uma vez (listagem + detalhes de todos os CEs). Custo: 1 clique por rodada.
Automatização total (VPS): Chrome for Testing + NSS + CDP + Recognition — ver `references/siscarga-cdp-captcha.md` (skill rfb-portal-integration).

## Alternativas avaliadas

- **CapSolver: NÃO resolve hCaptcha enterprise** (afirmação do usuário 2026-08-06 — confiar; não gastar tempo testando CapSolver se o portal for enterprise por config)
- 2captcha: workers humanos, resolve classic; enterprise exige rqdata (que o portal não expõe no HTML)
- Extensão NopeCHA (automation): resolve o checkbox rápido, mas o token é do backend — rejeitado igual à API
- A página do portal não expõe `data-rqdata`; NopeCHA sem rqdata resolve como classic
