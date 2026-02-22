# AGENTS Operating Rules

This file defines how humans and AI agents must work in this repository.

## Mission

Build a controlled legal document engine for Catalonia arras contracts with:

- deterministic schema integrity
- auditable mutation history
- bounded AI behavior

## Mandatory Engineering Constraints

1. **No unlogged mutation**
   Every schema mutation must write an entry to `contract_logs`.
2. **No raw AI contract editing**
   AI responses are structured instructions only.
3. **No trust in client-derived values**
   Backend calculates derived fields (for example `remaining_amount`).
4. **No silent clause overwrite**
   Manually edited clauses require explicit override intent.
5. **No schema drift without validation**
   Every update path must be schema-validated and type-validated.

## Required AI Response Contract

AI output must parse into one of:

- `{"action":"update_field","path":"...","value":...}`
- `{"action":"rewrite_clause","clause_id":"...","new_text":"..."}`
- `{"action":"no_action","reason":"..."}`

If output fails validation, reject it and log the failure.

## Logging Contract

For each mutation, persist:

- `contract_id`
- `action_type`
- `field_path`
- `old_value`
- `new_value`
- `triggered_by` (`user` or `ai`)
- `ai_prompt` and `ai_response` (when AI-triggered)
- timestamp

No exceptions.

For each AI chat attempt (including `no_action` or rejected updates), persist:

- prompt
- raw response
- parsed action (if available)
- status and error (if any)
- timestamp

## Documentation Sync Policy

The files below are mandatory project controls:

- `readme.md`
- `agents.md`
- `implementation.md`

Whenever any of these change areas are modified, update affected docs in the same patch:

- architecture
- data model/schema
- AI mutation policy
- security/compliance rules
- deployment strategy
- phase roadmap

## Pull Request Checklist

- [ ] Backend validations enforce schema and legal constraints
- [ ] Mutation writes are fully logged
- [ ] AI output contract tests pass
- [ ] Manual clause edit protections pass
- [ ] `readme.md`, `agents.md`, and `implementation.md` are still aligned
