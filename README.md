# Bumrush dedicated server

Install a headless Bumrush server on an **Ubuntu 24.04 Intel/AMD x86_64** machine with SSH access and root or sudo privileges. The package includes its runtime; no Godot editor, GPU, or desktop is needed. Start with two modern CPU cores and 2 GB RAM, then measure your workload. These are sizing estimates, not a capacity guarantee.

## Quick start

Run this command on the Linux server:

```sh
curl -fsSL https://raw.githubusercontent.com/pontinhos-dev/Bumrush-server/main/install.sh | bash -s -- --quickstart
```

The installer downloads and checks the server release, installs its dependencies, creates a dedicated service account, installs and starts `bumrush-main`, and generates a secure **16-character Owner passkey**. It saves a private client enrollment ZIP and prints connection instructions. The passkey is displayed only when output goes to a terminal; it is not printed into noninteractive CI logs.

It uses the public IPv4 address from your SSH connection when available. If that address is private, unavailable, or IPv6, it asks ipify for the server's public IPv4 address. Supplying `--host` skips that lookup; use a public IPv4 address or DNS name resolving to IPv4. The default gameplay listener uses IPv4.

To set the address players should use explicitly, add `--host`. Replace `YOUR_SERVER_ADDRESS` with your public IP address or DNS name:

```sh
curl -fsSL https://raw.githubusercontent.com/pontinhos-dev/Bumrush-server/main/install.sh | bash -s -- --quickstart --host YOUR_SERVER_ADDRESS
```

`curl` must already be available to run the download command. On a minimal Ubuntu installation, install it with `sudo apt-get update && sudo apt-get install -y curl ca-certificates`.

Before running downloaded code, you can [inspect the installer](https://github.com/pontinhos-dev/Bumrush-server/blob/main/install.sh). Alternatively, download it to a file, review it, and run `bash install.sh --quickstart`.

## Connect and moderate

1. Allow **UDP 27960** through the cloud provider's firewall. If UFW is already active, the installer adds the game UDP rule while preserving its other rules; it does not enable an inactive firewall. Configure any other host firewall yourself. The installer cannot change a cloud provider's security group or router forwarding rules.
2. Connect from the matching Bumrush client using the Multiplayer menu, or enter `connect YOUR_SERVER_ADDRESS 27960` in its console.
3. Download `/opt/bumrush/bumrush-main-admin.zip` through your trusted SSH connection. On your own computer, substitute your actual SSH username and server address:

   ```sh
   scp SSH_USER@YOUR_SERVER_ADDRESS:/opt/bumrush/bumrush-main-admin.zip .
   ```

4. Extract the ZIP into the folder containing `Bumrush.exe`. It contains `cfg/admin.cfg` and `cfg/server-main.crt`. Keep both files private. Preserve existing CFG entries if you already administer another server; the Credentials dialog shows which CFG file the client currently uses.
5. Keep an SSH tunnel open on your computer while moderating:

   ```sh
   ssh -N -L 27961:127.0.0.1:27961 SSH_USER@YOUR_SERVER_ADDRESS
   ```

The client uses the saved credentials to authenticate automatically when you join the matching server. Enter `admin` in the console or `/admin` in chat to open the administration menu. You can play normally while acting as Owner.

The TLS administration listener stays on server loopback at **TCP 27961**; the tunnel carries administration traffic. You do not need to expose that TCP port publicly. Use a free local forwarding port and update the CFG's `admin_port` if another tunnel already occupies 27961.

The ZIP and its CFG contain the actual Owner secret. Transfer them only through a trusted route and never attach them to an issue or game release. If installing directly as root, use an SSH account that can read the protected ZIP or copy it to your SSH account with private ownership and permissions first.

## Operate the service

```sh
sudo systemctl status bumrush-main
sudo journalctl -u bumrush-main -f
sudo systemctl restart bumrush-main
sudo systemctl stop bumrush-main
```

Configuration lives at `/opt/bumrush/instances/main/config/server.cfg`; durable identities and bans live in `/opt/bumrush/instances/main/data/`. The quickstart recovery passkey is retained privately at `/opt/bumrush/quickstart/main/owner-passkey`.

Rerunning quickstart preserves existing credentials and configuration. It does not silently update a running instance to a different release. Use the packaged release-management tools for a deliberate update or rollback. Back up the instance's configuration and data before updates.

See [hosting](docs/server-hosting.md), [administration](docs/server-commands.md), [operations](docs/server-operations.md), and the [release workflow](docs/server-release-workflow.md) for configuration, staff permissions, updates, and recovery.

## What is published here

This repository distributes the installer and public operating documentation. The matching Linux server package and checksum are [GitHub Release assets](https://github.com/pontinhos-dev/Bumrush-server/releases). Private server state, enrollment files, and the game project's source and asset tree do not belong in this repository.

The manually triggered [Linux smoke workflow](.github/workflows/smoke-server.yml) installs the published release on Ubuntu 24.04, checks the service and loopback administration listener, verifies a repeat install preserves enrollment and configuration, then stops the service. This checks installation and startup; it does not establish multiplayer capacity or replace a real external-client connection test.
