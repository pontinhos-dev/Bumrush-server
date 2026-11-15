# Bumrush Dedicated Server

Host your own **Bumrush** multiplayer server on Linux. Install a ready-to-run server, invite players by address, and moderate matches from inside the game.

The quick start sets up an isolated system service, generates Owner credentials, and prints connection instructions. No Godot editor, graphics card, or desktop session is required.

[Quick start](#quick-start) · [Connect as Owner](#connect-as-owner) · [Documentation](#documentation) · [Releases](https://github.com/pontinhos-dev/Bumrush-server/releases) · [Troubleshooting](docs/troubleshooting.md)

## Requirements

| Item | Requirement |
| --- | --- |
| Operating system | Ubuntu 24.04 LTS with systemd |
| Architecture | Intel/AMD x86_64; ARM is not supported by this package |
| Access | SSH and an account with `sudo`, or root |
| Starting resources | 2 modern CPU cores and 2 GB RAM; a planning estimate, not a measured capacity guarantee |
| Storage | Room for the runtime, an additional release during updates, and private backups |
| Network | Public IPv4 or IPv4 DNS name, with inbound **UDP 27960** allowed |
| Players | Up to 8 connected players; clients must use a compatible game protocol |

This repository contains the installer and operating guides. The runtime is distributed through [GitHub Releases](https://github.com/pontinhos-dev/Bumrush-server/releases), rather than committed to Git.

## Quick start

### 1. Connect to your server

Create an Ubuntu 24.04 x86_64 machine with your hosting provider, then SSH into it. Replace the example username and address:

```sh
ssh YOUR_SSH_USER@YOUR_SERVER_ADDRESS
```

If `curl` is missing on a minimal image, install it first:

```sh
sudo apt-get update
sudo apt-get install -y curl ca-certificates
```

### 2. Install Bumrush

Run this **on the Linux server**:

```sh
curl -fsSL https://raw.githubusercontent.com/pontinhos-dev/Bumrush-server/main/install.sh | bash -s -- --quickstart
```

The installer:

- Installs the headless runtime dependencies.
- Downloads the latest server release and verifies GitHub's SHA256 digest and the package manifest.
- Creates the `bumrush` service account and the `bumrush-main` systemd service.
- Generates a cryptographically random **16-character Owner passkey** and a private client enrollment ZIP.
- Starts the server, checks its administration endpoint, and prints the connection steps.

To advertise a particular IPv4 address or DNS name, add `--host`:

```sh
curl -fsSL https://raw.githubusercontent.com/pontinhos-dev/Bumrush-server/main/install.sh | bash -s -- --quickstart --host YOUR_SERVER_ADDRESS
```

Without `--host`, setup uses the public IPv4 address reached through SSH. For private/NAT addresses or IPv6 SSH sessions, it asks [ipify](https://www.ipify.org/) for the public IPv4 address. An explicit `--host` skips that lookup. The gameplay listener uses IPv4 by default.

You can [review the installer](install.sh) before running it. To download and review it locally instead:

```sh
curl -fsSLo install.sh https://raw.githubusercontent.com/pontinhos-dev/Bumrush-server/main/install.sh
less install.sh
bash install.sh --quickstart --host YOUR_SERVER_ADDRESS
```

`--version TAG` selects a specific published runtime release. Rerunning quick start preserves an existing installation; it **does not upgrade it**. Use the [update procedure](docs/server-release-workflow.md) for that.

### 3. Open the gameplay port

Allow inbound **UDP 27960** in your provider's firewall or security group. Preserve your SSH rule. If UFW is already active, setup adds the gameplay rule; it does not enable an inactive firewall or configure a provider's firewall or router.

| Port | Purpose | Public access |
| --- | --- | --- |
| UDP 27960 | Gameplay | Allow players to connect |
| TCP 27961 | TLS administration | **Keep private**; quick start binds it to loopback |
| Your SSH TCP port | Server access and admin tunnel | Keep your existing access policy |

### 4. Join the game

Open a compatible Bumrush client, choose **Multiplayer**, and enter the server's address and port. You can also use the game console:

```text
connect YOUR_SERVER_ADDRESS 27960
```

The generated Owner passkey is for administration. It is not a password players need to join.

## Connect as Owner

Complete these steps **on your gaming PC**. Setup prints commands with your SSH username, address, and port filled in.

1. Download your private enrollment ZIP:

   ```sh
   scp YOUR_SSH_USER@YOUR_SERVER_ADDRESS:/opt/bumrush/bumrush-main-admin.zip .
   ```

2. Extract the ZIP. Copy `cfg/admin.cfg` and `cfg/server-main.crt` into the `cfg` folder beside `Bumrush.exe`. If you already have an admin CFG, append the new entry instead of replacing other servers' credentials.

3. Open an SSH tunnel and leave that terminal running while moderating:

   ```sh
   ssh -N -L 127.0.0.1:27961:127.0.0.1:27961 YOUR_SSH_USER@YOUR_SERVER_ADDRESS
   ```

4. Join the server. The client authenticates using the saved credentials. Enter `admin` in the console or `/admin` in chat to open the administration menu.

You can play normally while moderating. Owner, Admin, and Moderator roles grant different permissions; the server checks every command. See [Administration](docs/server-commands.md) for staff management, commands, and silent chat commands.

**Keep the ZIP and admin CFG private.** They contain your actual Owner passkey. Administration uses certificate-validated TLS through SSH; TCP 27961 does not need public exposure. Custom SSH ports and tunnel conflicts are covered in [Getting started](docs/getting-started.md).

## Manage your server

Run these commands over SSH:

```sh
sudo systemctl status bumrush-main --no-pager
sudo journalctl -u bumrush-main -n 100 --no-pager
sudo systemctl restart bumrush-main
sudo systemctl stop bumrush-main
sudo systemctl start bumrush-main
```

The service starts automatically after a reboot. The default match is free-for-all on Switchyard. Change maps, player limits, the server name, and voice settings using the [configuration reference](docs/server-configuration.md).

### Important paths

| Path | Contents |
| --- | --- |
| `/opt/bumrush/instances/main/config/server.cfg` | Server configuration |
| `/opt/bumrush/instances/main/data/` | Identities, bans, TLS keys, audit logs, and persistent state |
| `/opt/bumrush/instances/main/current/` | Active runtime release |
| `/opt/bumrush/quickstart/main/owner-passkey` | Root-only copy of the initial generated passkey |
| `/opt/bumrush/bumrush-main-admin.zip` | Private client enrollment, readable by the SSH account that installed it |

Configuration, identities, and bans stay separate from runtime releases. Back them up before maintenance. Use the documented procedures to [back up and restore](docs/server-operations.md) or [update and roll back](docs/server-release-workflow.md); do not replace an existing installation with fresh initialization.

## Documentation

| Guide | What it covers |
| --- | --- |
| [Getting started](docs/getting-started.md) | First deployment, client enrollment, custom SSH ports, and connection checks |
| [Hosting options](docs/server-hosting.md) | Quick start, manual installation, Docker, cloud firewalls, and home hosting |
| [Configuration](docs/server-configuration.md) | Maps, ports, player limits, voice, live settings, and restarts |
| [Administration](docs/server-commands.md) | Roles, staff, moderation, console/chat use, and credentials |
| [Operations](docs/server-operations.md) | Services, private backups, restoration, and recovery |
| [Updates and rollback](docs/server-release-workflow.md) | Verify, stage, activate, and roll back a release |
| [Troubleshooting](docs/troubleshooting.md) | Installation, connectivity, TLS, enrollment, and service failures |
| [Security and privacy](docs/security.md) | Trust, credentials, firewall boundaries, logs, and safe issue reports |
| [Maintainer guide](docs/server-development.md) | Distribution layout, provenance, validation, and publishing |

## Validation and limits

The initial Linux package passed **62 game regression checks** before export. An Ubuntu 24.04 test also verified native service startup, live Owner passkey authentication over TLS, and unchanged credentials/configuration after a repeated install.

These checks establish installation and startup behavior. They do not establish eight-player capacity, a bandwidth guarantee, or connectivity through your particular provider's firewall. Test an external client and measure your workload before advertising a server broadly.

For common failures, start with [Troubleshooting](docs/troubleshooting.md). When reporting a problem, include the release tag, operating system, installation method, and a sanitized error excerpt. Never attach your admin ZIP, CFG, private keys, or server data directory. See [Security reporting](SECURITY.md) for sensitive reports.

## Third-party notices

The release includes Godot and libsodium license notices. Keep the runtime, PCK, native administration library, and bundled notices together. This distribution repository does not grant a separate license to reuse the game's assets or recoverable runtime code.
