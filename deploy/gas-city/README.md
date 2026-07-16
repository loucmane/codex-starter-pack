# Shared Gas City deployment contract

This directory is the source-controlled, secret-free contract for the shared
Gas City control plane at `/home/loucmane/gas-city`. It is intentionally
**dormant** until the Aegis migration, provider canaries, and recovery gates
pass. Installing these files must not move a project, modify an active project
checkout, or start an agent.

The current lock status is `staged_pending_provisioning`. A null observed model
or receipt digest is deliberate: neither provider has produced production
evidence yet. POC receipts are not production receipts.

## Authority and exclusions

- Git remains authoritative for project source and durable documentation.
- Aegis Beads on its dedicated Dolt service becomes authoritative for work
  state only after exact Taskmaster reconciliation passes.
- Obsidian is a deterministic, disposable projection; it is never a writer to
  Beads.
- Graphiti, Cognee, and Ollama are excluded from this phase. No memory service,
  local model, or MCP endpoint for them belongs in worker configuration.
- Taskmaster remains rollback evidence until the canary and 24–72-hour soak
  complete. Do not delete its files during cutover.

`runtime-lock.json` is the machine-readable desired-state lock. `config/`
contains the city, pack, provider, and machine-site templates. `compose.yaml`
and `docker/` define the runtime boundary. `bin/` contains host-side provider
launchers; it never mounts a real user home.

## Manual Claude and Codex sessions

An Aegis cutover is not complete until the project enrollment is activated.
Enrollment is explicit; neither `.beads` nor `.taskmaster` selects authority.
The external binding is stored at
`runtime/authority/enrollments/<canonical-repository-key>.json`, while a
secret-free mode-`0600` pointer is atomically published in the primary
repository's Git common directory as `.git/aegis-authority-enrollment.json`.
Linked worktrees resolve that same Git common directory, so they cannot drift
from the primary checkout's authority state.

After the generation-2 Beads receipt and its lifecycle history have committed,
and while workers and Taskmaster updates are still stopped, run the pinned
runtime directly with the same activation timestamp recorded by the cutover:

```bash
python3 ~/gas-city/runtime/authority/task-authority.py activate-enrollment \
  --project-root /home/loucmane/codex \
  --city-root /home/loucmane/gas-city \
  --activated-at 'YYYY-MM-DDTHH:MM:SSZ'
```

The command validates the exact Aegis repository identity, loopback Dolt
coordinates, application-secret metadata, generation-2 receipt, and pinned
task-authority, `bd`, Claude, Codex, and Claude-settings digests. It writes the
external binding first and publishes the Git-common-dir pointer last. A crash
before the final publish leaves the repository unenrolled during the stopped
cutover; a crash after it leaves a complete enrollment. Divergent reruns are
refused.

Once enrolled, a normal unwrapped process with missing, partial, stale, or
mismatched authority variables fails closed in readiness, Claude PreToolUse,
the Codex guard, Aegis task selection, and Taskmaster mutation helpers. There
is no advisory or break-glass authority bypass. Start attended subscription
sessions through:

```bash
~/gas-city/bin/aegis-claude
~/gas-city/bin/aegis-codex
```

These launchers validate the live receipt and all pinned files, reject API-key,
endpoint, model, configuration, MCP, sandbox, and auth-boundary overrides,
read `runtime/secrets/aegis-app-password` without following aliases, place the
password only in the child environment, and `exec` the pinned subscription
CLI. Claude is fixed to `claude-fable-5`; Codex is fixed to `gpt-5.6-sol` with
`xhigh` reasoning. The wrapper itself does not read provider credentials and
does not modify a shell profile. Its child `PATH` includes a fail-closed
`task-master` shim, so an enrolled agent cannot mutate rollback evidence by
invoking the legacy CLI directly. The final provider process is also launched
through the root-owned `/usr/bin/bwrap`: the repository remains available at
its normal path, but its exact `.taskmaster` tree is overlaid read-only by the
kernel. Direct file writes, renames, and alternate executables therefore fail
even when an agent bypasses the shim. Missing, user-writable, or incorrectly
owned `bwrap` is a launch failure.

Rollback ordering is equally strict: stop workers, commit and verify the
generation-3 Taskmaster lifecycle receipt, then deactivate enrollment:

```bash
python3 ~/gas-city/runtime/authority/task-authority.py deactivate-enrollment \
  --project-root /home/loucmane/codex \
  --rollback-generation 3
```

Deactivation atomically renames the active pointer to a generation-named
archive in the Git common directory. Until that rename succeeds, the active
marker sees the generation mismatch and all mutations remain fail-closed. If
the rename commits but result reporting or directory sync fails, an identical
rerun verifies the archived pointer and generation-3 receipt and succeeds.
Only after deactivation does the repository return to legacy implicit
Taskmaster compatibility. Other, unenrolled repositories are unaffected.

## Network and identity topology

The HQ and Aegis databases are independent Dolt processes with different data
mounts, databases, application users, root credentials, and private networks.
HQ adopts the existing stopped `~/gas-city/.beads/dolt` store through a narrow
bind mount so initialization does not discard Gas City's existing schema,
commits, or working set; Aegis starts in a new dedicated named volume:

```text
host gc/bd --> 127.0.0.1:33070 --> hq-dolt-loopback --> hq-dolt
host gc/bd --> 127.0.0.1:33071 --> aegis-dolt-loopback --> aegis-dolt

HQ worker    --> gas-city-hq-control    --> gas-city-hq-dolt
Mayor        --> gas-city-hq-control    --> gas-city-hq-dolt
           |                           \--> gas-city-aegis-dolt
           \--> gas-city-hq-egress-proxy    --> gas-city-hq-egress
Aegis worker --> gas-city-aegis-control --> gas-city-aegis-dolt
             \--> gas-city-aegis-egress-proxy --> gas-city-aegis-egress
```

The database containers have no published ports and remain only on internal
control networks. Two non-root, read-only, capability-free `socat` relays use
fixed destinations and publish only to host loopback through separate ingress
bridges with inter-container communication and outbound masquerading disabled;
there is no public host bind. This sidecar boundary is required because Docker
does not materialize a host port mapping for a container attached only to an
`internal: true` bridge. Workers cannot use host loopback, so the launcher verifies a lock-bound
worker city file whose only differences are the two service-DNS endpoints. No
static bridge address is assumed. Aegis workers never join the HQ network and
HQ workers never join the Aegis network. The Aegis Dolt service alone is
dual-homed onto both private control networks so the trusted Fable Mayor can
route `gc bd --rig aegis` and `gc sling` from HQ. Only the exact Mayor identity
receives both endpoint-keyed credentials and the minimal read-only Aegis Beads
metadata/config overlay; ordinary HQ agents have neither, even though TCP
reachability exists on their shared control network. Separate boundary proxies
remain on separate outbound bridges and cannot become a cross-network
application bridge.

Gas City 1.3.5's bundled managed Dolt is not an acceptable fallback because its
verified default listener is broad and initially unauthenticated. Both
`[dolt]` and `rigs[].dolt_*` therefore name explicit external loopback
endpoints. If either external endpoint is missing or unhealthy, keep the city
stopped; never remove those overrides to make startup pass.

## Files that must stay outside Git

Create these roots owner-only:

```text
~/gas-city/runtime/secrets/               # mode 0700
  hq-root-password                       # mode 0600
  hq-app-password                        # mode 0600
  aegis-root-password                    # mode 0600
  aegis-app-password                     # mode 0600
  github-app-id                          # mode 0600; guarded App identity
  github-installation-id                 # mode 0600; guarded installation identity
  github-app-private-key.pem             # mode 0600; delivery signing key
~/gas-city/runtime/state/                 # mode 0700
  provider-auth/{claude,codex}/           # attended owner-only auth sources
  provider-sessions/<scope>/<agent>/<provider>/<session>/
                                          # isolated writable home per session
  model-receipts/                         # runtime evidence, never prefilled
  dolt-backups/{hq,aegis}/                # mode 0700; server-visible native backups
```

Generate four distinct 32-byte-or-longer values using an approved password
generator. The container entrypoint accepts only a conservative printable
alphabet and refuses reused root/application credentials. Never put a secret in
`runtime-lock.json`, Compose environment values, a Dockerfile, a receipt, or a
shell history entry.

