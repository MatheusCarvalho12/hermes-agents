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
- `GET /boletos?pagina=N` → **listagem do cedente** (fonte da verdade do idintegracao real: campos `idintegracao`, `TituloValor` no formato `150,00`, `TituloDataVencimento` no formato `dd/MM/yyyy HH:mm:ss`, `TituloNossoNumero`). Filtros como `numerodocumento` são IGNORADOS (retorna a página inteira) — para mapear um boleto local a um idintegracao, cruze por `TituloValor` + `TituloDataVencimento`
- `GET /boletos/impressao/{idImpressao}` → PDF do boleto (**só existe com situação REGISTRADO**; FALHA/REJEITADO → 400)
- `POST /boletos/baixa/lote` → baixa; corpo = **array de IDs** (`["ID1"]`) — NÃO objeto `{"Boletos": [...]}` (objeto → 400 `"O corpo da requisição deve ser um array de IDs"`)
- `POST /webhooks` → cadastro (só funciona em produção): `{ativo, url, eventos: {registrou, liquidou, baixou, protestou, alterou, rejeitou}, headers: {auth: "..."}}`; resposta ecoa o header `auth` — não logar resposta completa

## Receita de emissão (validada empiricamente — Santander 033, carteira RCR)
Payload mínimo que REGISTRA:
1. `TituloNossoNumero`: numérico (1–13 dígitos), **OBRIGATÓRIO** — sem ele: 400 `"TituloNossoNumero: Campo obrigatório"` mesmo com registro automático habilitado
2. `TituloNumeroDocumento`: **≤ 15 caracteres** — maior: `"TituloNumeroDocumento - Tamanho máximo do campo é 15 caracteres"` (não usar UUID/`boleto_id` inteiro). **Alfanumérico puro** (`[0-9A-Za-z]`, sem hífen/espaço) — hífen → banco rejeita `0901 clientNumber`; derivar por SHA-256 hex truncado a 15 chars (validado 2026-08-07)
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
8. **`idintegracao` de consulta NÃO é o UUID interno do sistema nem é derivável localmente** — é o código alfanumérico gerado pela PlugBoleto (ex.: `M03OCNAW1`). Se o banco guardar o UUID interno (`{uuid}-1-of-1`) como ref, `GET /boletos?idintegracao=<uuid>` responde `200 {"_mensagem": "Nenhum registro encontrado"}` e o download de PDF falha com `pdf_unavailable` (404). **Diagnóstico**: listar `GET /boletos?pagina=1` do cedente e cruzar por `TituloValor`+`TituloDataVencimento` para achar o idintegracao real; corrigir a ref no banco (UPDATE cirúrgico) e re-testar `boletos/impressao/{idImpressao}`. Ver `references/idintegracao-ref-mapping.md`
9. **"Valor mínimo" NÃO é limitação da PlugBoleto (CORRIGIDO 2026-08-07 — premissa do usuário refutada por probe real)**: boleto de R$100,00 **REGISTROU** com payload 100% válido em produção (idintegracao `O5ISFBNGW`, baixado depois). Os bloqueios reais eram do PAYLOAD (ver pitfall 10), não do valor. Lições que permanecem: (a) boleto `pendente` no banco local ≠ boleto existente no provider — boleto que não aparece na listagem `GET /boletos?pagina=N` do cedente nunca terá PDF, não importa o ref; (b) antes de baixar PDF de um pendente, confirmar na listagem do cedente (FONTE DA VERDADE); (c) **não aceitar premissa de limitação sem probe real** — testar a API com payload mínimo válido (valor pequeno, pagador real, baixar depois) antes de declarar "o provider não permite X".
10. **Bloqueios reais de emissão por payload (validado 2026-08-07)**: (a) CPF/CNPJ do sacado com dígito verificador inválido → API responde `"CPF 20466849645 é inválido"` — validar DV ANTES de emitir (erro `client_document_invalid` NÃO-retryable; outbox não deve re-tentar payload inválido); (b) `TituloNumeroDocumento` com hífen ou char fora de `[0-9A-Za-z ]` → banco rejeita `0901 clientNumber` — derivar alfanumérico puro (ex.: SHA-256 hex truncado a 15 chars) e NUNCA usar sufixo do `boleto_id` que contenha hífen; (c) "emissão com sucesso" só existe quando a listagem do cedente mostra o boleto — conferir SEMPRE após emitir (o `200` do lote não é prova).

## Validação sem poluir produção
- 1º: montar o payload com o código real (shape check local — nenhum campo vazio onde não pode)
- 2º: 1 teste real com pagador real + NossoNumero único + NumeroDocumento curto → conferir `situacao=REGISTRADO` → baixar PDF → baixar o título de teste
- Nunca emitir boletos de teste em massa em produção

## Referência
- `references/emissao-receita.md` — cronologia da descoberta empírica (erros exatos em sequência até REGISTRADO) + exemplo de payload
