---
name: captcha-solving
description: "Use quando integração com hCaptcha via NopeCHA ficar presa."
---

# Captcha solving (hCaptcha via NopeCHA)

Padrões validados em integração real com o portal Siscarga da Receita Federal (2026-08-06): fluxo de token, polling, e a regra de ouro **polling > proxy**.

## Fluxo típico (hCaptcha Token API)
1. Extrair da página: `sitekey` (atributo `data-sitekey`; fallback para sitekey pública conhecida) e `rqdata` (hCaptcha Enterprise — `data-rqdata` no container do widget; sem ele, o solve enterprise falha/fica processing).
2. `POST https://api.nopecha.com/v1/token/hcaptcha` com `{key, sitekey, url, useragent, cookie?, data:{rqdata}?, proxy?}` → `{data: job_id}`.
3. Poll: `GET ?id=<job>&key=<key>` — `409`/`error:14` = ainda processando; `429`/`app:11` = rate limit (retry com backoff); `data` = token pronto.
4. Submeter o form com o token (muitos portais esperam o token em `response` E `h-captcha-response`).

## Códigos NopeCHA (não retry)
- `app/error 15` / HTTP 401 → key inválida (`invalid_key`)
- `app/error 16` / HTTP 403 → sem crédito (`out_of_credit`)
- `app/error 18` / HTTP 402 → feature indisponível
- `app/error 14` → job incompleto (RETRY); `app:11` / 429 → rate limit (RETRY com backoff)

## REGRA DE OURO: polling curto mata solves legítimos — aumente o polling ANTES de culpar proxy
- hCaptcha SEM proxy residencial BR leva **3–10+ min por solve** (challenge difícil em IP estrangeiro/datacenter).
- Exemplo real: `NOPECHA_MAX_POLLS=150` (2.5 min/tentativa) → 3 tentativas esgotadas → `captcha_failed` falso em 800s. Com 600 polls (10 min/tentativa), o MESMO solve completou.
- **Proxy residencial é ACELERADOR, não requisito**: hCaptcha serve challenges fáceis para IP real → solves em segundos. Mas se o fluxo já funciona com polling longo, proxy só reduz latência/custo.
- Ordem de debug: (1) aumentar polling (grátis), (2) só então considerar proxy (`{scheme, host, port, username?, password?}` no payload).

## Validação em camadas (não queimar crédito à toa)
- Testar o passo de autenticação (ex: mTLS) SEPARADO do captcha — auth não depende do solver e falha rápido.
- `curl -s https://api.nopecha.com/status -H "Authorization: Bearer <key>"` → `{plan, credit, quota}` — confirma key válida antes do teste E2E.
- "Job aceito" ≠ "solve completo" — o accept só prova a key/sitekey; o token pode nunca chegar (fica `processing` até o polling esgotar).
- Solve com retry automático (2-3 tentativas) absorve flake de job incompleto; mas com polling curto, retries só multiplicam o tempo perdido.

## Pitfall de ambiente
- Testes "live" (real API) ficam skipped sem `RUN_REAL_API=1` + credenciais — o E2E real com solver pode levar 10-30+ min por query; rodar em background com notificação, nunca em foreground bloqueante.