`GAS_CITY_AEGIS_DOLT_VOLUME` defaults to the production volume
`gas-city-aegis-dolt-data`. Set it to a unique name only for an isolated
rehearsal so stale simulated credentials or data cannot be mistaken for the
production Aegis store.

Do not retain database passwords in project `.beads/.env` files. Attended host
operations read the applicable password from `runtime/secrets`; provider
containers receive the same file as a read-only Docker secret and set the
Beads connection environment only in the child process. HQ uses loopback port
33070 and user `gas_city_hq`; Aegis uses loopback port 33071 and user
`aegis_beads`. The application account for one service has no grant on the
other service because the services do not share a privilege store.

## Provisioning runbook

All commands in this section are attended. Keep the supervisor stopped and both
workspace and Aegis rig suspended throughout provisioning.

The host must provide a root-owned, non-user-writable, executable
`/usr/bin/bwrap` (Bubblewrap). It is required for attended Claude and Codex
sessions after enrollment; verify this prerequisite before the Taskmaster
freeze. Containerized workers use the separate Docker isolation boundary and
do not invoke this host launcher.

1. Run the source-bundle provisioner; never copy the manifest by hand. It first
   verifies its own manifest entry, the manifest-bound staged runtime lock,
   every source byte and mode, and the exact gc 1.3.5, bd 1.1.0, and Dolt 2.2.0
   binaries. It then proves the machine supervisor and managed provider are
   stopped, captures a private byte-for-byte pre-copy bundle outside the city,
   and installs only non-topology files. Existing `city.toml`, `pack.toml`,
   `packs.lock`, and `.gc/site.toml` remain unchanged. For a genuinely empty
   city it installs the manifest-bound provider launchers first and invokes
   exactly `GC_DOLT=skip gc init --file config/city.toml --preserve-existing
   --skip-provider-readiness --no-start /home/loucmane/gas-city`; it neither
   contacts a Dolt endpoint nor probes a provider, registers, or starts the
   city. A killed init must pass the upstream existing-city resume path before
   the provisioner accepts the scaffold.

   ```bash
   /home/loucmane/codex/deploy/gas-city/bin/provision-control-plane prepare \
     --source-root /home/loucmane/codex/deploy/gas-city \
     --city-root /home/loucmane/gas-city \
     --transaction-dir /home/loucmane/.gas-city-provisioning/aegis-cutover-1
   ```

   Preserve the returned `stage_receipt`. An identical rerun must be
   `already-staged` with zero mutations. A partial run resumes only from its
   anchored intent; third-party destination drift fails closed. Do not put the
   transaction directory under `~/gas-city`.

2. Materialize the verified build inputs described in `artifacts/README.md`,
   then build and promote all four local images through the deployed,
   manifest-verified admin. No Docker Hub Dolt tag is used and no image ID is
   copied manually:

   ```bash
   /home/loucmane/gas-city/bin/gas-city-admin build-images \
     --lock /home/loucmane/gas-city/runtime-lock.json \
     --context /home/loucmane/codex/deploy/gas-city \
     --docker /usr/bin/docker

   /home/loucmane/gas-city/bin/gas-city-admin promote-images \
     --lock /home/loucmane/gas-city/runtime-lock.json \
     --docker /usr/bin/docker
   ```

   Promotion advances the lock only to `provisioned_pending_canary` and binds
   all four immutable `sha256:` image IDs to the private build receipt.

3. Record the existing HQ Dolt status, commit, and working-set diff and take a
   private cold snapshot of `~/gas-city/.beads/dolt`. Create the four distinct
   owner-only external secret files. Create the two owner-only native-backup
   roots before Compose evaluates its required bind sources:

   ```bash
   install -d -m 0700 \
     /home/loucmane/gas-city/runtime/state/dolt-backups/hq \
     /home/loucmane/gas-city/runtime/state/dolt-backups/aegis
   ```

   Select the HQ data root explicitly; Compose refuses to guess it. For a
   fresh city whose stage receipt reports
   `topology_action: initialized_external`, create a separate external-server
   root as the owning user. Keep the new local `.beads` scaffold pristine for
   the guarded external initializer. Do not let Docker create a missing bind
   source as root:

   ```bash
   install -d -m 0700 /home/loucmane/gas-city/runtime/state/dolt-data/hq
   ```

   For an existing managed-city cutover, use the already cold-snapshotted
   `/home/loucmane/gas-city/.beads/dolt` instead; do not recreate or chmod it.
   Set `GAS_CITY_HQ_DOLT_DATA_DIR` to exactly the applicable reviewed path on
   every Compose invocation.

   Start only the two Dolt services, two
   egress proxies, and two fixed loopback relays through the staged receipt;
   the wrapper rejects worker
   services and every other mutating Compose command in this phase:

   ```bash
   GC_CITY_ROOT=/home/loucmane/gas-city \
   GAS_CITY_HQ_DOLT_DATA_DIR=/exact/reviewed/hq-data-root \
   GAS_CITY_HQ_DOLT_BACKUP_DIR=/home/loucmane/gas-city/runtime/state/dolt-backups/hq \
   GAS_CITY_AEGIS_DOLT_BACKUP_DIR=/home/loucmane/gas-city/runtime/state/dolt-backups/aegis \
   /home/loucmane/gas-city/bin/compose-locked \
     --provisioning-stage /home/loucmane/.gas-city-provisioning/aegis-cutover-1/stage-receipt.json \
     up --detach hq-dolt aegis-dolt hq-egress-proxy aegis-egress-proxy hq-dolt-loopback aegis-dolt-loopback
   ```

   Require both health checks to pass, confirm the only host listeners are
   `127.0.0.1:33070` and `127.0.0.1:33071`, and prove the HQ bind source is the
   exact cold-snapshotted store.

4. Before changing HQ topology, initialize the empty Aegis Beads client binding
   against its dedicated external service. This is safe while Taskmaster still
   owns task authority; it creates no migrated issues. It is required because
   the guarded HQ cutover proves Aegis remains isolated and therefore refuses a
   missing or unverified Aegis `.beads` binding:

   ```bash
   GAS_CITY_TARGET_DOLT_PASSWORD_FILE=/home/loucmane/gas-city/runtime/secrets/aegis-app-password \
   /home/loucmane/gas-city/bin/gas-city-admin initialize-aegis-beads \
     --lock /home/loucmane/gas-city/runtime-lock.json \
     --target-repo /home/loucmane/codex \
     --bd /home/loucmane/gas-city/bin/bd \
     --dolt /home/loucmane/gas-city/bin/dolt \
     --git /usr/bin/git
   ```

   The initializer forces `BD_BACKUP_ENABLED=false` for every pinned bd
   preflight and attestation. Gas City owns the attended native backup and
   restore receipts; the least-privilege Aegis account must never attempt to
   register bd's opportunistic backup remote or create `.beads/backup` during
   a read-only export. After the live empty-target attestation, the same
   crash-safe transaction registers `issue_prefix=ags` and Gas City 1.3.5's
   exact 13 custom issue types in the external Dolt `config` table, then
   explicitly applies pinned Beads schema migrations with auto-commit so later
   dry-run imports cannot advance the baseline head, and finally
   publishes the matching canonical local config and minimal project metadata
   emitted by pinned `gc rig set-endpoint`; it does not rewrite `city.toml` or
   `.gc/site.toml`. Both representations are attested before publication. Run
   the command a second time immediately: it must return
   `already-initialized` without changing the published tree.

