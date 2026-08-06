# Siscarga — portal, URLs e campos (mapeado 2026-08-06 com dados reais)

## URLs (sessão mTLS autenticada)

- Auth JSP: `https://www4c.receita.fazenda.gov.br/g33159/jsp/LogonCertificado.jsp?ind=11`
- Auth servlet: `https://www4c.receita.fazenda.gov.br/g33159/servlet/certificado.LogonCertificado?ind=11` (referer = JSP)
- Home autenticada: `/carga-web/siscarga_home.view` (marca sucesso; versão atual v5.1.0)
- Form consulta: `/carga-web/ConsultarCargaConsignatarioMenu.do` (hCaptcha sitekey `15095c53-b7e0-45b3-a2b7-f8ca4ef81cc5`)
- Submissão (POST): `/carga-web/ConsultarCargaConsignatarioExibirCargas.do`
- Detalhe CE: `/carga-web/ConsultarDadosBasicosCEMercante.do?nrCE=<número>`
- Manifesto: `ConsultarManifestoMaritimoPorNumero.do?nrManifesto=...`; Escala: `ApresentarDadosEscala.do?nrEscala=...`

## Form real (HTML do portal — TODOS os campos)

```
dtInicial       text   MM/AAAA (obrigatório)
dtFinal         text   MM/AAAA (opcional)
cnpjCpf         text   14 dígitos
crgOrdem        checkbox value=on   ← OBRIGATÓRIO (ordem)
response        hidden (token captcha)
consignatario   hidden S
origem          hidden e1
check           checkbox value=on   ← OBRIGATÓRIO
status          hidden 1            ← OBRIGATÓRIO
h-captcha-response (token)
```

**Pitfall real**: um adapter que enviava só dtInicial/dtFinal/cnpjCpf/consignatario/origem/response retornava "0 registros" para um CNPJ que TEM 7 CEs. Com o form completo (crgOrdem/check/status) o browser retornou os 7.

## Comportamentos do portal

- Período inválido → página re-renderiza com "Data inicial do período inválida..." e 0 registros
- Token de captcha inválido → form re-renderizado SEM mensagem (campos preenchidos, 0 registros) — o HTML da resposta tem o form de novo
- GET direto nos resultados → página "Erro no Processamento: java.lang.NullPointerException"
- "Nenhum registro encontrado" = resposta legítima de 0 cargas
- Botão "Voltar" do detalhe leva para ExibirAjudaSiscarga.do (não para a listagem)

## Campos por nível (dados reais: CNPJ 63.478.683/0001-07, TUKTUK, 06-08/2026)

### Nível 1 — Listagem (cada CE)
`nr_ce` (link), `nr_bl`, `tipo` (HBL), `porto_origem` (CNNGB - NINGBO), `situacao` (ENTREGUE), `data_situacao` (22/07/2026), `hora_situacao` (13:55:36), `nr_manifesto` (link), `embarcacao` (9945849 - COSCO SHIPPING ARGENTINA)

### Nível 2 — Detalhe do CE (Dados Básicos)
- Manifesto/Conhecimento: nr_manifesto, porto_carregamento (CNNGB-NINGBO), porto_descarga (BRRIO/BRRIO002 - TERMINAL LIBRA - TECON 1 - RJ), tipo_conhecimento (HBL), bl_servico (N), ce_master_vinculado (link), data_emissao_bl (03/06/2026)
- Embarcador: nome (YIWU BORUI IMPORT&EXPORT CO., LTD)
- Consignatário: bl_a_ordem (N), cnpj, razao_social, dados_complementares
- Parte a ser Notificada: cnpj, razao_social, dados_complementares
- Transportador: cnpj (18.625.479/0001-17), razao_social (CIL AGENCIADORA DE CARGAS E LOGISTICAS LTDA.)
- Procedência/Destino: nr_bl_original (ZSJY26050025), porto_origem, pais_procedencia (CHINA), uf_destino_final (RJ), porto_destino_final (BRRIO - RIO DE JANEIRO), nr_documento_despacho (26BR00011432811 — DUIMP, link)
- Mercadoria: descricao_1, descricao_2, peso_bruto_kg (13.923,000), cubagem_m3 (68,000), categoria (IMPORTADA), situacao (ENTREGUE 22/07/2026)
- Frete: recolhimento (PREPAID), modalidade (HH - HOUSE TO HOUSE), moeda (220 - DOLAR DOS EUA), valor_basico (3.700,00), componentes (tabela: componente, moeda, valor, recolhimento)

### Nível 3 — Itens de carga
`nr_item` (0001), tipo, `id_contêiner` (CCLU7919845). Links: Lista de Itens, Lista de Houses, Imprimir Extrato.

## Artefatos reais salvos (referência p/ testes unitários do parser)

- `/private/tmp/siscarga_menu.html` — form com todos os campos
- `/private/tmp/siscarga_listagem_browser.md` — DOM da listagem (7 CEs)
- `/private/tmp/siscarga_ce_detalhe.md` — DOM do detalhe completo (CE 132605207319565)
- `/private/tmp/ces/132605207319565.md` — idem
- `/private/tmp/siscarga_lib_result.html` — resposta do POST com token NopeCHA (form re-renderizado = token rejeitado)

## Exemplo real de extração visual (fluxo browser)

```
agent-browser --headed open <LogonCertificado.jsp?ind=11>   # Keychain autentica
agent-browser open <Menu.do>                                # form
agent-browser fill @e8 06/2026 / @e9 08/2026 / @e10 <cnpj>
# usuário clica no hCaptcha ("Sou humano")
agent-browser click @e6                                    # enviar
agent-browser read > listagem.md                           # DOM completo
agent-browser click @e16                                   # 1º CE
agent-browser read > ce.md
agent-browser back                                         # voltar (NÃO usar link Voltar)
```
