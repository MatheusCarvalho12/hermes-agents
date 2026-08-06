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
