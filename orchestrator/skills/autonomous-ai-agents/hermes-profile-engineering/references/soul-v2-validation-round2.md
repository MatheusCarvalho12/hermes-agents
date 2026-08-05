# Validação SOUL v2 — rodada 2 (task GRANDE, 2026-08-05)

Resultado real da 2ª rodada de validação do SOUL v2 + kit curado, com a demanda
do tamanho que o usuário realmente pede (correção dele: "minhas tasks não vão ser
uma coisa pequena assim").

## Setup testado
- Perfil: frontend-developer, SOUL v2 (45 linhas, inglês, com Scope Discipline).
- Kit: 23 skills ativas (21 do kit + humanizer reposto + i-have-adhd); opt-out --remove.
- Task: `t_b6e8e378` "GRANDE: refatorar dashboard Mega Logística 360 (visual+performance, mantém negócio)".
- Contrato: `docs/design-system-dashboard.md` (414 linhas, spec do designer, commitada separadamente).

## O que funcionou (confirmado)
1. **Gatilho por description em task grande**: worker carregou 14 skills e usou de verdade
   (frontend-design, accessibility, shadcn, vitest, react-testing-library, playwright,
   performance, lighthouse, responsive-design, nm-pensive-test-review, react-doctor, code-review,
   security-review, humanizer). SOUL mínimo bastou — sem tabela de 30 gatilhos.
2. **Spec do designer como contrato**: entregou lazy loading dos panels, tokens Inter/JetBrains + `.num`,
   View Transition no toggle, dark sem box-shadow, sem hardcode hex, componentes novos
   (DataTable, badge, card, table, tooltip). Validado contra os critérios de aceite da seção 8 da spec.
3. **Aproveitou trabalho parcial de run anterior** (stash `wip: partial dashboard refactor`):
   encontrou, validou (build/lint), e integrou como baseline em vez de refazer do zero.

## O que falhou (processo — mesmo padrão da rodada 1)
- **Protocol violation de novo**: worker fez a refatoração INTEIRA (29 arquivos, +1707/-490) mas:
  (a) só commitou o StatusBadge; (b) deixou 19 arquivos não commitados no working tree;
  (c) não chamou `kanban_complete` → blocked após 4 runs.
- Summary não veio completo — a prova teve que ser o diff + build/testes re-rodados pelo orquestrador.
- Recovery completo (validado): verificar build/testes/tsc → validar diff contra critérios de aceite
  da spec (grep hardcode hex, startViewTransition, fontes) → commitar o trabalho órfão em nome do worker
  (com .gitignore para test-results/assets de mockup) → kanban comment + complete.
- **Conclusão**: 2ª ocorrência consecutiva de "entrega bem mas não fecha o protocolo" — é padrão de
  processo do worker, não de qualidade. Próxima iteração: reforço mais agressivo do fechamento
  (SOUL/body) e reportar ao usuário como problema de processo.

## Tempo
- Task grande: ~22 min de trabalho real (4 runs, o último 1383s). Aceitável para a escala,
  mas o tempo de recuperação manual do orquestrador (validar + commitar + fechar) soma ~5-10 min.

## Lições para a próxima rodada
1. Body de task grande deve repetir o contrato (paths da spec) e exigir "skills no summary" + "kanban_complete".
2. Verificação pré-commit do orquestrador em task com spec: validar os CRITÉRIOS DE ACEITE, não só build/testes.
3. `git status --short` pós-run é o detector de escopo vazado e de trabalho órfão.
4. **Validar entrega visual por SCREENSHOT, não só por testes**: para mostrar ao usuário um componente
   React entregue, montar uma página demo standalone (`badge-demo.html` + `.tsx` na raiz do front, com
   `<script type="module">` e `import "./src/index.css"`) e servir via `vite --port <livre>` — o CSS do
   projeto NÃO entra sozinho numa página standalone (sem o import, os badges renderizam como texto puro;
   o `browser_snapshot` acessível também não mostra pills — usar `browser_vision` para confirmar a renderização
   visual). Remover a demo depois (não commitar) e derrubar o vite (regra do usuário: nada de processo sobrando).
   Para preview interativo do usuário: `open_preview(url="http://localhost:<porta>/badge-demo.html")`.
