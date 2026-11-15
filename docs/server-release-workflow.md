# Server releases and named instances

[Hosting](server-hosting.md) · [Operations](server-operations.md) · [Development](server-development.md)

## Build and verify

Use `python tools/build_server.py --godot /path/to/godot` for Linux and `python tools/build_client.py --godot /path/to/godot` for Windows. Engine and template checks happen before the regression gate. Builds copy scripts, runtime assets, tests, docs and deployment inputs into a frozen source tree using ordinary copies. The gate and export use that same tree. Working-project edits cannot change the artifact being built.

The server archive is published by atomic replacement after export and verification. Its manifest records the source SHA256 fingerprint, engine, game protocol, gate result and package file hashes. Gate logs remain under `.godot/releases/gate-*`. Windows builds retain `build/client-manifest.json`. Failed checks leave the previous published archive in place.

```sh
python3 tools/bumrushctl.py local verify server-linux-x86_64.tar.gz
python3 tools/bumrushctl.py local verify ./server-linux-x86_64
```

Verification is read-only. It rejects modified, missing, unlisted or unsafe files, archive links and escaping paths. Obtain packages from your trusted build machine; hashes establish integrity against the included manifest.

## Publish the GitHub quick start

The public distribution repository is `pontinhos-dev/Bumrush-server`. It contains `install.sh` (copied from `deploy/server/quickstart.sh`), `tools/quickstart.py`, and public operator documentation. Keep the game source project and all private instance state separate. Publish `build/server-linux-x86_64.tar.gz` as a GitHub Release asset; do not commit the archive into Git. GitHub supplies its SHA256 asset digest, which the bootstrap requires before extracting or running the package. A published SHA256 sidecar is also useful for manual downloads.

Run the distribution repository's `Linux server installation smoke test` workflow after publishing. It provisions Ubuntu 24.04, checks native startup and loopback administration, repeats installation to verify credential/configuration preservation, then stops the test service. This is separate from the game's regression gate and eight-player capacity testing. Runtime tags must identify the same release players use. Update the public installer and documentation alongside changes to the supported operational workflow.

A documentation or deployment-only refresh preserves the tested runtime provenance:

```sh
python3 tools/bumrushctl.py local repack original.tar.gz --overlay /path/to/project --output refreshed.tar.gz
```

Only `docs/` and `deploy/` are overlaid. Executable, PCK, source fingerprint and gate record remain intact; `repacked_from` records the original archive hash. Run deployment checks for deployment changes.

## Install once

Create the native service user once, then install from the extracted package:

```sh
getent passwd bumrush >/dev/null || sudo useradd --system --user-group --home-dir /var/lib/bumrush --shell /usr/sbin/nologin bumrush
sudo python3 tools/bumrushctl.py local install server-linux-x86_64.tar.gz --root /opt/bumrush --instance main --user bumrush --register-service --start
```

Root installation assigns config/data ownership and initializes as that service user. Docker uses `--backend docker`, omits `--register-service`, and owns config/data as container UID 10001. Omit `--start` to install without starting. Native `--register-service` copies/enables the generated unit; it does not start without `--start`.

```text
/opt/bumrush/
  releases/<archive-hash>/          verified runtime packages
  instances/main/
    instance.json                  active, previous and pending release IDs
    current -> ../../releases/...  activated package
    config/server.cfg              operator settings
    data/                          private identity, admins, bans and profiles
    bumrush-main.service           generated native unit
    compose.yaml                   generated for Docker
```

An interrupted installation can be resumed without regenerating existing identity files. Repeat installation preserves instance settings and private files and does not activate a different release. Use `update` for that. Each operation holds `.operation.lock`. If interrupted, confirm no operation is running before removing that specific stale lock.

## Stage and activate an update

```sh
sudo python3 /opt/bumrush/instances/main/current/tools/bumrushctl.py local update next-release.tar.gz --root /opt/bumrush --instance main
```

This verifies/stages the package and sets `pending`. The active process keeps running. There are no scheduled updates. Back up `config/`, `data/` and `instance.json` before maintenance.

Activate when ready:

```sh
sudo python3 /opt/bumrush/instances/main/current/tools/bumrushctl.py local update next-release.tar.gz --root /opt/bumrush --instance main --restart
```

Activation prepares the runtime/image, stops the service/container, switches the package, starts and checks certificate-validated TLS `status`. Failed startup stops the candidate, restores the previous release, clears a native service start-limit failure and checks that restored server. Config and credentials are preserved. Success records `previous` and clears `pending`. Clients must use a compatible game protocol; consult each release's manifest and compatibility notes.

## Roll back

```sh
sudo python3 /opt/bumrush/instances/main/current/tools/bumrushctl.py local rollback --root /opt/bumrush --instance main --restart
```

Without `--restart`, rollback only stages the previous release. Runtime rollback preserves current config/state. This release keeps existing ConfigFile, administrator, ban and profile formats readable. Future shape changes require explicit versioned migrations and recovery instructions.

## Another instance

```sh
sudo python3 tools/bumrushctl.py local install server-linux-x86_64.tar.gz --root /opt/bumrush --instance second --user bumrush --game-port 27962 --admin-port 27963 --register-service --start
```

For Docker use `--backend docker --root /srv/bumrush --instance second --game-port 27962 --admin-port 27963 --start`. Every path, service name, Compose project, published/listen port and local admin profile belongs to that instance. Overlapping ports within the hosting root are rejected. Allow/forward each game UDP port separately. Services and Compose projects are named `bumrush-main` and `bumrush-second`.

The default control profile is `instances/<name>/data/owner.profile.json`. `--admin-profile /absolute/path` selects a different enrolled local owner. Docker profiles must live inside that instance's data directory. Health and shutdown use the same selected profile. Update native unit overrides or Docker environment settings when changing it later.

## Existing manual installations

Existing `/etc/bumrush` and `/var/lib/bumrush` instances can retain their current units and profiles. Preserve config/data while replacing the runtime pair during maintenance. To adopt named instances, stop and back up the old instance, prepare a named instance, then transfer its original config/data with correct ownership before starting. Do not initialize over transferred credentials. Verify the configured ports and each profile's TLS port.
