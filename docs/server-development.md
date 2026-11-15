# Release validation and repository scope

[Documentation index](README.md) · [Hosting](server-hosting.md) · [Release management](server-release-workflow.md)

This repository distributes the Bumrush server installer, operator documentation, and downloadable runtime packages. The Git checkout does not contain the separate Godot game project, its tests, editable asset source files, or runtime build scripts. The downloadable package necessarily includes the scripts and resources required to run the game; a packaged game is not a source-confidentiality boundary. Server owners do not need to build Godot or compile the game.

## What a release contains

The Linux x86_64 archive includes `bumrush-server`, its `bumrush-server.pck`, `admin_crypto.linux.x86_64.so`, operator helpers under `tools/`, deployment templates under `deploy/server/`, license notices, documentation, and `manifest.json`. Keep the runtime components together.

The manifest records the engine, platform, game protocol, source fingerprint, regression result, and file hashes. Use it with the release notes to identify compatibility. Avoid substituting a helper, native library, or PCK from a different release.

## Automated validation

The [Linux installation workflow](https://github.com/pontinhos-dev/Bumrush-server/actions/workflows/smoke-server.yml) is manually triggered. It installs a published release on Ubuntu 24.04, starts its systemd service, checks loopback-only administration, validates private enrollment, authenticates the generated Owner passkey through certificate-validated TLS, and executes `status`.

It then repeats installation and checks that configuration, the passkey, administrator registry, and client ZIP are unchanged. The test service is stopped afterward. Public runs exercise the anonymous curl route. Private previews use a read-only CI token only for the release download, verify the checksum, and provision without passing the token into the installer.

Successful native runs are recorded in [GitHub Actions](https://github.com/pontinhos-dev/Bumrush-server/actions/workflows/smoke-server.yml). They provide installation/startup evidence, not a promise about full-match capacity or outside-client reachability.

## Runtime build gate

Maintainers use the separate game's `tools/build_server.py` entry point with its matching Godot editor/templates. It freezes source inputs, runs the full default regression gate, then exports and packages that same source snapshot. Failed checks block publication and retain evidence.

The initial quick-start release passed 62 default game checks before export. Those checks include gameplay, animation, settings, effects, administration, movement, demos, session cleanup, and local multiplayer integration. The Linux installation workflow is a separate check of the exported package. A Windows-hosted export alone does not establish Linux startup correctness.

Do not copy build commands from the game project into this distribution checkout: the necessary project files are intentionally absent. Request access to the source project if you need to modify runtime behavior.

## Compatibility and behavior

The server owns authoritative simulation; clients submit validated input, predict movement, and reconcile to accepted state. The runtime simulates at 120 Hz and publishes snapshots at 30 Hz. Hit-history rewind is bounded by the configured `max_unlag`.

Game networking, administration, demo container formats, demo state schemas, and content revisions are independently versioned. Consult the package manifest and release notes rather than treating an old protocol number in a guide as current compatibility policy.

The dedicated server hosts one configured deathmatch arena and accepts saved/manual addresses. It does not provide a master-server list, account authentication, matchmaking, automatic NAT traversal, or a UDP relay. Names are not verified identity. IP-based moderation can affect several people behind the same router.

## Checks required on your deployment

After installing or updating:

1. Confirm the service is healthy, its administration listener is loopback-only, and state permissions remain private.
2. Join from a compatible client outside the server's network; local TLS health is not a UDP reachability test.
3. Test movement, firing, reload, inventory, death/respawn, voice/chat, and reconnect.
4. Confirm the Owner and a lower-privilege staff account have the intended access.
5. Test restart/reboot recovery and one protected backup restore.
6. Measure CPU, frame time, resident memory, bandwidth, and packet loss under the intended player and recording load.

External WAN capacity, home router behavior, provider firewall settings, and sustained eight-player performance must be measured for the deployed machine. Do not present a short localhost sample from an older protocol as a capacity guarantee.

## Maintaining the distribution

Keep installer behavior, documented flags, release asset names, and package layout aligned. Validate docs links and examples when changing operating procedures. Keep generated private enrollment files, logs, game source, and backups out of this repository.

Write the SHA256 sidecar with POSIX LF endings, including when preparing it on Windows. GNU `sha256sum --strict --check` must accept it before upload. An archive's own manifest does not replace an outer checksum obtained from the trusted release route.

Use [release readiness](release-readiness.md) before public distribution. Update runtime packages only through the game project's validated release workflow; do not silently replace published runtime components after testing.
