---
name: receita-portals
description: "Portais RFB com certificado A1: Siscarga, CCTa."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [receita, siscarga, certificado, mtls, hcaptcha, nopecha, proxy, e-cpf]
    related_skills: [kanban-orchestration, agent-browser]
---

# Portais da Receita Federal com certificado A1

Classe de trabalho: autenticar e extrair dados de portais da RFB que exigem
**certificado digital A1 (e-CPF/e-CNPJ)** no handshake TLS (mTLS) — Siscarga
(CE-Mercante), CCTa/Portal Único, Duimp. O certificado é um PFX com senha;
campos típicos: CNPJ na OU (14 dígitos) ou no CN após `:`.

## 1. Validar o certificado (antes de qualquer código)

```bash
openssl pkcs12 -in "cert.pfx" -clcerts -nokeys -passin pass:'SENHA' \
  | openssl x509 -noout -subject -dates -issuer
```
- Senha errada → "Mac verify error: invalid password?".
- CNPJ: `OU=00250354000194` (e-CPF com procuração) ou `CN=NOME:63478683000107` (e-CNPJ).
- O nome do arquivo costuma trazer o vencimento; conferir `not_valid_after`.

## 2. Auth mTLS via HTTP (código)

- Decodificar o PFX **em memória** com `cryptography` (`pkcs12.load_key_and_certificates`) — nunca depender de `openssl` CLI no runtime.
- httpx precisa de **arquivos PEM**: escrever cert+key em tempdir `0700` (`tempfile.TemporaryDirectory` + chmod) e `ssl.create_default_context().load_cert_chain(...)`.
- Fluxo Siscarga: `GET LogonCertificado.jsp?ind=11` → `GET servlet/certificado.LogonCertificado?ind=11` (com `Referer`) → sucesso = URL final contém `/carga-web`. Qualquer outra coisa = certificado rejeitado.

## 3. hCaptcha (NopeCHA)

- Endpoint: `https://api.nopecha.com/v1/token/hcaptcha` (o `/v1/token` genérico responde "Invalid request").
- Payload: `{key, sitekey, url, useragent, cookie, rqdata?, proxy?}`. Cookies: **somente** os de domínio hCaptcha (`hcaptcha.com`, `newassets.hcaptcha.com`) — nunca enviar cookies da sessão da Receita.
- Polling: `GET ?id=<job>&key=<key>`; HTTP 409 ou `error:14` = processando; 429/app 11 = rate limit (retry com backoff); 15/16/18 e 401/402/403 = erro de conta (não retry).
- **Pitfall #1 — polling curto mata solves**: `NOPECHA_MAX_POLLS=150` (2.5 min) falha sem proxy; solves legítimos levam 5-10+ min. Usar 600 (10 min) como default e não confiar em 150.
- **Pitfall #2 — variabilidade**: cada solve é loteria (1-30 min); retry 3-4x com novo job é o padrão; um probe que completou em 7 min não garante o próximo.

## 4. Proxy residencial (GeoNode — padrão validado)

- **Geo-targeting vai no USERNAME, não no dropdown "Gateway"** (o Gateway é só o ponto de entrada e o trial mostra só FR/US/SG — o país de saída é sufixo do user):
  - `user-type-residential-country-br` — Brasil
  - `...-country-br-city-sao-paulo` — cidade
- Endpoint: `http://user:pass@proxy.geonode.io:9000` (testar com `curl -x ... http://ip-api.com/json` → `countryCode: BR`).
- O par username/password da conta serve tanto para a API/MCP quanto para o proxy; sem sufixo o rotate cai em país aleatório (ex: Filipinas).
- Sem proxy o solve do hCaptcha da Receita é imprevisível (10-40 min ou nunca); com proxy residencial BR cai para segundos-minutos.
- Config do flowmex: `FLOWMEX_SISCARGA_NOPECHA_PROXY={"scheme":"http","host":"proxy.geonode.io","port":9000,"username":"...","password":"..."}` (pydantic-settings parseia JSON de env).

## 5. Navegação VISUAL do portal (para mapear campos que o parser não pega)

- **Browser remoto (Browser Use/Nous) → 403**: não tem o certificado; mTLS é impossível em nuvem.
- **agent-browser headless → trava** no handshake (sem UI para o seletor de certificado).
- **agent-browser `--headed` → FUNCIONA**: o Chrome usa o Keychain do sistema (Login) e apresenta o certificado; o usuário vê a janela e pode resolver o hCaptcha manualmente (cliques programáticos no checkbox do hCaptcha são rejeitados — o widget re-renderiza).
- Fluxo visual: `agent-browser --headed open <url>` → `snapshot` → preencher (`fill @eN`) → usuário clica "Sou humano" → clicar enviar. Cuidado: navegar para "ajuda" perde o estado do captcha; voltar ao menu mantém os campos.

## 6. Siscarga — fatos do portal (validado 2026-08-06, v5.1.0)

- Base: `https://www4c.receita.fazenda.gov.br`; menu: `/carga-web/ConsultarCargaConsignatarioMenu.do`; consulta: `/carga-web/ConsultarCargaConsignatarioExibirCargas.do`.
- Período **obrigatório em MM/AAAA** ("Data inicial do período inválida" se mandar yyyy-mm-dd). Campo "até" é opcional.
- Form real tem campos que parsers simples omitem: `crgOrdem` (checkbox), `check` (checkbox), `status=1` (hidden) — além de `dtInicial, dtFinal, cnpjCpf, response, consignatario=S, origem=e1`.
- Marcadores de resposta: "Nenhum registro encontrado" = vazio legítimo; "NullPointer" = submissão malformada; página vazia após submit = token de captcha expirou (re-solve).
- Detalhes: `ConsultarDadosBasicosCEMercante.do?nrCE=...`, manifesto `ConsultarManifestoMaritimoPorNumero.do?nrManifesto=...`, escala `ApresentarDadosEscala.do?nrEscala=...` — as páginas de detalhe têm os campos "visuais" (pesos, volumes, consignatário, navio) que a listagem não carrega.

## 7. MCP do GeoNode (scraping) no Hermes

- Endpoint `https://scraper.geonode.io/mcp` + header `X-Api-Key`; handshake exige `Accept: application/json, text/event-stream` (testar com curl POST initialize).
- Config: `hermes config set mcp_servers.geonode.url ...` + `.headers.X-Api-Key ...` (sem hot-reload — tools `mcp_geonode_*` entram na próxima sessão).
- MCP ≠ proxy do NopeCHA: o MCP serve scraping (extract/crawl), não expõe endpoint de proxy HTTP cru.

## Verificação empírica (regra do projeto)

Draft → testar com caso real (certificado real, portal real) → medir → iterar.
Nunca "pronto" sem evidência. Detalhes da sessão de validação em
`references/siscarga-portal.md`.
