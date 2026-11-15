# Develop and validate dedicated servers

[Documentation index](README.md) · [Hosting](server-hosting.md) · [Operations](server-operations.md)

The server is part of the same Godot project as the client. `dedicated_server` exports and explicit `--server` startup enter the headless hosting path. Plain `--headless` continues to support offline tests and asset tools. Server configuration/state is independent of player preferences.

## Build the Linux package

Use the Godot 4.7.2 editor and matching export templates. The build helper rejects a mismatched editor, runs the repository’s isolated integration-check gate, optionally downloads official templates, verifies the archive SHA512, exports the release, and packages the runtime, admin helper, deployment examples, documentation, and a SHA256 manifest. Failed checks stop the export and retain their logs under `.godot/checks/`.

```sh
python tools/build_server.py --godot /path/to/godot --install-templates
python tools/build_server.py --godot /path/to/godot
```

The `Linux Dedicated Server` preset emits `bumrush-server` plus `bumrush-server.pck` for x86_64. The package uses the release export runtime. The current preset preserves resources that existing scripts preload. The dedicated scene builds collision geometry and simulation without rendering its arena meshes. Asset removal and alternative CPU targets should be validated as separate changes.

The build helper runs the complete default regression gate before export. Use `python tests/run_checks.py` for the same checks during development. See [architecture and compatibility](architecture.md) for mode and replay boundaries.

The helper runs on Windows or Linux. A successful export on Windows confirms packaging and compilation, and the executable still needs a Linux boot check. The deployment image targets Ubuntu 24.04. Source runs use the normal Godot editor binary with `--headless`.

## Simulation and protocol

The server owns authoritative movement and gameplay state. Clients submit bounded input intent, predict their own movement, and reconcile to acknowledged server state. The simulation runs at 120 Hz with 30 Hz state snapshots. Client positions and velocities are observations for presentation, rather than authoritative motion commands. Combat uses server-accepted inputs and state, with a maximum 200 ms history window controlled by `max_unlag`.

Keep movement rules shared between local prediction, authoritative simulation, and replay. Preserve the one-command/one-effect behavior across retransmission, stale input, respawn, weapon switch, and reconnect. Test input loss and delay as well as clean loopback networking. History rewind must restore live collision state after a query and respect map geometry and player life transitions.

The game protocol is versioned in `scripts/network_policy.gd`, currently version 19. The session facade publishes the same version. Mode envelopes travel in snapshots independently of demo state versions. A public-server release requires matching server/client protocol and engine compatibility. Keep RPC names, signatures, and node paths aligned across client and server. Update the protocol when message shape or semantics change, and update the documentation’s current protocol number with it.

Protocol 16 adds a reliable suicide request containing the current life ID. Authority derives the victim from the sender, rejects stale lives, and uses the mode's existing death and respawn rules. Switchyard's invisible perimeter collision is shared by clients and dedicated servers. Falling below the shared map kill height is lethal on authority.

Admission validates version, identity fields, capacity, and bans before allocating a playable actor. Pending connections expire and all untrusted messages have size/rate/type bounds. Leave object deserialization disabled. Game clients receive values, rather than executable objects or arbitrary server scripts.

## Extend administration

`scripts/server_config.gd` owns server configuration, initialization, path resolution, durable file helpers, and command tokenization. `scripts/server_runtime.gd` owns TLS identities and credential revisions; `admin_suite.gd` and `admin_permissions.gd` own the shared command policy, moderation, targeting, votes and audit history. SSH/Python and in-game clients use that dispatcher through the same TLS interface.

For each new command, define accepted arguments, permission, persistence, and error responses, then add it to [server-commands.md](server-commands.md). Keep credentials out of logs and command history. TLS validates the instance certificate before authentication. Limit request sizes and rates before expensive command work, and perform game-state mutations on the main thread.

## Verification checklist

Use the repository’s dedicated-server and multiplayer checks together with the existing LAN harness. Run focused GDScript tests through their ordinary SceneTree entry points and Python orchestration checks through their documented help/CLI. Retain logs with the tested release and engine version.

```sh
godot --headless --path . --script res://tests/server_world_check.gd
godot --headless --path . --script res://tests/server_client_check.gd
GODOT=/path/to/godot python tests/run_server_checks.py
python tests/run_server_admin_checks.py --godot /path/to/godot
python tests/run_lan_checks.py --godot /path/to/godot
```

