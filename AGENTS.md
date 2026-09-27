# Project workflow

## Agent roles and task boundaries

- Start with [architecture](docs/ARCHITECTURE.md) for current code paths and
  commands; [documentation lookup](docs/README.md) routes to topic guides.
- Read [agent roles](docs/AGENT_ROLES.md) and the
  [task board](docs/AGENT_TASKS.md) before starting work or editing files.
- Read the [shared memory skill](docs/agents/SKILL.md) at task startup; search
  log headings and read only entries relevant to the task. Record important
  findings before they are forgotten and a short handoff when finished.
- Use the [context lookup](docs/agents/CONTEXT_INDEX.md) for inactive knowledge;
  read only relevant topic notes and verify their dated branch/source context.
- Write only your own agent log. All agents may improve the common `SKILL.md`,
  coordinating edits. Follow its rules for keeping notes and disposable local
  artifacts concise and clean.
- Follow the role assigned by the user or Lead / Architect. Do not assume all
  four roles or start unrelated backlog work. Without an assigned task, limit
  work to read-only orientation and report that an assignment is needed.
- Before edits, agree on the task owner, allowed files, acceptance criteria,
  and validation. The Lead coordinates assignments and overlapping files.
- Skills describe capabilities, not additional authority. Report out-of-scope
  issues for assignment instead of fixing them opportunistically.
- Work only in climate2. Use the repository-local Meow-5 Git identity; never
  change global Git identity or touch another repository.

## Record new ideas before implementation

- Before changing code for a newly proposed feature, optimization, architectural
  direction, or behavior, record the idea in a tracked Markdown file.
- Product and implementation ideas belong in `docs/NEXT_REQUIREMENTS.md`.
  Publication and repository-policy changes belong in
  `docs/PROJECT_DIRECTION.md`.
- Record the problem, desired behavior, important constraints, and whether the
  idea is planned or implemented.
- The Markdown update must happen before the first implementation edit for that
  idea. Do not backfill the record only after the code is complete.
- Do not edit `docs/REFACTOR.md`; it remains the fixed source plan.

## Cite every external resource

- Whenever a change adds or uses an external package, API, webpage, dataset,
  image, icon, font, code sample, media file, service, or other third-party
  resource, cite it in both `README.md` and `templates/references.html` in the
  same change.
- Prefer the original provider or canonical project page. State what the
  resource contributes and include its licence or required attribution when
  available.
- Do not ship a new external resource with unknown ownership or unclear reuse
  terms. If an inherited resource has incomplete provenance, label that
  limitation honestly until it can be replaced or fully attributed.

## Protect secrets and private data

- Never stage, commit, or push `.env` files, credentials, passwords, API or
  authentication tokens, private keys, populated databases, session data,
  personal account data, or machine-specific configuration.
- Keep sensitive values in ignored local files or environment variables. Only
  clearly fake, non-functional placeholders may appear in example files.
- Before every commit and push, inspect the staged file list and scan staged
  content for likely secrets. `.gitignore` is only a backstop and does not make
  an already tracked or staged secret safe.
- If sensitive material is found, stop without printing its value, remove it
  from the change, and tell the owner that the credential may need revocation
  or rotation before any GitHub publication.