5. Activate the final stopped topology before sealing any endpoint evidence.
   This ordering is mandatory: it makes the endpoint receipt's before and after
   manifests include the exact final `city.toml`, `pack.toml`, `packs.lock`, and
   `.gc/site.toml`, so endpoint rollback and then control-plane rollback remain
   composable. Activation verifies the promoted images and staged receipt,
   installs only those four deferred files, validates the full deployed bundle
   and Gas City configuration, and proves the supervisor stayed stopped:

   ```bash
   /home/loucmane/codex/deploy/gas-city/bin/provision-control-plane activate-topology \
     --source-root /home/loucmane/codex/deploy/gas-city \
     --city-root /home/loucmane/gas-city \
     --transaction-dir /home/loucmane/.gas-city-provisioning/aegis-cutover-1
   ```

   Preserve `activation-receipt.json`. An interrupted activation resumes only
   when every deferred file is either its anchored prestate or its exact final
   manifest entry; all other mixtures fail closed. An identical completed run
   is zero-mutation `already-activated`.

   For a newly initialized city only, initialize the virgin external HQ
   database after activation and before its endpoint transition. This guarded
   command accepts only the exact empty `hq` database or a known empty subset
   left by an interrupted pinned initialization. It journals before invoking
   exact `bd 1.1.0 init --server --external --reinit-local`, rejects foreign
   tables and every issue/content row, requires the exact pinned 26-table and
   two-view empty schema, registers Gas City 1.3.5's exact 13 custom issue
   types in both the external Dolt `config` table and local config, explicitly
   applies pinned Beads schema migrations, proves the supervisor stayed
   stopped, and is idempotent:

   ```bash
   GAS_CITY_HQ_DOLT_PASSWORD_FILE=/home/loucmane/gas-city/runtime/secrets/hq-app-password \
   /home/loucmane/gas-city/bin/gas-city-admin initialize-hq-beads \
     --city-root /home/loucmane/gas-city \
     --lock /home/loucmane/gas-city/runtime-lock.json \
     --evidence-dir /home/loucmane/gas-city/runtime/evidence/beads-initialization/hq-external-1
   ```

   Existing managed cities skip only that initialization. Both new and
   existing cities then run the same guarded HQ endpoint transition. The
   provisioner's first stopped-supervisor probe occurs before its backup and
   intentionally captures any upstream-generated
   `.gc/scripts/gc-beads-bd.sh`. The cutover anchors the activated topology,
   performs the official dry run and apply, requires the HQ project identity,
   and proves both endpoints without starting the supervisor:

   ```bash
   GAS_CITY_HQ_DOLT_PASSWORD_FILE=/home/loucmane/gas-city/runtime/secrets/hq-app-password \
   /home/loucmane/gas-city/bin/gas-city-admin endpoint-transition-hq \
     --city-root /home/loucmane/gas-city \
     --lock /home/loucmane/gas-city/runtime-lock.json \
     --evidence-dir /home/loucmane/gas-city/runtime/evidence/endpoint-transition/hq-external-cutover-1
   ```

   Preserve the returned `receipt_path` for either path. A fresh city is not
   allowed to finalize without it. Finalization performs no topology mutation:
   it revalidates the activation, exact transition receipt, current stopped
   endpoint tree, full deployed manifest, and Gas City configuration:

   ```bash
   /home/loucmane/codex/deploy/gas-city/bin/provision-control-plane finalize \
     --source-root /home/loucmane/codex/deploy/gas-city \
     --city-root /home/loucmane/gas-city \
     --transaction-dir /home/loucmane/.gas-city-provisioning/aegis-cutover-1 \
     --endpoint-transition-receipt /home/loucmane/gas-city/runtime/evidence/endpoint-transition/hq-external-cutover-1/transition-receipt.json
   ```

   If the cutover is abandoned, stop the six bootstrap services, take a final
   database backup, run the exact endpoint rollback first, and then restore the
   pre-copy control bundle. Never edit endpoint metadata manually or start the
   old managed service from the endpoint receipt alone:

   ```bash
   /home/loucmane/gas-city/bin/gas-city-admin endpoint-rollback-hq \
     --city-root /home/loucmane/gas-city \
     --lock /home/loucmane/gas-city/runtime-lock.json \
     --transition-receipt /home/loucmane/gas-city/runtime/evidence/endpoint-transition/hq-external-cutover-1/transition-receipt.json \
     --evidence-dir /home/loucmane/gas-city/runtime/evidence/endpoint-rollback/hq-external-cutover-1

   /home/loucmane/codex/deploy/gas-city/bin/provision-control-plane rollback \
     --source-root /home/loucmane/codex/deploy/gas-city \
     --city-root /home/loucmane/gas-city \
     --transaction-dir /home/loucmane/.gas-city-provisioning/aegis-cutover-1 \
     --endpoint-rollback-receipt /home/loucmane/gas-city/runtime/evidence/endpoint-rollback/hq-external-cutover-1/rollback-receipt.json
   ```

   Before HQ transition—including after topology activation—
   `provision-control-plane rollback` needs no endpoint receipt and restores
   the original topology directly. Before activation it accepts each deferred
   topology file only in the exact upstream `gc init --no-start` state bound by
   `stage-receipt.json`; after or during activation it accepts only that state
   or the exact manifest destination. This makes rollback crash-resumable
   without treating an arbitrary intermediate file as trusted. A city
   initialized from an empty target is
   returned to an exactly empty tree; its promoted lock, control manifest, and
   immutable image-build receipt are first copied into the private transaction
   evidence directory. Rollback refuses symbolic links, special files, or
   nested mounts instead of deleting across an unproven boundary. After
   transition/finalization it refuses
   rollback unless endpoint rollback first restores the receipt's activated
   pre-transition state and proves it stayed stopped; control rollback then
   restores the original pre-provisioning bytes. An identical control rollback
   is zero-mutation `already-restored`.

6. Authenticate each provider with the guarded bootstrap command. The HQ
   control network and its filtered egress proxy must already be healthy. Run
   each command from a real attended terminal; redirected, piped, or headless
   execution is intentionally rejected:

   ```bash
   ~/gas-city/bin/provider-auth-bootstrap claude
   ~/gas-city/bin/provider-auth-bootstrap codex
   ```

   The command accepts exactly `claude` or `codex`, verifies the provider's
   immutable worker and egress-proxy images through the deployed runtime lock
   and private image receipt, confirms that Docker resolves those same image
   IDs, and rejects a proxy outside the exact HQ control/egress networks. It
   then runs
   only the subscription login command (`claude auth login --claudeai` or
   `codex login --device-auth`) on the private HQ control network. Its sole bind
   mount is a newly generated owner-only disposable home. It does not mount or
   inspect the host home, project files, database credentials, GitHub
   credentials, or an existing provider-auth source.

   The provider's own interactive browser/device prompt is shown directly in
   the terminal. The bootstrap wrapper never prints or replays credential JSON.
   After a successful login it rejects symlinks, unsafe ownership/modes,
   duplicate-key or malformed JSON, and unexpected artifact paths. It copies
   only the expected artifact into the owner-only seed directory through an
   atomic mode-`0600` installation, then removes the disposable home:

   - sign Codex CLI 0.144.4 into the intended ChatGPT subscription inside the
     Codex bootstrap home, then install `auth.json` as
     `runtime/state/provider-auth/codex/auth.json`;
   - sign Claude into the intended subscription inside the Claude bootstrap
     home, then install `.credentials.json` as
     `runtime/state/provider-auth/claude/credentials.json`;
   A first-time bootstrap refuses to overwrite an existing seed. Rotation is an
   explicit compare-and-swap operation: hash the current seed, pass that exact
   lowercase digest, and select the same provider. The command rechecks the
   existing safe file immediately before atomic replacement and rejects stale
   digests, symlinks, concurrent bootstrap, absent seeds, or a login that
   produces no credential change:

   ```bash
   current_sha=$(sha256sum ~/gas-city/runtime/state/provider-auth/codex/auth.json | awk '{print $1}')
   ~/gas-city/bin/provider-auth-bootstrap codex \
     --rotate --expected-current-sha256 "$current_sha"
   unset current_sha
   ```

   Repeat with `claude` and
   `runtime/state/provider-auth/claude/credentials.json` when rotating Claude.
   A SHA-256 digest is comparison metadata, not the credential; never print or
   inspect the JSON itself.

   Create a dedicated GitHub App for delivery. Grant the App only repository
   `Contents: write`, `Pull requests: write`, and the implicit
   `Metadata: read`; install it only on `loucmane/codex-starter-pack`. Store its
   decimal App ID, decimal installation ID, and PEM private key in the three
   exact owner-only files listed above. Do not pre-generate or retain a PAT or
   installation token, use the host `gh` session, mount `~/.ssh`, or reuse a
   personal key. Configure one active ruleset for `main`, with no bypass
   actors, that requires a pull request, forbids deletion and non-fast-forward
   updates, and requires at least one strict status check. The host broker
   verifies those effective rules through GitHub before every authority
   session and refuses to issue a credential if any part of the contract
   differs.

   After the isolated model preflight succeeds, the manifest-bound
   `github-app-token-broker` signs its App JWT through root-controlled OpenSSL,
   requests one token for that one repository and exact permission set, and
   requires GitHub's returned lifetime to be 50–65 minutes. It writes a new
   mode-`0400` token and receipt beneath the session's host-owned broker state.
   Only that token and its receipt enter the authority-bearing container; the
   App private key never does. The supervisor revalidates repository,
   permissions, rules, token digest, receipt digest, lifetime, and at least five
   minutes of remaining validity before configuring `gh` and Git. A failed or
   expired issuance stops the worker; there is no static-token fallback.

   Treat `auth.json`, Claude credentials, and the GitHub App private key as
   passwords. The launcher copies only the provider authentication file into a
   new writable home
   scoped by rig, agent, provider, and exact session. A worker can refresh its
   own subscription session but cannot persist configuration into another role
   or session. New sessions are always seeded from the attended owner-only
   source; refresh or reauthenticate that source through the bootstrap workflow
   when it expires.
   `claude-settings.json` disables project-wide MCP auto-enablement, preserves
   the dangerous-mode warning, and disables safeguard-driven model switching.

