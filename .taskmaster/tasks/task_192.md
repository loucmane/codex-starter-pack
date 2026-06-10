# Task ID: 192

**Title:** Closeout must normalize compound Bash evidence

**Status:** done

**Dependencies:** 187 ✓

**Priority:** high

**Description:** Aegis closeout can become unreconcilable when tracked Bash commands use pipes or compound shell segments; the tracker records fragments such as tail/grep/python pieces that handoff repair cannot reconcile.

**Details:**

Treat a piped or compound Bash command as a single evidence unit for S:W:H:E purposes, or normalize/prune segment fragments during handoff repair and closeout. Preserve security classification for each segment, but do not require every shell pipeline fragment to appear as separate implementation/changelog/session evidence. Regression fixture from the HP-Coach #73 closeout failure: commands like git diff | grep, pnpm typecheck | tail, and aegis verify | python3 should not leave closeout.evidence.session/tracker/implementation/changelog permanently failing after the meaningful evidence has been logged. Tests should assert handoff repair plus closeout --dry-run converges for logged piped diagnostic/verification commands, and negative tests should prove mutating commands inside compound Bash are still tracked and cannot be hidden by pipes.

**Test Strategy:**

No test strategy provided.
