#!/usr/bin/env python3
"""
Sync Hermes Agents → GitHub (hermes-agents distribution repo).

Roda automaticamente (cron ou manual):
1. Re-monta as distributions dos 5 perfis (SOUL, config sanitizado, skills ativas, plugins)
2. Sanitiza configs (remove chaves MCP reais)
3. Regenera README.md com o estado real dos agentes
4. Bump versão (patch) nos distribution.yaml se algo mudou
5. Commit + push (tag v<versão> se bump)
6. Sem mudanças = silencioso (watchdog pattern)

Uso: python3 sync-hermes-agents.py [--check]   (--check = só reporta se tem mudança, NÃO muta)
"""
import os, re, shutil, subprocess, sys, datetime

BASE = os.path.expanduser("~/.hermes")
REPO = "/Users/amaterei/dev/hermes-agents"
PROFILES = ["frontend-developer", "backend-developer", "database-developer", "designer", "default"]
LABEL = {"default": "orchestrator"}

def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def get_active_skills(profile):
    """Lista skills ativas NÃO-builtin via CLI. Parse por índice fixo:
    cells = ['', name, category, source, trust, status, ''] — len>=7.
    Separador é │ (U+2502), NÃO ┃. Não filtrar células vazias (categoria vazia colapsa p/ 4)."""
    cmd = ["hermes"]
    if profile != "default":
        cmd += ["-p", profile]
    cmd += ["skills", "list", "--enabled-only"]
    out = sh(cmd, env=dict(os.environ, COLUMNS="400"), timeout=120).stdout
    active = []
    for line in out.split("\n"):
        if "\u2502" in line and "Name" not in line and "\u2501" not in line:
            cells = [c.strip() for c in line.split("\u2502")]
            if len(cells) >= 7:
                name, source, status = cells[1], cells[3], cells[5]
                if status == "enabled" and source != "builtin":
                    active.append(name)
    return sorted(active)

def find_skill_dir(root, display_name):
    """Procura a pasta da skill em QUALQUER profundidade (categorias contam)."""
    direct = os.path.join(root, display_name)
    if os.path.exists(os.path.join(direct, "SKILL.md")):
        return direct
    for dirpath, dirnames, filenames in os.walk(root):
        if "SKILL.md" in filenames:
            try:
                with open(os.path.join(dirpath, "SKILL.md"), encoding="utf-8", errors="ignore") as f:
                    head = f.read(2000)
                m = re.search(r"^name:\s*(.+)$", head, re.M)
                if m and m.group(1).strip() == display_name:
                    return dirpath
            except Exception:
                pass
    return None

SECRET_RE = re.compile(r"(sk-[A-Za-z0-9_\-]{8,}|ctx7sk-[A-Za-z0-9_\-]{8,}|ghp_[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_\-]{20,}|AKIA[A-Z0-9]{16,}|xox[baprs]-[A-Za-z0-9\-]{10,})")

def sanitize(text):
    return SECRET_RE.sub("<SUA_CHAVE_AQUI>", text)

AGENT_META = {
    "orchestrator": {"emoji": "\U0001f39b\ufe0f", "papel": "Orquestrador — gerencia o time via Kanban, decide quem faz o quê, delega e administra o Hermes."},
    "frontend-developer": {"emoji": "\U0001f3a8", "papel": "Frontend — React, shadcn/ui, performance/Lighthouse, a11y e UI pt-BR humanizada."},
    "backend-developer": {"emoji": "\u2699\ufe0f", "papel": "Backend — FastAPI, SQLAlchemy/Alembic, pytest, APIs REST e segurança."},
    "database-developer": {"emoji": "\U0001f5c4\ufe0f", "papel": "Database — Postgres, SQL, modelagem, migrações e otimização."},
    "designer": {"emoji": "\U0001f3af", "papel": "Designer — design system, branding, tokens, Figma e direção visual."},
}

