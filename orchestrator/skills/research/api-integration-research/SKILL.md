---
name: api-integration-research
description: "Research a third-party API: docs, auth, endpoints, test."
---

# API Integration Research

Pesquisar um serviço/API de terceiros para integrar (importar dados, migrar,
sync): descobrir a doc oficial, mapear autenticação + endpoints, testar com
contas reais e entregar um relatório com fonte citada no repo do projeto.

## Workflow

1. **Confirme o alvo.** O usuário pode errar o nome do produto (ex.: "mem0"
   quando era "Mainô"). Valide o nome contra a URL/link que ele mandou ANTES
   de pesquisar — uma busca no nome errado queima tempo e confunde o usuário.
2. **Ache a documentação oficial** (nesta ordem):
   - Busca: `site:<dominio> api`, `<nome> api documentação`, `<nome> api reference`
   - Docs subdomínio (docs., ajuda./help., changelog./reference.)
   - Se a doc é GitBook/Mintlify: existe **`llms.txt`** no root e toda página
     tem versão Markdown **appendando `.md`** na URL — extrai páginas inteiras
     de uma vez (web_extract), incluindo schemas OpenAPI embutidos.
   - Collections Postman públicas (documenter.getpostman.com) — mapa rápido de
     módulos/endpoints.
   - Central de ajuda/artigos (coleções "Via API", "Integrações").
3. **Mapeie a autenticação primeiro** (é o caminho crítico):
   - Protocolo (OAuth2/JWT, API key, basic), endpoint, payload, resposta
     (tokens + escopo), validade (ex.: JWT 24h + refresh_token).
   - **Pré-requisitos externos**: anote qualquer credencial que só o provedor
     emite (ex.: `application_uid` do Mainô). Sem ela, NADA funciona — vira
     pendência nº 1 e precisa ser solicitada ao provedor.
   - Alternativas de auth (ex.: header `X-Api-Key` que o cliente gera no
     painel) para desbloquear testes sem o pré-requisito.
4. **Enumere endpoints por módulo** em tabela: método, path, filtros
   relevantes (especialmente `ultima_modificacao`/datas p/ sync incremental),
   paginação (limites por página, janelas de período máx), idempotência
   (Idempotency-Key), campos deprecados (→ mapear já na forma nova).
5. **Teste com contas reais** que o usuário forneceu:
   - SÓ leitura quando as contas são de produção usadas por clientes — nunca
     alterar dados.
   - Login SaaS pode **bloquear IP de datacenter** (timeout do browser remoto,
     reCAPTCHA pesado). Se o browser remoto falhar, troque para browser com IP
     residencial (agent-browser local / Chrome do usuário, ou proxy
     residencial) — não insista no browser remoto.
   - Navegue o app logado para ver módulos, créditos/planos e a tela de
     configurações de integração (onde o cliente gera chaves).
6. **Valide o SHAPE real da resposta ANTES de codar o parse** (validado
   2026-08-06, Mainô): a doc oficial pode divergir da API real — caso real:
   doc mostra `{value: {cnpj: {...}}}` e a API responde `{cnpj: {...}}` sem o
   wrapper; envelopes variam POR MÓDULO (`/stakeholders`→`stakeholders`,
   `/produtos`→`produtos`, `/nfes`→`notas_fiscais`). Método: script com
   credenciais reais via `op read` (nunca imprimir tokens — só status HTTP,
   tamanho e KEYS do JSON) que autentica e lista 1 página de cada módulo; se
   o dump reportar `count=0` num módulo que o script direto mostra com dados
   (24KB+), é parse errado, não "sem dados". Fluxo de verificação completo em
   `kanban-orchestration` (seção worktrip de integração externa).
7. **Entregue**: relatório Markdown com fonte citada em `docs/` do repo, numa
   branch própria. Se outro agente está trabalhando no mesmo repo, use
   **`git worktree add <caminho> -b <branch> origin/main`** (diretório
   separado) — nunca branch na working copy compartilhada; commite só os
   arquivos seus, deixe alterações dos outros intocadas.

## Entregável do relatório

- Contexto do serviço + fluxo de acesso (URLs, login, ambientes)
- Mapa completo de endpoints (tabela por módulo)
- O que a API NÃO cobre (lacunas) — decide escopo do dump
- Implicações para a integração (caminho limpo vs scraping, dependências)
- Pendências como checkboxes (pré-requisitos externos, testes pendentes)

## Pitfalls

- Nome do produto errado pelo usuário → validar contra URL fornecida (passo 1).
- Docs GitBook/Mintlify sem índice navegável via web_extract → usar `llms.txt`
  + sufixo `.md` (passo 2).
- Auth com pré-requisito emitido pelo provedor → não tentar "descoberta" de
  token sem ele; registrar como pendência e seguir com o mapa de endpoints.
- Contas de produção usadas em teste → read-only; nunca POST/DELETE/PUT.
- Browser remoto sem proxy residencial → timeouts/reCAPTCHA em SaaS brasileiro
  (Mainô, Receita, etc.) não significam site fora do ar; trocar de browser.
- Commit acidental do trabalho de outro agente → worktree separado + `git add`
  seletivo.

## Verificação

- Relatório commitado e pushado na branch (nunca só descrito).
- Cada endpoint/claim do relatório rastreável a uma URL de fonte.
- Pendências listadas como checkboxes no relatório.

## References

- `references/maino-api.md` — conhecimento condensado da API Mainô (base URL,
  auth, mapa de endpoints, lacunas, contas de teste) para a integração Flowmax.
