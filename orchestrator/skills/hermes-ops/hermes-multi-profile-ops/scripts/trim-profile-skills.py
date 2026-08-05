#!/usr/bin/env python3
"""Trim per-profile skill sets: disable everything except the KEEP set.

Usage (run with the app's venv python):
  ~/.hermes/hermes-agent/venv/bin/python trim-profile-skills.py <perfil> <keep-skill> [<keep-skill> ...]
  ~/.hermes/hermes-agent/venv/bin/python trim-profile-skills.py     # apply the known team distribution

Why this exists: `hermes profile create --clone` copies the FULL `skills/` dir of the
source profile (~75-90 skills). Every cloned profile needs a trim so workers only load
the skills of their role (2026-08: 327 -> 53 active across the 4 dev profiles).

Notes / pitfalls encoded:
- Reversible: skills stay on disk; only `skills.disabled` is written.
- Uses the app's own save_disabled_skills (same path as `hermes skills config`) —
  `hermes config set skills.disabled '[...]'` writes a string and silently fails.
- Disabled names MUST be the CLI's canonical DISPLAY names, not folder names:
  `Design System` (display) != `design-system` (folder); `test-review` != `nm-pensive-test-review`.
- `hermes skills list` truncates long names with "…" unless COLUMNS is wide (we force COLUMNS=400).
- Backs up the profile config.yaml before writing.
"""
import os, subprocess, sys

HERMES_AGENT = os.path.expanduser("~/.hermes/hermes-agent")
PROFILES_ROOT = os.path.expanduser("~/.hermes/profiles")
sys.path.insert(0, HERMES_AGENT)

# Distribution atual do time (validada 2026-08). Fonte da verdade: references/team-inventory.md.
KNOWN_DISTRIBUTION = {
    "frontend-developer": {
        # papel
        "accessibility", "code-review", "frontend-design", "lighthouse",
        "test-review", "performance", "r3f-animation", "react-doctor",
        "react-testing-library", "responsive-design", "scroll",
        "security-review", "sentry-react-sdk", "shadcn", "spline-interactive",
        "view-transitions", "vitest",
        # metodologia
        "spike", "systematic-debugging", "test-driven-development",
        # transversais
        "humanizer", "i-have-adhd",
    },
    "backend-developer": {
        "api-design-principles", "code-review", "fastapi", "http-api",
        "test-review", "ruff", "security-review", "sentry-fix-issues",
        "sentry-python-sdk", "sentry-sdk-setup",
        "sqlalchemy-alembic-expert-best-practices-code-review",
        "spike", "systematic-debugging", "test-driven-development",
        "humanizer", "i-have-adhd",
    },
    "database-developer": {
        "bigquery-basics", "postgres-best-practices",
        "humanizer", "i-have-adhd",
    },
    "designer": {
        "design-principles", "Design System", "design-tokens", "figma",
        "typography", "claude-design", "design-md", "popular-web-designs",
        "sketch", "humanizer", "i-have-adhd",
    },
}

def installed_names(profile: str) -> set:
    out = subprocess.run(
        ["hermes", "-p", profile, "skills", "list"],
        capture_output=True, text=True, env={**os.environ, "COLUMNS": "400"},
    ).stdout
    names = set()
    for line in out.splitlines():
        if "│" not in line:
            continue
        parts = [p.strip() for p in line.split("│")]
        if len(parts) >= 2 and parts[1] and not parts[1].startswith("Name"):
            names.add(parts[1])
    return names

def trim(profile: str, keep: set):
    home = os.path.join(PROFILES_ROOT, profile)
    if not os.path.isdir(home):
        print(f"!! perfil não encontrado: {profile}")
        return
    cfg_path = os.path.join(home, "config.yaml")
    os.system(f'cp {cfg_path} {cfg_path}.bak-$(date +%Y%m%d-%H%M%S)')
    os.environ["HERMES_HOME"] = home
    from hermes_cli.skills_config import save_disabled_skills
    from hermes_cli.config import load_config
    all_names = installed_names(profile)
    missing = keep - all_names
    if missing:
        print(f"!! {profile}: KEEP não encontrado na lista instalada: {sorted(missing)}")
        print("   (confira o display name com: COLUMNS=400 hermes -p <perfil> skills list)")
    disabled = all_names - keep
    save_disabled_skills(load_config(), disabled)
    print(f"== {profile}: {len(all_names)} instaladas -> ativas {len(keep & all_names)} | desabilitadas {len(disabled)}")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        trim(sys.argv[1], set(sys.argv[2:]))
    else:
        for profile, keep in KNOWN_DISTRIBUTION.items():
            trim(profile, keep)