7. Validate configuration while stopped. Run these checks from the city root,
   not from a linked project worktree: Git performs repository discovery even
   for the global `beads.role` probe, so an inherited worktree `GIT_DIR` is not
   an acceptable operator environment. Ensure the required maintainer role is
   present, put only the manifest-bound city tools on the front of `PATH`, and
   inject the HQ credential from its private file without printing it:

   ```bash
   cd /home/loucmane/gas-city
   git config --global beads.role maintainer
   export PATH=/home/loucmane/gas-city/bin:/usr/bin:/bin
   IFS= read -r GC_DOLT_PASSWORD < runtime/secrets/hq-app-password
   export GC_DOLT_PASSWORD
   BEADS_DOLT_PASSWORD="$GC_DOLT_PASSWORD" \
   DOLT_CLI_PASSWORD="$GC_DOLT_PASSWORD" \
   BD_BACKUP_ENABLED=false \
     gc config show --validate
   BEADS_DOLT_PASSWORD="$GC_DOLT_PASSWORD" \
   DOLT_CLI_PASSWORD="$GC_DOLT_PASSWORD" \
   BD_BACKUP_ENABLED=false \
     gc doctor --json
   unset GC_DOLT_PASSWORD
   gc supervisor status --json
   ```

   Both validation commands must report no blocking failure, and the
   supervisor must still report `running:false`. A failed external endpoint
   check is a stop condition, not permission to use managed Dolt.

8. Take a fresh, immutable Taskmaster snapshot and database backups immediately
   before the announced 10–20 minute Taskmaster update freeze. Run the exact,
   idempotent migration and its independent reconciliation gate. Do not resume
   Aegis unless source record count, exported Bead count, dependency/hierarchy
   edge counts, IDs, fields, and target emptiness/allowlist all match. Re-running
   reconciliation must produce zero mutations.

   Before freezing, explicitly review every active child under a non-active
   parent. The current source intentionally contains pending `193.1`–`193.7`
   beneath done task `193` and pending `208.2`–`208.5` beneath deferred task
   `208`. Exact migration preserves them as open Beads issues, so obtain an
   operator decision to keep them open or correct their Taskmaster statuses
   through Taskmaster before the snapshot. Never normalize them in the
   converter or edit the frozen migration artifacts.

   With the step-4 Aegis binding still empty and all workers stopped, take the
   source snapshot and run the guarded migration against the unchanged primary
   Aegis checkout:

   ```bash
   /home/loucmane/gas-city/bin/gas-city-admin snapshot-taskmaster \
     --repo /home/loucmane/codex \
     --output /home/loucmane/gas-city/runtime/evidence/snapshots/aegis-cutover

   GAS_CITY_TARGET_DOLT_PASSWORD_FILE=/home/loucmane/gas-city/runtime/secrets/aegis-app-password \
   /home/loucmane/gas-city/bin/gas-city-admin migrate-taskmaster \
     --lock /home/loucmane/gas-city/runtime-lock.json \
     --snapshot /home/loucmane/gas-city/runtime/evidence/snapshots/aegis-cutover \
     --target-repo /home/loucmane/codex \
     --evidence-dir /home/loucmane/gas-city/runtime/evidence/migration/aegis \
     --bd /home/loucmane/gas-city/bin/bd \
     --dolt /home/loucmane/gas-city/bin/dolt \
     --dolt-host 127.0.0.1 --dolt-port 33071 \
     --dolt-user aegis_beads --dolt-database aegis_beads \
     --no-tls --tag master --prefix ags

   GAS_CITY_TARGET_DOLT_PASSWORD_FILE=/home/loucmane/gas-city/runtime/secrets/aegis-app-password \
   /home/loucmane/gas-city/bin/gas-city-admin reconcile-taskmaster \
     --lock /home/loucmane/gas-city/runtime-lock.json \
     --snapshot /home/loucmane/gas-city/runtime/evidence/snapshots/aegis-cutover \
     --target-repo /home/loucmane/codex \
     --evidence-dir /home/loucmane/gas-city/runtime/evidence/reconciliation/aegis-1 \
     --bd /home/loucmane/gas-city/bin/bd \
     --dolt /home/loucmane/gas-city/bin/dolt \
     --dolt-host 127.0.0.1 --dolt-port 33071 \
     --dolt-user aegis_beads --dolt-database aegis_beads \
     --no-tls --tag master --prefix ags
   ```

   `migrate-taskmaster` remains a one-way empty-target operation. The separate
   `reconcile-taskmaster` gate accepts only the exact graph re-derived from the
   frozen snapshot, performs a stdin-only bd dry-run, and requires identical
   Dolt head, working set, branches, and canonical export before and after. It
   writes a zero-mutation receipt and can be rerun into a new evidence
   directory; each run must return `already-reconciled` with
   `mutation_count: 0`. Foreign records, field or edge drift, source drift, or
   any dry-run mutation fail closed.

   Do not rerun `bd init` directly in Aegis and do not create `.beads/.env`.
   A changed or unproved step-4 binding, a contaminated target, source drift,
   or a changed Taskmaster snapshot is a stop condition—not permission to
   repair state manually.