The world check compares dedicated collision geometry with the normal arena, without render nodes. The client check exercises manual connections, saved addresses, and the in-game admin entry point. The server harness exercises real server/mover/observer processes and the admin harness uses both Godot and Python clients through real TLS. Exported-runtime and Linux service checks remain separate deployment tests.

1. Initialize in a temporary directory, start headless, and check that an empty server has zero players and no wave progression or local host avatar.
2. Connect ordinary matching clients, then verify movement, input reconciliation, combat, ammunition/reload, inventory, pickups, voice/chat relay, death, respawn, reconnect, and late join.
3. Fill all eight player slots, reject a ninth, and verify rejected/pending peers release resources.
4. Inject invalid, duplicate, stale, oversized, and excessive inputs. Check bounded work and authoritative state.
5. Test hit-history bounds, walls, changing player lives, and restoration after rewind.
6. Exercise the real Python and in-game admin clients, wrong credentials/certificates, owner/moderator permissions, revocation, bans and expiry, read-only configuration, reload, restart, and orderly shutdown.
7. Reboot the exported Linux runtime and repeat a real client join. Confirm state survives process restart.
8. On Ubuntu, validate the native service with `systemd-analyze verify`, service start/stop/restart, reboot recovery, journald, and private state permissions.
9. Validate Compose config, build the image, initialize a volume, join a match, administer it, stop/restart, and confirm persistent state and published port boundaries.

An external network join and full-load latency test are distinct from local process integration tests. Record which checks ran and which remain pending for each release.

## Known limits to communicate

The dedicated server hosts the configured deathmatch arena and supports private saved addresses. There is no master server registry, account identity, matchmaking, relay, or automatic router traversal. Moderation uses IP addresses and session peer IDs. A same-NAT ban can affect multiple players. Application flood limits and server authority improve control of gameplay state, while volumetric denial of service still needs host/provider network capacity and filtering.

Godot documents dedicated exports, UDP hosting, and certificate verification in its official guides. [Dedicated server export](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_dedicated_servers.html), [high-level multiplayer](https://docs.godotengine.org/en/stable/tutorials/networking/high_level_multiplayer.html), [TLS configuration](https://docs.godotengine.org/en/stable/classes/class_tlsoptions.html)

## Verified deployment checks

On 12 November 2026, the final protocol-11 Linux x86_64 runtime was booted in an isolated Ubuntu 24.04 VM. Initialization, systemd unit validation, service start/restart/stop, TLS owner commands, persisted live configuration, and Linux resident-memory reporting passed. Fresh initialization also passed with the server’s home and data directory sharing one path, including the engine-created cache folders. The packaged Dockerfile and Compose deployment built and ran there with a fresh state volume, a healthy TLS status check, persistent configuration, and graceful container stop. A native Windows client authenticated through each of the native-service and Docker UDP paths, moved 8.21 m with server input acknowledgment, and fired a scattergun with authoritative ammunition changing from 80 to 79.

These checks used local virtual networking. External cloud/home router reachability and sustained WAN behavior depend on the deployed host and network and require their own join/load checks.

## Protocol 13 regression coverage

`network_replication` checks projections/privacy, complete-roster validation, rendered-tick encoding, clock alignment at 0/50/150/200 ms RTT, earliest receipt, subscription generations and session cleanup. `server_network` adds a moving-target shot aimed through the gameplay camera. For native camera capture use `tests/run_server_checks.py --rendered --latency-ms 150 --loss .05 --stall-seconds 3`; repeat at 0, 50, 150 and 200 ms. Its fixture uses the same collision geometry on both sides.

`server_release` checks mutation/path rejection, repack provenance, repeat staging, independent instance generation and failed-activation recovery. `runner` checks file-copy isolation in both directions. `server_catalog` checks generated docs/defaults against runtime catalogs; regenerate with `python tools/server_docs.py`.

Use `python tests/run_checks.py --extended --check server_capacity` for eight real clients and zero/one/eight recorder measurements. These are local measurements; external WAN reachability and sustained capacity require deployment-specific checks.

Passkey work uses the packaged native extension on a bounded background worker; never hash on the simulation thread or substitute a fast password hash. Rebuild it from pinned sources using `python tools/build_admin_crypto.py --target all`. Linux packages include `admin_crypto.linux.x86_64.so` beside the server binary/PCK. Keep all three together.

Run `python tests/run_checks.py --check admin_network --check admin_host --check admin_suite` for the integrated administration entry points. Actual Linux runtime validation must be reported separately from Windows-hosted dedicated-process checks and successful ELF cross-compilation.
