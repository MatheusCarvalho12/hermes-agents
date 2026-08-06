# Siscarga + hCaptcha via CDP (receita validada 2026-08-06, portal real)

Fluxo automatizado de ponta a ponta que FUNCIONOU tecnicamente no Siscarga
(prova: mTLS 6×, desafios abertos 4×, NopeCHA Recognition respondendo tiles 3×).
Único bloqueio na sessão: rate-limit do hCaptcha após ~12 tentativas no mesmo
perfil — o serviço deve usar perfil novo por tentativa.

## Setup mTLS via NSS (equivalente VPS/Linux — SEM Keychain)

- `pk12util -d "sql:<user-data-dir>" -i cert.pfx -W <pfx-pass> -K <key-pass>`
  importa o certificado no NSS DB do perfil do Chrome.
- Com o cert no NSS, **Chrome headed E headless autenticam mTLS sem dialog**
  (validado com Chrome for Testing 151 + certificado e-CPF real).
- Verificar: `certutil -L -d sql:<dir>` (nickname = friendlyName do PFX).
- Sem NSS: Chrome headed pede o cert via Keychain (1 clique do usuário);
  headless TRAVA no handshake (sem UI) — era o bloqueio antigo.

## Chrome for Testing + CDP (a base do fluxo)

- Binário: `~/.agent-browser/browsers/chrome-<ver>/.../Google Chrome for Testing`
- `--remote-debugging-port=9224 --user-data-dir=<perfil-com-NSS> --no-first-run`
- Node com WebSocket nativo (Node 21+) fala CDP direto; top-level `await` ok,
  mas: **`return` no top-level de .mjs é ilegal** (usar `await fn(); process.exit()`)
  e **`require` + top-level await conflitam** (usar `import`).

## hCaptcha: os iframes são targets OOPIF

- `Page.getFrameTree` **NÃO lista** os iframes do hCaptcha (cross-origin).
- Eles aparecem como targets `type: iframe` no `/json/list`, cada um com
  `webSocketDebuggerUrl` próprio → conectar DIRETO neles para Runtime.
- O `src` do iframe NÃO tem o hash `#frame=checkbox` (é interno) — detectar
  por DOM: frame com `#checkbox` = checkbox; frame com `.task-image` ou
  `.prompt-text` = challenge.
- `Input.dispatchMouseEvent` usa coords do VIEWPORT DA PÁGINA — somar o
  `getBoundingClientRect()` do iframe na página ao rect do elemento no iframe.

## Desafio de imagem: extrair do DOM (getcaptcha é criptografado!)

- Protocolo 2025/2026: o response do `getcaptcha` é **criptografado** (binário,
  não-JSON) — interceptar Network não adianta; o JSON só existe descriptografado
  na memória do widget (hook no JSON.parse não captura — o parse acontece em
  contexto interno e o iframe recarrega).
- Extrair do DOM do iframe challenge:
  - task: `.prompt-text` / `#task` (ex.: "Selecione todos os animais que nascem de ovos")
  - tiles: `document.querySelectorAll('.task-image')`; imagem no filho `.image`
    com style `background: url(&quot;https://imgs3.hcaptcha.com/tip/...&quot;)`
    (regex: `url\(&quot;([^&]+)&quot;\)|url\(["']?([^"')]+)["']?\)`)
  - area_select: 0 `.task-image`, 1 imagem grande (mesmo regex de url)
- Aguardar o corpo renderizar DENTRO do iframe (polling com `awaitPromise: true`
  no Runtime.evaluate, até ~15s) — o prompt aparece antes das imagens.

## NopeCHA Recognition — formato NOVO (lib 2.0.1 está desatualizada)

- Lib: `Server returned error: {'error': 10, ..., 'type': 'You are using an
  outdated format for hCaptcha...'}` → usar direto `POST /v1/recognition/hcaptcha`.
- Payload aceito (validado com o sitekey real):
  ```json
  {
    "key": "<KEY>",
    "data": {
      "request_type": "image_label_binary",
      "requester_question": {"en": "<task text>"},
      "tasklist": [
        {"task_key": "00000000-0000-0000-0000-000000000001", "datapoint_uri": "data:image/jpeg;base64,..."}
      ]
    }
  }
  ```
- **`task_key` NÃO é validado** — UUID fake sequencial funciona.
- `datapoint_uri`: base64 com prefixo `data:image/...;base64,` (baixar a URL do
  imgs3.hcaptcha.com com User-Agent e codificar).
- Resposta: POST → `{data: job_id}`; poll `GET ?id=<job>&key=<KEY>` (error 14 =
  processando). Binary → `[[false,false,false,true,...]]` (booleans = tiles a
  clicar); area_select → `[x, y]` (coords na imagem).
