# Codex Execution Engine

## ⚠️ CRITICAL: READ BEFORE RESPONDING ⚠️
- This file **is the operating system** for Codex-based sessions.
- Run it **before any substantive reasoning or tool use**.
- Treat every section as an executable checklist, not passive docs.

<!-- AEGIS:BEGIN codex-runtime -->
## Aegis Continuation

Continuation contract: a short intent (continue / go / proceed / next / resume) advances the Aegis workflow by exactly ONE safe step — resolved from `aegis next` (its `next_safe_action`), never from memory — then re-consult. It is not new authority. Surface and ask before repairs (`aegis repair --apply`), non-dry-run `closeout`, protected/owned paths, switching tasks, or push/PR. Never automatic: merge, force-push, history rewrite, `.aegis/` writes, BLOCKED-readiness bypass, skipping S:W:H:E. "Finish this" still stops at these boundaries. Full text in `.aegis/contract.md`.

<!-- AEGIS:END codex-runtime -->

## 🚦 CODEx READINESS CHECK
**[`templates/engine/core/codex-readiness.md`](templates/engine/core/codex-readiness.md)**
- Confirm the session launched with the expected profile (`/status` → workspace-write, on-request).
- Verify tools available in this shell-only sandbox (`shell`, `update_plan`, optional `web_search`).
- If network or MCP access is disabled, note it before planning work.

## 🧠 STRUCTURED REASONING PROTOCOL
**[`templates/engine/core/ultrathink-protocol.md`](templates/engine/core/ultrathink-protocol.md)**  
**[`templates/engine/core/pre-ultrathink.md`](templates/engine/core/pre-ultrathink.md)**
- Begin deep-work tasks with the codex-tuned ULTRATHINK loop.
- For casual chat, acknowledge the request and skip formal protocols.

## 🧭 CORE MODULES

### Execution Engine
- **Activation**: [`templates/engine/activation/context-aware.md`](templates/engine/activation/context-aware.md)
- **Execution Loop**: [`templates/engine/execution/swhe-format.md`](templates/engine/execution/swhe-format.md)
- **Navigation**: [`templates/engine/navigation/template-protocol.md`](templates/engine/navigation/template-protocol.md)
- **Common Flows**: [`templates/engine/navigation/common-flows.md`](templates/engine/navigation/common-flows.md)

### Enforcement & Safeguards
- **Behavioral Hooks**: [`templates/engine/enforcement/behavioral-hooks.md`](templates/engine/enforcement/behavioral-hooks.md)
- **Cannot Proceed**: [`templates/engine/enforcement/cannot-proceed.md`](templates/engine/enforcement/cannot-proceed.md)

### Support Systems
- **Template Anatomy**: [`templates/engine/structure/template-system.md`](templates/engine/structure/template-system.md)
- **Error Recovery**: [`templates/engine/fallbacks/error-handling.md`](templates/engine/fallbacks/error-handling.md)
- **Debug Aids**: [`templates/engine/debugging/system-debug.md`](templates/engine/debugging/system-debug.md)
- **Examples**: [`templates/engine/examples/practical.md`](templates/engine/examples/practical.md)

---

## 📚 DOCUMENTATION HUB

**For Users**
- **User Guide**: [`templates/USER-GUIDE.md`](templates/USER-GUIDE.md)
- **Quick Reference**: Phrase-to-handler map inside the user guide.
- **Common Patterns**: [`templates/workflows/examples/common-workflows.md`](templates/workflows/examples/common-workflows.md)
- **Troubleshooting**: `templates/USER-GUIDE.md#troubleshooting`

**For Development**
- **Handler Registry**: [`templates/registry/`](templates/registry/) — search via `rg` before loading.
- **Workflows**: [`templates/workflows/domain/README.md`](templates/workflows/domain/README.md)
- **Conventions**: [`templates/CONVENTIONS.md`](templates/CONVENTIONS.md)

**For Extending**
- **Creating Handlers**: [`templates/integration/guides/creating-handlers.md`](templates/integration/guides/creating-handlers.md)
- **Documentation Standard**: [`templates/conventions/docs/documentation-standards.md`](templates/conventions/docs/documentation-standards.md)
- **Improvement Playbook**: [`templates/handlers/orchestrators/system-improvement.md`](templates/handlers/orchestrators/system-improvement.md)

---

## 🔑 OPERATING PRINCIPLES (CODEX EDITION)

1. **Registry-first discovery** – Use `rg`, `find`, or MCP search tools (if configured) over the `templates/registry/` tree before improvising.
2. **Load on demand** – Only open handlers when needed; follow them through end-of-handler confirmation steps.
3. **Evidence or it didn’t happen** – Capture proofs from files, command output, or MCP responses.
4. **Tool discipline** – Prefer built-in shell tools (`rg`, `sed`, `python3`) and documented MCP servers; escalate/ask before leaving constraints.
5. **Profile awareness** – Know whether you’re in `deep-work` or `fast-iterate`; reasoning depth changes expectations.
6. **Conversation context** – For small-talk or non-work queries, acknowledge and respond without invoking the full engine.

## 🛡️ Codex Enforcement Utilities
- `scripts/codex-task sessions update --work <W> --handler <H> --evidence <E> --note <text>` appends S:W:H:E entries to the active session progress log.
- `scripts/codex-task work-tracking update --document TRACKER --work <W> --handler <H> --evidence <E> --note <text>` mirrors the entry in the ACTIVE work-tracking docs.
- `scripts/codex-task scanner run <tool> --work <W> --handler <H> --evidence <E> --log-note <text>` runs SSOT scanners and (optionally) logs the result.
- `scripts/codex-guard validate [--include-untracked]` ensures changed session/work-tracking files carry valid handler/evidence data before completion.
- Run the guard prior to handoff/compaction; auto-fix support remains on the roadmap (log TODOs in work-tracking).


---

## 🧩 REMINDERS
- Templates are executable programs, not references.
- `templates/registry` is the index — search it first.
- Handlers ship complete workflows — run them fully.
- Respect configured sandboxes, approval modes, and network policies.
- When blocked, state the blocker and request guidance; don’t guess.

---

## 🤝 TASK MASTER INTEGRATION
**Import Task Master’s development workflow commands and guidelines** (works with Codex when the MCP server is enabled). Treat the contents as part of this engine.
@./.taskmaster/CLAUDE.md
