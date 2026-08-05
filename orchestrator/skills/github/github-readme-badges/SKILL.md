---
name: github-readme-badges
description: "Use when creating GitHub README badges (shields.io)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, readme, badges, shields, portfolio, markdown]
    related_skills: [github-repo-management, github-pr-workflow]
---

# GitHub README Badges & Polish

Como deixar o README de um repo com cara de portfólio profissional: badges shields.io com logo, emojis contextuais, LICENSE detectável e release "Latest" visível.

## Preferências do usuário (Matheus) — obrigatório

1. **Emoji com significado contextual, SEMPRE.** O usuário rejeitou emojis decorativos/aleatórios em títulos de seção: ❌ 🧑💻 para "O time" (cara no notebook), ❌ 🚀 para "Restaurar em outra máquina" (foguete). Correções aprovadas:
   | Seção | Emoji certo | Motivo |
   |---|---|---|
   | O time / equipe | 👥 | grupo de pessoas |
   | Restaurar / backup | 💾 | disquete = salvar/restaurar |
   | Atualizar | 🔄 | setas circulares |
   | Segurança / o que vai | 🛡️ | escudo |
   | Skills / módulos | 🧩 | peças que se encaixam |
   | Thanks / agradecimento | 🙏 | mãos em prece |
   | Licença / documento | 📜 | pergaminho |
2. **Badge com logo de tecnologia > emoji** para agentes/stacks que têm logo oficial (React, FastAPI, Postgres, Figma, Kubernetes). Emoji só onde não há logo que faça sentido.
3. **README dinâmico**: se o repo é gerado por script (ex: distributions de agentes), o README é regenerado a cada sync com badges, contadores e data — nunca editar na mão (o script sobrescreve).

## Técnica shields.io (validadas em produção)

Formato básico de badge com logo:
```
![label](https://img.shields.io/badge/-label-COR?logo=LOGO&logoColor=white)
```

### PITFALL CRÍTICO: hífen no label quebra o badge
O shields.io usa `-` como separador de segmentos. `frontend-developer` é interpretado como "texto=frontend, cor=developer" (cor inválida) → **"404: badge not found"** renderizado no README.
**Fix:** escapar hífen com `--`:
```
❌ /badge/-frontend-developer-61DAFB?logo=react   → 404 badge not found
✅ /badge/-frontend--developer-61DAFB?logo=react → renderiza "frontend-developer"
```
Em Python: `safe = label.replace("-", "--")`.

### PITFALL: logo inexistente retorna 200 mas renderiza VAZIO
`img.shields.io/badge/-t-000?logo=users` retorna HTTP 200 mesmo quando o logo não existe no Simple Icons — o badge aparece sem ícone (e alguns renderers mostram "logo not found"). **Nunca confie no status HTTP.** Verifique se o logo realmente renderiza comparando a largura do SVG (`width=15` = sem logo, `width>=33` = com logo). Script pronto: `scripts/verify-badge-logos.sh`.

Logos validados que renderizam: `react`, `fastapi`, `postgresql`, `figma`, `kubernetes`, `git`, `github`, `rocket`, `loop`, `vault`, `npm`, `githubsponsors`, `creativecommons`, `openai`, `robot`.
Logos que retornam 200 mas NÃO renderizam (evitar): `users`, `download`, `sync`, `refresh`, `shield`, `lock`, `code`, `heart`, `scales`, `database`, `layers`, `package`, `people`, `cloud`, `key`, `check`, `eye`.

### Badges de topo (estado do repo)
```
![License](https://img.shields.io/badge/license-MIT-blue)
![Release](https://img.shields.io/github/v/release/OWNER/REPO)
![Agentes](https://img.shields.io/badge/agentes-5-orange)
![Skills](https://img.shields.io/badge/skills-55-green)
```

## LICENSE (badge MIT no sidebar)

O GitHub só mostra "MIT license" no sidebar do repo se existir **arquivo `LICENSE` na raiz** — falar "MIT" no README não basta. Criar `LICENSE` com o texto MIT padrão + `Copyright (c) <ano> <Nome>`. Depois `gh api repos/OWNER/REPO/license` confirma o spdx_id.

## Releases (badge "Latest")

**Tags ≠ releases.** O sidebar só mostra "Latest" quando uma Release é publicada a partir de uma tag. Automatizar no fluxo de bump:
```bash
gh release create v1.0.5 --title "v1.0.5" --notes "$NOTAS" --repo OWNER/REPO
# se a tag já tem release (re-run): gh release edit v1.0.5 --notes "$NOTAS" --repo OWNER/REPO
```

## Verificação final

Depois do push, validar visualmente no navegador (browser_navigate + browser_vision perguntando explicitamente por "404 badge not found" / imagem quebrada) — snapshot de acessibilidade não mostra imagens quebradas; o vision sim.

## Passos recomendados

1. Montar README com badges de topo + tabela com badges de agente/stack (escapando hífen!)
2. Criar `LICENSE` na raiz se quiser badge de licença
3. Publicar Release a partir da tag mais recente
4. Push + browser_vision para conferir renderização real
5. Se o README é gerado por script, aplicar as mesmas regras no gerador (não editar o output na mão)
