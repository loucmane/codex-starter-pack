"""Explicit, exact-readback migration of a preserved legacy source transaction."""

from pathlib import Path
from copy import deepcopy
import json
import re

from project_context import DEFAULT_REGISTRY, build_context
from workflow_begin import _scaffold_state, run_profile_readiness
from workflow_common import (
    CommandRunner,
    WorkflowError,
    active_begin_spec,
    atomic_write_json,
    journal_path,
    load_bead,
    load_journal,
    result_payload,
)
from workflow_ownership import (
    bead_digest,
    ensure_external_owner,
    require_workspace,
    require_external_candidate,
    owner_binding,
    owner_payload,
    _verify_delta,
)


def _prepare_wire_reconciliation(journal, spec, context, bead, path):
    """Recognize only the preserved, single-extra-JSON-encoding failure."""
    require_external_candidate(bead)
    records = journal.get("external_ownership", {})
    record = records.get(spec.bead_id, {})
    binding = owner_binding(spec, context)
    if record.get("state") == "verified" and record.get("binding") == binding:
        return
    legacy = owner_payload(spec, context)
    if record.get("state") != "pending" or record.get("binding") != legacy:
        raise WorkflowError("wire reconciliation requires the exact legacy pending intent")
    _verify_delta(record["before"], bead, json.dumps(legacy))
    history = journal.setdefault("ownership_reconciliations", [])
    if not isinstance(history, list):
        raise WorkflowError("ownership reconciliation history is invalid")
    history.append(
        {
            "kind": "legacy-wire-encoding",
            "prior_intent": deepcopy(record),
            "readback": deepcopy(bead),
            "readback_sha256": bead_digest(bead),
        }
    )
    records[spec.bead_id] = {
        "state": "pending",
        "binding": binding,
        "before": deepcopy(bead),
        "reconciliation": True,
    }
    atomic_write_json(path, journal)


def adopt_external(
    root: Path, expected_digest: str, runner: CommandRunner, *, repair_legacy_wire: bool = False
) -> dict:
    if not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
        raise WorkflowError("expected Bead digest must be a full SHA-256")
    spec = active_begin_spec(runner, root)
    context = build_context(root, DEFAULT_REGISTRY)
    require_workspace(runner, spec, context)
    path = journal_path(runner, spec)
    journal = load_journal(path)
    if journal is None or journal["phase"] not in {"claimed", "ready"}:
        raise WorkflowError("explicit adoption requires a preserved claimed/ready legacy journal")
    before = load_bead(runner, context, spec.bead_id)
    if bead_digest(before) != expected_digest:
        raise WorkflowError("Bead changed since the authorized ownership readback")
    if _scaffold_state(runner, root, spec) != "exact":
        raise WorkflowError("legacy scaffold is not exact")
    if "STATE: READY" not in run_profile_readiness(runner, spec):
        raise WorkflowError("legacy local readiness is not READY")
    if repair_legacy_wire:
        _prepare_wire_reconciliation(journal, spec, context, before, path)
    after = ensure_external_owner(
        runner, spec, context, journal, path, reconcile_digest=expected_digest
    )
    return result_payload(
        "adopt-external",
        "bound",
        bead_id=spec.bead_id,
        before_sha256=expected_digest,
        after_sha256=bead_digest(after),
        journal=str(path),
        readiness="not-asserted: dependencies still apply",
    )
