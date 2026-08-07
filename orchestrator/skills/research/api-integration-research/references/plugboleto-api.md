# PlugBoleto / TecnoSpeed API — webhooks e endpoints (banco de conhecimento)

Fontes: doc oficial na Central de Atendimento TecnoSpeed (Zendesk) + leitura do
adapter `HttpPlugBoletoProvider` do repo flowmex-v1 (2026-08-06).

## Docs oficiais (Zendesk)

- Cadastro de webhooks: `atendimento.tecnospeed.com.br/hc/pt-br/articles/360022264534-Cadastrando-notificações-de-Webhook`
- Artigos relacionados (na mesma HC): "Configurando WebHooks", "Consultando o
  cadastro das notificações de Webhook", "Atualizando o cadastro das notificações de Webhook".

## Bases URL

- Produção: `https://plugboleto.com.br/api/v1`
- Homologação: `https://homologacao.plugboleto.com.br/api/v1`
- ⚠️ **Webhooks só funcionam em PRODUÇÃO no PlugBoleto** (obs. da própria doc).

## Autenticação (todas as chamadas)

Headers: `Content-Type: application/json`, `cnpj-sh`, `token-sh`, `cnpj-cedente`
(CNPJ/CPF do cedente da vez). Emissões aceitam `Idempotency-Key`.

## Cadastro de webhook

`POST {base}/webhooks`

- Body: `ativo` (bool), `url` (endpoint do seu sistema), `eventos` `{registrou,
  liquidou, baixou, protestou, alterou, rejeitou}` (booleans), `headers` {uma
  ÚNICA propriedade, ex. `"auth": "meu-token"`}, `headers_adicionais` [{...}]
  (se precisar mais de um header), `data_ativacao` (ISO 8601, opcional — recebe
  notificações só de boletos criados a partir dessa data).
- Retorno: `{"_status":"sucesso","_mensagem":"...","_dados":[]}`; erro de
  validação vem em `_dados` com `_campo`/`_erro`.
- **Não há assinatura HMAC**: a autenticação do webhook é o header custom que
  VOCÊ define no cadastro (o emissor ecoa esse header nos POSTs). Ex.: cadastrar
  `headers: {"auth": "<secret>"}` e validar esse header no endpoint.
- Entrega: POST para a `url` cadastrada; em falha, **3 tentativas extras com
  ~15s de intervalo** → endpoint deve responder 2xx rápido (idempotente).

## Payload recebido no webhook

```json
{
  "body": {
    "tipoWH": "notifica_registrou | notifica_liquidou | notifica_baixou | notifica_rejeitou | notifica_alterou | notifica_protestou",
    "dataHoraEnvio": "21/09/2018 03:59:44",
    "titulo": {
      "situacao": "REGISTRADO",
      "idintegracao": "a1a1...",
      "TituloNossoNumero": "10",
      "PagamentoData": "20/09/2018",
      "PagamentoValorPago": "50,00",
      "PagamentoDataCredito": "20/09/2018",
      "PagamentoValorAcrescimos": null,
      "TituloMovimentos": [...]
    },
    "CpfCnpjCedente": "123456789"
  },
  "kind": "webhook", "method": "POST", ...
}
```

- `titulo.idintegracao` = referência única do boleto → usar como chave de
  lookup no nosso banco (no Flowmex == `plugboleto_reference`).
- `PagamentoValorPago` em formato brasileiro com vírgula ("50,00").
- `notifica_alterou` traz `TituloValor` e `TituloDataVencimento` (banco mudou
  vencimento/valor, situação permanece).
- **Recomendação da doc**: ao receber o webhook, capturar `idintegracao` e
  fazer GET `{base}/boletos?idintegracao=...` para obter o estado completo.

## Endpoints (validados no adapter do flowmex-v1)

- Consulta: `GET {base}/boletos?idintegracao=<ref>` — situacao em
  "REGISTRADO"/"LIQUIDADO"/"BAIXADO"/"REJEITADO"/"INCLUIDO_CARTORIO"..., campo
  `idImpressao` (hash p/ PDF), `PagamentoValorPago`.
