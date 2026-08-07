# Vault Hermes — mapa de itens (sem valores)

Levantado 2026-08-06 via `op item list --vault Hermes --format json` (+ itens
descobertos em 2026-08-07). Usar os IDs nas refs `op://Hermes/<item-id>/<campo>`
quando o título tiver acento/espaço.

| Item | ID | Campos relevantes |
|---|---|---|
| Mainô — IGCD | `4tdj67dwz6yfx3ghrcnbt27w3y` | password, username (email), **Application UID** |
| Chaves de API Mainô | `x7ii723dq4vu5f2i2a6eebv3oe` | email×2 (TUKTUK/RLS), senha×2, api-key×2 (application_uid), docs, [FILE] CHAVES API MAINÔ.txt (**file id `rq45mv4bkyqsqqya6a7gz5zst4`**) — 10+ contas de empresas |
| Flowmex (login) | `kqmvz42feaoxpp6tin5midtcie` | username=pedro@importa.ai, password |
| NopeCHA | `7oec4armp4jfcmemahkbfa5qxy` | username, **credencial**, validFrom, expires, Docs |
| Siscomex Portal Unico API | `jam4e3hujp6zck4gypr6cgmhem` | username, credential, **SISCOMEX_CLIENT_ID**, **SISCOMEX_CLIENT_SECRET** |
| Flowmex staging | `qt2gasua4xmzgk4rw2lxigochy` | env vars: MAINO_BASE_URL, MAINO_CRED_KEY, SISCOMEX_*, PLUGBOLETO_*, OPENFINANCE_*, FLOWMEX_BILLING_* (inclui WEBHOOK_SECRET/DEDUPE_SECRET), TENANT_ORGANIZATION_ID, TEST_CNPJ, SISCARGA_PROXY_SECRET, SISCARGA_NOTE, SISCARGA_PROVIDER_URL, PLUGBOLETO_ENV |
| **Banco de dados Flowmex** | `5l2tcno7z4y7rzl65lpwztw3ke` | **Connection string** (Neon de produção: postgresql://…@ep-shiny-dust-acilckht-pooler.sa-east-1.aws.neon.tech) |
| Certificado Siscarga/Siscomex | `inevhv22pdxsf33n2odlppmdz4` | [DOCUMENT] certificado A1 |
| Cloudflare Flowmex (scoped) | `hftj7eitsybyztksd4rpbu4fvu` | API_CREDENTIAL (token scoped), username=account id, notes com projeto Pages |
| Secrets Cloudfare Flowmex | `ppt3a6rtzg42xtgw2shj5u5nla` | **Api-token**, **Account-id** (wrangler/deploy) |
| R2 flowmex-files S3 | `begzkhwhi6m4z5ciclbzdltefq` | API_CREDENTIAL |
| Sentry Flowmex | `frhkf3al3yrvq7nk2luojyhzhm` | SECURE_NOTE |
| Taskiq Flowmex dual tokens | `cuw6rbtnlaocx434esexqu2ium` | SECURE_NOTE |
| Fly Open Finance proxy Flowmex | `anbn5lsi37x3frecp4m4eegguy` | API_CREDENTIAL |
| Service Account Auth Token: Hermes | `pwymhbtewc6xtqd3472mplqtau` / `wq6kgmaiddupsea4z5hzqmidbe` | tokens SA (2 itens) |
| GitHub / outros | `wzlgk4y2z4e3al2vg3bpich734` etc. | LOGINs de infra |

## Refs já mapeadas no Hermes (hermes secrets onepassword status)

- FLOWMEX_MAINO_APPLICATION_UID → op://Hermes/4tdj67dwz6yfx3ghrcnbt27w3y/Application UID
- FLOWMEX_MAINO_USERNAME / FLOWMEX_MAINO_PASSWORD → mesmo item (username/password)
- NOPECHA_API_KEY → op://Hermes/NopeCHA/credencial
- SISCOMEX_CLIENT_ID / SISCOMEX_CLIENT_SECRET → op://Hermes/Siscomex Portal Unico API/<campo>
- MAINO_BASE_URL, MAINO_CRED_KEY, TEST_CNPJ, SISCARGA_*, PLUGBOLETO_*, OPENFINANCE_*, FLOWMEX_BILLING_*, TENANT_ORGANIZATION_ID → op://Hermes/qt2gasua4xmzgk4rw2lxigochy/<campo>

## Observações

- TUKTUK/RLS: ESTÃO no item "Chaves de API Mainô" (email/senha/api-key) — o
  api-key do item é o application_uid do Mainô. O arquivo CHAVES API MAINÔ.txt
  tem as contas das empresas (nome + application_uid + email + senha por bloco).
- Só existe 1 vault (Hermes, 38 itens) — não há chaves fora dele.
- Nunca commitar valores nem refs com valores resolvidos; o config.yaml do
  Hermes guarda apenas as refs (seguro para versionar).