9. Run one controlled worker at a time. The launcher rejects the user's active
   primary Aegis checkout and accepts only a Gas City assigned worktree or
   dedicated agent directory. It mounts that exact worktree read/write, then
   overlays both its `.git` marker and the canonical primary/common Git
   directory read-only. A host-generated broker gives the worker a durable,
   session-private `GIT_DIR` whose object store has a read-only alternate to
   the primary object store. Thus unsetting `GIT_DIR`, invoking `/usr/bin/git`
   directly, or writing metadata paths cannot mutate primary/common refs,
   config, hooks, objects, or another worktree's index. It also mounts read-only city runtime paths, its isolated
   per-session provider home, and the
   applicable application credential. It never mounts the entire `.gc` tree or
   a user home. Containers are non-root, capability-free, read-only at the
   image layer, resource-limited, use Docker's default seccomp profile, and
   connect to only one database network. Codex's inner bwrap sandbox is disabled
   because this outer Docker boundary is the sandbox; `seccomp=unconfined` is
   forbidden.

   Aegis workflow kickoff is a provider-free first container stage after
   generation-2 authority and secret loading. The immutable startup helper runs
   `gc hook --claim --json`, proves the claimed pinned formula graph and its
   exactly-one-child input convoy, and derives the durable source task from
   that graph. It never derives source work from `GC_BEAD_ID`, which may name a
   convoy, molecule, or other infrastructure record. The helper validates the
   existing outer polecat worktree and the broker's private Git directory,
   while separately binding the canonical source common directory, prepares
   or resumes only `polecat/<work-bead>`, compare-validates its exact
   `metadata.branch` and `metadata.work_dir`, and then invokes:

   ```bash
   ./.aegis/bin/aegis kickoff --target-dir . --bead '<verified-work-bead-id>'
   ```

   The Aegis source repository is intentionally not foundation-installed into
   itself. The launcher mounts a private nested tmpfs at `.aegis/bin`; the
   supervisor writes one exact mode-`0500` launcher there. That launcher loads
   the root-owned, SHA-256-bound offline `aegis-runtime.whl` through the
   root-owned runtime shim. For every invocation the shim serializes on a lock
   inside that tmpfs, creates a temporary foundation manifest only when no real
   manifest exists, retains its descriptor, and removes only the exact inode it
   created. A real manifest is never overwritten. Thus `.aegis/bin` and
   installation assets never touch the host worktree; only the intentional
   Bead-scoped workflow state persists. No pip, package index, `npx`, or network
   runtime resolution is used.

   Before an AI process starts, the host broker validates and freezes the
   startup receipt outside every container-writable mount, then rebinds that
   exact file read-only for the provider stage. On a verified clean exit, the
   broker requires a fast-forward descendant of the frozen starting/base
   commits, unchanged protected refs/config/hooks, and a clean worktree. It
   imports objects without creating an import ref, compare-and-swaps only the
   authorized `polecat/<work-bead>` ref, and resynchronizes only that linked
   worktree's HEAD/index. Crash, model mismatch, receipt tamper, non-fast-forward
   history, or a host ref race promotes nothing and retains the private Git
   state for restart evidence.

   This boundary protects host Git metadata. It does not parse or constrain an
   HTTPS push refspec after TLS encryption. The short-lived App token and
   mandatory no-bypass `main` ruleset prevent the worker from directly updating,
   deleting, or force-pushing the default branch, while the one-repository App
   scope limits the blast radius. If the broker cannot prove that remote policy,
   it withholds the write token and stops the session; local Git broker success
   is not evidence of remote branch authorization. The token can still write an
   unprotected branch during its sub-hour lifetime, because GitHub rulesets do
   not dynamically bind a credential to its one assigned
   `polecat/<work-bead>` ref and the local proxy cannot inspect encrypted GitHub
   API mutations. A deployment requiring that stronger remote invariant must
   give the provider only read authority and move the exact-ref push and PR
   mutation to a post-finalize host delivery broker whose write credential is
   never mounted.

   The explicit ID must equal the branch suffix. The authoritative issue must
   also be one assigned, non-ephemeral `in_progress` source-work `task`, with
   the expected Gas City/`BEADS_ACTOR` assignee and exact recorded
   `metadata.branch` and canonical `metadata.work_dir`. Convoy, formula,
   molecule, epic, wisp, unassigned, and foreign-assignee records are refused.
   The Aegis-local `mol-polecat-work` override changes only the pinned upstream
   workspace-setup description. It validates the startup receipt, branch, Git
   common directory, current-work state, and Beads metadata before running the
   project setup command; it creates no nested worktree and grants no broad gate
   allowance. The kickoff validates generation-2 Beads authority and performs
   only pinned, read-only `bd show`; it never calls Taskmaster.

10. Require host-owned model evidence before the authority-bearing provider
    session starts. The launcher creates a distinct preflight container and a
    host-owned Unix-socket receiver. The receiver authenticates the exact
    Docker init/supervisor process and locked image before provider code runs;
    its immutable receipts remain outside every container mount and are bound
    to the current frozen Git generation.

    Claude runs from an empty image directory with `--tools ""`, empty MCP
    configuration, safe mode, no hooks, and no session persistence. Its
    provider-authored assistant event must report exactly `claude-fable-5` and
    contain no tool block.

    Codex 0.144.4 runs `exec --json --ephemeral` from the same empty directory
    with read-only sandboxing, approval `never`, empty MCP, web/skills/rules and
    mutating feature families disabled, and a SHA-256-bound preflight-only model
    catalog. The catalog preserves the wire request `gpt-5.6-sol` at `xhigh`
    while removing shell, patch, image-input, search, code-mode, and multi-agent
    capability metadata. Stock 0.144.4 still advertises the non-mutating
    `update_plan` and `view_image` utilities whenever an execution environment
    exists; the lock records that exact pair and the receipt requires zero tool
    invocation. The CLI's trusted stderr signal must report that the server
    selected `gpt-5.6-sol` and that it matches the requested model. The JSONL
    lifecycle must complete exactly once with one exact `READY` agent message.
    Any reroute, fallback, error item, tool event, malformed lifecycle, missing
    server signal, nonzero exit, or output overflow fails closed.

    The subsequent worker transcript is retained only as a run-bound audit
    digest and cannot make a positive model claim. Positive model authority
    comes solely from the successful isolated preflight. Only after these
    independent host receipts pass may the null observed fields in the lock
    advance; never hand-edit them based on requested flags.

11. A canary is not delivery-ready until the scoped GitHub credential has
    proved authenticated read, feature-branch push, and draft-PR creation
    without changing the repository's SSH remote. The worker uses a transient
    SSH-to-HTTPS rewrite plus a file-backed credential helper; it never runs
    `git remote set-url` and never persists the token in Git config.

12. Pass the Aegis canary, crash/restart recovery, deterministic Obsidian
    rebuild, backup/restore drill, and then a 24–72-hour soak with no unexplained
    model, Beads, reconciliation, projection, or supervisor drift. Additional
    projects stay out of scope until this gate completes.

## Guarded evidence and promotion commands

Run only the deployed, manifest-bound admin entrypoint shown below. It
self-verifies its own file and the immutable deployed admin-module bundle
against `runtime-lock.json` before importing or dispatching any command. Never
substitute `scripts/gas-city-admin` from a mutable checkout. It accepts no image
tag, caller-supplied model name, or shortened soak duration.

```bash
# Build four untagged targets and write the append-only image receipt. This does
# not mutate the staged lock.
/home/loucmane/gas-city/bin/gas-city-admin build-images \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --context /home/loucmane/gas-city \
  --docker /usr/bin/docker

# Re-inspect every local sha256:<64-hex> ID, rehash the receipt, then atomically
# advance only to provisioned_pending_canary.
/home/loucmane/gas-city/bin/gas-city-admin promote-images \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --docker /usr/bin/docker
```

Before the HQ cold capture, stop every process capable of opening the data
directory. The guarded capture itself proves the Docker container is absent or
stopped, the loopback listener is closed, and no process or open descriptor
holds the source. It copies the full directory first, then derives HQ `status`,
main head, staged diff, and working diff from that byte-identical copy using the
lock-pinned Dolt binary. Source and payload scans surround every phase, so a
read-side mutation fails closed; capture never runs Dolt against the source.

```bash
/home/loucmane/gas-city/bin/gas-city-admin capture-cold-backup \
  --source-data-dir /home/loucmane/gas-city/.beads/dolt \
  --output /home/loucmane/gas-city/runtime/evidence/backup/hq-pre-cutover \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --dolt /home/loucmane/gas-city/bin/dolt \
  --docker /usr/bin/docker \
  --database-relative-path hq \
  --endpoint-host 127.0.0.1 --endpoint-port 33070 \
  --container-name gas-city-hq-dolt
```

The cold-capture guard accepts only the locked HQ identity:
`gas-city-hq-dolt`, `127.0.0.1:33070`, and the `hq` database directory. It
repeats the container/listener/process/open-file proof and exact source scan
after copied-payload state derivation, immediately before committing the pass
manifest; deleted open files and memory mappings also count as live holders.

The cold backup directory is append-only and mode `0700`; receipt artifacts are
mode `0600`. The `data/` root remains mode `0700`, while descendants preserve
the source mode and mtime exactly—even empty directories—so the original Dolt
layout can be restored without guessing metadata. `source-file-manifest.json`
records every typed relative entry, mode, mtime, size, and SHA-256.
`cold-backup-manifest.json` binds that inventory, payload, strict before/after
stop probes, generated HQ state, capture time, counts, and byte total. A source
or copied-payload change during capture leaves only failed forensic evidence
and can never produce a passing manifest.

