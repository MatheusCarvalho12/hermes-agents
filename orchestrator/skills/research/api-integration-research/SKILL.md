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
   - Zendesk help centers (`atendimento.<empresa>.com.br/hc/...`) — artigos de
     webhook/integração ficam lá e extraem inteiros via web_extract (ex.:
     TecnoSpeed/PlugBoleto).
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
   - **Limites de janela de período só aparecem na chamada real** (Mainô,
     2026-08-06): `GET /nfes_emitidas` recusa período >90 dias com HTTP 200 +
     corpo `{"error":"Somente é possível fazer buscas de no máximo um período
     de 90 dias"}` (JSON, não ZIP) → dump reporta count=0 MUDO. Todo endpoint
     de exportação por data: testar com janela grande ANTES de implementar o
     fetcher; resposta de erro JSON no corpo = erro tipado, nunca silencioso.
   - **application_uid (ou chave de app) é vinculado à conta que o gerou**
     (Mainô, 2026-08-06): UID do IGCD + credenciais de outra conta → 401;
     UID + credenciais da conta dona → 200 multi-empresa. Ao receber contas de
     teste, pedir também o UID/chave da APLICAÇÃO vinculada a elas.
7. **Entregue**: relatório Markdown com fonte citada em `docs/` do repo, numa
   branch própria. Se outro agente está trabalhando no mesmo repo, use
   **`git worktree add <caminho> -b <branch> origin/main`** (diretório
   separado) — nunca branch na working copy compartilhada; commite só os
   arquivos seus, deixe alterações dos outros intocadas.
   - **Pedido de "só pesquisar" (usuário: "não desenvolve de cara")**: entregue
     os achados NA CONVERSA (estado atual do código, doc oficial, credenciais
     disponíveis no vault, lacunas) e AGUARDE a decisão do usuário antes de
     criar branch/relatório no repo ou tocar em código. A fase de relatório
     commitado vem depois do ok dele.

## Webhooks de provedor (padrão push, validado 2026-08-06 — PlugBoleto)

Quando a integração recebe push do provedor (webhook) em vez de só polling:
- Endpoint sem auth de sessão; validação por **header custom definido no cadastro** (ex.: `auth`), comparar com `hmac.compare_digest`; sem secret configurado → 503 fail-closed.
- **Dedupe determinístico**: `HMAC(dedupe_secret, f"{evento}|{id}")` como chave de idempotência reusando a constraint única existente (ex.: outbox) — reentrega do provedor não duplica comando.
- **Nunca processar inline**: validar → enfileirar comando/reconcile que JÁ existe na aplicação → 200 imediato (processamento assíncrono reusa retry/persistência existentes).
- **Evento desconhecido ou id órfão → 200 sem retry** (provedor faz 3 retries ~15s; 4xx/5xx vira loop de reentrega).
- Tolerar envelope documentado (`{"body": {...}}`) E payload direto — o formato real varia entre entrega inicial e retries.

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
- **TODAS as credenciais armazenadas falhando de uma vez = suspeitar da CHAVE de
  criptografia, não das credenciais** (validado 2026-08-07, Mainô/Flowmex):
  credenciais persistidas cifradas (AESGCM) podem ter sido gravadas com uma
  chave que se perdeu/rotacionou → `InvalidTag` em 100% das linhas, sync falha
  com erros genéricos (`credential_missing`/`projection_error`). Diagnóstico:
  descriptografar 1 blob com a chave atual (sem imprimir valores) ANTES de
  re-digitar nada. Correção: re-cadastrar via endpoint oficial da aplicação —
  o service autentica cada credencial no provedor e mapeia por CNPJ (resposta
  com `configured/unmatched/rejected` = validação real, zero adivinhação); se
  o ambiente roda em container, alinhar a secret do runtime à chave do vault
  e REDEPLOYAR (secret nova só vale após redeploy).
- Browser remoto sem proxy residencial → timeouts/reCAPTCHA em SaaS brasileiro
  (Mainô, Receita, etc.) não significam site fora do ar; trocar de browser.
- Commit acidental do trabalho de outro agente → worktree separado + `git add`
  seletivo.
- **Mapeamento de credencial por CNPJ é automático e reflete o acesso REAL da
  conta no provedor** (validado 2026-08-07, Mainô): o cadastro oficial
  autentica cada conta e vincula SÓ os CNPJs que o payload de autenticação
  devolve. Filial/matriz com CNPJs diferentes NÃO é bug de cadastro se a conta
  não acessa a filial — para ter certeza, autentique com as credenciais reais
  e liste as CHAVES do JSON (mascarando tokens): CNPJ ausente = conta não
  acessa (falta credencial própria da filial, não re-cadastro). Sinal de que
  FALTAM chaves no vault: `active_company_count > configured_company_count` no
  endpoint de status de credenciais.
- **Validação pós-correção de credenciais**: disparar 1 sync real por empresa
  e conferir dados novos no banco (ex.: count de notas subiu) — "cadastrado
  com sucesso" NÃO prova que o sync funciona; jobs que falhavam em segundos
  com `credential_missing`/`projection_error` devem completar com contadores
  de leitura/atualização > 0.

## Verificação

- Relatório commitado e pushado na branch (nunca só descrito).
- Cada endpoint/claim do relatório rastreável a uma URL de fonte.
- Pendências listadas como checkboxes no relatório.

## References

- `references/maino-api.md` — conhecimento condensado da API Mainô (base URL,
  auth, mapa de endpoints, lacunas, contas de teste) para a integração Flowmax.
- `references/plugboleto-api.md` — conhecimento condensado da API
  PlugBoleto/TecnoSpeed (webhooks: cadastro, payloads, retry, produção-only;
  endpoints de emissão/consulta/baixa/PDF) + contexto do fluxo Flowmex V1 +
  design do contrato de webhook (endpoint, dedupe via billing_idempotency,
  repasse de env no gateway).
