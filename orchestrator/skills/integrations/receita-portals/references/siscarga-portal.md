# Siscarga — detalhes da sessão de validação (2026-08-06)

## Credenciais de teste (flowmex, ambiente local)

- Certificado: `~/Downloads/Certificado Francisco Moises - (chico@2026) Venc. 16-07-2027.pfx`
  - Senha: `chico@2026` (vem no nome do arquivo)
  - e-CPF A1 de FRANCISCO MOISES DE OLIVEIRA:36037974349, issuer AC Certisign RFB G5
  - CNPJ na OU: `00250354000194`; válido até 16/07/2027
- NopeCHA: plano Professional, key `sub_...` (formato aceito; ~79k créditos de 80k)
- GeoNode: username `geonode_...` + password UUID — o PAR serve para API/MCP e proxy
- CNPJs de teste: 46972197000121, 46972197000202, 63478683000107

## Fluxo E2E validado (gateway HTTP + NopeCHA + proxy BR)

1. `cert_files(pfx, senha)` → tempdir 0700 com PEMs → `ssl` context → `httpx.AsyncClient(verify=tls_context, follow_redirects=True)`
2. `GET LogonCertificado.jsp?ind=11` → `GET certificado.LogonCertificado?ind=11` (Referer) → URL final contém `/carga-web` = auth OK
3. `GET ConsultarCargaConsignatarioMenu.do` (Referer do servlet) → extrair sitekey (regex `data-sitekey`) e rqdata (`data-rqdata`, hCaptcha enterprise)
4. NopeCHA: `POST /v1/token/hcaptcha` com `{key, sitekey, url, useragent, cookie(hCaptcha-only), proxy}` → job id → poll `GET ?id&key` (409/error 14 = processando)
5. `POST ConsultarCargaConsignatarioExibirCargas.do` com form completo:
   `dtInicial=MM/AAAA, dtFinal=MM/AAAA, cnpjCpf, crgOrdem=on, response=token, consignatario=S, origem=e1, check=on, status=1, h-captcha-response=token`
6. Parse: "Nenhum registro encontrado" → []; senão tabela com links `ConsultarDadosBasicosCEMercante.do?nrCE=...`

## Medições reais (sem proxy vs com proxy)

- `NOPECHA_MAX_POLLS=150` sem proxy: 3 tentativas × ~4.4 min = **800s → captcha_failed**
- `NOPECHA_MAX_POLLS=600` sem proxy: 1º probe completou em ~7 min (0 registros); E2E seguinte **não completou em 3×10 min** (variabilidade)
- Com proxy BR (GeoNode `-country-br`): CNPJ 1 e 2 completaram em poucos minutos (0 registros — resposta legítima do portal)
- Conclusão: polling 600 é necessário, proxy BR é o que torna o solve confiável/rápido

## Descobertas do formulário (v5.1.0, 10/03/26)

- Rótulo real: "Período de Emissão do Conhecimento (mm/aaaa)" — o período é do CONHECIMENTO, não da carga
- Checkbox "ou Carga à ordem" (campo `crgOrdem`?)
- Campos hidden/checkbox que o adapter original não enviava: `crgOrdem`, `check`, `status=1`
- O parser original nunca preenchia situacao/data/hora/embarcacao do SiscargaRecord (colunas posicionais relativas ao link CE; página de detalhe tem os dados completos)
- Páginas de detalhe (campos "visuais" que o usuário quer): CE (ConsultarDadosBasicosCEMercante.do), manifesto, escala — pesos, volumes, consignatário, embarcação, portos, datas

## Browser visual

- `agent-browser --headed open <url>` autentica com o cert do Keychain do sistema (o usuário pode resolver o hCaptcha manualmente na janela; clique programático no checkbox é rejeitado — ref muda/re-renderiza)
- `agent-browser --auto-connect` falha se o Chrome do usuário não tem `--remote-debugging-port`
- Browser remoto (browser_use/Browserbase): 403 Forbidden (sem mTLS)
- Após o usuário resolver o captcha: clicar no botão "enviar" (imagem onclick, não botão `<button>`)

## Alembic: rollback silencioso em env.py (lição de 2026-08-06)

Sintoma: `alembic upgrade head` imprime "Running upgrade" para todas as migrations, exit 0, mas o banco fica vazio (schemas não existem) e `alembic current` não mostra revisão.

Causa: `version_table_schema="runtime"` + migration base que cria o schema → o alembic cria a version table antes do schema existir → `InvalidSchemaNameError` em banco limpo. Fix do worker adicionou `await connection.execute(CREATE SCHEMA ...)` no env.py, MAS o execute abre **transação implícita** no SQLAlchemy; o alembic roda dentro dela e não commita (transação "externa"); ao sair do `async with connectable.connect()`, tudo faz ROLLBACK.

Fix correto: `await connection.commit()` após o CREATE SCHEMA (validação: drop schemas → upgrade head → schemas persistem → pytest verde).

Diagnóstico que funcionou: comparar o DSN real usado (asyncpg direto lista schemas) vs o que o alembic diz que fez; verificar `alembic current`; reproduzir o env.py num script isolado com/sem commit.