The HQ distinct-server native restore drill writes its own immutable recovery
receipt. It proves the pre-existing city ledger can be restored, but it is not
the recovery evidence used to activate Aegis task authority:

```bash
GAS_CITY_SOURCE_DOLT_PASSWORD_FILE=/home/loucmane/gas-city/runtime/secrets/hq-root-password \
GAS_CITY_RESTORE_DOLT_PASSWORD_FILE=/run/operator/hq-restore-root-password \
/home/loucmane/gas-city/bin/gas-city-admin backup-restore-drill \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --source-repo /home/loucmane/gas-city \
  --restore-repo /run/operator/empty-restore-rig \
  --backup-dir /home/loucmane/gas-city/runtime/state/dolt-backups/hq/pre-cutover-native \
  --bd /home/loucmane/gas-city/bin/bd \
  --dolt /home/loucmane/gas-city/bin/dolt \
  --docker /usr/bin/docker \
  --source-container gas-city-hq-dolt \
  --restore-container gas-city-hq-restore-drill \
  --source-host 127.0.0.1 --source-port 33070 --source-user root --source-database hq \
  --restore-host 127.0.0.1 --restore-port 33072 --restore-user root --restore-database hq \
  --evidence-output /home/loucmane/gas-city/runtime/evidence/recovery/hq-restore-drill.json
```

After the exact Taskmaster migration, run the same native drill against the
new authoritative `aegis_beads` store and a different empty restore server.
This second receipt must reproduce the migration's exact Dolt head and
canonical export and is the only recovery receipt accepted for generation 1:

```bash
GAS_CITY_SOURCE_DOLT_PASSWORD_FILE=/home/loucmane/gas-city/runtime/secrets/aegis-root-password \
GAS_CITY_RESTORE_DOLT_PASSWORD_FILE=/run/operator/aegis-restore-root-password \
/home/loucmane/gas-city/bin/gas-city-admin backup-restore-drill \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --source-repo /home/loucmane/codex \
  --restore-repo /run/operator/empty-aegis-restore-rig \
  --backup-dir /home/loucmane/gas-city/runtime/state/dolt-backups/aegis/post-migration-native \
  --bd /home/loucmane/gas-city/bin/bd \
  --dolt /home/loucmane/gas-city/bin/dolt \
  --docker /usr/bin/docker \
  --source-container gas-city-aegis-dolt \
  --restore-container gas-city-aegis-restore-drill \
  --source-host 127.0.0.1 --source-port 33071 --source-user root --source-database aegis_beads \
  --restore-host 127.0.0.1 --restore-port 33072 --restore-user root --restore-database aegis_beads \
  --evidence-output /home/loucmane/gas-city/runtime/evidence/recovery/aegis-post-migration-restore.json
```

Each temporary restore container must already be running on loopback port
`33072` with a new, independent data volume and an empty target database; it
must not mount either live Dolt data source. It must bind the applicable host
backup root read-only at the identical absolute path inside the container; the
live source service binds that same root at that same path read/write. This
identity bind is mandatory because Dolt resolves the path in the server while
bd validates it in the operator host. The requested `--backup-dir` must be a
strict child of the shared host root. The command derives and records the same
server-visible absolute path; a relocated or arbitrary host path is rejected.
Native backup administration is attended with the distinct root-password files
shown above. Application credentials remain the normal runtime credentials and
are not elevated. The command inspects both running
containers, binds their full IDs, image IDs, published ports, and data-mount
and backup-mount identities and modes, proves the restore export is empty
before mutation, and retains a
byte-and-metadata manifest beside the native backup. Each receipt also records
the exact lock-bound `bd`/Dolt toolchain, real-clock `captured_at` (immediately
after native backup sync), and `verified_at` (after distinct-container
head/export verification). The CLI has no timestamp override. Generation-1
authority initialization additionally recomputes the Aegis migration target,
head, and export and requires source endpoint `127.0.0.1:33071`, user/database
`root`/`aegis_beads`, container `gas-city-aegis-dolt`, and—after image
provisioning—the exact locked Dolt image ID.

The live HQ and Aegis database containers remain unpublished. For those source
endpoints the drill separately inspects and binds the exact
`*-dolt-loopback` publisher: locked egress-proxy image ID, container ID,
read-only/capability-free/no-new-privileges settings, fixed `socat` argument
vector, loopback port, and the one expected shared control network. The
independent restore container must publish `33072` directly. A missing,
retargeted, differently-networked, or unlocked relay fails closed; recovery
evidence never requires exposing a database container on the host.

### Task-authority lifecycle

Production authority is an exact, append-only lifecycle rather than a mutable
standalone receipt. Generation 1 records Taskmaster authority, generation 2
activates the reconciled Beads store, and generation 3 is the only accepted
rollback to Taskmaster. Each transition binds its immutable intent, previous
generation digest, baseline snapshot/migration/recovery evidence, and fresh
stopped-worker evidence.

First suspend the Aegis rig, stop the Gas City supervisor, close its active
sessions, and stop all provider containers. The evidence command accepts no
caller boolean, PID, or caller-built process list. It invokes the lock-pinned
`city/bin/gc` to inspect the supervisor, exact `aegis`/`ags` rig, and active
sessions. It also directly inspects Docker isolated-worker containers and host
`/proc` provider processes for exact `aegis` / `ags` / `aegis_beads` identity;
partial or contradictory Aegis identity fails closed.

```bash
GAS_CITY_HQ_DOLT_PASSWORD_FILE=/home/loucmane/gas-city/runtime/secrets/hq-app-password \
/home/loucmane/gas-city/bin/gas-city-admin authority-capture-stopped \
  --city-root /home/loucmane/gas-city \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --output /home/loucmane/gas-city/runtime/evidence/workers/generation-1.json \
  --docker /usr/bin/docker

GAS_CITY_HQ_DOLT_PASSWORD_FILE=/home/loucmane/gas-city/runtime/secrets/hq-app-password \
/home/loucmane/gas-city/bin/gas-city-admin authority-initialize \
  --city-root /home/loucmane/gas-city \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --snapshot /home/loucmane/gas-city/runtime/evidence/snapshots/aegis-cutover \
  --migration-evidence /home/loucmane/gas-city/runtime/evidence/migration/aegis/evidence-manifest.json \
  --recovery-evidence /home/loucmane/gas-city/runtime/evidence/recovery/aegis-post-migration-restore.json \
  --target-repo /home/loucmane/codex \
  --stopped-evidence /home/loucmane/gas-city/runtime/evidence/workers/generation-1.json \
  --docker /usr/bin/docker

/home/loucmane/gas-city/bin/gas-city-admin authority-verify \
  --city-root /home/loucmane/gas-city
```

Initialization must report generation 1 in `taskmaster` mode, transition
`initialize-taskmaster`, and no pending attempt. Capture a new stopped record
immediately before activation; evidence is append-only and must not be
rewritten.

```bash
GAS_CITY_HQ_DOLT_PASSWORD_FILE=/home/loucmane/gas-city/runtime/secrets/hq-app-password \
/home/loucmane/gas-city/bin/gas-city-admin authority-capture-stopped \
  --city-root /home/loucmane/gas-city \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --output /home/loucmane/gas-city/runtime/evidence/workers/generation-2.json \
  --docker /usr/bin/docker

GAS_CITY_HQ_DOLT_PASSWORD_FILE=/home/loucmane/gas-city/runtime/secrets/hq-app-password \
/home/loucmane/gas-city/bin/gas-city-admin authority-activate-beads \
  --city-root /home/loucmane/gas-city \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --stopped-evidence /home/loucmane/gas-city/runtime/evidence/workers/generation-2.json \
  --docker /usr/bin/docker

/home/loucmane/gas-city/bin/gas-city-admin authority-verify \
  --city-root /home/loucmane/gas-city
```

The lifecycle hook rereads the immutable stopped record and reruns the gc,
Docker, and `/proc` proof at `before-attempt`, `before-transition`, and
`after-transition`. Final verification must show the ordered
`initialize-taskmaster` and `activate-beads` records, generation 2 in `beads`
mode, and no pending recovery. If the receipt committed but the post-commit
history write failed, never replay the transition. Preserve the error and run
the narrow recovery, which appends history only when one immutable intent
exactly matches the already committed receipt:

