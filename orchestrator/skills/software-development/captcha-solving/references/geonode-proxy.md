# GeoNode — proxy residencial BR + MCP (validado 2026-08-06, portal Siscarga)

## Proxy residencial HTTP (para NopeCHA / scraping autenticado)

Endpoint validado: `proxy.geonode.io:9000` — HTTP proxy com auth no username.

### REGRA CRÍTICA: o país vai no USERNAME, não no dropdown "Gateway"
O dropdown "Gateway" (France/US/Singapore no trial) é só o ponto de ENTRADA.
O geo-targeting é por sufixos no username do endpoint (doc oficial docs.geonode.com):

```
<api_user>-type-residential-country-br
<api_user>-type-residential-country-br-city-sao-paulo
<api_user>-type-residential-country-gb-state-england
<api_user>-type-residential-country-gb-asn-1273
```

- Sem `-country-<code>` o tráfego sai de PAÍS ALEATÓRIO (observado: Filipinas).
- Trial 48h sem cartão mostra só 4 gateways no dropdown — mas o targeting BR
  funciona via username mesmo no trial (84k IPs BR disponíveis).

### Teste rápido (sempre antes de gastar crédito de solve)
```bash
curl -s -m 30 -x "http://USER-type-residential-country-br:PASS@proxy.geonode.io:9000" \
  "http://ip-api.com/json"   # → countryCode: "BR" = ok
```

### Preços 2026 (páginas oficiais)
- GeoNode: **$0.27–0.79/GB** PAYG; BR = 84.210 IPs (São Paulo 22k, Salvador/Brasília 16.5k, latência 0.2s); trial 48h; "1 TB free" promocional sem cartão.
- Alternativa: **IPRoyal** (BR 908k IPs, cupom oficial `ROYAL3`, crédito não expira, ~$1.75–7/GB).
- Custo real por solve de captcha ≈ KB → 1GB dura milhares de solves; depósito mínimo dura meses.

### Config no flowmex-core (services/core/.env — NÃO versionado)
```
FLOWMEX_SISCARGA_NOPECHA_PROXY={"scheme":"http","host":"proxy.geonode.io","port":9000,"username":"<user>-type-residential-country-br","password":"<pass>"}
```
pydantic-settings faz o JSON parse para o dict `{scheme, host, port, username?, password?}` que o adapter do Siscarga envia no payload do NopeCHA.

## MCP do GeoNode (Scraper API)

- Endpoint: `https://scraper.geonode.io/mcp` (StreamableHTTP)
- Auth: header `X-Api-Key: <api_key>` (dashboard → API Keys; formato `geonode_...`)
- **Pitfall**: sem `Accept: application/json, text/event-stream` o servidor responde HTTP 406 ("Client must accept both...").
- Tools: extract, job, jobs, batch, batch_status, cancel_batch, crawl, crawl_status, cancel_crawl, statistics.
- Config no Hermes (sem hot-reload — restart para ativar):
```bash
hermes config set mcp_servers.geonode.url "https://scraper.geonode.io/mcp"
hermes config set mcp_servers.geonode.headers.X-Api-Key "<key>"
hermes config set mcp_servers.geonode.timeout 180
```
- Escopo: MCP é para SCRAPING (extract/crawl via infra deles). Não substitui o fluxo mTLS do Siscarga (o portal exige o certificado do cliente). Para o NopeCHA, o que vale é o endpoint de proxy HTTP acima.

## Segredos
Credenciais vivas (NopeCHA key, GeoNode user/pass) ficam em `services/core/.env` — nunca duplicar em skill/repo.
