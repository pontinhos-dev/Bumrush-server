# Releases, updates, and named instances

[Documentation index](README.md) · [Hosting](server-hosting.md) · [Operations and backups](server-operations.md) · [Release validation](server-development.md)

Runtime archives are GitHub Release assets. This Git repository contains the installer and operating documentation; it does not contain the game source or runtime build tools. Use the release package for the commands below.

## Verify a download

Download the Linux archive and its SHA256 sidecar from the trusted release page. From the directory containing both files:

```sh
sha256sum --check server-linux-x86_64.tar.gz.sha256
tar -xzf server-linux-x86_64.tar.gz
python3 -B server-linux-x86_64/tools/bumrushctl.py local verify server-linux-x86_64.tar.gz
```

The helper checks the file manifest and rejects modified, missing, unlisted, unsafe, or linked archive members. The checksum detects corruption; a sidecar from the same origin is not an independent publisher signature. Obtain both through the publisher's HTTPS release route before executing package tools.

Use `python3 -B` to avoid adding bytecode caches to verified package directories. Keep the binary, PCK, native library, and helpers from the same release together.

The manifest records engine, platform, game protocol, source fingerprint, regression results, and file hashes. Read each release's compatibility notes. Game, administration, and demo versions are independent; prefer matching client/server releases.

## Installed layout

```text
/opt/bumrush/
  releases/<archive-hash>/           verified runtime packages
  instances/main/
    instance.json                   active, previous, pending release IDs
    current -> ../../releases/...   selected runtime
    config/server.cfg               instance settings
    data/                           private identity, accounts, bans, profiles
    bumrush-main.service            generated native unit
  quickstart/main/owner-passkey      root-only original enrollment receipt
  bumrush-main-admin.zip             private client enrollment for its SSH user
```

Docker installations commonly use `/srv/bumrush`; each generated instance has its own `compose.yaml`. Hand-managed installations may use other paths and are not converted automatically.

`local install` initializes once. Repeating it preserves config, credentials, bans, and the active release; it does not activate a new archive. Interactive manual installation asks for a passkey. Quick start additionally generates a secure passkey and client enrollment ZIP.

Each local package operation holds `.operation.lock` under the hosting root. If an interrupted process leaves a stale lock, first confirm no live installer or updater owns the operation. Remove only that specific stale file. Do not delete instance state to bypass a lock.

## Stage and activate an update

Read the release notes, check client compatibility, download and verify the archive, and make a [protected backup](server-operations.md#back-up-and-restore). Then stage the archive using its absolute path:

```sh
sudo python3 -B /opt/bumrush/instances/main/current/tools/bumrushctl.py local update /path/to/next-release.tar.gz --root /opt/bumrush --instance main
```

`/path/to/next-release.tar.gz` is a placeholder for the downloaded file. Staging verifies it, creates a separate release directory, and records it as pending. The active process keeps running. There are no scheduled automatic updates.

During maintenance, activate that archive:

```sh
sudo python3 -B /opt/bumrush/instances/main/current/tools/bumrushctl.py local update /path/to/next-release.tar.gz --root /opt/bumrush --instance main --restart
```

Activation stops the instance, switches the runtime, starts it, and checks certificate-validated TLS `status`. On startup failure the installer attempts to restore and check the previous runtime. Config and credentials are preserved. Success records the previous release and clears pending state.

Inspect logs afterward and join from a compatible client to check movement, firing, respawning, and Owner access. Retain the previous release until validation is complete. Runtime rollback cannot reverse incompatible data migrations; follow migration-specific release instructions.

For a generated Docker instance, use the same commands with its existing `--root /srv/bumrush`. The workflow prepares the image and controls that instance's generated Compose project.

## Roll back

```sh
sudo python3 -B /opt/bumrush/instances/main/current/tools/bumrushctl.py local rollback --root /opt/bumrush --instance main --restart
```

Without `--restart`, rollback only stages the previous runtime. Config and data remain in place. Use a tested backup restore when state itself needs recovery. A previous release must have been recorded and retained.

## Another instance

From an extracted package directory with the archive one level above:

```sh
sudo python3 -B tools/bumrushctl.py local install ../server-linux-x86_64.tar.gz --root /opt/bumrush --instance second --user bumrush --game-port 27962 --admin-port 27963 --register-service --start
```

For Docker add `--backend docker`, use `--root /srv/bumrush`, and omit `--register-service`. Each instance has separate ports, config/data, release selection, service or Compose name, and local control profile. Port overlap within a hosting root is rejected. Allow/forward each gameplay UDP port separately.

The second native service is `bumrush-second`. A distinct SSH tunnel and client CFG entry are needed for its administration port. The automated bootstrap intentionally configures only `main`.

## Health and shutdown identity

The default profile is `instances/<name>/data/owner.profile.json`. `--admin-profile /absolute/path` selects another enrolled local Owner. Docker profiles must remain inside that instance's data directory. Health and shutdown share the selected profile.

Before revoking that account, enroll and test a replacement, then update the service or Compose environment. Preserve profile-relative certificate and credential paths. Staff passkey CFGs and local token profiles serve different roles.

## Build and publish policy

Only maintainers with the separate game source project can build a runtime. Builds use the gated server build entry point; this distribution repository cannot reproduce the binary by itself. See [release validation](server-development.md) and [release readiness](release-readiness.md).

Publish archives and checksums as Release assets, not Git blobs. Exclude instance state, credentials, client admin CFGs, enrollment ZIPs, logs containing personal data, and backups. Updating the live documentation does not change an already published archive.