- Emissão em lote: `POST {base}/boletos/lote` (até ~800; envelope `_dados`/
  `_sucesso`/`_falha`; referência por `TituloCodigoReferencia`/`idintegracao`).
- Baixa: `POST {base}/boletos/baixa/lote` `{"Boletos":[ref]}` (+
  `motivoCancelamento:"02"` p/ banco 077); descarte de pré-registro:
  `POST {base}/boletos/lote/descarte`.
  ⚠️ **Validado 2026-08-07 na API real: o corpo objeto `{"Boletos":[...]}` é
  REJEITADO com 400 "O corpo da requisição deve ser um array de IDs de
  integração"** — o adapter do Flowmex usa o formato objeto; testar array
  `["id"]` (na tentativa com array o boleto já estava FALHA → 404 "Nenhum
  boleto encontrado", não conclusivo). Confirmar formato exato antes de
  confiar no fluxo de baixa.
- PDF: `GET {base}/boletos/impressao/{idImpressao}`; se sem hash, fluxo
  assíncrono `POST {base}/boletos/impressao/lote` `{"TipoImpressao":"0",
  "Boletos":[ref]}` → protocolo → `GET {base}/boletos/impressao/lote/{protocolo}`
  até `content-type: application/pdf` (poll ~8×1.5s).

## Validação real de emissão (2026-08-07, API produção — descobertas que a doc NÃO mostra)

- **token-sh sem prefixo `token-`**: header espera o valor limpo (`e50e24...`).
  Com prefixo → 401 `"Software House não encontrada"` (erro enganoso).
- **`GET {base}/cedentes` retorna contas + convênios por cedente**
  (`contas[].convenios[].numero_convenio`, `cod_beneficiario`, `agencia`,
  `conta`+`conta_dv`) — a FONTE para preencher `plugboleto_convenio_id` no
  banco da aplicação (não existe campo de convênio no 1Password; o item
  "PlugBoleto e OpenFinance — Flowspeed" tem só docs/tokens).
- **Conta/DV separados**: a API exige `CedenteContaNumero='13006945'` +
  `CedenteContaNumeroDV='8'`; número concatenado `130069458` com DV vazio →
  403 "Número do Banco, Conta e/ou Digito Verificador inválidos". O Open
  Finance costuma entregar número+DV concatenados — normalizar ao cadastrar.
- **`TituloNossoNumero` é OBRIGATÓRIO** para convênio RCR/registro automático
  (ex.: IGCD convênio 666552) — sem ele → 400 "Campo obrigatório". Formato
  numérico (timestamp 10 dígitos funcionou; boleto manual de teste usava "30").
  ⚠️ **O adapter do Flowmex (`_emit_payload`) NÃO envia o campo** (comentário
  do código dizia "não fabricar NossoNumero até smoke-test" — o smoke-test
  provou que o convênio EXIGE) → PENDENTE: incluir no payload (sequencial por
  convênio ou timestamp).
- Pagador mínimo aceito: nome + documento (11/14) + endereço completo
  (CEP 8, rua, número, bairro, cidade, UF). Email/telefone/complemento
  opcionais (fallback email `noreply@invalid.local`, número `S/N`).
- Emissão OK real: `POST /boletos/lote` com pagador mínimo + NossoNumero →
  `_sucesso[].idintegracao` (ex.: `Z6CPHNSA1`), `situacao: SALVO`, HTTP 200.
  Boleto do Luiz (sem NossoNumero correto) ficou `situacao: FALHA`.
- Estado Flowmex V1 (Neon, 2026-08-07): IGCD conta 033/3122/13006945-8 →
  `plugboleto_convenio_id='666552'`, `plugboleto_conta_id='42547'` gravados
  (conta `openfinance-emp-46972197000121-almT5XSs8z`; conta_numero corrigida
  `130069458→13006945`, conta_dv `''→'8'`). LOGGY/PIM/IJL: convênio banco 208.
  AZX/ELEVEN/TNW/DPG/RLS/LTF/RCN/MONSTER: conta SEM convênio (não emitem).
  IGCD conta 341 não existe na API.
- Webhook cadastrado (produção) para IGCD: url
  `https://flowmex-gateway.matheuscarvalho.workers.dev/api/webhooks/plugboleto`,
  header `auth` = FLOWMEX_BILLING_PLUGBOLETO_WEBHOOK_SECRET, eventos todos ativos.

## Fluxo Flowmex (contexto da integração)

- V1 usa POLLING via outbox PostgreSQL + taskiq: `PLUGBOLETO_RECONCILE_STATUS`
  (retry enquanto "pendente") e `PLUGBOLETO_RECONCILE_LIQUIDATION` (retry até
  "liquidado") em `apps/api/src/flowmex/application/billing_write.py`.
- Mapa de status: `_PLUGBOLETO_STATUS` em
  `apps/api/src/flowmex/adapters/outbound/billing_providers.py`.
- Liquidação confirmada → comando `MAINO_SETTLE_RECEIVABLE` no mesmo outbox
  (repassa o pagamento ao Mainô).

## Design aplicado no Flowmex V1 (contrato de implementação do webhook, 2026-08-06)

- Endpoint `POST /api/webhooks/plugboleto`, SEM auth de sessão; validação header
  `auth` == `FLOWMEX_BILLING_PLUGBOLETO_WEBHOOK_SECRET` via `hmac.compare_digest`;
  secret não configurado → HTTP 503 `{"detail":"webhook_not_configured"}`.
- Parse tolerante do payload: aceitar envelope `{body: {...}}` (formato da doc)
  E payload direto `{tipoWH, titulo, ...}`.
- Mapeamento: `notifica_liquidou` → `PLUGBOLETO_RECONCILE_LIQUIDATION`; demais
  (`registrou`/`baixou`/`rejeitou`/`alterou`/`protestou`) → `PLUGBOLETO_RECONCILE_STATUS`.
  tipoWH desconhecido → log + 200 (não gerar retry no provedor).
- Padrão "webhook como gatilho do reconcile": o handler NÃO duplica lógica de
  parse/consulta de status — enfileira o comando outbox existente e responde 200
  imediato; quem consulta e persiste é o `BillingOutboxService` atual.
- Dedupe: `dedupe_key = "plugboleto_wh:" + HMAC-SHA256(dedupe_secret, f"{tipoWH}|{idintegracao}")`
  reusando a tabela `billing_idempotency` existente (NENHUMA migration nova);
  em dev sem dedupe_secret, fallback `f"{tipoWH}|{idintegracao}"`.
- Lookup inverso: novo método `find_charge_id_by_plugboleto_reference(provider_reference)`
  no `billing_write_repository.py` (não existia); evento órfão → log + 200.
- Config: `billing_plugboleto_webhook_secret` + `billing_plugboleto_webhook_dedupe_secret`
  (env `FLOWMEX_BILLING_PLUGBOLETO_WEBHOOK_SECRET` / `..._DEDUPE_SECRET`); validar
  que vêm juntos.
- Vault Hermes "Flowmex staging" (`qt2gasua4xmzgk4rw2lxigochy`) JÁ tem os 2
  secrets (criados no trabalho da V2 — reuso é decisão do usuário).
- Gateway: env vars novas precisam de repasse em `apps/gateway/src/container-env.ts`
  (FastApiContainerBindings + billingConfiguration, requiredString quando
  `FLOWMEX_BILLING_INTEGRATIONS_LIVE=true`) + `wrangler.*.jsonc` → secrets.required
  (container NÃO herda secrets do Worker automaticamente).
- Histórico do repo: tabelas `webhook_events` / `flowmex_billing_webhook_events`
  foram REMOVIDAS na migration 0028 — não há inbox reaproveitável.
- Cadastro real na PlugBoleto: fazer SÓ depois do deploy do endpoint em produção
  (senão a PlugBoleto entrega webhooks para URL 404 → retries perdidos).
