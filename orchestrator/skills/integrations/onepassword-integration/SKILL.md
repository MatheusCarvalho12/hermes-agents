---
name: onepassword-integration
description: Use when pulling secrets from the user's 1Password vault.
---

# 1Password + Hermes (op CLI)

O usuário mantém segredos de todos os projetos no 1Password (vault `Hermes`:
API keys, credenciais de fornecedores, tokens). O Hermes tem integração NATIVA:
`hermes secrets onepassword` (doc: hermes-agent.nousresearch.com/docs/user-guide/secrets/onepassword).

## Fluxo (forma certa, validada 2026-08-06)

1. **Token de Service Account** (formato `ops_...`): o usuário pode compartilhar
   o token; guardar em `~/.hermes/.env` como `OP_SERVICE_ACCOUNT_TOKEN` (é o
   lugar que a doc manda — nunca no config.yaml nem no repo).
2. Habilitar: `hermes secrets onepassword setup --account my.1password.com --token-env OP_SERVICE_ACCOUNT_TOKEN --token "$OP_SERVICE_ACCOUNT_TOKEN"`
3. Mapear: `hermes secrets onepassword set VAR "op://Vault/Item/campo"` — toda
   env var resolvida no startup de qualquer processo Hermes (gateway, cron, workers).
4. Validar: `hermes secrets onepassword status` (mostra refs com erro) e
   `op whoami` (confirma SERVICE_ACCOUNT).

## Pitfalls (todos encontrados em produção 2026-08-06)

1. **O setup reescreve a linha do token SEM aspas** no dotenv. Extrair o token
   com regex `ops_[A-Za-z0-9_\-]+`, NUNCA `cut -d'"' -f2` — o cut sem aspas
   pega a linha inteira e o valor vira `OP_SERVICE_ACCOUNT_TOKEN=ops_...` com
   o prefixo DENTRO → erro `failed to DecodeSACredentials ... unrecognized
   auth type` (parece token inválido, mas é extração errada).
2. **Refs op:// rejeitam acento e espaço no TÍTULO do item**: `Mainô — IGCD`
   → `invalid character in secret reference: 'ô'`; `Flowmex staging` → "isn't
   an item in the vault". Correção: usar o **ID do item**:
   `op://Vault/<item-id>/<campo>` (ID via `op item list --format json`).
3. **Service account exige `--vault`** nos comandos `op item get`/`read` por
   nome: `a vault query must be provided when this command is called by a
   service account`. Sempre `--vault Hermes` (ou usar IDs na ref).
4. **Nunca imprimir valores de segredo** no chat/output (redact_secrets pode
   estar off no config). Validar mascarando: `len + v[:4] + v[-4:]`.
5. `op item list` pode funcionar uma vez e falhar depois se a extração do
   token mudou (cut vs regex) — o sintoma é o mesmo erro do pitfall 1.
6. Sem app 1Password instalado no Mac: não existe sessão desktop — o
   service account token é o ÚNICO caminho (sem token: `no account found`).
7. **Nunca usar `UID` como nome de variável em script bash** — é readonly
   (uid do usuário); `UID=...` falha silencioso e a ref sai com valor errado
   (ex.: application_uid="501" → 401 na API). Usar `MAINO_UID`/`APP_UID`.
8. **`op read` de FILE anexo com acento/espaço no NOME falha silencioso** (retorna
   vazio, ex.: `CHAVES API MAINÔ (1).txt`): usar o **file id** —
   `op://Vault/<item-id>/<files[].id>` (pegar o id com `op item get <id> --vault Hermes
   --format json` → campo `files[].id`). Sintoma clássico: "arquivo veio 0 bytes"
   quando na verdade tem conteúdo.
9. **Caçar credenciais espalhadas pelo vault**: para "achar a chave de X",
   iterar `op item list` e em cada item ler labels/types/notes MASCARADOS
   (nunca valores), filtrando por substring (ex.: "maino", "neon", "key").
   Campos type=STRING/URL podem ser lidos direto quando não-secretos (ex.:
   connection string Neon é type=URL — mas contém senha: só ler dentro de
   scripts). Verificar OUTROS vaults também (`op vault list`) — o esperado
   pode estar fora do vault principal.
10. **`op item get` exige o UUID COMPLETO** (2026-08-07): prefixo de 12 chars
    (ex.: `kqmvz42feaox`) falha com `"kqmvz42feaox" isn't an item in the
    "Hermes" vault` mesmo sendo o começo do id real (26 chars). O `item list`
    retorna ids completos — NÃO truncar ao capturar. Sintoma idêntico ao de
    item inexistente: sempre conferir o id inteiro antes de culpar permissão.
11. **Itens categoria DOCUMENT não respondem `op item get --format json`**
    (2026-08-07): saída vazia → JSONDecodeError no parse (parece erro de
    permissão). Usar `op document get <id-completo> --vault Hermes` (com o id
    COMPLETO; com prefixo truncado retorna 0 bytes silencioso). Secure notes
    (SECURE_NOTE) com env vars: os valores são FIELDS com label em UPPER
    (ex.: `MAINO_BASE_URL`) — ler via `op item get --format json` e mapear
    labels→values; o notesPlain é só texto descritivo.
12. **Label de campo com ESPAÇO falha silencioso no `op read`**
    (2026-08-07): `op://Vault/<id>/Application` retorna VAZIO quando o campo
    real é "Application UID" (com espaço) — o valor vazio vira `application_uid=""`
    → 422/401 na API e parece problema de credencial. Pegar o **field id**
    (`op item get <id> --vault Hermes --format json` → campo `fields[].id`)
    e usar `op://Vault/<item-id>/<field-id>`.
13. **Secrets que os workers do Hermes aplicam** vêm da seção `secrets:` do
    `~/.hermes/config.yaml` (refs `op://Hermes/...`) — é o "1Password: applied
    N secrets" do kanban. Para reproduzir localmente, ler os itens apontados
    pelas refs (nomes de campos dos itens podem diferir dos labels — conferir
    com `op item get --format json`).

## Verificação segura de refs (mascarada)

```bash
export OP_SERVICE_ACCOUNT_TOKEN=$(python3 -c "import re; l=[x for x in open('/Users/amaterei/.hermes/.env') if 'OP_SERVICE_ACCOUNT_TOKEN' in x][0]; print(re.search(r'ops_[A-Za-z0-9_\-]+', l).group(0))")
python3 -c "
import os, subprocess
refs = {'VAR': 'op://Hermes/<item-id>/<campo>'}
for k, ref in refs.items():
    v = subprocess.run(['op','read',ref], capture_output=True, text=True).stdout.strip()
    print(f'{k}: len={len(v)} mascara={v[:4]}...{v[-4:] if len(v)>8 else \"\"}')"
```

## Vault do usuário

Itens e IDs do vault `Hermes`: `references/vault-hermes.md` (atualizar ao criar
novas refs). Formato do token SA: `ops_` + JSON base64url
(signInAddress/userAuth SRPg-4096/muk/secretKey — confere com a doc oficial
1password.dev/service-accounts/security).
