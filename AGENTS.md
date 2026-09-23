# Project workflow

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
