# NopeCHA: biblioteca, extensão e fluxo Chrome+CDP (validado 2026-08-06, Siscarga)

## Biblioteca `nopecha` 2.0.1 (PyPI)

- `pip install nopecha` (no venv do projeto: `uv pip install --python .venv/bin/python nopecha`).
- Clientes: `nopecha.api.httpx.HTTPXAPIClient` (sync) e `AsyncHTTPXAPIClient` (async).
- **BUG do cliente async**: `solve_raw` monta `/token/?key=...&id=...` SEM o host
  → httpx falha: `Request URL is missing an 'http://' or 'https://' protocol`.
  O sync usa `f"{self.host}/token/"` (correto). **Use o sync**:
  ```python
  api = HTTPXAPIClient(KEY)
  token = await anyio.to_thread.run_sync(lambda: api.solve_hcaptcha(sitekey, url, proxy=PROXY, useragent=UA))
  # token = {'data': 'P1_...'}
  ```
- Endpoint da lib: `https://api.nopecha.com/token/` (genérico) com body
  `{key, type: "hcaptcha", sitekey, url, enterprise: false, proxy, data: {rqdata}|null, useragent}`.
  **A API ACEITA** (diferente de comentário antigo que dizia "Invalid request").
  O endpoint da doc oficial é `/v1/token/hcaptcha` (sitekey/url/proxy/cookie/
  useragent/data.rqdata) — ambos geram tokens; a aceitação pelo portal é outra história.
- Retries internos: `post_max_attempts=10` (exp throttle), `get_max_attempts=120`
  (linear, até 60s) — pior caso de polling ~30-90 min; não usar em foreground.

## Formato do campo `cookie` (developers.nopecha.com/formatting/cookie)

```json
[{"name": "JSESSIONID", "value": "...", "domain": "www4c.receita.fazenda.gov.br",
  "path": "/", "hostOnly": true, "httpOnly": true, "secure": true,
  "session": true, "expirationDate": 1234567890}]
```
- Todos os campos obrigatórios exceto `expirationDate` (só p/ cookies persistentes).
- Enviar cookies da SESSÃO real do site (JSESSIONID/LogonCert/`__cf_bm`) — o
  solver acessa a página como sessão autenticada. (No Siscarga não mudou o
  resultado, mas é o formato correto da doc.)

## Extensão NopeCHA (resolver no browser real)

- Gerar: `from nopecha.extension import build_chromium; build_chromium({"key": KEY}, outpath)`
  — baixa `chromium_automation.zip` da release `NopeCHALLC/nopecha-extension`.
  Se a lib falhar (FileNotFoundError manifest.json = download falhou), baixar
  manual: `curl -sL <browser_download_url> -o ext.zip && unzip` e injetar a key
  no campo `"key"` do `manifest.json`.
- ID da extensão (chromium): `dknlfmjaanfblgfdfebhijalfmhmjjjo`.
- **Resolve sozinho em ~15s** (widget "I am human is now checked. You are verified").
- **PITFALL CRÍTICO**: a extensão preenche `textarea[name="h-captcha-response"]`
  mas NÃO roda o `onSuccess` da página → o hidden `response` do form fica vazio
  → submit rejeitado. Copiar antes de submeter:
  ```js
  document.getElementById('response').value = document.querySelector('textarea[name="h-captcha-response"]').value
  ```
  (O clique humano passa porque o onSuccess roda; a extensão não.)

## Chrome + extensão + CDP (portável para VPS Linux)

```bash
# Mac (mTLS via Keychain do sistema — headed OK; headless TRAVA no handshake)
"/path/Google Chrome for Testing" --remote-debugging-port=9222 \
  --user-data-dir=/tmp/perfil --load-extension=/tmp/ext --no-first-run

# Linux VPS: importar o PFX no NSS do Chrome antes (certutil -A / pkcs12)
# e rodar --headless=new (extensões suportadas desde Chrome 109)
```
- Conectar: `agent-browser --cdp 9222 open <url>` (fill/click/snapshot com @refs).
- JS via WebSocket CDP (Node 21+ tem WebSocket nativo):
  ```js
  const targets = await (await fetch('http://localhost:9222/json/list')).json();
  const page = targets.find(t => t.type === 'page' && t.url.includes('alvo'));
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  // Runtime.evaluate com returnByValue:true para ler/setar valores e submeter
  ```
- Botões de imagem (JSP antigo): `img[onclick*="submit()"]` = enviar,
  `img[onclick*="limpar"]` = limpar — identificar via
  `[...document.querySelectorAll('img')].map(i => i.getAttribute('onclick'))`.

## Créditos (2026)
- hCaptcha token = 10 créditos; recognition = 1. Jobs que não completam gastam
  crédito mesmo assim. `/v1/status` mostra credit/quota/plan.
- Plano Professional do usuário: quota 80.000/ciclo.