```bash
/home/loucmane/gas-city/bin/gas-city-admin authority-recover-history \
  --city-root /home/loucmane/gas-city

/home/loucmane/gas-city/bin/gas-city-admin authority-verify \
  --city-root /home/loucmane/gas-city
```

Capture authority evidence from the fixed live Aegis receipt and the frozen
Taskmaster snapshot. This command semantically replays the complete
two-generation lifecycle and every bound external artifact, then rehashes
`runtime/authority/aegis.json` and both generation records. A standalone valid
generation-2 receipt is insufficient. It requires Beads mode, exact
`aegis` / `ags` / `aegis_beads` identity, no missing history, and no pending
attempt rather than accepting a passing boolean:

```bash
/home/loucmane/gas-city/bin/gas-city-admin capture-authority-evidence \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --snapshot /home/loucmane/gas-city/runtime/evidence/snapshots/aegis-cutover \
  --output /home/loucmane/gas-city/runtime/evidence/canary/authority.json
```

Provider promotion evidence is also derived, not filled in. After one isolated
Aegis canary session for each provider exits, preserve its supervisor-created
`model-receipt.json` and persisted JSONL transcript. First generate each locked
model receipt with `verify-model`, then bind both supervisor receipts to their
exact `runtime/state/provider-sessions/rig-aegis/<agent>/<provider>/<session>`
transcripts. The capture rejects a nonzero exit, fallback, model/effort drift,
transcript hash drift, mismatched agent/session paths, shared Claude/Codex
session identity, or a receipt outside the exact Aegis session roots. It has no
worker-exit or isolated-session boolean flags.

```bash
/home/loucmane/gas-city/bin/gas-city-admin verify-model \
  --provider claude \
  --transcript /home/loucmane/gas-city/runtime/state/provider-sessions/rig-aegis/witness/claude/CLAUDE_SESSION/projects/canary.jsonl \
  --lock /home/loucmane/gas-city/runtime-lock.json

/home/loucmane/gas-city/bin/gas-city-admin verify-model \
  --provider codex \
  --transcript /home/loucmane/gas-city/runtime/state/provider-sessions/rig-aegis/polecat/codex/CODEX_SESSION/sessions/canary.jsonl \
  --lock /home/loucmane/gas-city/runtime-lock.json

/home/loucmane/gas-city/bin/gas-city-admin capture-provider-evidence \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --claude-supervisor-receipt /home/loucmane/gas-city/runtime/state/model-receipts/rig-aegis/witness/claude/CLAUDE_SESSION/model-receipt.json \
  --claude-transcript /home/loucmane/gas-city/runtime/state/provider-sessions/rig-aegis/witness/claude/CLAUDE_SESSION/projects/canary.jsonl \
  --codex-supervisor-receipt /home/loucmane/gas-city/runtime/state/model-receipts/rig-aegis/polecat/codex/CODEX_SESSION/model-receipt.json \
  --codex-transcript /home/loucmane/gas-city/runtime/state/provider-sessions/rig-aegis/polecat/codex/CODEX_SESSION/sessions/canary.jsonl \
  --output /home/loucmane/gas-city/runtime/evidence/canary/providers.json
```

Build the Obsidian projection twice through the real Aegis CLI. Both output
directories must be new and distinct beneath `runtime/evidence/obsidian`.
`capture-obsidian-evidence` pins `city/bin/bd` to the runtime lock, performs two
actual Beads-backed builds, runs each vault's inventory/hash self-check, and
requires byte-identical ownership manifests, source digest, and Dolt head. It
then writes one private append-only evidence record; it accepts no
`deterministic_rebuild`, `vault_check_ok`, or read-only-authority switches.

```bash
/home/loucmane/gas-city/bin/gas-city-admin capture-obsidian-evidence \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --target-repo /home/loucmane/codex \
  --first-vault /home/loucmane/gas-city/runtime/evidence/obsidian/canary-build-1 \
  --second-vault /home/loucmane/gas-city/runtime/evidence/obsidian/canary-build-2 \
  --output /home/loucmane/gas-city/runtime/evidence/canary/obsidian.json
```

The GitHub delivery and controlled Aegis canary use one run-bound intent; no
operator supplies a PR number, commit, repository identity, ownership result,
or pass boolean. `start-controlled-canary` reads the lock-pinned Beads export,
requires the exact `ags-*` item to be `in_progress` under an
`aegis/gastown.polecat_*` owner, and binds its authoritative
`metadata.branch=\"polecat/<bead-id>\"` and `metadata.work_dir`,
replays the full generation-1-to-generation-2 authority history, and probes the
primary checkout with Git. It also uses `gh` to derive the authenticated
repository, write permission, default branch, and exact remote base commit.
Issue a fresh operator token through the same broker immediately before this
command. The token is read from its owner-only file and is never placed in argv
or evidence; the App private key never enters `gas-city-admin`.

```bash
install -d -m 0700 /home/loucmane/gas-city/runtime/state/github-delivery
github_start_state=$(mktemp -d \
  /home/loucmane/gas-city/runtime/state/github-delivery/operator-start.XXXXXXXX)
/home/loucmane/gas-city/bin/github-app-token-broker issue \
  --state-dir "$github_start_state" \
  --repository loucmane/codex-starter-pack \
  --default-branch main \
  --app-id-file /home/loucmane/gas-city/runtime/secrets/github-app-id \
  --installation-id-file /home/loucmane/gas-city/runtime/secrets/github-installation-id \
  --private-key-file /home/loucmane/gas-city/runtime/secrets/github-app-private-key.pem \
  >/dev/null
GAS_CITY_GITHUB_TOKEN_FILE="$github_start_state/token" \
/home/loucmane/gas-city/bin/gas-city-admin start-controlled-canary \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --target-repo /home/loucmane/codex \
  --bead-id ags-CANARY
/usr/bin/unlink -- "$github_start_state/token"
unset github_start_state
```

Preserve the returned `intent_path`, `expected_branch`, `base_commit`, and the
Bead-derived worktree path. The branch is exactly `polecat/ags-CANARY`, as
required by the installed Gas City formula; a branch for another Bead/run is
rejected. Do not create a second worktree, manually rewrite branch metadata, or
close the Bead from the polecat. Let `mol-polecat-work` commit and push that
branch, then hand ownership to `aegis/gastown.refinery`. The refinery validates
or creates the PR, runs its merge checks, merges it, records the canonical
`metadata.pr_url`, and closes the Bead. This ownership transition is part of
the evidence contract, not an operator-supplied assertion.

After all reported PR checks have succeeded, the PR is merged, and the
authoritative `ags-CANARY` record is closed under
`aegis/gastown.refinery`, capture the result. The intent expires after 24
hours.

```bash
github_capture_state=$(mktemp -d \
  /home/loucmane/gas-city/runtime/state/github-delivery/operator-capture.XXXXXXXX)
/home/loucmane/gas-city/bin/github-app-token-broker issue \
  --state-dir "$github_capture_state" \
  --repository loucmane/codex-starter-pack \
  --default-branch main \
  --app-id-file /home/loucmane/gas-city/runtime/secrets/github-app-id \
  --installation-id-file /home/loucmane/gas-city/runtime/secrets/github-installation-id \
  --private-key-file /home/loucmane/gas-city/runtime/secrets/github-app-private-key.pem \
  >/dev/null
GAS_CITY_GITHUB_TOKEN_FILE="$github_capture_state/token" \
/home/loucmane/gas-city/bin/gas-city-admin capture-controlled-canary \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --intent /home/loucmane/gas-city/runtime/evidence/canary-runs/RUN_ID/intent.json \
  --canary-worktree /home/loucmane/gas-city/.gc/worktrees/aegis/polecats/POLECAT_ALIAS
/usr/bin/unlink -- "$github_capture_state/token"
unset github_capture_state
```

