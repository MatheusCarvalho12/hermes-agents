# Read-only Hermes architecture audit

Use this reference with the `Read-only Hermes Architecture Audit` procedure in `SKILL.md`. It records the validated audit shape from the multi-profile review; it does not authorize edits.

## Canonical inventory commands

```bash
printf 'HERMES_HOME=%s\n' "${HERMES_HOME:-$HOME/.hermes}"
COLUMNS=400 hermes profile list
COLUMNS=400 hermes skills list
COLUMNS=400 hermes -p <profile> skills list
```

`hermes skills list` is authoritative for the names shown to the loader, source/trust, and enabled/disabled status. A filesystem walk of `skills/**/SKILL.md` remains necessary to find physical duplication and frontmatter collisions. Do not calculate disabled sets from folder names alone: display names can differ from folders (for example, title-cased display names or sanitized install directories).

## Read-only evidence to collect

For the root and every directory under `profiles/`:

- absolute root path, `config.yaml` presence/parseability, and `SOUL.md` presence;
- skill counts from the CLI plus physical `SKILL.md` count;
- enabled/disabled names from the CLI, with long names preserved via `COLUMNS=400`;
- MCP names, enabled flags, command basename, argument count, and environment-key presence only;
- profile-level `AGENTS.md`, `.hermes.md`, and `CLAUDE.md` presence;
- headings/line counts and skill/trigger mention counts in `SOUL.md`.

When searching recursively, label nested repository/vendor context separately from profile context. A repository checkout under `HERMES_HOME` may contain its own `AGENTS.md` files that are not global Hermes instructions.

## Duplication and conflict checks

Hash every `SKILL.md` and group by hash across profile roots. Repeated copies are expected when profiles are isolated, but report their scale because cloning can leave every profile carrying the same broad skill set. Also group by parsed frontmatter `name` within each root:

- multiple files with the same canonical name are actionable collisions;
- same basename with divergent hashes across profiles is a drift/conflict signal;
- a CLI entry count lower than physical `SKILL.md` count usually indicates duplicate canonical frontmatter names or loader deduplication;
- folder/display mismatches should be reported as canonical-name hazards, not silently normalized.

## Secret-safe MCP inspection

Read only structural YAML fields from `config.yaml`. Report server names and `enabled` values, but redact all environment values, token/API-key values, `.env` contents, `auth.json`, and untrusted raw argument strings. It is safe to report that a secret-bearing environment key exists without printing its name or value. Never create a backup or audit output file during a read-only review.

## Trigger coverage

For each profile, compare the number of active CLI skills with the number of active skill names explicitly mentioned in `SOUL.md`. Treat a dedicated `Skills`/`Triggers` section as positive evidence, but still flag active skills with no mapping. The orchestrator profile deserves the same check: a short SOUL with no explicit trigger section is a real architecture finding even if specialized profiles have detailed trigger sections.

## Validated examples

The reviewed installation showed all gateways as `stopped`, 77 exact duplicate-content groups across roots, a duplicate canonical `grilling` name in two default skill paths, and folder/display mismatches such as `nm-pensive-test-review` → `test-review` and `design-system` → `Design System`. These are examples of findings to detect, not permanent assumptions about any future installation.