- Erro típico quando tasklist vazio: "tasklist must be a non-empty array".

## Clique nos tiles: real (Input), não el.click()

- `el.click()` via JS **não seleciona** os tiles (hCaptcha usa pointer events) —
  o DOM nunca marca `selected` e o submit falha ("Por favor, tente novamente").
- Usar `Input.dispatchMouseEvent` mousePressed+mouseReleased (clickCount:1) nas
  coords centrais do tile (com offset do iframe!). Verificar seleção no DOM
  (classe `selected`/`aria-checked`) antes do botão "Verificar"
  (`.button-submit`).

## Submit no Siscarga: hidden `response` OBRIGATÓRIO

- O `onSuccess` do portal copia o token do widget para o hidden
  `response` — com token injetado programaticamente (extensão ou JS) **o
  onSuccess NÃO roda** → hidden fica vazio → portal rejeita silenciosamente.
- SEMPRE: `document.getElementById('response').value = <token>` antes do submit.
- Submeter: `document.forms['ConsultarCargaConsignatarioExibirCargasForm'].submit()`
  (POST — GET nos resultados dá NullPointerException).

## Rate-limit do hCaptcha (importante para o serviço)

- Após ~10-12 tentativas no mesmo perfil/IP, o hCaptcha para de servir desafios:
  checkbox clicado, sem challenge E sem token (widget "preso").
- **Perfil novo (user-data-dir) por tentativa** + backoff; a sessão do portal
  expira — re-autenticar por rodada.

## Extensão NopeCHA (automation build) — não é bala de prata

- `build_chromium()` da lib falha (download do GitHub quebra) → manual:
  baixar `chromium_automation.zip` da release do NopeCHALLC/nopecha-extension,
  extrair, injetar `"key": "<KEY>"` no `manifest.json`, `--load-extension=<dir>`.
- A extensão resolve o checkbox em ~15s (token P1_ gerado) **mas o siteverify
  do Siscarga rejeitou o token** (igual à API) — não resolveu o submit.

## undetected-chromedriver (avaliado, descartado)

- Precisa `setuptools` (distutils sumiu no Python 3.12+): `uv pip install setuptools`.
- Driver × browser: `uc.Chrome(version_main=<ver>)` para casar (150×151 quebra).
- **O uc não expõe CDP HTTP** (a flag `--remote-debugging-port` é ignorada no
  Chrome patcheado) — impossível anexar Node/agent-browser; usar Chrome for
  Testing + CDP direto.

## Proxy residencial no Chrome — NÃO use credenciais inline

- `--proxy-server="http://user:pass@host:port"` → **`ERR_NO_SUPPORTED_PROXIES`**
  (Chrome removeu credenciais inline no --proxy-server; sem dialog em headless).
- Solução validada: **forward proxy local sem auth** com `gost`
  (github.com/ginuerzh/gost, binário único):
  ```
  /tmp/gost -L :8888 -F "http://<user>:<pass>@proxy.geonode.io:9000" &
  # Chrome aponta pro local:
  --proxy-server="http://127.0.0.1:8888"
  ```
- Validado contra o Siscarga real: saída por IP BR residencial (ex.
  200.4.118.104), mTLS via NSS funciona ATRAVÉS do proxy (CONNECT normal), e o
  challenge do hCaptcha abre por IP novo.
- **Rotação de IP = burlar o rate-limit do hCaptcha**: cada tentativa com IP
  residencial novo (GeoNode rotativo) não acumula volume por IP — o rate-limit
  de ~10-12 interações só dispara com IP fixo. É a resposta para "não tem como
  burlar?" — sim, rotação de IP via proxy residencial.
- Baixar as imagens do challenge (imgs3.hcaptcha.com) com o fetch do Node NÃO
  passa pelo proxy — quando o IP local está rate-limitado, o imgs3 bloqueia;
  baixar com `curl -s -x <proxy-local>` (variável PROXY_URL no script).

## CDP: pitfalls de conexão e navegação

- **Deadlock com Chrome recém-iniciado**: NÃO esperar no /json/list um target
  `page` com URL "receita" (o Chrome novo está em about:blank e nunca navega
  sozinho) — pegar o primeiro `type: page` e navegar.
- **`Runtime.evaluate` pendura durante handshake mTLS/navegação** (o contexto
  não existe ainda e a promise nunca resolve) — para esperar a autenticação,
  fazer **polling da URL do target via /json/list** até `carga-web` aparecer;
  só então usar Runtime.
- `Network.getResponseBody`: campo `base64Encoded` + Content-Encoding
  (gzip/brotli) — decodificar base64 e descomprimir antes de parsear.
- Network do target da PÁGINA não vê requests dos iframes OOPIF — habilitar
  `Network.enable` nos targets dos iframes também.