Capture re-probes the primary checkout before and after, requires its HEAD,
branch, status bytes, origin, and common Git directory to match the intent,
and requires a clean worktree sharing that common directory. It derives the PR
identity/state/head/base/merge commit, merger and time from `gh`, reparses every
reported check, and requires the remote base ref to equal the merge commit. It
then clones the repository into the private run directory, checks out that
merge detached, requires a clean status, and runs `git fsck --full --strict`.
Finally it re-exports Beads and proves the exact item preserved its polecat
branch/worktree metadata, records the captured PR URL and target, and is
`closed` under the exact refinery owner. Every raw Git, `gh`, clone, and Beads output is an owner-only
SHA-256-bound artifact beneath `runtime/evidence/canary-runs/RUN_ID`; the two
promotion inputs are that run's `github.json` and `canary.json`. The intent also
binds the exact Git, GitHub CLI, and lock-pinned Beads binary hashes and their
observed version output; capture and promotion reject tool replacement.

Canary promotion requires exactly eight owner-only receipt paths: cold backup,
exact Taskmaster-to-Beads migration, distinct-server recovery, isolated
provider/model canary, the live generation-2 authority receipt and frozen
snapshot, run-bound merged GitHub delivery, deterministic Obsidian double
build, and the controlled Aegis canary with clean verification clone. Missing, extra,
world-readable, semantically incomplete, or digest-mismatched evidence fails
closed.

```bash
/home/loucmane/gas-city/bin/gas-city-admin promote-canary \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --backup-evidence /home/loucmane/gas-city/runtime/evidence/backup/hq-pre-cutover/cold-backup-manifest.json \
  --migration-evidence /home/loucmane/gas-city/runtime/evidence/migration/aegis/evidence-manifest.json \
  --recovery-evidence /home/loucmane/gas-city/runtime/evidence/recovery/aegis-post-migration-restore.json \
  --authority-evidence /home/loucmane/gas-city/runtime/evidence/canary/authority.json \
  --provider-evidence /home/loucmane/gas-city/runtime/evidence/canary/providers.json \
  --github-evidence /home/loucmane/gas-city/runtime/evidence/canary-runs/RUN_ID/github.json \
  --obsidian-evidence /home/loucmane/gas-city/runtime/evidence/canary/obsidian.json \
  --canary-evidence /home/loucmane/gas-city/runtime/evidence/canary-runs/RUN_ID/canary.json

/home/loucmane/gas-city/bin/gas-city-admin start-soak \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --output /home/loucmane/gas-city/runtime/evidence/soak/start.json
```

During soaking, run `observe-soak` at least hourly, including within five minutes
of both boundaries. It appends canonical owner-only JSONL under an exclusive
lock. Each row is computed from the current locked promotion receipts and the
latest host-owned successful session receipt for both Claude and Codex; two
stable read-only Beads exports and before/after Dolt heads; a live source-fresh
Aegis vault check; lock-pinned gc supervisor status; and the fully replayed
authority history. A provider's session receipt may be no more than six hours
old. The completed 24-hour window must contain at least four distinct receipts
from each provider, so an idle canary receipt cannot masquerade as a soak.
Schedule a small real Aegis exercise for each provider at least every six hours.
Rows are SHA-256-linked to their predecessor. The command accepts no status or
check results, and `finish-soak` rejects the old caller-authored
`{"checks":{"models":"pass",...}}` shape. Receipt, projection, authority, or
artifact drift invalidates the soak.

```bash
/home/loucmane/gas-city/bin/gas-city-admin observe-soak \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --target-repo /home/loucmane/codex \
  --vault /home/loucmane/gas-city/runtime/evidence/obsidian/canary-build-1 \
  --observations /home/loucmane/gas-city/runtime/evidence/soak/observations.jsonl
```

Observations may never have a gap longer than one hour. The finish command uses
the real clock, requires at least 86,400 seconds, and exposes no duration or time
override:

```bash
/home/loucmane/gas-city/bin/gas-city-admin finish-soak \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --start-receipt /home/loucmane/gas-city/runtime/evidence/soak/start.json \
  --observations /home/loucmane/gas-city/runtime/evidence/soak/observations.jsonl \
  --output /home/loucmane/gas-city/runtime/evidence/soak/finish.json

/home/loucmane/gas-city/bin/gas-city-admin promote-production \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --soak-evidence /home/loucmane/gas-city/runtime/evidence/soak/finish.json
```

`promote-production` rehashes and revalidates every canary artifact and every
soak observation before it writes the append-only production manifest and
atomically changes the lock status. `load_runtime_lock` independently requires
the digest-bound canary manifest for `canary_passed_soaking` and both the canary
and production manifests for `production`; hand-editing the status cannot skip
the gates. The runtime lock binds the official gc 1.3.5, Beads 1.1.0, and Dolt
2.2.0 release archive digests in addition to their installed binary digests.

## Model-guard behavior

`provider-supervisor.py` ignores prompts and arbitrary JSON that merely mention
a model name. For Claude preflight authority it recognizes only the exact
provider-authored `assistant.message.model`. For Codex preflight authority it
requires the pinned CLI's `OpenAI-Model` server-response signal to report an
exact requested/server match, plus one valid tool-free `codex exec --json`
lifecycle. The Codex catalog and CLI command bind the `xhigh` request; the
server-selected model signal binds the actual Sol route.

The authority-bearing session starts only after the host commits that preflight
receipt. Its transcript is read from the end of pre-existing JSONL and hashed,
but provider-writable session content is never promoted as model authority. A
missing receipt, changed model, fallback/reroute, tool invocation during
preflight, or provider exit without the matching host receipt is failure. Model
flags and safe settings are necessary but are not evidence by themselves.

## Stop and rollback

At the first failed gate:

1. Suspend the Aegis rig and workspace, stop the Gas City supervisor, and stop
   launching provider containers.
2. Preserve the rejected transcript, model receipt, Dolt logs, exact database
   volumes, migration manifest, and pre-cutover backups. Do not delete or
   recreate evidence.
3. Restore the dedicated Aegis Dolt volume from the verified pre-cutover backup
   if the database changed. The HQ volume is separate and must not be replaced
   as collateral rollback.
4. Point operational work back to the unchanged Taskmaster snapshot and verify
   its full dependency graph before reopening Taskmaster updates.
5. Rebuild Obsidian from the restored authority; never repair it manually.

An authority rollback is a committed generation-3 transition, not a receipt
edit. After generation 2, run a new native backup/restore drill against the
current `aegis_beads` source on a distinct restore server. Its real
`captured_at` must be strictly later than Beads activation, verification must
finish before rollback, and capture must be no more than 15 minutes old at the
transition. Then stop workers again and create a unique stopped record:

```bash
GAS_CITY_HQ_DOLT_PASSWORD_FILE=/home/loucmane/gas-city/runtime/secrets/hq-app-password \
/home/loucmane/gas-city/bin/gas-city-admin authority-capture-stopped \
  --city-root /home/loucmane/gas-city \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --output /home/loucmane/gas-city/runtime/evidence/workers/generation-3.json \
  --docker /usr/bin/docker

GAS_CITY_HQ_DOLT_PASSWORD_FILE=/home/loucmane/gas-city/runtime/secrets/hq-app-password \
/home/loucmane/gas-city/bin/gas-city-admin authority-rollback-taskmaster \
  --city-root /home/loucmane/gas-city \
  --lock /home/loucmane/gas-city/runtime-lock.json \
  --stopped-evidence /home/loucmane/gas-city/runtime/evidence/workers/generation-3.json \
  --rollback-recovery /home/loucmane/gas-city/runtime/evidence/recovery/post-beads-restore.json \
  --docker /usr/bin/docker

/home/loucmane/gas-city/bin/gas-city-admin authority-verify \
  --city-root /home/loucmane/gas-city
```

Rollback succeeds only as generation 3 in `taskmaster` mode, with the fresh
post-generation-2 recovery record bound into history. Its restored Dolt head
and canonical export digest must exactly equal the migration baseline recorded
at generation 1. If Beads changed after cutover, rollback to the frozen
Taskmaster snapshot is refused because it would discard authoritative work;
keep Beads authoritative and recover it instead. Reusing the original
pre-cutover receipt, backdating evidence, or editing
`runtime/authority/aegis.json` cannot pass full-chain verification.

Stopping the Compose services and leaving the city unregistered is a safe
runtime rollback. Removing project repositories, rewriting Git history,
deleting Taskmaster, or deleting either Dolt volume is not part of rollback.
