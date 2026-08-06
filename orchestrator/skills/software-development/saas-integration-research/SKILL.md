---
name: saas-integration-research
description: Research a SaaS/ERP to plan an integration or migration.
---

# SaaS/ERP integration research

Quando o produto precisa importar (dump) dados de um sistema externo — ERP ou
SaaS que o cliente usa hoje — para migrar features ou substituir o sistema.
Validado no caso real Mainô → Flowmax (2026-08-06, ver
`references/maino-worked-example.md`).

## 1. Descobrir API oficial ANTES de pensar em scraping
- Docs costumam viver num subdomínio do produto: `docs.`, `changelog.`,
  `ajuda.`/help center. Se o site institucional não mostra, buscar
  `"<produto>" API integração` + `documenter.getpostman.com` (collections
  Postman públicas = mapa de endpoints pronto).
- GitBook/Mintlify expõem **`llms.txt`** e versão **Markdown anexando `.md`** à
  URL da página de docs — extração limpa via web_extract em vez de navegar.
- Help center: procurar coleções "Via API" / "Integrações" — os artigos dão os
  requisitos reais (ex.: application_uid fornecido pelo fornecedor) e links
  para a referência técnica.
- Testar o endpoint de autenticação com curl/httpx ANTES de navegar no app.

## 2. Pitfall: nome no prompt ≠ URL fornecida
Usuário pode escrever o nome errado (typo/homônimo — caso real: "mem0" quando
era "Mainô", maino.com.br). A URL/contexto anexado MANDA: pesquisar o produto
da URL, não o homônimo. Se o nome dito não aparece no app depois de logado,
confirmar em 1 linha ("é o <url> mesmo?") antes de aprofundar.

## 3. Pitfall: site bloqueia IP de datacenter
Browser remoto (Browserbase) = timeouts + reCAPTCHA agressivo em app de
produção. Trocar para **agent-browser LOCAL** (IP residencial do usuário) —
login flui sem captcha. Sessão nomeada (`AGENT_BROWSER_SESSION=nome`) mantém
cookies entre comandos.

## 3.5 Credenciais do fornecedor: 1Password do usuário
Antes de pedir chaves/credenciais ao usuário (application_uid, api keys,
contas de teste), checar o vault 1Password dele — o item do fornecedor costuma
ter TUDO (ex.: item "Mainô — IGCD" tinha o Application UID; "Chaves de API
Mainô" tinha api-keys; "NopeCHA" a chave do solver). Conectar via
`hermes secrets onepassword` (skill `onepassword-integration`): mapear as refs
como env vars do Hermes e validar mascarado. Isso destrava testes reais da API
sem depender de o usuário reenviar segredos.

## 4. Inventário de uso real (o que migra)
Pedir contas de teste ao usuário; são contas de PRODUÇÃO — **só leitura, nunca
alterar dados**. Módulo a módulo:
- `agent-browser snapshot -i -u` nos menus SPA revela as rotas
  (`url=https://app...`); abrir cada rota e anotar contagens/estado.
- Extração em SPA com `agent-browser eval` + padrão leaf-node:
  `[...document.querySelectorAll('*')].filter(e=>e.children.length===0&&/regex/.test(e.textContent)).map(e=>e.textContent.trim())`
  → `[...new Set(...)]` para listas únicas (ex.: números de processo).
- Regra de escopo: **só migra o que está preenchido/em uso**; módulo vazio ou
  não contratado fica fora (confirmar com o usuário).

## 5. Design do fluxo plug-and-play (mínimo de passos)
- Botão "Conectar e importar" → modal de login (credenciais do cliente no
  sistema externo) → 1 clique → **job assíncrono** (fila + worker) → progresso
  na tela → resumo final. Usuário usa o resto do app enquanto importa.
- Auth: OAuth2/token do fornecedor; guardar refresh token criptografado
  (AES-256-GCM com master key); jobs idempotentes com checkpoint por módulo;
  paginação + filtro `ultima_modificacao` para retomada.
- Dependência externa (ex.: application_uid só fornecido pelo fornecedor) =
  pendência explícita + fallback (ex.: X-Api-Key do painel do cliente).

## 6. Entrega
- `docs/research-<sistema>.md` no repo: mapa da API + inventário de uso +
  design. Segundo doc com inventário por conta se houver múltiplas contas.
- Tickets kanban verticais com contrato (ver skill `kanban-orchestration`):
  adaptador client → schema → endpoints+jobs → spec design → frontend;
  `--parent` encadeado; fronteira de arquivos e "PROIBIDO tocar" no body.
