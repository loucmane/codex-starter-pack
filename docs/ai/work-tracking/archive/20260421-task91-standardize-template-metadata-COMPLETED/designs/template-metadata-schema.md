# Task 91 Template Metadata Schema

## Schema Timestamp
- 2026-04-21 17:27 CEST

## Required First-Pass Keys
The first rollout will require these keys on in-scope modular template documents:

- `title`
- `type`
- `status`

## Recommended Existing Keys to Preserve
Where already present, preserve the current structural keys instead of forcing a destructive rename:

- `id`
- `category`
- `version`
- `description`
- family-specific fields such as `tools`, `dependencies`, `triggers`, `role`, `domain`, `stability`, `trigger`, `action`, `blocks`

## Family Mapping Rules

### Handlers
Current common pattern:
- `name`
- `role`
- `domain`
- `stability`

First-pass standardization:
- `title` = `name`
- `type` = `role`
- `status` = `stability`
- keep `domain` unchanged for now rather than forcing a rename to `category`

### Behaviors
Current common pattern:
- `trigger`
- `action`
- `blocks`
- `category`
- `enforcement`

First-pass standardization:
- `title` = human-readable title derived from the first heading
- `type` = `behavior`
- `status` = `stable` unless a file explicitly indicates otherwise

### Guides
Current common pattern:
- `title`
- `description`
- `version`

First-pass standardization:
- add `type: guide`
- add `status: stable` unless a file explicitly indicates otherwise

### Matrices
Current common pattern:
- `id`
- `type`
- `category`

First-pass standardization:
- add `title` from the first heading
- add `status: stable` unless a file explicitly indicates otherwise

### Registry Components
Current common pattern:
- `id`
- `type`
- sometimes `name`

First-pass standardization:
- add `title` from `name` or the first heading
- add `status: stable` unless the file already carries another deliberate state

### Engine Modules with Partial Frontmatter
Current common pattern:
- `id` or `name`
- `type`
- other module-specific keys

First-pass standardization:
- add `title` from `name` or the first heading
- add `status: stable` unless a deliberate different state already exists

## Exclusions for First Pass
These document classes should not be batch-rewritten until a separate policy is defined:

- top-level aggregate docs such as `templates/BEHAVIORS.md`, `templates/CONVENTIONS.md`, `templates/HANDLERS.md`, `templates/MATRICES.md`, `templates/TOOLS.md`, `templates/USER-GUIDE.md`
- generated/reference overviews such as `templates/metadata/template-overview.md`
- engine/readme/report-style docs with no frontmatter that act as narrative or generated references rather than modular templates

## Initial Batch Priority
Start with the highest-volume modular families:
1. `templates/handlers/triggers/`
2. `templates/handlers/orchestrators/`
3. `templates/handlers/operators/`
4. `templates/behaviors/`
5. smaller follow-up families (`guides`, `matrices`, `registry`, selected `engine/*`)

## Portability Layer
To make this system reusable across projects, metadata enforcement is now split into:

1. **Generic guard logic**
   - `scripts/codex-guard` enforces required metadata keys based on a policy file.
2. **Repo-local policy data**
   - `templates/metadata/template-metadata-policy.json` defines ordered include/exclude rules, enforcement flags, and required keys.
3. **Repo-local rollout sequencing**
- this repo currently enforces `handlers`, `behaviors`, `guides`, `matrices`, and `registry-components`, while leaving selected engine families declared but not yet enforced.

This means another project can adopt the same foundation by:
- keeping the same guard behavior
- creating its own metadata policy file
- deciding which families are enforced, deferred, or exempt

The goal is to make `title` / `type` / `status` a portable baseline while leaving file-family scope as configuration rather than code.

## Progress Log
- **2026-04-21 17:27** — [S:20260421|W:task91-standardize-template-metadata|H:analysis|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-schema.md] Defined the first-pass metadata schema and family-specific mapping rules for Task 91
- **2026-04-21 17:50** — [S:20260421|W:task91-standardize-template-metadata|H:analysis|E:templates/metadata/template-metadata-policy.json] Documented the new portability layer: generic guard logic plus repo-local metadata policy data
- **2026-04-21 18:40** — [S:20260421|W:task91-standardize-template-metadata|H:analysis|E:templates/metadata/template-metadata-policy.json] Updated the portability notes after the guide family became the third enforced policy-driven slice
- **2026-04-22 15:53** — [S:20260422|W:task91-standardize-template-metadata|H:analysis|E:templates/metadata/template-metadata-policy.json] Updated the rollout notes after matrices became the fourth enforced policy-driven family
- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:analysis|E:templates/metadata/template-metadata-policy.json] Updated the rollout notes after registry components became the fifth enforced policy-driven family
