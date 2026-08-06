# Proxy residencial BR + MCP do GeoNode (pesquisa 2026-08-06)

## Por que proxy residencial para hCaptcha

O hCaptcha (empresa independente) classifica o IP de quem resolve o desafio: **residencial = humano** (challenge fácil, segundos) vs **datacenter = bot** (challenge difícil, minutos). Proxy de datacenter (Fly.io/GRU, Cloudflare Workers, AWS) NÃO ajuda — mesma classe de IP suspeito. No NopeCHA, o proxy vai no payload do job (`proxy: {scheme, host, port, username?, password?}`) e o worker DELES visita o hCaptcha por ele.

## GeoNode — como funciona

- **O país NÃO se escolhe no dropdown "Gateway"** (isso é só o ponto de entrada). O geo-targeting vai no **username**:
  - País: `<user>-country-br` → ex: `geonode_XXXX-type-residential-country-br`
  - Cidade: `<user>-country-br-city-sao-paulo`
  - Formato completo do user: `user-type-residential-country-<code>`
- Endpoint: `http://<username>:<password>@proxy.geonode.io:9000` (HTTP, auth básica)
- Sem sufixo no username: cai em pool rotativo global (ex: Filipinas) — sempre conferir o IP de saída
- Prova: `curl -x "http://user:pass@proxy.geonode.io:9000" http://ip-api.com/json` → `countryCode: BR`, ISP local (ex: LANG & WALDOW LTDA, PR)
- Trial: 48h ilimitado, sem cartão; dropdown de gateways do trial limitado a France/US/Singapore — mas o targeting BR via username funciona no trial
- Preços (página oficial): residencial from $0.27/GB (PAYG; $0.79/GB no tier inicial); Brasil: 84.210 IPs, 12 cidades (SP 22k, Salvador 16.5k, Brasília 16.5k), latência 0.2s
- Doc de geo-targeting: docs.geonode.com (username params `-country-`, `-state-`, `-city-`, `-as-`)

## Comparativo de provedores (2026)

| Provedor | Preço/GB | Geo BR | Modelo | Obs |
|---|---|---|---|---|
| GeoNode | $0.27–0.79 | ✅ city-level | PAYG | mais barato verificado |
| IPRoyal | $1.75–7 | ✅ 908k IPs | PAYG, crédito não expira | cupom oficial ROYAL3 (3%) |
| Webshare | $3.50/mo+ | ✅ | mensal (free tier) | bom, mensalidade fixa |
| DataImpulse | ~$1 | ✅ | PAYG | reputação menor |
| Bright Data / Oxylabs | $3.5–6 | ✅ | — | caros |

Para solve de hCaptcha o volume é ~KB/solve → 1GB ≈ 10k solves → depósito mínimo (~$5) dura meses.

## MCP do GeoNode (Scraper API)

- Endpoint: `https://scraper.geonode.io/mcp` (StreamableHTTP)
- Auth: header `X-Api-Key: <key>` (chave no dashboard → API Keys)
- Tools: extract, job, jobs, batch, batch_status, cancel_batch, crawl, crawl_status, cancel_crawl, statistics
- Config no Hermes (config.yaml via `hermes config set`):
  - `mcp_servers.geonode.url` = https://scraper.geonode.io/mcp
  - `mcp_servers.geonode.headers.X-Api-Key` = <key>
  - `mcp_servers.geonode.timeout` = 180
- MCP não tem hot-reload: tools `mcp_geonode_*` entram na próxima sessão
- Handshake de teste: POST com headers `Content-Type: application/json` + `Accept: application/json, text/event-stream` + `X-Api-Key` (sem o Accept → 406)
- Limitação: o Scraper API do GeoNode NÃO serve para o Siscarga (exige mTLS do certificado do cliente — scraper não tem o PFX)

## Nota de chaves (confusão comum)

- NopeCHA key: prefixo `sub_...` (conta Professional do usuário)
- Morph API key: formato `sk-...` (dashboard morphllm.com) — key `sub_...` é rejeitada com 401 invalid_api_key
- GeoNode: username `geonode_...` + password UUID; ambas aceitas como X-Api-Key no MCP
