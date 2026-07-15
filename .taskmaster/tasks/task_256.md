# Task ID: 256

**Title:** Canonical Codex Home Topology Diagnostics and Migration Plan

**Status:** done

**Dependencies:** None

**Priority:** high

**Description:** Create the plan-first, read-only Aegis foundation for consolidating Codex and Remote Control onto one canonical CODEX_HOME without touching live homes, servers, shell routing, Blog, or host topology.

**Details:**

Adopt one official Codex binary, one canonical CODEX_HOME and CODEX_SQLITE_HOME, one native Remote Control server, one session database, project-local trusted configuration and hooks, and one client-local exact-hash hook trust store as the binding steady-state architecture. Deliver a binding ADR that rejects the dual-home wrapper topology as the steady state. Implement secret-safe read-only diagnostics that inventory candidate Codex homes, configuration locations, SQLite ownership, installed and running client versions, sockets and lifecycle metadata, wrapper or PATH shadowing, project trust, session ownership, split-brain indicators, and stale pre-trust thread evidence with explicit provenance and known or unknown confidence. Never infer hook approval from tracked guidance or on-disk trust. Emit the exact stale-thread diagnosis only when reliable timestamps prove that the thread predates a valid trust change. Implement a deterministic no-mutation migration planner that blocks cutover when active work or ownership is unknown and produces the exact drain-first Task 257 sequence, rollback boundaries, preservation requirements, and attended checkpoints. Add tests for one-home healthy state, dual-home split brain, simultaneous servers, wrapper shadowing, stale and fresh threads, cross-home sessions, absent or malformed metadata, secret redaction, no-write behavior, deterministic plans, and fail-closed unknown active work. Preserve source and packaged parity where applicable. Non-goals: no writes to either live Codex home, no server start stop restart signal or kill, no shell or wrapper edits, no Blog changes, no session auth trust or hook-hash copying, no hook bypass, no host cutover, no wrapper retirement, and no Taskmaster-to-Gas-Town migration. Deliver through full source workflow, focused and regression verification, attended PR, and stop at exact-head merge approval.

**Test Strategy:**

No test strategy provided.
