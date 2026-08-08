# Mapeamento idintegracao: quando o sistema guarda o UUID interno em vez do idintegracao real

Caso real (Flowmex, 2026-08-07): boletos emitidos via `POST /boletos/lote` ficaram com
`boletos.plugboleto_id_integracao = '{uuid_interno}-1-of-1'` (ex.: `24a0eb80-374b-4f30-a545-761f64d3fb7f-1-of-1`),
mas a PlugBoleto registra o idintegracao como código alfanumérico próprio (ex.: `M03OCNAW1`).
Sintoma: `GET /boletos/{id}/pdf` → 404 `{"error":"Official boleto PDF is unavailable","code":"pdf_unavailable"}`
(causa: `_consult` por idintegracao responde `{"_status":"sucesso","_mensagem":"Nenhum registro encontrado","_dados":[]}`).

## Passo a passo de diagnóstico (validado)

1. **Teste o endpoint individual antes do agregador** — se `GET /boletos/{id}/pdf` já falha,
   o bug não é do merge/bundle.
2. **Confira o ref no banco** (a coluna pode ter nome enganoso):
   - tabela `boletos`: `id` = interno (`...-boleto-1`), `plugboleto_id_integracao`, `valor`, `vencimento`, `raw` (muitas vezes vazio)
   - tabela `flowmex_billing_boleto_details`: `boleto_id` (FK), `public_id` (o id exposto pela API, `bol_...`), `has_pdf`, `normalization_state`
   - tabela `flowmex_billing_pdf_assets`: `object_key` (cache R2 — vazio = nunca baixado)
   - O id exposto pela API (`bol_...`) é o `public_id`; a query de resolução usa
     `WHERE public_id = :id AND normalization_state = 'ready'`.
3. **Reproduza com curl direto** (headers: `cnpj-sh`, `token-sh` SEM prefixo `token-`, `cnpj-cedente`):
   - `GET /boletos?idintegracao=<ref-salvo>` → "Nenhum registro encontrado" = ref errado
   - `GET /boletos?pagina=1` (listagem do cedente) → mostra o idintegracao REAL + `TituloValor` (`150,00`) + `TituloDataVencimento` (`dd/MM/yyyy HH:mm:ss`)
   - Filtros da listagem (`?numerodocumento=`) são ignorados pela API — não use para mapear
4. **Cruzamento**: o boleto local R$150 venc 26/08 → na listagem achar o registro com `TituloValor: '150,00'` → idintegracao real (`M03OCNAW1`).
5. **Prova antes do fix**: consultar por idintegracao real → `idImpressao` → `GET /boletos/impressao/{idImpressao}` → PDF (validar conteúdo com pypdf: páginas + texto contém o valor).
6. **Fix de dados**: `UPDATE boletos SET plugboleto_id_integracao = '<real>' WHERE id = '<interno>'` (cirúrgico, com WHERE de segurança).
7. **Prova pós-fix**: repetir `GET /boletos/{public_id}/pdf` → 200 `application/pdf` (mesmo byte-size do download direto indica que veio do provider, não de cache errado).

## Observações
- `TituloNossoNumero` derivado por hash local NÃO coincide com o idintegracao da API
  (o hash local é numérico; o idintegracao é alfanumérico gerado pela PlugBoleto).
- `raw` da emissão geralmente não é persistido → não dá para recuperar o idintegracao de lá.
- O `vencimento` no banco pode divergir do `TituloDataVencimento` da API — cruzar por VALOR é o mais confiável.
- Prevenção em código: auto-heal no download (fallback: listar + cruzar por valor/vencimento quando a consulta por ref der 0 registros; persistir o ref corrigido).
