---
name: captcha-solver-integrations
description: Use when integrating captcha solvers (NopeCHA).
---

# Captcha Solver Integrations (NopeCHA + hCaptcha)

Padrões validados 2026-08-06 no Siscarga da Receita Federal (flowmex-core):
fluxo mTLS → página com hCaptcha Enterprise → solver → submit. Vale para
qualquer portal com hCaptcha Enterprise.

## Diagnóstico nº 1: solve "lento" vs "nunca completa" (fazer ANTES de culpar o código)
1. Aumente a janela de polling (ex: 150 → 600 polls) e rode de novo.
2. Completa com polling maior = LENTO → fix é aumentar a janela (grátis).
3. Falha igual = NUNCA COMPLETA → challenge difícil → proxy residencial (abaixo).
4. NUNCA confiar em 1 sucesso: variação real entre tentativas (na mesma sessão:
   uma completou em ~7 min, outra nunca em 40 min, mesmo alvo). Múltiplas rodadas
   antes de concluir "resolveu".

## Proxy: só residencial resolve challenge difícil
- Datacenter (Fly.io, Cloudflare, AWS) = MESMA classe suspeita — não melhora.
  Residencial do MESMO país do portal (BR p/ Receita) é o ideal.
- Payload do solver aceita `{scheme, host, port, username, password}` — formato
  exato dos provedores de proxy HTTP com auth.
- SEMPRE validar o IP do proxy ANTES de gastar crédito de solve: consulta
  `ip-api.com/json` via proxy (curl -x ou requests[proxies]) — confirmar país +
  ISP residencial.

## NopeCHA (API v1/token/hcaptcha)
- POST job `{key, sitekey, url, useragent, cookie[], rqdata?, proxy?}` → `{data: job_id}`;
  poll `GET ?id=<job>&key=<key>`.
- 409 / `error: 14` = processando; 429 / `app: 11` = rate limit (backoff);
  401/app15 = invalid_key, 402/app18 = feature_unavailable, 403/app16 = out_of_credit
  (não retry — conta, não transient).
- Health/crédito: `GET https://api.nopecha.com/status` com `Authorization: Bearer <key>`
  → plano, crédito, janela.
- Token hCaptcha expira ~2 min após solve; página vazia no submit = token morto → re-solve.

## E2E real com solver (disciplina de tempo/custo)
- Rodar em background + `notify_on_complete`; nunca polling manual com sleep.
- Matar quando a falha for PREVISÍVEL (3 tentativas esgotadas no 1º alvo = os
  outros vão falhar igual; economiza crédito e 20-40 min).
- Testes de query longa só imprimem no fim (pytest -s idem) — não dá para
  acompanhar progresso; o log do processo é o que importa.

## Keys invertidas (lição real)
Usuário pode trocar as keys de provedores: a do solver (NopeCHA) e a de outra
ferramenta (Morph). Sintoma: 401 num serviço que "deveria" funcionar. Checar
formato (NopeCHA/Morph aceitam `sk-...`; key `sub_...` era a do NopeCHA) e o
endpoint de status de cada um antes de concluir "key inválida".

## Referência
- `references/geonode-proxy.md` — proxy residencial barato com geo BR: targeting
  via username, preços 2026, alternativas (IPRoyal/Webshare).
