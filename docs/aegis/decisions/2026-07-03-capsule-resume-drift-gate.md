# Capsule Evaluation Gate: Resume-Drift Refresh

Date: 2026-07-03

## Decision

The owner's primary interactive workflow is resume-heavy, not cold-start-heavy. The Session
Zero Capsule remains valuable, but this deployment's primary success gate is now
resume-time drift refresh rather than cold-start A/B.

## Rationale

The original falsifier asked whether the capsule reduces orientation cost for a fresh agent
starting from zero context. That is still a valid product question for headless runs,
scheduled agents, new users, and cold-start-heavy deployments. It is not the operator's
normal workflow: the owner usually resumes or compacts a long-running session.

Waiting for a fixed number of genuine startup events in this workflow would measure a
pattern the operator does not organically produce. Forcing artificial cold starts would make
the metric cleaner while making the behavior less representative.

## New Primary Gate For This Deployment

For the owner's interactive workflow, the capsule is kept if it reliably refreshes reality
on resume/compact with low noise. The expected value is to correct stale conversation
assumptions before work continues.

Useful resume-drift signals include:

- stale verification state caught after HEAD moved
- branch or PR state corrected
- Taskmaster/task truth corrected
- uncommitted or unshipped work surfaced
- risk-register item re-surfaced with a useful close condition
- drift sentinel caught stale docs or state
- capsule changed or validated the next action
- false/noisy capsule items stayed rare

## Roadmap Impact

Keep the deployed capsule core and delivery witness path. Reclassify PR-3 narration and PR-4
surface retirement as dogfood-gated follow-ons:

- PR-3 narration remains optional until computed capsules prove insufficient to preserve
  intent across resumes.
- PR-4 retirement remains blocked until the delivery witness is live as a required check and
  resume-drift evidence shows the capsule/witness can replace old scaffolding without losing
  delivery discipline.

Cold-start A/B remains a secondary evaluation track for deployments where cold starts are
real, but it is no longer the blocking gate for this operator workflow.
