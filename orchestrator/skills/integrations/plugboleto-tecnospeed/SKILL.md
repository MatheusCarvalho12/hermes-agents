---
name: plugboleto-tecnospeed
description: Use ao integrar/ajustar a API de boletos PlugBoleto.
---

# PlugBoleto (TecnoSpeed) — API de boletos

## Quando usar
Emissão, consulta, baixa, PDF, webhooks de boletos PlugBoleto; diagnóstico de falha de registro (situação FALHA/REJEITADO).

## Credenciais e auth (produção)
- Base: `https://plugboleto.com.br/api/v1` (homologação: `https://homologacao.plugboleto.com.br/`)
- Headers obrigatórios em TODA chamada: `cnpj-sh` (CNPJ da software house), `token-sh` (**SEM o prefixo `token-`** — com o prefixo a API responde 401 `"Software House não encontrada"`), `cnpj-cedente` (CNPJ da empresa emissora — cada cedente tem o próprio)
- Token/convênio no payload: `CedenteConvenioNumero` = número do convênio (obtido via `GET /cedentes`, não via vault); `CedenteContaNumero` = conta SEM DV + `CedenteContaNumeroDV` separado (ex.: `13006945` + `8`; número+DV concatenado → 403 `"Número do Banco, Conta e/ou Digito Verificador inválidos"`)

## Endpoints essenciais
- `GET /cedentes` → estrutura completa por cedente: `contas[]` (codigo_banco, agencia, conta, conta_dv, `ativo`) e `convenios[]` (numero_convenio, carteira, registro_automatico, ativo). **É aqui que se descobre o número do convênio de cada conta** (não está no 1Password)
- `POST /boletos/lote` → emissão (array de títulos; resposta `_dados._sucesso[]` com idintegracao/idImpressao/situacao e `_dados._falha[]` com erros campo a campo)
- `GET /boletos?idintegracao=X` → consulta (situacao, motivo, UrlBoleto, idImpressao, todos os campos do título)
- `GET /boletos/impressao/{idImpressao}` → PDF do boleto (**só existe com situação REGISTRADO**; FALHA/REJEITADO → 400)
- `POST /boletos/baixa/lote` → baixa; corpo = **array de IDs** (`["ID1"]`) — NÃO objeto `{"Boletos": [...]}` (objeto → 400 `"O corpo da requisição deve ser um array de IDs"`)
- `POST /webhooks` → cadastro (só funciona em produção): `{ativo, url, eventos: {registrou, liquidou, baixou, protestou, alterou, rejeitou}, headers: {auth: "..."}}`; resposta ecoa o header `auth` — não logar resposta completa

## Receita de emissão (validada empiricamente — Santander 033, carteira RCR)
Payload mínimo que REGISTRA:
1. `TituloNossoNumero`: numérico (1–13 dígitos), **OBRIGATÓRIO** — sem ele: 400 `"TituloNossoNumero: Campo obrigatório"` mesmo com registro automático habilitado
2. `TituloNumeroDocumento`: **≤ 15 caracteres** — maior: `"TituloNumeroDocumento - Tamanho máximo do campo é 15 caracteres"` (não usar UUID/`boleto_id` inteiro)
3. `TituloDocEspecie: "01"` (duplicata mercantil) — **OBRIGATÓRIO**; sem ele o webservice do banco rejeita: `1090:O campo 'documentKind' é obrigatório` (o campo da API é `TituloDocEspecie`, NÃO `TituloDocumento`)
4. Sacado: nome, CPFCNPJ, endereço completo (CEP 8 dígitos, logradouro, número, bairro, cidade, UF). Email/telefone/complemento opcionais (fallbacks ok)

## Ciclo de vida / situações
`SALVO` (aceito pela API) → processa no banco → `REGISTRADO` | `REJEITADO` (motivo com código do webservice, ex.: `1090:...`) | `FALHA` (motivo textual). PDF/UrlBoleto só aparecem depois de REGISTRADO.

## Pitfalls
1. token-sh SEM prefixo `token-` (adapters costumam remover; em teste curl use sem prefixo)
2. Conta bancária: número e DV são campos separados na API; sistema pode armazenar concatenado → 403 na emissão
3. `TituloNumeroDocumento` curto — nunca usar UUID inteiro
4. documentKind = `TituloDocEspecie` (não `TituloDocumento`)
5. Baixa: corpo em array de IDs
6. Webhook: resposta de consulta ecoa o header `auth` — não logar resposta completa
7. Campo obrigatório pode aparecer em 2 camadas: validação da API (400 `_falha[]`) e validação do banco via webservice (situacao REJEITADO com `motivo` codificado) — testar o ciclo completo (não só o 200 do lote)

## Validação sem poluir produção
- 1º: montar o payload com o código real (shape check local — nenhum campo vazio onde não pode)
- 2º: 1 teste real com pagador real + NossoNumero único + NumeroDocumento curto → conferir `situacao=REGISTRADO` → baixar PDF → baixar o título de teste
- Nunca emitir boletos de teste em massa em produção

## Referência
- `references/emissao-receita.md` — cronologia da descoberta empírica (erros exatos em sequência até REGISTRADO) + exemplo de payload
