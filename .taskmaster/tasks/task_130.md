# Task ID: 130

**Title:** Aegis Normal-Language Workflow Acceptance and First-Pass Closeout Hardening

**Status:** done

**Dependencies:** 129 ✓

**Priority:** high

**Description:** Prove and harden the installed Aegis workflow so a fresh Claude session can handle a normal user request without a long checklist prompt: detect/init/start Aegis as needed, create workflow scaffolding, use native source tools, log S:W:H:E evidence, verify, repair only through Aegis, close out, and run doctor.

**Details:**

Focus on realistic live acceptance rather than package publication. Create fresh and existing temp projects that use native MCP registration or the closest local equivalent, then prompt Claude in normal language such as 'Add a visible Add to cart button.' Record whether Claude infers the Aegis lifecycle from installed CLAUDE.md, .aegis/contract.md, hooks, and aegis next. Improve Aegis guidance, next-action responses, log defaults, handoff repair, closeout readiness, or installed docs until first-pass behavior is clean. Success requires no synthetic handler names, no direct edits to IMPLEMENTATION.md or CHANGELOG.md, no huge checklist prompt, and no hidden dependency on Taskmaster or Serena.

**Test Strategy:**

No test strategy provided.
