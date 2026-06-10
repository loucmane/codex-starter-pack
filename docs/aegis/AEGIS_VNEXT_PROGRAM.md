# Aegis vNext — Program Document

> Canonical source of truth for the Aegis redesign program. Supersedes the four chat
> transcripts it was distilled from. Authored 2026-06-10. Owner: loucmane.
> Status of the program: Phase 0 backlog (#195–#201) exists; six gap tasks + hygiene
> fixes pending kickoff. Nothing in this doc is committed code.
>
> **Phase 1 implementation contract:** `docs/aegis/AEGIS_CAPSULE_SPEC.md` (the Session
> Zero Capsule spec) is the binding implementation contract for Phase 1 — it pulls the
> Q1 capsule forward and implements slices of G1/G3/G4 with G6 built in. Where this
> document and the spec disagree, the spec wins. In particular, the spec's §2 decision
> (**no hash chain** — killed by adversarial review as a false-alarm machine in a
> single-user repo) supersedes the "hash-chained" wording in G3, F2, §2, and §5 of this
> document for v1. Phase 1 delivery is sliced as nine PRs (spec §1.2): 1a–1d ledger,
> 2a–2b brief/injection, 3 narration, 3.5 delivery witness, 4 retirement.

---

## 0. How this document came to be (provenance)

Five analysis passes, in order:
1. **Live deployment (2026-06-08..10):** Aegis dogfooded on HP-Coach; 34 gate activations
   recorded, 5 emergency upstream fixes (#190–#194 + evidence-normalization + #197 deliver).
2. **Diagnostic fan-out (5 agents):** source architecture + artifact mining + landscape +
   adversarial critique of 13 proposals + synthesis. Produced the 90-day redesign direction.
3. **Gate-activation fixture:** 34 events catalogued from the chat transcript (the only place
   resolved gate activations exist), for the replay corpus.
4. **Blueprint judge-panel (8 agents):** 4 first-principles visions + frontier research +
   adversarial killer + strategy judge + synthesis. Produced Aegis 2.0 (the 6–18mo arc).
5. **Dev-session synthesis + claims verification (this pass):** task-level audit of the real
   #195–#201 backlog; 18 external build-vs-buy claims verified against primary sources
   (10 confirmed, 8 partially-confirmed, 0 contradicted).

Three actors run the program:
- **codex session (dev's Claude) = builder** — implements in /home/loucmane/codex.
- **HP-Coach session = dogfood lab + adversarial verifier** — generates the corpus, live-accepts
  upstream changes before "done", runs product backlog under the strict profile as test load.
- **Owner = approval gate** + the handful of decisions only the owner can make (§9).

---

## 1. The founding measurement (the program's empirical license)

From the fully-recorded 2-day deployment corpus:
- **34 gate activations, 22 blocks.**
- **1 true positive** (E01: observe-stop caught untracked screenshot byproducts).
- **1 validated boundary mechanism** (E29: Stop-gate fired live — but caught ceremony residue
  produced by the logging system itself, not a work mistake).
- **13 workflow-state false positives** · 6 interior ceremony blocks · 3 ceremony self-catches ·
  2 detector divergences · **1 state corruption caused by a repair action** (E19).
- **~47% of tool calls** during implementation were governance bookkeeping.
- **5 emergency upstream PRs in 2 days**; replay would have caught all five.

**The conclusion, in one line:** gate value concentrates at phase boundaries. Both genuine
catches were boundary/completeness checks; **zero interior per-mutation blocks caught a real
mistake.** Therefore: keep boundary gates, delete interior interrogation, record everything
passively, and never ship a gate change unreplayed.

**A structural observability flaw this exposed:** resolved gate activations leave NO trace in any
repo artifact — they exist only in chat transcripts. The artifact miner concluded "the Stop-gate
never fired"; it fired (E29) and was invisible post-resolution. **Headline requirement: after the
recorder ships, no gate activation may be visible only in chat.**

---

## 2. The thesis (what makes Aegis cutting-edge)

Aegis is a **repo-native evidence engine for autonomous coding work**: a passive, hash-chained
flight record no agent can fake, projected into things nobody ships together — cited cross-session
memory the agent actually uses, autonomy priced by displayed track record, independent
fresh-context verification recorded in the same chain, and **policy that is regression-tested code
rather than vibes.** Blocking is the smallest part, not the center.

The differentiator, sharpened by verification: the tool-call **gate layer has commoditized**
(Microsoft AGT, ACS, Cedar/AgentCore, MCP gateways — all shipped in the last 90 days). The
**flight-recorder category exists** (Vorlon shipped, Honeycomb EA). The **one thing nobody ships**
is replaying recorded agent corpora against new *policy versions* — "CI for governance policy."
That, plus the integration (memory IS the audit record; the witness is cheap only because inputs
are ledger-pinned; the contract is honest only because the track record is unfakeable), is the
moat. Each piece alone is absorbable; the chain of custody between them is not.

**Success criterion is the inversion test, not compliance:** an agent under Aegis ships better
work faster than the same agent without it, with governance overhead < 5% of session spend.

---

## 3. The foundation (F1–F7) — the agreed redesign substrate

F1 **Replay governance** — every gate decision recorded (state hash, payload digest, verdict,
   reason, policy version); policy changes regression-tested against recorded corpora before rollout.
F2 **Passive hash-chained ledger** — WHAT auto-captured at PostToolUse (one event per command,
   diff/output hashes), mirrored append-only outside the worktree; WHY annotated at phase
   boundaries only; Stop/closeout gate on annotation completeness.
F3 **Mechanism-based risk tiers** — OS-sandbox interior never blocks; named-state-surface writes
   require an active envelope; boundary crossings + protected-path denylist escalate; audited
   break-glass; human factor required for outward actions.
F4 **Event-log state core** — append-only log = single source of truth; current-work / tracker /
   handoff / plan are regenerated projections; journaled transitions for external surfaces.
F5 **Delivery lifecycle** — closeout → deliver (scoped push → PR → CI → recorded human merge
   approval) → archive; GitHub as source of truth & independent witness. Live-proven (HP-Coach #73 / PR #133).
F6 **Mode lattice** — task / observation / advisory / maintenance / recovery as policy presets,
   derived from state where possible.
F7 **Worktree envelopes** — per-repo out-of-tree state store; envelopes carry agent_id + parent_id;
   lightweight child envelopes for subagents; per-worktree invariants.

---

## 4. Phase 0 backlog — status, gaps, and hygiene

### Existing tasks (codex Taskmaster)
- **#194** Surface post-closeout GitHub delivery state — **status: done, but all 5 subtasks pending**
  (HYGIENE: reconcile honestly against git; every Phase-0 task depends on it).
- **#195** Replay harness — *text says "two true positives"; must be corrected to the fixture's
  labels: one TP (E01) + one must-fire mechanism (E29, ceremony_self_catch).*
- **#196** deliver-report. **#197** size budgets. **#198** passive-ledger spike. **#199** mode-lattice
  spec. **#200** MCP version handshake. **#201** break-glass contract.

### Six gap tasks (load-bearing, currently unowned)
G1 **Gate-decision recorder + policy versioning + shadow lane** — the unowned half of T0; #198's
   acceptance and lexical-pattern retirement both require it. **#198 must depend on it.** Critical path.
G2 **Shared detector module (readiness + repair)** — the 2 divergences and the E19 corruption came
   from these being independent codepaths. **#201 must depend on it** (break-glass must not emit
   repair commands from the divergent path that corrupted #73). Make the corruption scenario a
   blocking fixture.
G3 **State + ledger out of the worktree, SQLite** *(wording superseded for v1: the capsule
   spec §2 kills the hash chain — append-only rows with timestamps; per-row checksums may
   come later, chaining does not return)* — #198 as written writes a bespoke in-worktree
   ledger → double-cutover debt. Do it right from day one. Hard T7 prerequisite.
G4 **Governance-overhead metric** (<5% of tool calls, <200ms p95 hook latency) — the program's
   success criterion; without it, killing the 47% tax is unverifiable and ceremony creep returns silently.
G5 **Closeout diff-accounting gate** — every file in the final diff maps to a ledger event; test
   deletions/weakenings escalate. The single highest-value NEW true-positive class (gate value
   lives at boundaries). #195 seeds the adversarial scenarios; nothing implements the catcher.
G6 **Prompt-injection threat model for auto-injected context** — HANDOFF auto-load, repair
   guidance, Stop-hook additionalContext are all injection channels; the memory work increases
   injected content. NIST's draft lists this control.

### Other untasked / fold-ins
- **Mechanism tiers (T3)** wholly untasked — shadow-first via the recorder, Cedar/ACS-shaped.
- **Journaled transitions** — spike DBOS Transact (MIT, verified) before building bespoke.
- **cwd fix** (friction 15) — fold into #200.

### Hygiene findings to fix before building on them
- #194 status reconciliation (above).
- **TM- vs PR- namespace collision:** Taskmaster #195–198 collide with PR numbers #195/#197/#198.
  Adopt "TM-197 vs PR #197" convention in trackers/commits (the fixture already flagged the reused
  #192 label).
- **Golden-corpus truth:** settle on the fixture's labeling (1 TP + 1 mechanism) before it becomes
  a regression assertion.

---

## 5. The 90-day shape — instrument first, change second, gate last

**Weeks 1–2 (instrument, change nothing):** land #197 + #200 (cwd fix folded in); start #195
*together with* the G1 recorder as one instrumentation push, wired into CI on gate PRs; G4 overhead
metric emitting from day one; shadow lane recording would-block/would-allow in both repos. Extend
the existing pytest infra (tests/: claude_adapter, meta_workflow_guard, session_continuation,
timestamp_guard, fixtures) — **not greenfield.**

**Weeks 3–6 (shadow + unify):** run #198 in shadow against the recorder, **forcing its events into
the out-of-worktree, hash-chained SQLite store (G3) with OTel/NCCoE-shaped fields from day one;**
unify readiness+repair into the G2 shared detector with normalize_completed_closeout as a golden
must-fail test; DBOS spike; Cedar shadow evaluation.

**Weeks 7–12 (the payoff cutover):** flip boundary-only enforcement **per-profile on HP-Coach**,
only after replay shows all 13+ historical FPs gone and E01/E29 still firing. Then #196 +
the G5 diff-accounting gate; #201/#199 ride behind the unified detector.

**Explicitly NOT in this window:** full T5 projection cutover, versioned-event schemas, saga
compensation, a bespoke journal before the DBOS spike, a bespoke policy DSL, microVMs, multi-agent
envelopes, aegis review (both blocked on state relocation), and **no new interior per-mutation gates
of any kind.**

---

## 6. The 6–18 month arc (Aegis 2.0, after the 90 days)

Spine = agent-native memory; grafts = trust (witness + contracts) and ecosystem (policy CI +
zero-ceremony record profile). Each quarter has a falsifiable proof point.

- **Q1 (mo 4–6) Memory becomes the instrument:** cross-task memory spine; `aegis ask` (structural,
  cited, injection-quarantined); `aegis ask --would` preflight via the replay engine; Session Zero
  Capsule (≤2k, structured-fields-only) absorbing kill+handoff compilation.
  *Proof / falsifier:* a cited `aegis ask` costs fewer tokens than the grep it replaces; a kill -9'd
  session resumes at the right plan step with zero human re-explanation. **If the agent ignores the
  Oracle and the capsule doesn't change first-tool-call behavior, the spine is falsified — re-plan.**
- **Q2 (mo 7–9) Trust by contract, verification by witness:** evidence-displayed/human-decided
  Autonomy Contracts (actuary amputated until n≥20/cell) with live downgrade; deliver-time
  Adversarial Witness (deterministic-first, ledger-pinned inputs, context-manifest event).
  *Proof:* one task merged with the human reading only the witness verdict, zero builder-diff reading.
- **Q3 (mo 10–12) Policy as tested code, evidence as a surface:** `aegis policy test` + required
  GitHub Action; `aegis night-report` + `verify-chain`; commit→event-range provenance line.
  *Proof:* a real policy change blocked/amended by replay over ≥200 decisions; zero policy changes
  ship untested in the quarter.
- **Q4 (mo 13–15) Fleet at honest scale:** per-repo coordination log; lease registration from
  approved contracts; one new boundary lease check; per-event agent identity.
  *Proof:* two concurrent agents run real tasks for a week with zero shared-state corruption.
- **Q5 (mo 16–18) Selective opening, earned computation:** computed grants for cells reaching n≥20
  (replay-tested first); red-team the memory-injection surface; Article 12/19-shaped export.
  *Proof:* a computed grant matches/improves on the owner's historical decisions in replay; a
  red-team poisoned-output fails to steer a fresh session through any memory surface.

---

## 7. Build-vs-buy register (verified against primary sources, 2026-06-10)

10 confirmed / 8 partially-confirmed / 0 contradicted. **Trust dates+versions; re-derive any
quantitative limit or lifecycle stage before it gates a decision.**

| Component | Decision | Verified nuance |
|---|---|---|
| **Transition journal** | **Spike DBOS Transact** (MIT, SQLite default, roll-forward) | ✅ confirmed; SQLite is single-node — Postgres path before any multi-node use |
| **Tier-b policy** | **Evaluate Cedar** (AgentCore Policy GA 2026-03-03) | ⚠️ "42–60× vs Rego" is from AWS Verified Permissions / the Cedar paper, NOT AgentCore; "WASM-embeddable" unstated by AgentCore — **re-benchmark in the spike** |
| **Hook taxonomy** | **Name interception points after ACS** (8 points: pre/post_tool_call…) | ⚠️ announced Build 2026-06-02 (not 06-04); v0.3.1-beta — shim, don't couple |
| **Delivery provenance** | **Custom in-toto predicateType** for agent-change provenance | ✅ registry has nothing agent-related; greenfield, upstreamable later |
| **PR attestation** | **Attest a sealed journal-bundle ARTIFACT per PR**, link from PR | ⚠️ GitHub attestations are **artifacts-only**; PR-attestation is not a primitive — must be custom-built |
| **Agentic code review** | **Consume** GitHub Copilot agentic review (GA 2026-03-05) as a verify input | ✅ confirmed; budgets Actions minutes (billed from 2026-06-01) |
| **Stop-hook feedback** | **Use `hookSpecificOutput.additionalContext`** for gate verdicts (≥2.1.157) | ✅ confirmed; cleaner than exit-2 errors; works on SubagentStop |
| **Journal sealing** | **Use `post-session` hook** (≥2.1.169) to seal/export before teardown | ✅ confirmed; keep a Stop/SessionEnd fallback for local CLI |
| **Fleet enforcement** | **Ride managed settings** (highest scope) | ✅ confirmed (3 channels + drop-in fragments); BUT array-merge lets devs widen `excludedCommands` — model as an open hole |
| **Tier-a interior-free** | **Only with OS enforcement** (Landlock/seccomp) | ✅ sandbox is default-OFF + a bypass stream (some silently patched) — until an OS profile exists, network-capable Bash stays gated; reads + workspace writes can flip now |
| **MCP tool ACL/audit** | **Integrate, don't build** (Kong / TrueFoundry / Azure Foundry) | ✅ established class; Aegis owns workflow-state governance gateways don't do |
| **Flight-recorder visualization** | **Differentiate on governance; design ledger for export (OTel GenAI)** | ✅ Vorlon shipped, Honeycomb EA — category exists; don't reinvent the viz layer |
| **Policy-vs-trajectory replay** | **BUILD — greenfield moat** | ⚠️ universal-negative, unprovable; blog-level prior art exists (replay-vs-OPA-rules) — **open-but-closing window; design the schema replay-ready now** |
| **Ledger schema fields** | **Align to NCCoE 4 dimensions** (id, authz, audit, non-repudiation) | ⚠️ NIST source is a **draft concept paper**, not published requirements — align, but **never market "NIST-compliant"** |
| **EU compliance shape** | **Build Article 12/19-shaped logging; keep dates soft** | ⚠️ Dec-2027 deferral is **provisional, not adopted** (formal vote expected June–July 2026); ISO/IEC 24970 at FDIS (technical content ~frozen — safe to track) |
| **Microsoft AGT** | **Option: align policy engine + OWASP mapping** (MIT) | ✅ confirmed; public-preview, expect churn — pin a release |

---

## 8. Standing rules (invariant across all phases)

1. **No gate-behavior change ships unreplayed** — replay over the (growing) corpus must show no lost
   true positives and no adversarial-suite regressions. This is the automated form of the 5 manual
   emergency fixes.
2. **Record first, change second, gate last** — every step is additive or shadow-mode by construction.
3. **HP-Coach runs a stable profile and opts into each phase per flag** — a bad phase rolls back by
   flag-flip, not by emergency upstream PR.
4. **Capture-time redaction is default** — scrub secrets at write time from the recorder's first version.
5. **No "replace with X"** without a coverage map (what it covers, what it doesn't, migration that
   preserves current HP-Coach workflows).
6. **Governance overhead stays measured and < 5%** of tool calls (G4); if witness LLM spend is
   reclassified as review-substitution, it must literally displace human-review minutes or it reverts.
7. **The must-fire set survives every policy change:** E01 (dirty-tree TP) and E29 (trailing-pending
   completeness); E19 (repair corruption) must become *unrepresentable*; detector divergence (E11/E12)
   *impossible by shared-detector construction.*

---

## 9. Owner decisions

**Decide soon (affect Phase 0 / Q1):**
- **Capture-time redaction:** recommend default-on from v1 (cheap now, painful to retrofit). [recommend: yes]
- **Spine scope:** per-repo vs shared across codex + HP-Coach. [recommend: per-repo, schema keeps a
  `repo` field so federation stays cheap]

**Decide at Q2+ (have time):**
- Witness/Policy-CI LLM spend: through Max-subscription subagents (household rule: never via API
  scripts), and the hard per-task ceiling that makes "review substitute" accounting honest.
- Retention/redaction policy for archived ledgers; whether any corpus is ever shareable.
- Trust-cell taxonomy (agent × surface × task-type) and whether computed grants ever activate, or
  grants stay human-decided permanently.
- External-release intent inside the 18-month window (pulls redaction/packaging/zero-ceremony forward).
- Claude Code agent-teams coupling for Q4 leases (build against experimental TeammateIdle/Task* hooks
  now vs keep the coordination log harness-agnostic).
- **Capsule authority on conflict:** when ledger truth contradicts the owner's recollection or a
  Taskmaster status, which wins by default? (Product-philosophy call — only the owner sets it.)

---

## 10. Immediate next actions

1. **codex session:** kickoff to (a) reconcile #194 status against git; (b) fix #195's TP labels;
   (c) add G1–G6 with corrected dependencies (#198→G1 recorder; #201→G2 shared detector). Repo is
   BLOCKED (no task on main) — goes through /kickoff.
2. **HP-Coach session:** clear the post-#73 completed-closeout interregnum so the lab stops
   misfiring on reads; then resume product backlog (#74 findQuestion hardening) as instrumentation
   test load.
3. **Spikes (weeks 3+):** DBOS Transact (green-lit); Cedar (re-benchmark, don't trust the
   misattributed figure).

---

## Appendix — companion artifacts (delivered separately)

- **Gate-activation fixture** (`aegis-gate-activations-hpcoach-20260608-20260610`): 34 events with
  verbatim block reasons, policy-version timeline, classifications, JSONL join keys, and #195
  ingestion notes. The replay corpus seed.
- **Diagnostic analysis JSON:** source architecture (file:line), artifact mining, landscape, P1–P13
  critique, 90-day roadmap.
- **Blueprint JSON:** 4 visions, frontier research + regulatory timeline, killer verdicts, strategy
  scoring, the Aegis 2.0 blueprint.
- **Claims-verification JSON:** 18 claims, per-claim evidence URLs + corrections + decision impact.
- **Ground truth transcript:** /home/loucmane/.claude/projects/-home-loucmane-dev-hpfetcher/221ed52e-6f5e-4e4d-b87d-297d8baca514.jsonl (270 MB).
