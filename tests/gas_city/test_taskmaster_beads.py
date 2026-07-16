from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from aegis_foundation import taskmaster_beads


def _top_task(
    task_id: str,
    *,
    title: str,
    status: str = "pending",
    priority: str = "medium",
    dependencies: list[object] | None = None,
    subtasks: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "id": task_id,
        "title": title,
        "description": f"Description for {title}",
        "details": f"Details for {title}",
        "testStrategy": f"Test {title}",
        "priority": priority,
        "dependencies": dependencies or [],
        "status": status,
        "subtasks": subtasks or [],
    }


def _subtask(
    child_id: int,
    *,
    parent_id: int,
    title: str,
    status: str = "pending",
    dependencies: list[object] | None = None,
    test_strategy: object = "Test child",
) -> dict[str, object]:
    record: dict[str, object] = {
        "id": child_id,
        "title": title,
        "description": f"Description for {title}",
        "details": f"Details for {title}",
        "dependencies": dependencies or [],
        "status": status,
        "parentId": "undefined",
        "parentTaskId": parent_id,
    }
    if test_strategy is not _MISSING:
        record["testStrategy"] = test_strategy
    return record


_MISSING = object()


def _payload() -> dict[str, object]:
    children = [
        _subtask(
            1,
            parent_id=12,
            title="Repeated title",
            status="done",
            test_strategy=_MISSING,
        ),
        _subtask(
            2,
            parent_id=12,
            title="Repeated title",
            dependencies=[1],
            test_strategy=None,
        ),
        _subtask(
            3,
            parent_id=12,
            title="Third child",
            dependencies=["12.2"],
            test_strategy="",
        ),
    ]
    tasks = [
        _top_task("12", title="Parent", dependencies=["1"], subtasks=children),
        _top_task("1", title="Root blocker", status="done", priority="high"),
        _top_task("13", title="Cancelled", status="cancelled", priority="low"),
        _top_task("14", title="Deferred", status="deferred", priority="high"),
    ]
    return {
        "master": {
            "tasks": tasks,
            "metadata": {
                "version": "1.0.0",
                "lastModified": "2030-01-02T03:04:05.678Z",
                "taskCount": len(tasks),
                "completedCount": 1,
                "tags": ["master"],
            },
        }
    }


