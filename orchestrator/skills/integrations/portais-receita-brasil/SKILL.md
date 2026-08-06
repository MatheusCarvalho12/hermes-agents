---
name: portais-receita-brasil
description: Autenticar/consultar Siscarga (RFB) com certificado A1.
---

# Portais Receita Brasil (Siscarga / CCTa)

Integração com portais da Receita Federal que exigem certificado digital A1 (e-CPF/e-CNPJ) em mTLS. Tudo abaixo foi validado contra o portal real `www4c.receita.fazenda.gov.br` (Siscomex Carga v5.1.0) em 2026-08-06.

## Quando usar
- Autenticar/consultar no Siscarga (CE-Mercante por consignatário) ou CCTa com um PFX
- Extrair dados de carga (listagem → detalhe do CE → itens/houses)
- Escolher solver de captcha ou proxy residencial BR para portais RFB

## Autenticação mTLS (validado)

### Via HTTP (adapter/Python)
- PFX decodificado em memória com `cryptography` (`pkcs12.load_key_and_certificates`), PEMs em tempdir 0700, `httpx` com `ssl.create_default_context().load_cert_chain(...)`
- Fluxo: `GET /g33159/jsp/LogonCertificado.jsp?ind=11` → `GET /g33159/servlet/certificado.LogonCertificado?ind=11` (com `Referer` da JSP) → final URL contendo `carga-web` = sessão autenticada
- Certificado válido = senha correta + `not_valid_after` futuro; CNPJ extraível do OU (14 dígitos) ou CN (`CN=NOME:CNPJ`)

### Via browser (exploração visual)
- **Browser remoto (Browser Use/Nous cloud, Browserbase) NÃO autentica** — 403 Forbidden: navegador cloud não carrega o PFX do usuário (mTLS é no handshake TLS)
- **`agent-browser` LOCAL com `--headed` FUNCIONA**: o Chrome do agent-browser usa o Keychain do macOS → apresenta o certificado → autentica e navega no portal real. Se o handshake travar (daemon "Resource temporarily unavailable"), é o seletor de certificado/Keychain esperando — fechar o daemon (`agent-browser close --all`) e reabrir com `--headed`
- `--auto-connect` no Chrome do usuário exige o Chrome rodando com `--remote-debugging-port` (sem isso: "No running Chrome instance found")

## hCaptcha do Siscarga (CRÍTICO — validado)

- **NopeCHA NÃO passa na validação do hCaptcha Enterprise da Receita** (2026-08-06): o token é devolvido (HTTP 200, job completa) mas o portal **rejeita silenciosamente** — re-renderiza o formulário vazio e retorna 0 registros. Sintoma: página de resposta contém o form vazio e a nota "Usuário não é servidor da RFB" (que é NOTA informativa, não erro)
- **Caminho validado que retorna dados reais: browser headed + captcha manual** (usuário clica "Sou humano" na janela do agent-browser)
- **PREFERÊNCIA DO USUÁRIO (2026-08-06, explícita): ele NÃO quer clicar captcha manualmente** ("não vou fazer mais nenhum, usa o NopeCHA aí, temos pra isso"). Ordem de tentativa: (1) NopeCHA/automação com retry — o usuário afirma que o token passa às vezes; investigar doc do NopeCHA (payload enterprise, rqdata, cookies da sessão, injetar token no textarea `h-captcha-response` via `agent-browser fill`) ANTES de pedir clique; (2) pedido de clique manual só como último recurso, no máximo uma vez
- Cliques programáticos no checkbox do hCaptcha são rejeitados (widget re-renderiza, ref muda no snapshot)
- SEMPRE validar a resposta da consulta: se vier o form re-renderizado (ou sem "Nenhum registro encontrado" e sem registros), o token foi rejeitado — não confundir com "0 registros legítimo"

## Formulário real de consulta (ConsultarCargaConsignatarioMenu.do)

Campos que o portal espera (form completo; omitir alguns devolve 0 registros):
`dtInicial`, `dtFinal` (formato **MM/AAAA** obrigatório — data completa é rejeitada), `cnpjCpf`, `consignatario=S` (hidden), `origem=e1` (hidden), `status=1` (hidden), `crgOrdem` e `check` (checkboxes, value=on), `response` + `h-captcha-response` (token)

- GET direto na URL de resultados (`ConsultarCargaConsignatarioExibirCargas.do?...`) → `NullPointerException` — o portal exige o POST do form
- Botão "Voltar" das páginas de detalhe pode levar à página de **Ajuda** (bug do portal) — usar `agent-browser back` em vez de clicar em Voltar

## Estrutura de dados do Siscarga

Três níveis (mapa completo de campos com exemplos reais em `references/siscarga-paginas-campos.md`):
1. **Listagem** — CE, Nr. BL, Tipo, Porto de Origem, Situação, Data/Hora da situação, Manifesto Eletrônico, Embarcação. Campos situação/data/hora/embarcação são comumente deixados `None` pelos parsers
2. **Detalhe do CE** (`ConsultarDadosBasicosCEMercante.do?nrCE=<n>`) — ~30 campos: manifesto/portos, tipo conhecimento, BL serviço, CE master vinculado, data emissão BL, embarcador, consignatário, parte notificada, transportador, procedência/destino (país/UF/porto), documento de despacho (DUIMP, link), mercadoria (descrição, peso bruto Kg, cubagem m3, categoria, situação), frete (recolhimento, modalidade, moeda, valor, componentes em tabela)
3. **Itens de carga / Houses** — nº do item, Id. Contêiner; lista de HBLs vinculados

## Proxy residencial BR (GeoNode) — para solvers que aceitam proxy

- **O dropdown "Gateway" NÃO é o seletor de país** — o geo-targeting vai no **username** do endpoint: `user-type-residential-country-br` (e `-city-<cidade>`)
- Endpoint: `http://<username-com-sufixo>:<password>@proxy.geonode.io:9000`
- Prova rápida: `curl -x "http://user:pass@proxy.geonode.io:9000" http://ip-api.com/json` → deve responder `countryCode: BR`
- Config em projetos Python (pydantic-settings): `FLOWMEX_SISCARGA_NOPECHA_PROXY={"scheme":"http","host":"proxy.geonode.io","port":9000,"username":"...","password":"..."}` (JSON parseado como dict)
- Detalhes de preços, MCP e alternativas: `references/geonode-proxy-mcp.md`

## Pitfalls
- **0 registros ≠ ausência de dados**: verificar (a) form completo, (b) captcha realmente aceito, (c) período correto — antes de concluir "não tem nada"
- NopeCHA polling curto demais (150 × 1s) mata solves legítimos de 5-10 min sem proxy — usar ≥600 polls ou proxy residencial
- Proxy de datacenter (Fly/Cloudflare/AWS) NÃO acelera hCaptcha — só residencial (IP real de banda larga) muda a dificuldade do desafio
- Sessão do agent-browser headed fica viva entre comandos; fechar com `agent-browser close` ao terminar

## Arquivos
- `references/siscarga-paginas-campos.md` — mapa completo de campos com exemplos reais
- `references/geonode-proxy-mcp.md` — pesquisa de proxies residenciais BR + MCP do GeoNode
