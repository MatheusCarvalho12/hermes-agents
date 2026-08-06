# Worked example: Mainô (maino.com.br) — ERP comex brasileiro

Projeto Flowmax (dev/flowmex/flowmex-platform): integração Mainô para
substituir o sistema do cliente. Pesquisa 2026-08-06; docs completos na branch
`feat/integrations-maino` → `docs/research-maino-api.md` + `docs/research-maino-usage.md`.

## API oficial (não precisa scraping)
- Base: `https://api.maino.com.br/api/v2` (~25 endpoints, seções 01–16)
- Docs: `https://changelog.maino.com.br/api-reference-maino/` — GitBook: anexar
  `.md` à URL da página para extração limpa
- Collection Postman: `https://documenter.getpostman.com/view/3466640/maino/7Lrd1hP`
- Help center: `ajuda.maino.com.br` → coleções "Via API" / "Integrações"

## Autenticação (OAuth2)
- `POST /api/v2/authentication` body `{application_uid, email, password}` →
  `{value: {<cnpj>: {access_token (JWT 24h), refresh_token, company_name, user_name}}}`
- Bearer em todas as chamadas; renovação com refresh_token
- Fallback: header `X-Api-Key` (chave da aba Integrações em
  app.maino.com.br/configuracoes)
- **Gargalo:** `application_uid` é fornecido pelo time Mainô sob solicitação
  (e-mail/WhatsApp) — registrar como pendência + fallback X-Api-Key

## App (inventário/uso)
- `app.maino.com.br` (login email+senha+reCAPTCHA v2; **bloqueia IP de
  datacenter** — usar agent-browser local, IP residencial)
- Rotas SPA principais: /processos, /dis, /produto_estoques, /crm, /pedidos,
  /contas_a_recebers, /nota_fiscals, /remessas_e_retornos, /cambio/operacoes_de_cambio
- Módulo "Cadastro inteligente" (Beta) cria processo/pedido a partir de
  PO/Proforma/Invoice/PDF — feature de IA do Mainô

## Endpoints-chave
- `GET /processos` (?page=&per_page=, default 300) — pré-embarque/embarque/
  despacho; fornecedores[], ordem_de_compra, conteineres (demurrage:
  free_time/tarifa/moeda/devolução), anexos, DI/DUIMP; campos legados
  deprecados (fornecedor→fornecedores[], agente_de_carga→agente_carga)
- `GET /nfes` (?status=finalizada&page=, 25/pág) + `GET /nfes_emitidas`
  (?data_inicio=dd/mm/aaaa&data_fim=) → ZIP XMLs+DANFEs
- `GET /produtos` (100/pág; ativos/zerados/código/NCM/ultima_modificacao) +
  `GET /posicao_estoques` (?data_inicio&data_fim)
- `GET /stakeholders` (?tipo=cliente|fornecedor|transportadora|fabricante|
  funcionario&ultima_modificacao&page) — CRM
- `GET /contas_a_recebers` (?status=em_aberto|pago|vencido&per_page≤100)
- `GET /dis` — DIs; `POST /dis` importa XML do Siscomex (multipart)
- `GET /comex/gestao_de_cambio/contratos` — só leitura
- `GET /estoque/movimentacoes`, `GET /contas_a_pagars`, `GET /contas_correntes`,
  `GET /fiscal/ncms`, `GET /representantes` — cobertura completa

## Inventário de uso (contas de teste, 2026-08-06)
| Módulo | TUKTUK (63.478.683/0001-07) | RLS (62.202.666/0001-80) |
|---|---|---|
| Processos | 13 (todos Pré-embarque, 9 c/ NF-e, 1 c/ DUIMP) | 16 (todos Pré-embarque, todos c/ NF-e, 3 c/ DUIMP) |
| NF-e emitidas | 33 (R$ 5,5M) | 70 (R$ 6,2M) |
| Produtos | 84 | 14 |
| Stakeholders | ~7 (clientes/fornecedores/transportadoras) | ~7 (mesmo grupo da TUKTUK) |
| Recebimentos | 92 (R$ 181k, 0 recebido) | 204 (R$ 185k, 67% recebido) |
| DIs | 2 | sem créditos DI/DUIMP |
| Não usado | câmbio, remessas, pedidos, marketplaces, exportação | idem |

Padrão de uso = **importação → NF-e de entrada → estoque → cobrança**;
migra só o que está preenchido.
