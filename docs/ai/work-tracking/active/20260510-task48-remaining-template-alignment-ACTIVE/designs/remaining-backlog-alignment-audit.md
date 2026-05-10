# Remaining Backlog Alignment Audit

## Purpose

The remaining Taskmaster backlog still includes historical migration-phase wording. This audit maps each pending parent task to the current portable-foundation direction so follow-up work is explicit instead of assumed.

## Classification Legend

| Classification | Meaning |
| --- | --- |
| Keep current | Wording broadly matches current foundation direction. |
| Re-scope | The task is still useful, but its description should be rewritten around current portable primitives. |
| Superseded or partial | Later completed work already covers part or all of the old wording; verify before implementation. |
| Defer | Low-value process/dashboard work until core portability and adapter contracts are stable. |
| Gate task | Treat as an evidence/validation gate, not a feature bundle. |

## Pending Parent Task Disposition

| Task | Current title | Disposition | Notes |
| --- | --- | --- | --- |
| 32 | Create Documentation Suite | Re-scope | Convert to current foundation documentation consolidation, not generic docs creation. |
| 34 | Implement A/B Testing Framework | Defer | Likely product/UX-style task; not foundational unless tied to template policy experiments. |
| 36 | Implement Template Governance Board | Defer | Governance process may be documented later; avoid heavyweight board mechanics now. |
| 37 | Build Telemetry Pipeline | Re-scope | If kept, make it static/report-based. Avoid live telemetry service assumptions. |
| 38 | Execute Phase 1 Reference Remediation | Gate task | Historical phase wrapper. Reconcile against current reference scanners before changing files. |
| 39 | Implement Auto-Fix Mode for Guard | Re-scope | Keep only if dry-run, patch preview, and explicit user approval are enforced. |
| 41 | Build Migration Health Dashboard | Defer | Dashboard wording is old; metrics/report files may already cover the need. |
| 44 | Setup Change Advisory Board Process | Defer | Process-only work; not a near-term foundation blocker. |
| 46 | Create Template Import/Export System | Re-scope | Best home for portable foundation packaging/adoption productization. Replace marketplace/ZIP-first wording with CLI manifest/install/adopt/doctor direction. |
| 47 | Build Error Recovery System | Re-scope | Could become recovery runbooks plus tested rollback/repair helpers; avoid broad autonomous recovery. |
| 48 | Execute Phase 2.3 Remaining Templates | Active alignment task | Use this task to prove remaining template/backlog gaps before implementation. |
| 50 | Setup Security Audit Process | Re-scope | Ground in Task 18 security validator and current CI evidence, not external audit ceremony. |
| 51 | Build Template Usage Analytics | Defer | Optional reporting layer; not required before portability installer. |
| 52 | Implement CI/CD Gates | Keep current | Important follow-up for making guard/adapter/portability evidence durable in CI. |
| 53 | Create Template Caching Layer | Defer | Only valuable if registry performance evidence proves a cache need. |
| 54 | Setup Knowledge Transfer Process | Re-scope | Convert to onboarding/runbook work after installer and adapter contracts settle. |
| 55 | Implement Migration Metrics Collection | Re-scope | Static metrics exist; align to current reports before adding more collectors. |
| 56 | Execute Phase 3 Automation Integration | Gate task | Historical phase wrapper. Reframe around proven automation gaps only. |
| 57 | Create Operational Runbook | Keep current | Useful after Task 48 clarifies current process and after installer direction is explicit. |
| 59 | Build Feedback Collection System | Defer | Optional process layer; can be repository-native markdown first. |
| 60 | Setup Post-Migration Monitoring | Re-scope | Monitoring should remain static/portable per Task 17; avoid service assumptions. |
| 61 | Implement Template Discovery Optimization | Re-scope | Use template registry evidence; optimize only if performance tests show a gap. |
| 62 | Create Agent Compatibility Layer | Re-scope | Best home for permanent multi-agent runtime adapter contracts using Tasks 103-107 as completed Claude evidence. |
| 63 | Execute Phase 4 Documentation Delivery | Gate task | Historical phase wrapper; convert to docs delivery validation after current docs are aligned. |
| 64 | Implement Cleanup Automation | Defer | Automation should follow validated cleanup policy; avoid deletion-heavy helpers. |
| 65 | Build Template Quality Scoring | Defer | Optional scoring layer; may use current metadata/metrics later. |
| 66 | Setup Deprecation Management | Re-scope | Useful as lifecycle policy if grounded in template lifecycle/versioning work. |
| 67 | Create Success Metrics Dashboard | Defer | Dashboard optional; prefer report artifacts first. |
| 68 | Implement Final Validation Suite | Keep current | Important as an eventual cross-system gate after installer and agent contracts. |
| 69 | Execute Phase 5 Enhancement Planning | Gate task | Historical phase wrapper; likely planning only after core productization. |
| 70 | Setup Long-term Maintenance | Re-scope | Convert to maintenance contract for the portable foundation and adapters. |
| 71 | Create Migration Archive | Re-scope | Archive policy should use current work-tracking/archive behavior. |
| 72 | Implement Post-Mortem Process | Defer | Process improvement task; not a foundation blocker. |
| 73 | Build Stakeholder Reporting | Defer | Optional communication/report layer. |
| 74 | Execute Phase 6 Cleanup | Gate task | Historical phase wrapper; run only when concrete cleanup list exists. |
| 75 | Create Knowledge Base | Re-scope | Could become the permanent operator guide after installer/adapter contracts. |
| 76 | Implement Celebration Planning | Defer | Not engineering-critical. Consider cancel/defer after backlog cleanup. |
| 77 | Setup Continuous Improvement | Defer | Process layer; revisit after final validation suite. |
| 78 | Create Final Documentation | Gate task | Final docs should wait until portability installer and adapter contract are stable. |
| 79 | Implement Production Verification | Keep current | Later release-readiness gate for the portable foundation. |
| 80 | Execute Production Deployment | Re-scope | For this repo, deployment likely means release/install/adoption readiness, not app deploy. |

## Immediate Follow-Up Candidates

| Candidate | Current Taskmaster home | Recommended action |
| --- | --- | --- |
| Portable foundation installer/adopter productization | Task 46 | Re-scope Task 46 after Task 48.1 completes. |
| Agent runtime adapter contract layer | Task 62 | Re-scope Task 62 using Tasks 103-107 as completed evidence. |
| CI durability for guards/adapters/installers | Task 52 | Keep as a high-priority follow-up once implementation surfaces are selected. |
| Final validation across foundation surfaces | Task 68 | Keep as later integration gate, not immediate implementation. |

## Recommended Sequence

1. Complete Task 48.1 with this audit and the two focused design decisions.
2. Update Taskmaster wording for Task 46 and Task 62 rather than creating duplicate new tasks.
3. Use Task 48.2 only for a proven small gap from the audit. If no code/template gap is found, Task 48.2 should be the Taskmaster alignment update plus evidence.
4. Prioritize Task 46 next if the user wants portability/productization first.
5. Prioritize Task 62 next if the user wants multi-agent adapter portability first.

## Progress Log

- **2026-05-10 16:00** — [S:20260510|W:task48-remaining-template-alignment|H:docs/design|E:docs/ai/work-tracking/active/20260510-task48-remaining-template-alignment-ACTIVE/designs/remaining-backlog-alignment-audit.md] Classified all pending parent tasks against the current portable foundation direction.
