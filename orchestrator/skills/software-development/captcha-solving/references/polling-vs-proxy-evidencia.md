# Evidência final: polling sozinho NÃO é confiável — proxy residencial BR é requisito (2026-08-06)

Corrige/qualifica a regra de ouro do SKILL.md: o primeiro sucesso com polling longo foi uma
exceção; a repetição provou que sem proxy o solve pode nunca completar.

## Sequência empírica (portal Siscarga real, NopeCHA Professional, certificado real)

| Config | Resultado |
|---|---|
| `NOPECHA_MAX_POLLS=150` (2.5 min/tentativa), sem proxy | `captcha_failed` em 800s (3 tentativas esgotadas) |
| `NOPECHA_MAX_POLLS=600` (10 min/tentativa), sem proxy | Completou UMA vez (~7 min; 0 registros legítimos) |
| `NOPECHA_MAX_POLLS=600` × 3 tentativas (~40 min), sem proxy | **`captcha_failed` de novo** — solve ficou `processing` para sempre |
| `NOPECHA_MAX_POLLS=600` + proxy residencial BR (GeoNode `-country-br`) | Completou em minutos, **2 CNPJs seguidos** (0 registros legítimos) |

## Conclusão operacional
1. Polling maior é NECESSÁRIO (remove falsos `captcha_failed` por janela curta) mas NÃO SUFICIENTE.
2. Sem proxy, o resultado é loteria: uma hora completa, na seguinte 40 min de espera + falha.
3. Proxy residencial BR = consistência. Tratar como requisito de produção, não acelerador.
4. Ordem de debug: polling → proxy → só então suspeitar do portal/parser.
