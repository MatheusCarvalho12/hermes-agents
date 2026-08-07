# Receita de emissão — descoberta empírica (2026-08-07, produção)

Sequência real de tentativas até `situacao=REGISTRADO` na API PlugBoleto (cedente Santander 033, carteira RCR, registro automático). Cada erro revelou o próximo campo obrigatório — APIs de emissão validam em camadas: gateway da API (400 `_falha[]`) e webservice do banco (situacao REJEITADO/FALHA com `motivo`).

## Erros na ordem exata
1. `token-sh` com prefixo `token-` → 401 `{"_erro":"Software House não encontrada"}`. **Fix:** remover o prefixo `token-`.
2. `CedenteContaNumero: '130069458'` + DV vazio → 403 `"Número do Banco, Conta e/ou Digito Verificador inválidos"` (campos: CedenteContaCodigoBanco, CedenteContaNumero, CedenteContaNumeroDV). **Fix:** conta SEM DV (`13006945`) + `CedenteContaNumeroDV: '8'` — o banco de dados pode armazenar número+DV concatenado.
3. Sem `TituloNossoNumero` → 400 `{"erroValidacao":true,"erros":{"TituloNossoNumero":"Campo obrigatório."}}`. **Fix:** numérico 1–13 dígitos (timestamp de 10 dígitos validado; formato curto `30` também visto em boleto existente).
4. `TituloNumeroDocumento` com 24 chars → situacao `FALHA`, motivo `"TituloNumeroDocumento - Tamanho máximo do campo é 15 caracteres"`. **Fix:** ≤ 15 chars (ex.: `FMX20260807002`).
5. Sem tipo de documento → situacao `REJEITADO`, motivo `"1090:O campo 'documentKind' é obrigatório."`. `TituloDocumento: 'DM'` NÃO resolve (campo ignorado). **Fix:** `TituloDocEspecie: '01'` (duplicata mercantil).
6. Payload final → situacao **REGISTRADO**, motivo None, idImpressao presente → `GET /boletos/impressao/{idImpressao}` retorna o PDF (200, ~25 KB).

## Exemplo de payload mínimo que registra
```json
[{
  "CedenteContaNumero": "13006945",
  "CedenteContaNumeroDV": "8",
  "CedenteConvenioNumero": "666552",
  "CedenteContaCodigoBanco": "033",
  "SacadoCPFCNPJ": "28140177000455",
  "SacadoEmail": "noreply@invalid.local",
  "SacadoEnderecoNumero": "1000",
  "SacadoEnderecoBairro": "BELA VISTA",
  "SacadoEnderecoCEP": "01310100",
  "SacadoEnderecoCidade": "SAO PAULO",
  "SacadoEnderecoLogradouro": "AV PAULISTA",
  "SacadoEnderecoPais": "Brasil",
  "SacadoEnderecoUF": "SP",
  "SacadoNome": "PARTNER COMERCIAL E IMPORTADORA LTDA",
  "TituloDataEmissao": "07/08/2026",
  "TituloDataVencimento": "07/09/2026",
  "TituloValor": "150,00",
  "TituloNumeroDocumento": "FMX20260807002",
  "TituloCodigoReferencia": "FMX20260807002",
  "TituloNossoNumero": "2786072393",
  "TituloDocEspecie": "01",
  "TituloLocalPagamento": "Pagavel em qualquer banco ate o vencimento.",
  "TituloMulta": "2,00",
  "TituloJuros": "1,00"
}]
```

## Descobertas de descoberta (como achar dados que não estão no vault)
- `GET /cedentes` retorna a árvore completa: cedente → `contas[]` → `convenios[]` (numero_convenio, carteira, registro_automatico, ativo, certificado). O número do convênio NÃO fica no 1Password — vem daqui.
- Boletos de teste antigos (situacao FALHA) não geram PDF (400) — PDF só com REGISTRADO.
- Situação muda assincronamente: o lote responde `SALVO` e o registro processa em ~segundos; consultar de novo com `?idintegracao=` para o estado final.

## Notas de segurança
- Resposta do cadastro/consulta de webhook ecoa o header `auth` — não logar a resposta completa.
- Para validar emissão sem poluir produção: 1 título real + baixa em seguida (corpo da baixa = array de IDs).
