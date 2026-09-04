"""Real Git/scaffold/ownership, fake scoped Beads API: never use a live store."""

import json
import subprocess
from pathlib import Path

import pytest

from test_gas_city_workflow_transitions import MultiBeadRunner, _bead, _fixture_project, begin
from workflow_common import WorkflowError
from workflow_coordinate import coordinate


class LedgerRunner(MultiBeadRunner):
    def __init__(self):
        super().__init__({"ga-test": _bead(), "ga-other": _bead(bead_id="ga-other")}, "ga-test")
        self.fail_after_write = False
        self.corrupt_write = False

    def run(self, argv, *, cwd=None, env=None, check=True):
        args = list(argv)
        if args and args[0].endswith("/gc") and "bd" in args:
            index = args.index("bd") + 1
            verb = args[index]
            if verb == "update" and "--append-notes" in args:
                self.calls.append(args)
                bead = self.beads[args[index + 1]]
                bead["notes"] = (bead.get("notes", "") + "\n" + args[-1]).strip()
                if self.corrupt_write:
                    bead["title"] = "unintended"
                if self.fail_after_write:
                    raise WorkflowError("lost response")
                return subprocess.CompletedProcess(args, 0, "updated", "")
            if verb == "create":
                self.calls.append(args)
                parent = args[args.index("--parent") + 1]
                bead = {
                    "id": parent + ".1",
                    "title": args[index + 1],
                    "description": args[args.index("--description") + 1],
                    "acceptance_criteria": args[args.index("--acceptance") + 1],
                    "status": "open",
                    "priority": 2,
                    "issue_type": "task",
                    "metadata": {},
                    "dependencies": [
                        {"id": parent, "dependency_type": "parent-child", "status": "in_progress"}
                    ],
                }
                self.beads[bead["id"]] = bead
                if self.fail_after_write:
                    raise WorkflowError("lost response")
                return subprocess.CompletedProcess(args, 0, json.dumps(bead), "")
            if args[index : index + 2] == ["dep", "add"]:
                self.calls.append(args)
                parent, blocker = args[index + 2 : index + 4]
                self.beads[parent]["dependencies"].append(
                    {"id": blocker, "dependency_type": "blocks", "status": "open"}
                )
                return subprocess.CompletedProcess(args, 0, "added", "")
        return super().run(args, cwd=cwd, env=env, check=check)


@pytest.fixture
def lane(tmp_path):
    root, registry = _fixture_project(tmp_path)
    runner = LedgerRunner()
    result = begin(root, "ga-test", slug="fixture", goals=[], registry=registry, runner=runner)
    return Path(result["spec"]["worktree"]), registry, runner, Path(result["journal"])


@pytest.mark.parametrize(
    "action,fields",
    [
        ("note", {"text": "Evidence captured"}),
        ("create", {"title": "Repair", "description": "Narrow scope", "acceptance": "Test passes"}),
    ],
)
def test_exact_single_operation_and_noop_replay(lane, action, fields):
    root, registry, runner, path = lane
    first = coordinate(root, "ga-test", action, fields, runner, registry=registry)
    second = coordinate(root, "ga-test", action, fields, runner, registry=registry)
    assert first["status"] == "applied" and second["status"] == "unchanged"
    records = json.loads(path.read_text())["coordination"]
    assert len(records) == 1
    record = next(iter(records.values()))
    assert record["state"] == "verified" and record["after_sha256"]
    writes = [args for args in runner.calls if "--append-notes" in args or "create" in args]
    assert len(writes) == 1
    assert writes[0][1:6] == [
        "--city",
        "/home/loucmane/gascity/city",
        "--rig",
        "future-project",
        "bd",
    ]
    if action == "create":
        assert first["bead_id"] == "ga-test.1"
        assert runner.beads["ga-test.1"]["status"] == "open"
        assert not runner.beads["ga-test.1"].get("assignee")


def test_depend_reuses_transactional_attach(lane):
    root, registry, runner, path = lane
    result = coordinate(
        root, "ga-test", "depend", {"blocker": "ga-other"}, runner, registry=registry
    )
    assert result["status"] == "applied"
    journal = json.loads(path.read_text())
    assert journal["attached_bead_ids"] == ["ga-other"]
    assert journal["external_ownership"]["ga-other"]["state"] == "verified"
    assert runner.beads["ga-other"]["metadata"] == runner.beads["ga-test"]["metadata"]
    assert "attached_bead_ids: [ga-other]" in (root / "plans/current").read_text()


@pytest.mark.parametrize(
    "action,fields",
    [
        ("note", {"text": "Evidence captured"}),
        ("create", {"title": "Repair", "description": "Scope", "acceptance": "Proof"}),
    ],
)
def test_ambiguous_partial_write_is_not_retried(lane, action, fields):
    root, registry, runner, path = lane
    runner.fail_after_write = True
    with pytest.raises(WorkflowError, match="lost response"):
        coordinate(root, "ga-test", action, fields, runner, registry=registry)
    count = len(runner.calls)
    with pytest.raises(WorkflowError, match="ambiguous"):
        coordinate(root, "ga-test", action, fields, runner, registry=registry)
    assert all(
        "create" not in args and "--append-notes" not in args for args in runner.calls[count:]
    )
    assert next(iter(json.loads(path.read_text())["coordination"].values()))["state"] == "pending"


def test_extra_bead_delta_preserved_and_refused(lane):
    root, registry, runner, path = lane
    runner.corrupt_write = True
    with pytest.raises(WorkflowError, match="non-note"):
        coordinate(root, "ga-test", "note", {"text": "Proof"}, runner, registry=registry)
    assert runner.beads["ga-test"]["title"] == "unintended"
    assert next(iter(json.loads(path.read_text())["coordination"].values()))["state"] == "pending"


@pytest.mark.parametrize(
    "defect", ["unowned", "routed", "assignee", "binding", "closed", "wrong-root"]
)
def test_live_ownership_is_checked_before_intent_or_write(lane, defect):
    root, registry, runner, path = lane
    bead_id = "ga-test"
    if defect == "unowned":
        bead_id = "ga-other"
    elif defect == "routed":
        runner.beads[bead_id]["metadata"]["gc.routed_to"] = "other/agent"
    elif defect == "assignee":
        runner.beads[bead_id]["assignee"] = "native-session"
    elif defect == "binding":
        runner.beads[bead_id]["metadata"]["workflow.external_owner"] = "forged"
    elif defect == "closed":
        runner.beads[bead_id]["status"] = "closed"
    else:
        root = Path(json.loads(path.read_text())["spec"]["canonical_root"])
    count = len(runner.calls)
    with pytest.raises(WorkflowError):
        coordinate(root, bead_id, "note", {"text": "Proof"}, runner, registry=registry)
    assert not json.loads(path.read_text()).get("coordination")
    assert all("--append-notes" not in args for args in runner.calls[count:])


@pytest.mark.parametrize(
    "action,fields",
    [
        ("close", {}),
        ("note", {"text": "x", "status": "closed"}),
        ("note", {"text": ""}),
        ("note", {"text": "x" * 16385}),
        ("depend", {"blocker": "external:other:ship"}),
        ("depend", {"blocker": "ga-test"}),
    ],
)
def test_no_arbitrary_control_flags(lane, action, fields):
    root, registry, runner, path = lane
    with pytest.raises(WorkflowError):
        coordinate(root, "ga-test", action, fields, runner, registry=registry)
    assert not json.loads(path.read_text()).get("coordination")
