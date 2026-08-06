# Siscarga — mapa de campos das páginas (validado 2026-08-06, portal real)

Exemplo real: CE 132605207319565, consignatário 63.478.683/0001-07 (TUKTUK COMERCIO ATACADISTA & VAREJISTA LTDA), período 06/2026-08/2026, 7 registros.

## Nível 1 — Listagem (ConsultarCargaConsignatarioExibirCargas.do, pós-POST)

Por CE, o portal mostra um bloco com:

| Campo | Exemplo real |
|---|---|
| CE-Mercante (link p/ detalhe) | 132605207319565 |
| Nr. do BL | ZSJY26050025 |
| Tipo | HBL |
| Porto de Origem | CNNGB - NINGBO (NINGPO) |
| Situação | ENTREGUE |
| Data da Situação | 22/07/2026 |
| Hora da Situação | 13:55:36 |
| No. do Manifesto Eletrônico (link) | 1326501145816 |
| Embarcação | 9945849 - COSCO SHIPPING ARGENTINA |

Cabeçalho: "Critério de Pesquisa Informado: Consignatário / Período de Emissão do Conhecimento" + "N - M de K registros encontrados" + paginação "ANTERIOR | PRÓXIMA".

## Nível 2 — Detalhe do CE (ConsultarDadosBasicosCEMercante.do?nrCE=<n>)

Seções e campos (exemplos reais):

**Lista de Itens de Carga** (tabela na própria página): Tipo, No. do Item (0001), Id.Contêiner (CCLU7919845). Links: "Lista de Itens", "Lista de Houses", "Imprimir Extrato".

**Manifesto/Conhecimento**
- Número do Manifesto: 1326501145816
- Porto / Terminal de Carregamento: CNNGB- NINGBO (NINGPO)
- Porto / Terminal de Descarregamento: BRRIO/ BRRIO002- TERMINAL LIBRA - TECON 1 - RJ
- Tipo de Conhecimento: HBL
- BL de Serviço: N
- No. CE-MERCANTE Master vinculado: 132605199418024 (link)
- Data de Emissão do BL: 03/06/2026

**Embarcador**: Dados Complementares (YIWU BORUI IMPORT&EXPORT CO., LTD)

**Consignatário**: BL a Ordem (N), CNPJ/CPF, Razão Social/Nome, Dados Complementares

**Parte a ser Notificada**: CNPJ/CPF, Razão Social/Nome, Dados Complementares

**Transportador ou representante**: CNPJ (18.625.479/0001-17), Razão Social (CIL AGENCIADORA DE CARGAS E LOGISTICAS LTDA.)

**Procedência e Destino da Carga**
- Número BL do Conhecimento de Embarque Original: ZSJY26050025
- Porto de Origem: CNNGB-NINGBO (NINGPO)
- País de Procedência: CHINA
- UF de Destino Final: RJ
- Porto de Destino Final: BRRIO-RIO DE JANEIRO
- Número/Tipo do Documento de Despacho: 26BR00011432811 (DUIMP) — LINK

**Mercadoria**
- Descrição 1 (texto livre longo: "1 X 40HQ CONTAINER STC 868 CARTONS WITH AIR PUMP, ...")
- Descrição 2 (opcional)
- Peso Bruto da Carga (Kg): 13.923,000
- Cubagem (em m3): 68,000
- Categoria: IMPORTADA
- Situação: ENTREGUE 22/07/2026 (link)

**Frete e Despesas de Transporte**
- Recolhimento de Frete: PREPAID
- Modalidade de Frete: HH-HOUSE TO HOUSE
- Moeda do Frete: 220-DOLAR DOS EUA
- Valor do Frete Básico: 3.700,00
- Componentes do Frete (tabela): Componente da Taxa de Frete / Moeda / Valor / Recolhimento (ex: "004- 04ª TAXA D" 45,00 PREPAID; "017- 16ª CAPATA" 650,00 COLLECT)

## Nível 3 — Itens / Houses

- Item: No. do Item + Id. Contêiner (cada container da carga)
- Houses: HBLs vinculados ao MBL (links)

## Dicas de extração

- No browser (agent-browser): `read` (sem URL) devolve o DOM da página atual como markdown — salvar por CE.
- `snapshot` mostra a árvore de acessibilidade com refs `@eN` para navegação (links de CE na listagem, links de seção no detalhe).
- Ao navegar entre detalhes: NÃO usar o link "Voltar" do portal (vai para a página de Ajuda); usar `agent-browser back`.
- Os refs mudam a cada snapshot; re-consultar antes de clicar.