def _source_bytes(payload: object | None = None) -> bytes:
    return (
        json.dumps(
            _payload() if payload is None else payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode()


def _records(content: bytes) -> list[dict[str, object]]:
    return [json.loads(line) for line in content.decode().splitlines()]


def _jsonl(records: list[dict[str, object]]) -> bytes:
    return b"".join(
        (
            json.dumps(
                record,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode()
        for record in records
    )


@pytest.fixture
def conversion() -> tuple[bytes, taskmaster_beads.ConversionResult]:
    source = _source_bytes()
    return source, taskmaster_beads.build_artifacts(source, prefix="ags")


def test_conversion_is_deterministic_and_preserves_mapping_semantics(
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, result = conversion
    rerun = taskmaster_beads.build_artifacts(source, prefix="ags")

    assert result.artifacts == rerun.artifacts
    assert [issue["id"] for issue in result.issues] == [
        "ags-0001",
        "ags-0012",
        "ags-0012.1",
        "ags-0012.2",
        "ags-0012.3",
        "ags-0013",
        "ags-0014",
    ]
    by_id = {str(issue["id"]): issue for issue in result.issues}
    assert by_id["ags-0012"]["issue_type"] == "epic"
    assert by_id["ags-0012.2"]["priority"] == 2
    assert "legacy:priority:inherited" in by_id["ags-0012.2"]["labels"]
    assert by_id["ags-0012"]["dependencies"][0]["depends_on_id"] == "ags-0001"
    assert by_id["ags-0012.2"]["dependencies"][0]["depends_on_id"] == "ags-0012.1"
    assert by_id["ags-0012.3"]["dependencies"][0]["depends_on_id"] == "ags-0012.2"
    assert by_id["ags-0013"]["status"] == "closed"
    assert by_id["ags-0013"]["close_reason"] == "cancelled in Taskmaster"
    assert by_id["ags-0014"]["status"] == "deferred"
    assert (
        by_id["ags-0012.1"]["metadata"]["migration"]["field_states"]["testStrategy"]
        == "missing"
    )
    assert (
        by_id["ags-0012.2"]["metadata"]["migration"]["field_states"]["testStrategy"]
        == "null"
    )
    assert (
        by_id["ags-0012.3"]["metadata"]["migration"]["field_states"]["testStrategy"]
        == "empty"
    )
    assert len(result.blockers) == 3
    assert len(result.hierarchy) == 3
    assert result.manifest["counts"]["total_dependency_relationships"] == 6
    assert result.manifest["source"]["sha256"] == hashlib.sha256(source).hexdigest()


def test_generated_export_exactly_reconciles_and_report_is_deterministic(
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, result = conversion
    source_hash = hashlib.sha256(source).hexdigest()

    first = taskmaster_beads.verify_export(
        result.artifacts["issues.jsonl"],
        source_bytes=source,
        artifacts=result.artifacts,
        expected_source_sha256=source_hash,
    )
    second = taskmaster_beads.reconcile_export(
        source,
        result.artifacts["issues.jsonl"],
        prefix="ags",
        expected_source_sha256=source_hash,
    )

    assert first == second
    assert first["status"] == "pass"
    assert first["counts"] == {
        "exported_issues_total": 7,
        "manifest_issues_total": 7,
        "unique_ids": 7,
        "unique_external_refs": 7,
        "blocker_relationships": 3,
        "hierarchy_relationships": 3,
        "provenance_rows": 7,
        "non_manifest_issues": 0,
        "non_manifest_external_refs": 0,
    }


def test_atomic_artifacts_are_idempotent_and_require_an_exact_set(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    _, result = conversion
    output = tmp_path / "migration"

    first = taskmaster_beads.write_artifacts(output, result.artifacts)
    mtimes = {
        name: (output / name).stat().st_mtime_ns
        for name in taskmaster_beads.ARTIFACT_NAMES
    }
    second = taskmaster_beads.write_artifacts(output, result.artifacts)

    assert first["changed_files"] == list(taskmaster_beads.ARTIFACT_NAMES)
    assert second["changed_files"] == []
    assert second["unchanged_files"] == list(taskmaster_beads.ARTIFACT_NAMES)
    assert mtimes == {
        name: (output / name).stat().st_mtime_ns
        for name in taskmaster_beads.ARTIFACT_NAMES
    }

    contaminated = dict(result.artifacts)
    contaminated["unexpected.json"] = b"{}\n"
    with pytest.raises(taskmaster_beads.ConversionError, match="artifact set must be exact"):
        taskmaster_beads.write_artifacts(output, contaminated)


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (
            lambda records: records.append(
                {
                    "_type": "issue",
                    "id": "ags-9999",
                    "external_ref": "foreign:issue:9999",
                }
            ),
            "contaminated target",
        ),
        (
            lambda records: records.append(copy.deepcopy(records[0])),
            "duplicate issue id",
        ),
        (
            lambda records: records.append(
                {
                    **copy.deepcopy(records[0]),
                    "id": "ags-9999",
                }
            ),
            "duplicate external_ref",
        ),
        (
            lambda records: records[0].__setitem__("id", "ags-9999"),
            "contaminated target",
        ),
        (
            lambda records: records[0].__setitem__(
                "external_ref",
                "taskmaster:master:9999",
            ),
            "contaminated target",
        ),
    ],
    ids=[
        "unrelated-row",
        "duplicate-id",
        "duplicate-external-ref",
        "non-manifest-id",
        "non-manifest-external-ref",
    ],
)
def test_reconciliation_rejects_contamination_and_duplicate_identity(
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
    mutator: object,
    match: str,
) -> None:
    source, result = conversion
    records = _records(result.artifacts["issues.jsonl"])
    mutator(records)  # type: ignore[operator]

    with pytest.raises(taskmaster_beads.ReconciliationError, match=match):
        taskmaster_beads.verify_export(
            _jsonl(records),
            source_bytes=source,
            artifacts=result.artifacts,
        )


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (
            lambda issue: issue.__setitem__("status", "open"),
            "status mapping drift",
        ),
        (
            lambda issue: issue.__setitem__("priority", 4),
            "priority mapping drift",
        ),
        (
            lambda issue: issue.__setitem__("source_system", "other"),
            "source_system provenance drift",
        ),
        (
            lambda issue: issue["metadata"]["migration"].__setitem__(
                "source_sha256",
                "0" * 64,
            ),
            "migration provenance drift in source_sha256",
        ),
    ],
    ids=["status", "priority", "source-system", "source-hash-provenance"],
)
def test_reconciliation_rejects_per_issue_mapping_and_provenance_drift(
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
    mutate: object,
    match: str,
) -> None:
    source, result = conversion
    records = _records(result.artifacts["issues.jsonl"])
    issue = next(record for record in records if record["id"] == "ags-0001")
    mutate(issue)  # type: ignore[operator]

    with pytest.raises(taskmaster_beads.ReconciliationError, match=match):
        taskmaster_beads.verify_export(
            _jsonl(records),
            source_bytes=source,
            artifacts=result.artifacts,
        )


def test_reconciliation_rejects_blocker_hierarchy_and_duplicate_edge_drift(
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, result = conversion
    original = _records(result.artifacts["issues.jsonl"])

    blocker_drift = copy.deepcopy(original)
    parent = next(issue for issue in blocker_drift if issue["id"] == "ags-0012")
    blocker = next(
        edge for edge in parent["dependencies"] if edge["type"] == "blocks"
    )
    blocker["depends_on_id"] = "ags-0013"
    with pytest.raises(taskmaster_beads.ReconciliationError, match="blocker graph"):
        taskmaster_beads.verify_export(
            _jsonl(blocker_drift),
            source_bytes=source,
            artifacts=result.artifacts,
        )

    hierarchy_drift = copy.deepcopy(original)
    child = next(issue for issue in hierarchy_drift if issue["id"] == "ags-0012.1")
    child["dependencies"] = [
        edge for edge in child["dependencies"] if edge["type"] != "parent-child"
    ]
    with pytest.raises(taskmaster_beads.ReconciliationError, match="hierarchy graph"):
        taskmaster_beads.verify_export(
            _jsonl(hierarchy_drift),
            source_bytes=source,
            artifacts=result.artifacts,
        )

    duplicate_edge = copy.deepcopy(original)
    parent = next(issue for issue in duplicate_edge if issue["id"] == "ags-0012")
    parent["dependencies"].append(copy.deepcopy(parent["dependencies"][0]))
    with pytest.raises(taskmaster_beads.ReconciliationError, match="duplicate dependency edge"):
        taskmaster_beads.verify_export(
            _jsonl(duplicate_edge),
            source_bytes=source,
            artifacts=result.artifacts,
        )


def test_reconciliation_rejects_semantic_and_source_hash_drift(
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, result = conversion
    records = _records(result.artifacts["issues.jsonl"])
    records[0]["title"] = "Changed after import"
    with pytest.raises(
        taskmaster_beads.ReconciliationError,
        match="semantic projection drift",
    ):
        taskmaster_beads.verify_export(
            _jsonl(records),
            source_bytes=source,
            artifacts=result.artifacts,
        )

    changed_source = source + b" "
    with pytest.raises(
        taskmaster_beads.ReconciliationError,
        match="manifest source SHA-256",
    ):
        taskmaster_beads.verify_export(
            result.artifacts["issues.jsonl"],
            source_bytes=changed_source,
            artifacts=result.artifacts,
        )

    with pytest.raises(
        taskmaster_beads.ReconciliationError,
        match="source SHA-256 mismatch",
    ):
        taskmaster_beads.verify_export(
            result.artifacts["issues.jsonl"],
            source_bytes=source,
            artifacts=result.artifacts,
            expected_source_sha256="0" * 64,
        )


def test_reconciliation_rejects_tampered_artifacts_and_duplicate_json_keys(
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, result = conversion
    tampered = dict(result.artifacts)
    tampered_records = _records(tampered["issues.jsonl"])
    tampered_records[0]["title"] = "Valid JSON with altered evidence"
    tampered["issues.jsonl"] = _jsonl(tampered_records)
    with pytest.raises(
        taskmaster_beads.ReconciliationError,
        match="persisted migration artifact digest mismatch",
    ):
        taskmaster_beads.verify_export(
            result.artifacts["issues.jsonl"],
            source_bytes=source,
            artifacts=tampered,
        )

    first_line, *remaining = result.artifacts["issues.jsonl"].splitlines()
    duplicate_key_line = first_line.replace(
        b'{"_type":"issue"',
        b'{"_type":"issue","_type":"issue"',
        1,
    )
    duplicate_key_export = b"\n".join([duplicate_key_line, *remaining]) + b"\n"
    with pytest.raises(
        taskmaster_beads.ReconciliationError,
        match="duplicate JSON object key",
    ):
        taskmaster_beads.verify_export(
            duplicate_key_export,
            source_bytes=source,
            artifacts=result.artifacts,
        )


def test_beads_timestamp_normalization_does_not_create_false_drift(
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, result = conversion
    records = _records(result.artifacts["issues.jsonl"])
    for issue in records:
        issue["created_at"] = "2031-01-01T00:00:00Z"
        issue["updated_at"] = "2031-01-01T00:00:01Z"
        issue["created_by"] = "beads-import"
        for dependency in issue.get("dependencies", []):
            dependency["created_at"] = "2031-01-01T00:00:00Z"
            dependency["created_by"] = "beads-import"

    report = taskmaster_beads.verify_export(
        _jsonl(records),
        source_bytes=source,
        artifacts=result.artifacts,
    )

    assert report["status"] == "pass"


def test_converter_fails_closed_on_ambiguous_graph_and_hash_input() -> None:
    payload = _payload()
    payload["master"]["tasks"][0]["subtasks"][1]["dependencies"] = ["1"]
    with pytest.raises(
        taskmaster_beads.ConversionError,
        match="ambiguous bare-string dependency",
    ):
        taskmaster_beads.build_artifacts(_source_bytes(payload))

    payload = _payload()
    payload["master"]["tasks"][1]["dependencies"] = ["12"]
    with pytest.raises(taskmaster_beads.ConversionError, match="contains a cycle"):
        taskmaster_beads.build_artifacts(_source_bytes(payload))

    with pytest.raises(taskmaster_beads.ConversionError, match="source SHA-256 mismatch"):
        taskmaster_beads.build_artifacts(
            _source_bytes(),
            expected_source_sha256="0" * 64,
        )


class _FakeMigrationRunner:
    def __init__(self, conversion: taskmaster_beads.ConversionResult) -> None:
        self.issues = conversion.artifacts["issues.jsonl"]
        self.expected_ids = [
            str(issue["id"]) for issue in _records(self.issues)
        ]
        self.preflight_export = b""
        self.first_export = self.issues
        self.final_export = self.issues
        self.dry_run = {
            "schema_version": 1,
            "created": len(self.expected_ids),
            "skipped": 0,
            "dry_run": True,
        }
        self.first_import = {
            "schema_version": 1,
            "created": len(self.expected_ids),
            "skipped": 0,
            "ids": list(self.expected_ids),
        }
        self.second_import = {
            "schema_version": 1,
            "created": len(self.expected_ids),
            "skipped": 0,
            "ids": list(self.expected_ids),
        }
        self.heads = [
            "11111111111111111111111111111111",
            "11111111111111111111111111111111",
            "7vse6duhku1cl388k3bl998q53iq6qeg",
            "7vse6duhku1cl388k3bl998q53iq6qeg",
        ]
        self.fail_event: str | None = None
        self.target_attestation = {
            "issue_count": "0",
            "working_set_changes": "1",
            "expected_config_changes": "1",
            "unexpected_working_changes": "0",
            "branch_count": "1",
            "main_branch_count": "1",
            "commit_count": "3",
        }
        self.failure_secret = "credential-value-must-not-leak"
        self.events: list[str] = []
        self.calls: list[tuple[tuple[str, ...], bytes | None]] = []
        self._actual_imports = 0
        self._head_calls = 0

    @staticmethod
    def _json(value: object) -> bytes:
        return (json.dumps(value, sort_keys=True) + "\n").encode()

    def _result(self, event: str, stdout: bytes) -> taskmaster_beads.CommandResult:
        self.events.append(event)
        if self.fail_event == event:
            secret = self.failure_secret.encode()
            return taskmaster_beads.CommandResult(9, secret, secret)
        return taskmaster_beads.CommandResult(0, stdout)

    def run(
        self,
        argv: object,
        *,
        stdin: bytes | None = None,
    ) -> taskmaster_beads.CommandResult:
        command = tuple(argv)  # type: ignore[arg-type]
        self.calls.append((command, stdin))
        executable = Path(command[0]).name
        if executable == "bd" and command[1:] == ("--version",):
            return self._result("version", b"bd version 1.1.0 (8e4e59d39)\n")
        if executable == "dolt" and command[1:] == ("version",):
            return self._result("dolt_version", b"dolt version 2.2.0\n")

        if executable == "bd" and "export" in command:
            if self._actual_imports == 0:
                return self._result("preflight_export", self.preflight_export)
            if self._actual_imports == 1:
                return self._result("first_export", self.first_export)
            return self._result("final_export", self.final_export)

        if executable == "bd" and "import" in command:
            assert stdin == self.issues
            assert command[-1] == "-"
            if "--dry-run" in command:
                return self._result("dry_run", self._json(self.dry_run))
            self._actual_imports += 1
            if self._actual_imports == 1:
                return self._result("first_import", self._json(self.first_import))
            return self._result("second_import", self._json(self.second_import))

        if executable == "dolt":
            if any("COUNT(*) FROM issues" in argument for argument in command):
                return self._result(
                    "preflight_attestation",
                    self._json({"rows": [self.target_attestation]}),
                )
            events = [
                "preflight_head",
                "dry_run_head",
                "first_head",
                "final_head",
            ]
            event = events[self._head_calls]
            head = self.heads[self._head_calls]
            self._head_calls += 1
            return self._result(event, self._json({"rows": [{"head": head}]}))

        raise AssertionError(f"unexpected command: {command}")


def _target(tmp_path: Path) -> Path:
    target = tmp_path / "rig"
    (target / ".beads").mkdir(parents=True, exist_ok=True)
    return target


def _run_operational(
    source: bytes,
    conversion: taskmaster_beads.ConversionResult,
    target: Path,
    runner: _FakeMigrationRunner,
    evidence_sink: taskmaster_beads.MigrationEvidenceSink | None = None,
) -> taskmaster_beads.OperationalMigrationResult:
    bd = "/locked/bin/bd"
    dolt = "/locked/bin/dolt"
    toolchain = {
        "schema_version": taskmaster_beads.LOCKED_TOOLCHAIN_SCHEMA,
        "runtime_lock_path": "/locked/runtime-lock.json",
        "runtime_lock_sha256": "a" * 64,
        "tools": {
            "bd": {
                "path": bd,
                "version": taskmaster_beads.TARGET_BEADS_VERSION,
                "binary_sha256": "b" * 64,
            },
            "dolt": {
                "path": dolt,
                "version": taskmaster_beads.TARGET_DOLT_VERSION,
                "binary_sha256": "c" * 64,
            },
        },
    }
    return taskmaster_beads.run_operational_migration(
        source,
        expected_source_sha256=hashlib.sha256(source).hexdigest(),
        target_directory=target,
        dolt=taskmaster_beads.DoltConnection(
            host="127.0.0.1",
            port=3306,
            user="aegis_beads",
            database="aegis_beads",
            no_tls=True,
        ),
        runner=runner,
        locked_toolchain=toolchain,
        bd_executable=bd,
        dolt_executable=dolt,
        evidence_sink=evidence_sink,
    )


def _run_reconciliation(
    source: bytes,
    target: Path,
    runner: _FakeMigrationRunner,
    evidence_sink: taskmaster_beads.MigrationEvidenceSink | None = None,
) -> taskmaster_beads.OperationalMigrationResult:
    bd = "/locked/bin/bd"
    dolt = "/locked/bin/dolt"
    return taskmaster_beads.run_operational_reconciliation(
        source,
        expected_source_sha256=hashlib.sha256(source).hexdigest(),
        target_directory=target,
        dolt=taskmaster_beads.DoltConnection(
            host="127.0.0.1",
            port=3306,
            user="aegis_beads",
            database="aegis_beads",
            no_tls=True,
        ),
        runner=runner,
        locked_toolchain={
            "schema_version": taskmaster_beads.LOCKED_TOOLCHAIN_SCHEMA,
            "runtime_lock_path": "/locked/runtime-lock.json",
            "runtime_lock_sha256": "a" * 64,
            "tools": {
                "bd": {
                    "path": bd,
                    "version": taskmaster_beads.TARGET_BEADS_VERSION,
                    "binary_sha256": "b" * 64,
                },
                "dolt": {
                    "path": dolt,
                    "version": taskmaster_beads.TARGET_DOLT_VERSION,
                    "binary_sha256": "c" * 64,
                },
            },
        },
        bd_executable=bd,
        dolt_executable=dolt,
        evidence_sink=evidence_sink,
    )


def test_operational_runner_executes_guarded_stdin_only_two_pass_migration(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, expected_conversion = conversion
    runner = _FakeMigrationRunner(expected_conversion)

    result = _run_operational(source, expected_conversion, _target(tmp_path), runner)

    assert runner.events == [
        "version",
        "dolt_version",
        "preflight_export",
        "preflight_attestation",
        "preflight_head",
        "dry_run",
        "dry_run_head",
        "first_import",
        "first_head",
        "first_export",
        "second_import",
        "final_head",
        "final_export",
    ]
    assert result.conversion.artifacts == expected_conversion.artifacts
    assert result.first_export == result.final_export == expected_conversion.artifacts[
        "issues.jsonl"
    ]
    assert result.report["status"] == "pass"
    assert result.report["counts"]["manifest_issues"] == 7
    assert result.report["idempotency"]["export_unchanged"] is True
    assert result.report["idempotency"]["dolt_main_head_unchanged"] is True
    assert result.report["idempotency"]["dry_run_head_unchanged"] is True
    assert result.report["idempotency"]["first_import_advanced_main"] is True
    assert result.report["credential_transport"] == "runner-environment-only"
    assert result.report["locked_toolchain"] == {
        "schema_version": taskmaster_beads.LOCKED_TOOLCHAIN_SCHEMA,
        "runtime_lock_path": "/locked/runtime-lock.json",
        "runtime_lock_sha256": "a" * 64,
        "tools": {
            "bd": {
                "path": "/locked/bin/bd",
                "version": "1.1.0",
                "binary_sha256": "b" * 64,
            },
            "dolt": {
                "path": "/locked/bin/dolt",
                "version": "2.2.0",
                "binary_sha256": "c" * 64,
            },
        },
    }

    import_calls = [
        (command, stdin)
        for command, stdin in runner.calls
        if Path(command[0]).name == "bd" and "import" in command
    ]
    assert len(import_calls) == 3
    assert all(stdin == expected_conversion.artifacts["issues.jsonl"] for _, stdin in import_calls)
    assert all("--dolt-auto-commit" in command for command, _ in import_calls)
    assert all("on" in command for command, _ in import_calls)
    export_calls = [
        command
        for command, _ in runner.calls
        if Path(command[0]).name == "bd" and "export" in command
    ]
    assert len(export_calls) == 3
    assert all("--readonly" in command and "--all" in command for command in export_calls)
    head_calls = [
        command
        for command, _ in runner.calls
        if Path(command[0]).name == "dolt" and "sql" in command
    ]
    assert len(head_calls) == 5
    assert sum("SELECT HASHOF('main') AS head;" in command for command in head_calls) == 4
    assert all("--password" not in command and "-p" not in command for command, _ in runner.calls)
    serialized_report = json.dumps(result.report, sort_keys=True)
    assert runner.failure_secret not in serialized_report


def test_operational_reconciliation_is_repeatable_exact_and_zero_mutation(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, expected_conversion = conversion
    runner = _FakeMigrationRunner(expected_conversion)
    issue_count = len(runner.expected_ids)
    stable_head = "7vse6duhku1cl388k3bl998q53iq6qeg"
    runner.preflight_export = expected_conversion.artifacts["issues.jsonl"]
    runner.target_attestation["issue_count"] = str(issue_count)
    runner.heads = [stable_head, stable_head, stable_head]
    evidence: dict[str, bytes] = {}

    result = _run_reconciliation(
        source,
        _target(tmp_path),
        runner,
        lambda name, content: evidence.__setitem__(name, content),
    )

    assert result.report["schema_version"] == taskmaster_beads.RECONCILIATION_RUN_SCHEMA
    assert result.report["action"] == "already-reconciled"
    assert result.report["counts"]["preexisting_records"] == issue_count
    assert result.report["state_before"] == result.report["state_after_dry_run"]
    assert result.report["state_before"] == result.report["state_after"]
    assert result.report["idempotency"] == {
        "status": "pass",
        "mutation_count": 0,
        "canonical_export_sha256": hashlib.sha256(
            taskmaster_beads._canonical_operational_export(
                expected_conversion.artifacts["issues.jsonl"],
                step="test",
            )
        ).hexdigest(),
        "first_raw_export_sha256": hashlib.sha256(
            expected_conversion.artifacts["issues.jsonl"]
        ).hexdigest(),
        "final_raw_export_sha256": hashlib.sha256(
            expected_conversion.artifacts["issues.jsonl"]
        ).hexdigest(),
        "dolt_main_head_before": stable_head,
        "dolt_main_head_after_dry_run": stable_head,
        "dolt_main_head_after": stable_head,
        "dry_run_head_unchanged": True,
        "dolt_state_unchanged": True,
        "export_unchanged": True,
        "raw_export_unchanged": True,
    }
    import_calls = [
        command
        for command, _stdin in runner.calls
        if Path(command[0]).name == "bd" and "import" in command
    ]
    assert len(import_calls) == 1
    assert "--dry-run" in import_calls[0]
    assert not any(
        "import" in command and "--dry-run" not in command
        for command, _stdin in runner.calls
    )
    assert set(evidence) == {
        "conversion/issues.jsonl",
        "conversion/blockers.jsonl",
        "conversion/hierarchy.jsonl",
        "conversion/manifest.json",
        "exports/first.jsonl",
        "exports/final.jsonl",
        "checkpoints/preflight-state.json",
        "checkpoints/post-dry-run-state.json",
        "checkpoints/final-state.json",
    }


def test_operational_reconciliation_rejects_foreign_or_drifted_target(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, expected_conversion = conversion
    runner = _FakeMigrationRunner(expected_conversion)
    runner.preflight_export = expected_conversion.artifacts["issues.jsonl"] + (
        b'{"id":"ags-foreign","title":"foreign"}\n'
    )
    runner.target_attestation["issue_count"] = str(len(runner.expected_ids))

    with pytest.raises(
        taskmaster_beads.OperationalMigrationError,
        match="failed exact export reconciliation",
    ):
        _run_reconciliation(source, _target(tmp_path), runner)


def test_operational_reconciliation_rejects_dry_run_head_mutation(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, expected_conversion = conversion
    runner = _FakeMigrationRunner(expected_conversion)
    runner.preflight_export = expected_conversion.artifacts["issues.jsonl"]
    runner.target_attestation["issue_count"] = str(len(runner.expected_ids))
    runner.heads = [
        "7vse6duhku1cl388k3bl998q53iq6qeg",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    ]

    with pytest.raises(
        taskmaster_beads.OperationalMigrationError,
        match="dry-run changed the Dolt head or working state",
    ):
        _run_reconciliation(source, _target(tmp_path), runner)


def test_operational_runner_emits_immutable_phase_evidence(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, expected_conversion = conversion
    runner = _FakeMigrationRunner(expected_conversion)
    evidence: dict[str, bytes] = {}

    def sink(name: str, content: bytes) -> None:
        assert name not in evidence
        evidence[name] = content

    result = _run_operational(
        source,
        expected_conversion,
        _target(tmp_path),
        runner,
        sink,
    )

    assert set(evidence) == {
        "conversion/issues.jsonl",
        "conversion/blockers.jsonl",
        "conversion/hierarchy.jsonl",
        "conversion/manifest.json",
        "checkpoints/empty-target.json",
        "checkpoints/first-import.json",
        "checkpoints/second-import.json",
        "exports/first.jsonl",
        "exports/final.jsonl",
    }
    assert evidence["conversion/issues.jsonl"] == expected_conversion.artifacts[
        "issues.jsonl"
    ]
    assert evidence["exports/first.jsonl"] == result.first_export
    assert evidence["exports/final.jsonl"] == result.final_export


def test_operational_runner_retains_first_mutation_checkpoint_on_later_failure(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, expected_conversion = conversion
    runner = _FakeMigrationRunner(expected_conversion)
    runner.fail_event = "first_export"
    evidence: dict[str, bytes] = {}

    with pytest.raises(taskmaster_beads.OperationalMigrationError):
        _run_operational(
            source,
            expected_conversion,
            _target(tmp_path),
            runner,
            lambda name, content: evidence.setdefault(name, content),
        )

    assert "checkpoints/first-import.json" in evidence
    assert "exports/first.jsonl" not in evidence
    assert "checkpoints/second-import.json" not in evidence


def test_operational_runner_rejects_dirty_or_multi_branch_target(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, expected_conversion = conversion
    runner = _FakeMigrationRunner(expected_conversion)
    runner.target_attestation["unexpected_working_changes"] = "1"
    runner.target_attestation["branch_count"] = "2"

    with pytest.raises(
        taskmaster_beads.OperationalMigrationError,
        match="unexpected working changes.*extra branches",
    ):
        _run_operational(source, expected_conversion, _target(tmp_path), runner)

    assert "dry_run" not in runner.events


def test_subprocess_runner_redacts_environment_from_repr() -> None:
    runner = taskmaster_beads.SubprocessMigrationCommandRunner(
        {
            "DOLT_CLI_PASSWORD": "dolt-secret",
            "BEADS_DOLT_PASSWORD": "beads-secret",
        }
    )

    rendered = repr(runner)

    assert "dolt-secret" not in rendered
    assert "beads-secret" not in rendered
    assert "<redacted>" in rendered
    command_result = taskmaster_beads.CommandResult(
        1,
        b"credential-value",
        b"credential-value",
    )
    assert "credential-value" not in repr(command_result)

    with pytest.raises(ValueError, match="positive integer"):
        taskmaster_beads.SubprocessMigrationCommandRunner(timeout_seconds=0)


def test_operational_runner_rejects_any_preexisting_export_before_import(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, expected_conversion = conversion
    runner = _FakeMigrationRunner(expected_conversion)
    runner.preflight_export = b'{"_type":"memory","id":"foreign"}\n'

    with pytest.raises(
        taskmaster_beads.OperationalMigrationError,
        match="contaminated target",
    ):
        _run_operational(source, expected_conversion, _target(tmp_path), runner)

    assert runner.events == ["version", "dolt_version", "preflight_export"]
    assert not any("import" in command for command, _ in runner.calls)


@pytest.mark.parametrize(
    ("phase", "match"),
    [
        ("dry-run", "dry-run import count drift"),
        ("first", "first import count drift"),
        ("second", "second import count drift"),
    ],
)
def test_operational_runner_rejects_import_count_drift(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
    phase: str,
    match: str,
) -> None:
    source, expected_conversion = conversion
    runner = _FakeMigrationRunner(expected_conversion)
    if phase == "dry-run":
        runner.dry_run["created"] = 6
    elif phase == "first":
        runner.first_import["created"] = 6
    else:
        runner.second_import["skipped"] = 6

    with pytest.raises(taskmaster_beads.OperationalMigrationError, match=match):
        _run_operational(source, expected_conversion, _target(tmp_path), runner)


@pytest.mark.parametrize(
    ("phase", "match"),
    [
        ("dry-run", "dry-run changed the Dolt main head"),
        ("first", "first Beads import did not advance"),
    ],
)
def test_operational_runner_requires_dry_run_noop_and_committed_first_import(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
    phase: str,
    match: str,
) -> None:
    source, expected_conversion = conversion
    runner = _FakeMigrationRunner(expected_conversion)
    if phase == "dry-run":
        runner.heads[1] = "22222222222222222222222222222222"
    else:
        runner.heads[2] = runner.heads[0]

    with pytest.raises(taskmaster_beads.OperationalMigrationError, match=match):
        _run_operational(source, expected_conversion, _target(tmp_path), runner)


def _drift_export(content: bytes, kind: str) -> bytes:
    records = _records(content)
    if kind == "count":
        records.pop()
    elif kind == "status":
        records[0]["status"] = "open"
    elif kind == "priority":
        records[0]["priority"] = 4
    elif kind == "provenance":
        records[0]["metadata"]["migration"]["source_sha256"] = "0" * 64
    elif kind == "graph":
        issue = next(record for record in records if record["id"] == "ags-0012")
        edge = next(item for item in issue["dependencies"] if item["type"] == "blocks")
        edge["depends_on_id"] = "ags-0013"
    else:  # pragma: no cover - test helper programming guard.
        raise AssertionError(kind)
    return _jsonl(records)


@pytest.mark.parametrize("kind", ["count", "status", "priority", "provenance", "graph"])
def test_operational_runner_fails_closed_on_first_export_drift(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
    kind: str,
) -> None:
    source, expected_conversion = conversion
    runner = _FakeMigrationRunner(expected_conversion)
    runner.first_export = _drift_export(runner.first_export, kind)

    with pytest.raises(
        taskmaster_beads.OperationalMigrationError,
        match="first post-import export failed exact export reconciliation",
    ):
        _run_operational(source, expected_conversion, _target(tmp_path), runner)

    assert "second_import" not in runner.events


def test_operational_runner_rejects_byte_or_dolt_head_change_on_second_import(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, expected_conversion = conversion

    export_changed = _FakeMigrationRunner(expected_conversion)
    normalized = _records(export_changed.final_export)
    normalized[0]["created_at"] = "2032-01-01T00:00:00Z"
    export_changed.final_export = _jsonl(normalized)
    with pytest.raises(
        taskmaster_beads.OperationalMigrationError,
        match="byte-exact canonical Beads export",
    ):
        _run_operational(source, expected_conversion, _target(tmp_path), export_changed)

    head_changed = _FakeMigrationRunner(expected_conversion)
    head_changed.heads[3] = "0123456789abcdefghijklmnopqrstuv"
    with pytest.raises(
        taskmaster_beads.OperationalMigrationError,
        match="changed the Dolt main head",
    ):
        _run_operational(source, expected_conversion, _target(tmp_path), head_changed)


def test_operational_runner_canonicalizes_dependency_order_only(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, expected_conversion = conversion
    runner = _FakeMigrationRunner(expected_conversion)
    records = _records(runner.final_export)
    record = next(item for item in records if len(item.get("dependencies", [])) > 1)
    record["dependencies"] = list(reversed(record["dependencies"]))
    runner.final_export = _jsonl(records)

    result = _run_operational(source, expected_conversion, _target(tmp_path), runner)

    assert result.report["idempotency"]["export_unchanged"] is True
    assert result.report["idempotency"]["raw_export_unchanged"] is False


def test_operational_runner_redacts_failed_command_output(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, expected_conversion = conversion
    runner = _FakeMigrationRunner(expected_conversion)
    runner.fail_event = "dry_run"

    with pytest.raises(taskmaster_beads.OperationalMigrationError) as captured:
        _run_operational(source, expected_conversion, _target(tmp_path), runner)

    message = str(captured.value)
    assert runner.failure_secret not in message
    assert "exit code 9" in message
    assert all(
        runner.failure_secret not in argument
        for command, _ in runner.calls
        for argument in command
    )


def test_operational_runner_validates_frozen_hash_before_any_command(
    tmp_path: Path,
    conversion: tuple[bytes, taskmaster_beads.ConversionResult],
) -> None:
    source, expected_conversion = conversion
    runner = _FakeMigrationRunner(expected_conversion)

    with pytest.raises(taskmaster_beads.ConversionError, match="source SHA-256 mismatch"):
        taskmaster_beads.run_operational_migration(
            source,
            expected_source_sha256="0" * 64,
            target_directory=_target(tmp_path),
            dolt=taskmaster_beads.DoltConnection(
                host="127.0.0.1",
                port=3306,
                user="aegis_beads",
                database="aegis_beads",
            ),
            runner=runner,
            locked_toolchain={
                "schema_version": taskmaster_beads.LOCKED_TOOLCHAIN_SCHEMA,
                "runtime_lock_path": "/locked/runtime-lock.json",
                "runtime_lock_sha256": "a" * 64,
                "tools": {
                    "bd": {
                        "path": "/locked/bin/bd",
                        "version": "1.1.0",
                        "binary_sha256": "b" * 64,
                    },
                    "dolt": {
                        "path": "/locked/bin/dolt",
                        "version": "2.2.0",
                        "binary_sha256": "c" * 64,
                    },
                },
            },
            bd_executable="/locked/bin/bd",
            dolt_executable="/locked/bin/dolt",
        )

    assert runner.calls == []