def build():
    skills_by_profile = {}
    for p in PROFILES:
        label = LABEL.get(p, p)
        src_root = BASE if p == "default" else os.path.join(BASE, "profiles", p)
        dst = os.path.join(REPO, label)
        os.makedirs(dst, exist_ok=True)

        for f in ["SOUL.md", "profile.yaml", "mcp.json"]:
            s = os.path.join(src_root, f)
            if os.path.exists(s):
                shutil.copy2(s, os.path.join(dst, f))

        s = os.path.join(src_root, "config.yaml")
        if os.path.exists(s):
            with open(s) as fh:
                raw = fh.read()
            with open(os.path.join(dst, "config.yaml"), "w") as fh:
                fh.write(sanitize(raw))

        # skills ativas (não-builtin), qualquer profundidade
        dst_skills = os.path.join(dst, "skills")
        if os.path.isdir(dst_skills):
            shutil.rmtree(dst_skills)
        os.makedirs(dst_skills, exist_ok=True)
        active = get_active_skills(p)
        skills_by_profile[label] = active
        src_skills = os.path.join(src_root, "skills")
        for name in active:
            d = find_skill_dir(src_skills, name)
            if d:
                rel = os.path.relpath(d, src_skills)
                dd = os.path.join(dst_skills, rel)
                os.makedirs(os.path.dirname(dd), exist_ok=True)
                shutil.copytree(d, dd, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))

        # plugins
        sp = os.path.join(src_root, "plugins")
        dp = os.path.join(dst, "plugins")
        if os.path.isdir(dp):
            shutil.rmtree(dp)
        if os.path.isdir(sp) and os.listdir(sp):
            shutil.copytree(sp, dp, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

        # cron jobs (sem lock/db/output)
        sc = os.path.join(src_root, "cron")
        dc = os.path.join(dst, "cron")
        if os.path.isdir(dc):
            shutil.rmtree(dc)
        if os.path.isdir(sc):
            jobs = [x for x in os.listdir(sc) if not x.startswith(".") and x not in ("output", "executions.db", "ticker_heartbeat", "ticker_last_success") and os.path.isfile(os.path.join(sc, x))]
            if jobs:
                os.makedirs(dc, exist_ok=True)
                for j in jobs:
                    shutil.copy2(os.path.join(sc, j), os.path.join(dc, j))
    return skills_by_profile

def bump_versions():
    changed = False
    for label in AGENT_META:
        p = os.path.join(REPO, label, "distribution.yaml")
        if not os.path.exists(p):
            continue
        with open(p) as f:
            txt = f.read()
        m = re.search(r"^version:\s*(\d+)\.(\d+)\.(\d+)\s*$", txt, re.M)
        if not m:
            continue
        v = f"{m.group(1)}.{m.group(2)}.{int(m.group(3)) + 1}"
        txt2 = re.sub(r"^version:\s*.*$", f"version: {v}", txt, count=1, flags=re.M)
        if txt2 != txt:
            with open(p, "w") as f:
                f.write(txt2)
            changed = True
    return changed

def gen_readme(skills_by_profile):
    today = datetime.date.today().strftime("%d/%m/%Y")
    total = sum(len(v) for v in skills_by_profile.values())
    lines = []
    lines.append("# \U0001f916 Hermes Agents — Time Multi-Perfil")
    lines.append("")
    lines.append("> Distribuições oficiais dos meus agentes [Hermes](https://hermes-agent.nousresearch.com) (Nous Research) — restauração em qualquer máquina com um comando.")
    lines.append(">")
    lines.append("> **Backup de configuração** — nunca contém memórias, sessões, `.env`, `auth.json` nem chaves de API (o installer do Hermes exclui isso por design).")
    lines.append("")
    lines.append("## \U0001f9d1\u200d\U0001f4bb O time")
    lines.append("")
    lines.append("| | Agente | Papel | Skills ativas |")
    lines.append("|---|---|---|---|")
    for label, meta in AGENT_META.items():
        n = len(skills_by_profile.get(label, []))
        lines.append(f"| {meta['emoji']} | `{label}` | {meta['papel']} | {n} |")
    lines.append("")
    lines.append(f"*Última atualização: {today} — {len(AGENT_META)} agentes, {total} skills ativas no total.*")
    lines.append("")
    lines.append("## \U0001f680 Restaurar em outra máquina")
    lines.append("")
    lines.append("```bash")
    lines.append("git clone https://github.com/MatheusCarvalho12/hermes-agents.git")
    lines.append("cd hermes-agents")
    lines.append("hermes profile install ./orchestrator --alias")
    lines.append("hermes profile install ./frontend-developer --alias")
    lines.append("hermes profile install ./backend-developer --alias")
    lines.append("hermes profile install ./database-developer --alias")
    lines.append("hermes profile install ./designer --alias")
    lines.append("```")
    lines.append("")
    lines.append("Suas memórias/sessões nascem vazias por design; chaves de API você preenche no `.env` de cada perfil (o installer gera `.env.EXAMPLE`).")
    lines.append("")
    lines.append("## \U0001f504 Atualizar (sem perder dados)")
    lines.append("")
    lines.append("```bash")
    lines.append("git pull")
    lines.append("hermes profile update orchestrator frontend-developer backend-developer database-developer designer")
    lines.append("```")
    lines.append("")
    lines.append("## \U0001f6e1\ufe0f O que vai / o que não vai")
    lines.append("")
    lines.append("**Incluído:** `SOUL.md`, `config.yaml` (sanitizado), `skills/` ativas, `plugins/`, `cron/`, `mcp.json`.")
    lines.append("")
    lines.append("**Excluído SEMPRE:** `.env`, `auth.json`, `memories/`, `sessions/`, `logs/`, `state.db*`, caches — garantido pelo `.gitignore` + installer nos dois lados.")
    lines.append("")
    lines.append("## \U0001f4e6 Skills por agente")
    lines.append("")
    for label, meta in AGENT_META.items():
        skills = skills_by_profile.get(label, [])
        lines.append(f"### {meta['emoji']} {label}")
        lines.append("")
        if skills:
            lines.append(" | ".join([f"`{s}`" for s in skills]))
        else:
            lines.append("_(sem skills de hub — só builtin)_")
        lines.append("")
    lines.append("## \U0001f4dc Licença")
    lines.append("")
    lines.append("MIT — uso pessoal/estudo. Feito com [Hermes Agent](https://github.com/NousResearch/hermes-agent).")
    lines.append("")
    with open(os.path.join(REPO, "README.md"), "w") as f:
        f.write("\n".join(lines))

def main():
    check_only = "--check" in sys.argv
    os.chdir(REPO)

    skills = build()

    status = sh(["git", "status", "--porcelain"]).stdout.strip()
    if status and not check_only:
        bump_versions()
        gen_readme(skills)
        if not os.path.exists(os.path.join(REPO, ".gitignore")):
            with open(os.path.join(REPO, ".gitignore"), "w") as f:
                f.write(".env\n.env.*\nauth.json\nmemories/\nsessions/\nlogs/\nstate.db*\ncache/\n__pycache__/\n*.pyc\n.DS_Store\n")
    else:
        gen_readme(skills)

    after = sh(["git", "status", "--porcelain"]).stdout.strip()
    if check_only:
        print("MUDANÇAS" if after else "LIMPO")
        return 0
    if not after:
        print("sync: sem mudanças")
        return 0

    sh(["git", "add", "-A"])
    c = sh(["git", "commit", "-m", "chore: sync agent distributions + README"])
    if c.returncode != 0:
        print(f"sync: commit falhou: {c.stderr[:200]}")
        return 1
    tag = None
    try:
        import yaml
        with open(os.path.join(REPO, "orchestrator", "distribution.yaml")) as f:
            tag = "v" + yaml.safe_load(f)["version"]
    except Exception:
        pass
    p = sh(["git", "push", "origin", "main"])
    if p.returncode != 0:
        print(f"sync: push falhou: {p.stderr[:300]}")
        return 1
    if tag:
        sh(["git", "tag", tag])
        sh(["git", "push", "origin", tag])
    print(f"sync: pushed ({tag or 'sem tag'})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
