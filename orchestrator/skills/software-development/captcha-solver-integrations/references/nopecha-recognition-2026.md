# NopeCHA Recognition — formato NOVO 2026 (hCaptcha desafio de imagem)

A biblioteca `nopecha` (2.0.1 e main) está **desatualizada** para recognition:
`Server returned error: {'error': 10, ..., 'type': 'You are using an outdated
format for hCaptcha. Please refer to the API documentation (nopecha.com/api-reference/#postHcaptcha)'}`.
Usar a API direto, formato abaixo (validado 2026-08-06 contra o Siscarga real).

## Endpoint e payload

`POST https://api.nopecha.com/v1/recognition/hcaptcha` — Auth: header
`Authorization: Basic <key>` e/ou `key` no body.

```json
{
  "key": "<API_KEY>",
  "data": {
    "request_type": "image_label_binary",
    "requester_question": { "en": "<texto da task>" },
    "tasklist": [
      { "task_key": "00000000-0000-0000-0000-000000000001",
        "datapoint_uri": "data:image/jpeg;base64,<...>" }
    ]
  }
}
```

- `request_type` válidos: `image_label_binary` (9 tiles, clicar nos que batem),
  `image_label_area_select` (1 imagem, clicar numa área/objeto),
  `image_drag_drop` (com `entities`).
- **`task_key` NÃO é validado** — UUID fake sequencial funciona (testado).
- `datapoint_uri`: base64 com prefixo `data:image/...;base64,`. Se a fonte for
  URL (ex. `https://imgs3.hcaptcha.com/tip/<hash>/<hash>`), baixar com
  User-Agent de browser e codificar.
- `requester_question.en` pode ir em PT (o texto da task como está no widget).

## Resposta

- POST → `{ "data": "<job_id>" }`
- Poll: `GET /v1/recognition/hcaptcha?id=<job>&key=<KEY>` a cada ~1s;
  `error: 14` = processando.
- Binary → `[[false,false,false,true,false,false,false,false,true]]` — booleans,
  `true` = tile a clicar (índice = posição no DOM `.task-image`).
- Area select → `[x, y]` — coords em pixels sobre a imagem.
- Erro comum: `tasklist must be a non-empty array` (payload vazio).

## Bugs da biblioteca (2.0.1 / main)

- **Async**: `AsyncHTTPXAPIClient` monta GET com URL relativa (`/token/?key=...`)
  → httpx "missing protocol" — usar o cliente SYNC (`HTTPXAPIClient`/`RequestsAPIClient`).
- `build_chromium()` falha com FileNotFoundError manifest.json (o download da
  release do GitHub quebra) → fazer manual: baixar `chromium_automation.zip` da
  release de `NopeCHALLC/nopecha-extension`, extrair, injetar `"key": "<KEY>"`
  no `manifest.json`, carregar com `--load-extension=<dir>`.
- A extensão automation resolve o checkbox (~15s) mas o token gerado é do
  backend do NopeCHA — se o siteverify do portal rejeita os tokens da API,
  rejeita os da extensão também (não é contorno).

## Desafio varia por sessão — detectar antes de resolver

hCaptcha serve tipos diferentes por sessão (classic checkbox, binary,
area_select, enterprise). Passos:
1. Clicar no checkbox (`#checkbox` no iframe).
2. Aguardar ~3s: se abriu iframe com `.task-image`/`.prompt-text` → desafio de
   imagem → extrair task + imagens do DOM → Recognition.
3. Se o checkbox passou direto → token no `textarea[name="h-captcha-response"]`.

## getcaptcha (2025/2026) é criptografado — não perder tempo interceptando

O response de `api.hcaptcha.com/getcaptcha/<sitekey>` é binário/criptografado
(não-JSON); o JSON do challenge só existe descriptografado na memória do widget
(iframe recarrega ao abrir o desafio, então hook no JSON.parse não captura).
Extrair do DOM: `.prompt-text`/`#task` (task) e `.task-image > .image` com
`background: url(&quot;https://imgs3.hcaptcha.com/...&quot;)`.

## Rate-limit

Após ~10-12 tentativas no mesmo perfil/IP, o hCaptcha para de servir desafios
(checkbox clicado, sem challenge e sem token). Usar perfil de browser novo por
tentativa + backoff. Libera sozinho em ~30-60min (não é bug do fluxo).

## Clicar nos tiles — cliques REAIS com offset do iframe (crítico)

`el.click()` via JS **NÃO seleciona** os tiles (o hCaptcha usa pointer events).
Usar `Input.dispatchMouseEvent` (mousePressed + mouseReleased, button left,
clickCount 1) nas coordenadas = centro do tile **no iframe** + offset do iframe
**na página principal** (`getBoundingClientRect` do iframe). Sem o offset os
cliques vão para o canto da janela (0 selecionados no DOM). Verificar seleção:
`className` contém `selected` ou `aria-checked="true"`.

## CDP: iframes do hCaptcha são targets separados

`Page.getFrameTree` **NÃO lista** iframes cross-origin (Chrome 151) — os iframes
do hCaptcha aparecem como `type=iframe` em `/json/list` com
`webSocketDebuggerUrl` próprio. Conectar direto neles para ler o DOM do
challenge e clicar. Detectar o checkbox por DOM (`!!document.querySelector('#checkbox')`),
não por `frame=checkbox` no src (o hash não fica no src).

## Submit — copiar token para o hidden `response`

Com automação o `onSuccess` do portal NÃO roda (o widget recebe o token mas o
callback que copia para o hidden não dispara). O form envia BOTH:
`response` (hidden, vazio se não copiar) e `h-captcha-response` (textarea).
Se o servidor valida o hidden → rejeita. Copiar manualmente:
`document.getElementById('response').value = <token>` antes do submit.

## Widget degrada na mesma sessão

Depois de 2-3 desafios abertos/falhos no mesmo perfil, o widget entra em
"Por favor, tente novamente" e não recupera — reiniciar com perfil novo em vez
de tentar reusar a sessão.
