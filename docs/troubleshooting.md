# Troubleshooting

[Documentation](README.md) · [Getting started](getting-started.md) · [Operations](server-operations.md)

Preserve configuration and server data while diagnosing a problem.

## Initial checks

Run over SSH:

```sh
sudo systemctl status bumrush-main --no-pager
sudo journalctl -u bumrush-main -n 100 --no-pager
sudo ss -lunp
sudo ss -ltnp
```

Default native installs use UDP 27960 for gameplay and TCP 27961 on **127.0.0.1** for administration. A listener proves local service availability, not external connectivity. Sanitize logs before sharing them; never attach a data directory or enrollment ZIP.

## Installer download fails

### `curl: command not found`

Install the initial download tool:

```sh
sudo apt-get update
sudo apt-get install -y curl ca-certificates
```

The bootstrap installs the remaining dependencies once it starts.

### HTTP 404 or missing release

Confirm the repository is public, `main/install.sh` exists, and a published release contains `server-linux-x86_64.tar.gz`. Anonymous quick start cannot access private previews or draft releases. With `--version`, check the exact tag.

Do not paste an access token into the download command or shell history. Maintainers should use trusted authenticated tooling while preparing a private release.

### HTTP 403 or API rate limit

GitHub can rate-limit anonymous release API requests, especially behind a shared public address. Check the error, wait for reset, or use the verified manual download path. Rapid retries do not resolve the limit.

### Unsupported platform

Quick start requires Ubuntu 24.04, Intel/AMD x86_64, systemd, and root/sudo. ARM instances, Debian, WSL without systemd, and containers without systemd are not equivalent targets. Use [Docker hosting](server-hosting.md) where appropriate rather than bypassing checks.

### Checksum, size, or manifest failure

Obtain the release again from the trusted repository. Do not bypass the digest or edit `manifest.json`. Setup verifies the outer GitHub SHA256 before running package code, then checks the internal manifest. Publishers must re-upload legacy assets that lack a required digest.

## Server will not start

Read service status and the journal. Common causes are an occupied port, invalid configuration, missing dependencies, or incomplete runtime files.

- Keep `bumrush-server`, `bumrush-server.pck`, and `admin_crypto.linux.x86_64.so` from the same release together.
- Check that another process is not using the configured ports.
- The service account must traverse runtime directories and write its config/data directories. Do not make `/opt/bumrush` world-writable.
- Use the installed service instead of starting another copy against the same data directory.

After fixing the cause:

```sh
sudo systemctl reset-failed bumrush-main
sudo systemctl start bumrush-main
```

Initialization refuses to overwrite existing identity files to protect accounts and bans. Do not delete them to bypass the error. Restore a coherent private backup or follow [recovery](server-operations.md).

## Service active, but players cannot connect

1. Use a compatible client protocol and the intended gameplay address/UDP port.
2. Confirm the server has a UDP listener on that port.
3. Allow UDP in both provider and host firewalls. TCP rules are insufficient.
4. For home hosting, forward UDP to the correct LAN machine. Double NAT or CGNAT may prevent inbound access.
5. Test with a player outside the server's network. Hairpin NAT may affect only local clients using a public address.
6. If IP detection selected an outbound NAT gateway rather than an inbound address, use the actual reachable address and update the client CFG's gameplay host.

The installer cannot configure security groups, router forwarding, DNS, or a CGNAT exit. See [Hosting](server-hosting.md).

## Can join, but administration does not work

1. Keep the gaming PC's SSH tunnel open.
2. Check the CFG's gameplay host/port, `admin_host="127.0.0.1"`, and the tunnel's **local** port.
3. Check that the certificate exists beside the active CFG and came through a trusted transfer.
4. Use Credentials to find the active file. A per-user CFG can override a portable one.
5. Confirm the account and role still exist and its passkey has not changed or been revoked.
6. Reconnect after changing servers or credentials; access binds to the current player connection.

Do not disable certificate validation or expose the TCP listener publicly to solve a tunnel issue.

### Tunnel reports `Address already in use`

Choose a free local port such as 27962 and set the CFG entry's `admin_port=27962`. The remote endpoint remains 127.0.0.1:27961. See [Getting started](getting-started.md#7-open-the-administration-tunnel).

### SCP cannot read the enrollment ZIP

It belongs to the SSH account used for setup. Retrieve it with that account or arrange a protected owner-authorized transfer. A later install by another SSH account does not take ownership automatically.

### Owner passkey was not printed

Noninteractive output intentionally omits it. The private enrollment ZIP contains the initial key. Root can also read `/opt/bumrush/quickstart/main/owner-passkey` through a trusted terminal; never paste it into an issue.

The receipt stores the **initial** key. If staff later changed the active passkey, the receipt is stale. Quick start will not rotate a live account to match it.

### TLS certificate mismatch

Use this server's certificate transferred through SSH. Keep `expected_name="bumrush-server"` unless deliberately configured otherwise. After restore/reinitialization, verify identity through a trusted route before replacing client trust. Do not accept arbitrary certificates from gameplay messages.

## Repeated install does not update the game

This is intentional. Use [Updates and rollback](server-release-workflow.md) during maintenance. A new `--host` argument also does not rewrite an existing private enrollment ZIP; edit the active client CFG if the address changes.

## Operation lock

An install/update may still be active, or interruption may have left `.operation.lock`. Verify no installation, update, rollback, or initialization is running before following [lock recovery](server-operations.md). Never remove a lock automatically while another process may be writing state.

## Performance below expectations

Measure the actual map, player count, voice use, and server frame time. Two cores/2 GB and the eight-player cap are not a promise that every shared VM sustains every workload. CPU contention, throttling, latency, and loss can affect cloud hosts.

Installation tests do not benchmark your provider or bandwidth cost. Do not change movement physics or network timing as a first diagnostic step.

## Ask for help safely

Include the release/client versions, Ubuntu version/architecture, installation method, a sanitized failing command and journal excerpt, and whether it fails locally or across the Internet.

Never attach `admin.cfg`, `owner.key`, `server.key`, `admins.json`, an enrollment ZIP, or a private backup. Use [Security reporting](../SECURITY.md) for sensitive reports.
