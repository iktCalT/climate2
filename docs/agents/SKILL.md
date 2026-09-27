---
name: climate2-agent-memory
description: Coordinate climate2 agent memory at task startup, checkpoints, and handoff through relevant logs and concise shared lessons.
---

# Shared agent memory

All agents read this file at task startup. Follow [roles](../AGENT_ROLES.md)
and [assignments](../AGENT_TASKS.md); this folder supplements them.

## Read only what helps

- Use the [context lookup](CONTEXT_INDEX.md) to find important but inactive
  knowledge; load only the relevant topic note and check its source/revision.
- Search log headings for the task ID, topic, or affected file, for example:
  `rg -n '^## .*map' docs/agents/*-log.md`. Read matching entries and explicitly
  linked dependencies; skip unrelated entries. Broaden the search if needed.
- Check the entry's date and branch/revision against current code. Logs are
  handoff evidence, not proof that another checkout contains the same changes.

## Ownership

- Agent 1, Lead / Architect: [lead-log.md](lead-log.md).
- Agent 2, Backend Developer: [backend-log.md](backend-log.md).
- Agent 3, Test / QA: [qa-log.md](qa-log.md).
- Agent 4, Reviewer / Debugger: [reviewer-log.md](reviewer-log.md).
- Everyone may read relevant logs; only the named owner writes or prunes their
  log. Report corrections in your own log and notify the owner; do not rewrite
  their account. The Lead's one-time creation of empty logs is setup only.
- Everyone may improve this `SKILL.md` without a separate task. Coordinate one
  writer at a time, reread before editing, and preserve others' changes. Keep
  reusable lessons here and task results in logs; do not broaden project scope.

## Remember and hand off

- Write down important decisions, evidence, blockers, and next steps as soon as
  they matter, especially before a pause or context reset. Do not rely on chat
  memory. Move lasting product/policy decisions to the existing requirements
  documents and link them; leave `docs/REFACTOR.md` unchanged.
- On completion, add or finalize a newest-first entry in your own log, usually
  at most 120 words. Include useful commands/results, not full output or chat.
  Use this format (a checkpoint may use `in progress` or `blocked`):

```markdown
## YYYY-MM-DD | TASK-ID | topic / affected files | done
- Result: what changed or was learned; branch/revision when relevant.
- Check: command and result, or not run and why.
- Next: blocker, next owner/action, or none; link durable decisions.
```

## Keep the space small

- Retain unresolved issues and current handoffs. Once resolved, condense your
  old entries; aim for the latest five completed tasks. Preserve lasting facts
  in the appropriate document before pruning. Use indexed topic notes for
  inactive context; avoid full transcript archives and duplicate documents.
- Clean old, unnecessary files and agent caches when safe and within scope.
  Inspect exact repo-local targets, ownership, references, and active processes
  first. Remove only your own verified disposable artifacts; coordinate shared
  cleanup with the owner. Age or ignored status alone does not prove disposability.
- Never broadly wipe directories, global agent caches, another agent's work,
  environments, credentials, databases, or required project files. Prefer
  recoverable removal; record material cleanup and recovery details in your log.
  If ownership or purpose is unclear, record the candidate for the Lead.
- Keep secrets, personal data, machine-specific paths, raw logs, and cache
  payloads out of this folder. These are instructions, not filesystem access
  controls; all agents must follow ownership and coordinate shared edits.
