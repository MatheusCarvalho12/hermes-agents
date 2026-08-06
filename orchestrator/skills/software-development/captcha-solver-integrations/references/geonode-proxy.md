# GeoNode — proxy residencial barato com geo Brasil (pesquisa 2026-08-06)

Fontes: docs.geonode.com + geonode.com/proxies-by-location/brazil-proxy (preços
verificados nas páginas oficiais).

## Preço (2026)
- Residential: $0.79/GB (~$0.27/GB em volume); PAYG, sem mensalidade mínima.
- Trial: 48h grátis (1 TB free, sem cartão). No trial o dropdown "Gateway" mostra
  só France/US/Singapore — isso NÃO limita o geo-targeting via username.
- Promo citada por agregadores (não verificada): 10GB/$5. Código oficial não
  existe; newsletter = $5 off. Sites de "30-75% off" = bait.

## GEO-TARGETING VAI NO USERNAME (não no dropdown "Gateway")
O dropdown "Gateway" é só o ponto de entrada (trial mostra France/US/Singapore;
indiferente para o país de saída). O país é um sufixo no username:

```
http://<user>-type-residential-country-<code>[:-state-<uf>|-city-<cidade>]:<pass>@proxy.geonode.io:9000
```

Exemplos (doc oficial):
- BR geral: `user-type-residential-country-br`
- São Paulo: `user-type-residential-country-br-city-sao-paulo`
- Docs: https://docs.geonode.com/docs/guides (tabela de parâmetros) e
  https://docs.geonode.com/docs/api-reference/geo-targeting/get-city/get

## Pool BR (tempo real na página)
84.210 IPs residenciais BR: São Paulo 22k, Salvador 16.5k, Brasília 16.5k,
Itápolis/Osasco/Santo André 5.5k cada; HTTP/SOCKS5; latência ~0.2s.

## Teste do IP antes de gastar crédito de solve
```
curl -x "http://user-type-residential-country-br:pass@proxy.geonode.io:9000" http://ip-api.com/json
```
Esperado: countryCode "BR" + ISP residencial. Só então rodar o E2E com o solver.

## Alternativas
- IPRoyal: BR com 908k IPs; dashboard tem "Country: Brazil" explícito; PAYG com
  crédito que não expira; cupom oficial `ROYAL3` (3%).
- Webshare: ~$3.50/mês entry (50% off frequente), free tier, país/cidade; sem PAYG
  puro para residencial.
- Bright Data / Oxylabs: $3.5-6/GB — caros demais para volume de solves.
