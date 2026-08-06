# Mainô API — knowledge bank (integração Flowmax)

Fonte: pesquisa 2026-08-06 (worktrip `feat/integrations-maino`, doc
`docs/research-maino-api.md` no repo flowmex). Valores conferidos na doc
oficial; revalidar se mudarem.

## Identidade

- ERP brasileiro de comex/importação (maino.com.br). Flowmax substitui para o
  cliente; "migração Mainô" já é intenção declarada no README do
  `services/finance` (scaffold, sem código ainda).
- App web: `app.maino.com.br` (login email+senha+reCAPTCHA v2; "Trocar conta"
  p/ multi-empresa; ambiente Produção — **não há sandbox**).

## Autenticação (caminho crítico)

- Base: `https://api.maino.com.br/api/v2`
- `POST /api/v2/authentication` body `{application_uid, email, password}`
  → `{value: {<cnpj>: {email, user_name, company_name, cnpj, access_token,
  refresh_token}}}`
- JWT válido 24h; `refresh_token` p/ renovar; `Authorization: Bearer <token>`.
- **Pré-requisito externo: `application_uid` — emitido pela equipe Mainô sob
  solicitação (e-mail/WhatsApp). SEM ELE NÃO GERA TOKEN.** Pendência nº 1.
- Alternativa: header `X-Api-Key` com chave da aba Integrações em
  `app.maino.com.br/configuracoes` (o cliente copia manualmente; pior UX).

## Docs oficiais

- API reference (GitBook, tem `.md` por página): `changelog.maino.com.br/api-reference-maino/`
- Collection Postman pública: `documenter.getpostman.com/view/3466640/maino/7Lrd1hP`
- Central de Ajuda: `ajuda.maino.com.br` → coleções "Via API" (16 artigos) e "Integrações"

## Mapa de endpoints (v2)

| Módulo | Endpoints |
|---|---|
| 01 Auth | `POST /authentication` |
| 03 Stakeholders | `GET /stakeholders` (`tipo=cliente\|fornecedor\|transportadora\|fabricante\|funcionario`, `ultima_modificacao`, `page`), `GET /stakeholders/{id}`, `POST /stakeholders` (upsert), `GET /stakeholders/{id}/financeiro_notas_fiscais` |
| 04 Representantes | `GET /representantes` (`ultima_modificacao`, 100/pág) |
| 05 Recebimentos | `GET /contas_a_recebers` (filtros: NF, CPF/CNPJ, datas, tags, `status=em_aberto\|pago\|vencido`, `per_page`≤100), `POST`, `DELETE /{id}` |
| 06 Pagamentos | `GET /contas_a_pagars` (descrição, vencimento ini/fim, `status=vencidas\|vencimento_iminente\|pagas\|nao_pagas\|nao_vencidas`, fornecedor_id; 50/pág fixo), `POST`, `DELETE /{id}` |
| 07 Contas bancárias | `GET /contas_correntes` |
| 08 Controle de estoque | `GET /produtos` (ativos, zerados, código, descrição, unidade, NCM, `ultima_modificacao`; 100/pág), `GET /posicao_estoques` (datas, page) |
| 09 Movimentações | `GET /estoque/movimentacoes` (`tipo=0\|1`, `motivo=1..17`, datas), `GET /{id}` |
| 10 Pedidos | `GET /pedidos`, `GET /pedidos/{id}/nota_fiscal`, `POST /pedidos/{id}/nota_fiscal` (finaliza→NF-e), `DELETE /pedidos/{id}`, `PUT /pedidos/{id}/update_status` |
| 11 NFC-e | `GET /nfces` (`transaction_id`, `exibir_xmls`, 100/pág), `GET /nfces/exporta_xmls` (datas, máx 31 dias, ZIP), `POST /cancelar_ou_criar_devolucao_nfces`, `POST /devolucao_nfces` |
| 12 Notas fiscais | `GET /nfes` (`status=finalizada`, 25/pág; default só protocoladas A/C/N), `POST /nfes` (cria, não transmite), `POST /nfes/conta_e_ordem` (Idempotency-Key), `POST /nfes/transmitir`, `GET /nfes_emitidas` (dd/mm/aaaa) → ZIP XMLs+DANFEs |
| 13 Classificação fiscal | `GET /fiscal/ncms` (`codigo_ncm`, `data_atualizacao`) — II/IPI/COFINS/GATT/dumping importação |
| 14 DI | `GET /dis`, `POST /dis` (multipart XML Siscomex → DI completa; webhook_url, AFRMM), `POST /dis/{id}/gerar_nfe` (assíncrono) |
| 15 Processos Comex | `GET /processos` (`per_page` até 300) — pré-embarque, embarque (navio/BL/AWB/CRT, incoterm), despacho (invoice, terminal), DI, anexos, contêineres com demurrage, ordem_de_compra; campos legados deprecados (`fornecedor`→`fornecedores[]`, `agente_de_carga`→`agente_carga`, `codigo_purchase_order`→`ordem_de_compra`) |
| 16 Câmbio | `GET /comex/gestao_de_cambio/contratos`, `GET /.../contratos/{id}` (só leitura; pagamentos por DI/DUIMP, código BACEN) |

## Lacunas (API não cobre)

- Fechamento de câmbio (escrita) — parceiro Ebury, só no app
- SPED Fiscal, marketplaces, MAI (assistente IA), usuários/permissões
- Relatórios do dashboard; sem sandbox (só produção)

## Testes

- Contas de teste: TUKTUK (opetuktukcomercio@gmail.com, CNPJ
  63.478.683/0001-07) e RLS (rlsinternacionalltda@gmail.com). **Produção
  usada por clientes → read-only.** Senhas ficam fora de skills/repo.
- **app.maino.com.br bloqueia IP de datacenter** (browser remoto deu timeout
  repetido; reCAPTCHA pesado) → usar browser residencial (agent-browser local)
  para explorar o app; a doc pública e a API não têm esse problema.
- Créditos TUKTUK observados: 1/3 usuários, 9/20 importações, 10/10 produtos,
  88/120 NF-es — sinal de plano Operação.
