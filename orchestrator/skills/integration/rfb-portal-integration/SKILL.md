---
name: rfb-portal-integration
description: "Siscarga/RFB: certificado A1, mTLS, captcha, proxy BR."
---

# RFB Portal Integration (Siscarga / CCTa / DUIMP)

Integração com portais da Receita Federal usando certificado digital A1 (e-CPF/e-CNPJ) em PKCS#12. Validado 2026-08-06 contra o portal REAL (Siscomex Carga v5.1.0) com certificado real, NopeCHA + proxy GeoNode BR e browser local.

## 1. Certificado A1 (PFX)

- Senha/validade/CNPJ: `openssl pkcs12 -in <pfx> -clcerts -nokeys -passin pass:<senha> | openssl x509 -noout -subject -dates -issuer`
- CNPJ da empresa mora numa OU de 14 dígitos (`OU=00250354000194`) ou no CN (`CN=NOME:63478683000107`)
- Em código: `cryptography.hazmat.primitives.serialization.pkcs12.load_key_and_certificates`; escrever PEMs em tempdir 0700 (contextmanager `cert_files` no adapter do flowmex) e usar `ssl.create_default_context().load_cert_chain(cert, key)` + `httpx.AsyncClient(verify=tls_context)`
- e-CPF autentica consultas de CNPJs de empresas (o portal valida o certificado, não o CNPJ do form)

## 2. Fluxo Siscarga (validado de ponta a ponta)

1. `GET /g33159/jsp/LogonCertificado.jsp?ind=11` → `GET /g33159/servlet/certificado.LogonCertificado?ind=11` (mTLS) → redireciona para `/carga-web/siscarga_home.view` (sucesso = sessão autenticada)
2. `GET /carga-web/ConsultarCargaConsignatarioMenu.do` — form com hCaptcha
3. Resolver hCaptcha (ver references/nopecha-hcaptcha.md)
4. `POST /carga-web/ConsultarCargaConsignatarioExibirCargas.do` com o form COMPLETO (ver references/siscarga-portal.md — campos `crgOrdem`/`check`/`status` são OBRIGATÓRIOS; omiti-los → "0 registros")
5. Listagem → detalhe de cada CE (`ConsultarDadosBasicosCEMercante.do?nrCE=<n>`) → itens de carga

Regras do portal:
- Períodos são `MM/AAAA` (formato exato do portal; data completa → "Data inicial do período inválida")
- `GET` direto nos resultados → `java.lang.NullPointerException` (só POST funciona)
- Token de captcha rejeitado → o form é re-renderizado SEM mensagem de erro (campos preenchidos, zero registros) — não confundir com "não há cargas"
- Botão "Voltar" da página de detalhe vai para a Ajuda (não para a listagem) — use `back` do browser, não o link

## 3. Campos do portal (o que o parser precisa pegar)

- **Listagem**: nr_ce, nr_bl, tipo, porto_origem, situacao, data_situacao, hora_situacao, nr_manifesto, embarcacao — situação/data/hora/embarcação ficam `None` se o parser não ler a tabela (erro real encontrado)
- **Detalhe do CE** (~30 campos): manifestos + portos carregamento/descarga, tipo conhecimento, BL serviço, CE master, data emissão BL, embarcador, consignatário, parte notificada, transportador, procedência/destino (país, UF, porto, documento DUIMP), mercadoria (descrição, peso kg, cubagem m³, categoria), frete (recolhimento, modalidade, moeda, valor, componentes)
- **Itens**: nº item, tipo, id contêiner
- Detalhe completo com dados reais: `references/siscarga-portal.md`

## 4. hCaptcha do portal

- Widget é hCaptcha **classic** (data-sitekey no HTML; SEM `data-rqdata` — não é enterprise explícito)
- NopeCHA: ver `references/nopecha-hcaptcha.md` — endpoint/payload/bugs da lib/taxas de sucesso
- **Fallback confiável**: browser headed + clique manual do usuário no checkbox (1 clique por sessão de extração; a sessão dura minutos e dá pra extrair tudo)

## 5. Proxy residencial BR (GeoNode)

- **O geo-targeting vai no USERNAME do endpoint, não no dropdown "Gateway"** (o Gateway só escolhe o ponto de entrada; sem sufixo o IP cai em país aleatório — ex. Filipinas)
- Username: `<api_user>-type-residential-country-br` (city: `-city-sao-paulo`); host `proxy.geonode.io:9000`; HTTP com user:pass
- Teste rápido: `curl -x http://user:pass@proxy.geonode.io:9000 http://ip-api.com/json` → `countryCode: BR` (residencial de verdade, ex. Terra Roxa/PR)
- Config flowmex: `FLOWMEX_SISCARGA_NOPECHA_PROXY={"scheme":"http","host":"proxy.geonode.io","port":9000,"username":"...","password":"..."}` (pydantic-settings parseia JSON)
- Proxy residencial BR faz o hCaptcha servir desafios fáceis → solve em segundos em vez de 10-30 min
- **No Chrome/CDP, credenciais inline NÃO funcionam** (`ERR_NO_SUPPORTED_PROXIES`) — usar forward proxy local sem auth (`gost -L :8888 -F "http://user:pass@proxy.geonode.io:9000"` + `--proxy-server=http://127.0.0.1:8888`). Rotação de IP residencial = burlar o rate-limit do hCaptcha (detalhes em `references/siscarga-cdp-captcha.md`)

## 6. Browser para mTLS (exploração visual)

- **Browser remoto (Browser Use/Browserbase) NÃO autentica** — não tem o PFX → `403 Forbidden`
- Chrome **headless** do agent-browser trava no handshake mTLS (não mostra o seletor de certificado; daemon fica pendurado)
- **`agent-browser --headed` autentica** — usa o Keychain do sistema (o certificado precisa estar no Keychain/Login do Mac)
- Fluxo visual validado: `agent-browser --headed open <LogonCertificado>` → home → menu → preencher campos → usuário clica no captcha → enviar → snapshot/read salvam o DOM completo
- `agent-browser read` (sem URL) = DOM da página atual (fonte de dados estruturados); `snapshot` = a11y tree com refs `@eN`
- Após extrair: `agent-browser close --all` (fecha só os browsers do agent-browser; o Chrome do usuário fica intacto)

## 7. Pitfalls

- "0 registros" ≠ sem cargas: conferir se o form foi enviado COMPLETO (crgOrdem/check/status) e se o token do captcha não foi rejeitado (form re-renderizado)
- NopeCHA pode demorar 10-30 min/job ou nunca completar (variação diária); retry automático com vários jobs
- O `snapshot` do `computer_use` local pode falhar (0x0) com permissão de acessibilidade pendente (`universalAccessAuthWarn`) — usar agent-browser/HTTP em vez de travar
- Sessões autenticadas do Siscarga expiram; re-autenticar antes de cada rodada

## Referências

- `references/siscarga-portal.md` — URLs, form completo, campos mapeados dos 3 níveis, dados reais de exemplo
- `references/nopecha-hcaptcha.md` — API NopeCHA: endpoints, payloads, biblioteca Python, bugs e taxas de sucesso
