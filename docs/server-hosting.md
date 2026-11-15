# Host a Bumrush server

[Documentation index](README.md) · [Configuration](server-configuration.md) · [Commands](server-commands.md) · [Operations](server-operations.md)

The dedicated server runs endless free-for-all on Switchyard by default. Furnace and FY Snow are also available. To choose a startup map, edit `[server] map` in `server.cfg` and restart. It supports up to eight players, with a separate server process owning movement, combat, inventories, pickups, scores, and respawns. Players connect by address or save an address as a favorite. Use the same release for server and clients.

The deployment target is Ubuntu 24.04 on an Intel/AMD x86_64 machine. The Linux package contains its own runtime. A GPU, display, Godot editor, Steam account, and desktop session are unnecessary. Start with two CPU cores and 2 GB RAM as a sizing estimate, then measure your instance under eight-player load. These are planning figures, not a measured capacity guarantee.

## One-command cloud setup

SSH into an Ubuntu 24.04 Intel/AMD x86_64 server, then run:

```sh
curl -fsSL https://raw.githubusercontent.com/pontinhos-dev/Bumrush-server/main/install.sh | bash -s -- --quickstart
```

These unauthenticated download URLs work when the repository and release are public; they do not grant access to a private preview repository.

The [distribution repository](https://github.com/pontinhos-dev/Bumrush-server) contains the inspectable installer and published runtime assets. No Git checkout or Godot installation is needed. `curl` must already be installed to download the script; on a minimal image, run `sudo apt-get update && sudo apt-get install -y curl ca-certificates` first.

The bootstrap installs system dependencies, verifies the latest release against GitHub's SHA256 digest and the package manifest, creates the service account, enrolls a cryptographically generated 16-character Owner passkey, enables `bumrush-main`, and checks that it answers TLS administration. The generated key is shown only on a terminal and saved privately for retry/recovery. Repeating setup preserves the account, bans, configuration, and active release; upgrades remain explicit.

The script uses the public IPv4 address reached through SSH, falling back to an HTTPS IPv4 lookup through ipify for private/NAT addresses or IPv6 SSH sessions. Add `--host YOUR_PUBLIC_IPV4_OR_DNS` to choose the advertised address explicitly and skip that lookup. The default gameplay listener uses IPv4. Add `--version v0.9.0` to select a published runtime release. These flags do not update an already installed instance.

After success it prints the gameplay address, an SCP command for `/opt/bumrush/bumrush-main-admin.zip`, and an SSH tunnel command. Download the ZIP on your gaming PC and copy its `cfg/admin.cfg` and `cfg/server-main.crt` into the game folder. Append the entry instead of replacing other credentials if an admin CFG already exists. Keep the SSH tunnel running while moderating; join through Multiplayer and open `admin` or `/admin`. TLS administration stays on server loopback. The ZIP contains the Owner passkey: keep it private.

An active UFW firewall gets the game UDP rule without changing SSH rules or enabling an inactive firewall. **Allow inbound UDP 27960 in your cloud provider's firewall yourself.** Router forwarding and provider security groups cannot be configured without their credentials. The script leaves other firewall systems unchanged and prints the required port.

The recovery key is `/opt/bumrush/quickstart/main/owner-passkey`, accessible only to root. The enrollment ZIP is readable only by the SSH account that performed setup. Existing manually enrolled accounts are preserved without generating replacement keys. If staff rotate the Owner passkey later, update your private CFG; quick start does not rotate or recover a changed passkey.

## Obtain the package manually

Download `server-linux-x86_64.tar.gz` and its `.sha256` sidecar from the [release page](https://github.com/pontinhos-dev/Bumrush-server/releases). This distribution Git checkout contains the installer and documentation; runtime binaries, deployment templates, and operator helpers are inside the archive. Building a runtime requires the separate game source project.

Use a trusted download route and verify before extracting or running package code:

```sh
sha256sum --check server-linux-x86_64.tar.gz.sha256
```

A checksum from the same publisher detects corruption; it is not an independent publisher signature. Keep `bumrush-server`, `bumrush-server.pck`, and `admin_crypto.linux.x86_64.so` together.

```sh
tar -xzf server-linux-x86_64.tar.gz
cd server-linux-x86_64
chmod +x bumrush-server
sudo apt-get update
sudo apt-get install -y ca-certificates libstdc++6 libfontconfig1 python3
python3 -B tools/bumrushctl.py local verify ../server-linux-x86_64.tar.gz
```

The manual commands below run from the extracted `server-linux-x86_64` package directory, with the archive one level above. They are not commands for the small Git checkout. `python3 -B` avoids adding bytecode caches inside verified release folders.

## Passkey administration

For the Owner passkey setup and private client CFG, follow [Server administration](server-commands.md#join-your-own-server-as-owner). New interactive service installation asks for the key; `tools/admin_setup.py` also supports standalone setup with a trusted client enrollment export. Keep the packaged native `.so` beside the Linux server and PCK. Legacy unattended token-only initialization below remains supported.

## Try a foreground instance

Run as an ordinary Linux user from the extracted package directory. Initialization creates a fresh configuration, TLS identity, administrator, and ban file. It refuses to replace existing credentials.

```sh
./bumrush-server --headless --audio-driver Dummy -- --init-server --config ./server.cfg --data-dir ./server-data
./bumrush-server --headless --audio-driver Dummy -- --server --config ./server.cfg --data-dir ./server-data
```

In another terminal, inspect the running process and its player list.

```sh
python3 -B tools/bumrushctl.py --profile server-data/owner.profile.json status
python3 -B tools/bumrushctl.py --profile server-data/owner.profile.json players
```

The game listens on UDP 27960. Administration listens on TLS TCP 27961 at loopback by default. This foreground initialization uses legacy token enrollment. For prompted passkey enrollment and a portable CFG, use the [standalone setup helper](server-commands.md#standalone-passkey-enrollment). The owner profile and credential are private files. Keep them outside publicly served folders and release archives.

Open the client’s Multiplayer menu, enter the server address and port, then join. The console also accepts `connect 192.0.2.10 27960`. Replace the documentation address with your actual server address. To save it, use `favorite Basement 192.0.2.10 27960`, then inspect `favorites`, or use the menu’s saved-server controls.

## Install a native service

The package installer verifies the release and creates isolated service/config/state paths. Create its service account before installing:

```sh
getent passwd bumrush >/dev/null || sudo useradd --system --user-group --home-dir /var/lib/bumrush --shell /usr/sbin/nologin bumrush
sudo python3 -B tools/bumrushctl.py local install ../server-linux-x86_64.tar.gz --root /opt/bumrush --instance main --user bumrush --register-service --start
sudo systemctl status bumrush-main
sudo journalctl -u bumrush-main -f
```

Repeating installation preserves configuration, credentials and bans. Use `update` for another release. The runtime is `instances/main/current`, configuration is `instances/main/config/server.cfg`, and private state is `instances/main/data/` under the chosen root.

## Use Docker Compose

Install Docker Engine and Compose on Linux. The same installer builds the package image and generates a Compose project with instance-specific ports/config/data:

```sh
sudo python3 -B tools/bumrushctl.py local install ../server-linux-x86_64.tar.gz --root /srv/bumrush --instance main --backend docker --start
sudo docker compose --project-name bumrush-main -f /srv/bumrush/instances/main/compose.yaml ps
sudo docker compose --project-name bumrush-main -f /srv/bumrush/instances/main/compose.yaml logs -f
```

Game UDP is public; TLS administration is published on host loopback. The config directory is writable for atomic validated saves. Data uses container UID 10001. Health and shutdown share `BUMRUSH_ADMIN_PROFILE`; the entrypoint preserves the server exit code and reports TERM fallback. [Docker installation](https://docs.docker.com/engine/install/ubuntu/)

The supplied Compose/unit files remain hand-managed examples. Create config/state once and preserve them on updates. Generated named instances support the documented staged-update and startup-recovery workflow.

## Cloud server networking

1. Create an Ubuntu 24.04 x86_64 VM with a public address and SSH access.
2. Copy and install the package using either native service or Compose instructions.
3. Allow inbound UDP 27960 in the provider security group or cloud firewall.
4. Allow the same UDP port in the host firewall. Keep your existing SSH access rule.
5. Give players the public address or a DNS hostname pointing to it. Test with a real client outside the server’s network.

For UFW-managed hosts, preserve the rule for your actual SSH port, then allow the game port. Do not enable an inactive firewall remotely before checking SSH access.

```sh
sudo ufw allow 27960/udp
sudo ufw status verbose
```

TLS administration can remain on loopback and be used through SSH. Direct in-game administration requires explicitly exposing the TLS listener and distributing its trusted certificate/profile. [Administrator setup](server-commands.md)

Docker publishes ports through its own firewall rules. Check the provider firewall and Docker’s firewall behavior when applying host filtering. The supplied Compose file restricts administration to loopback at the publish rule. [Docker firewall behavior](https://docs.docker.com/engine/network/packet-filtering-firewalls/)

## Basement Linux networking

1. Give the Linux computer a DHCP reservation or stable LAN address.
2. Install the server and allow its UDP port on the computer’s firewall.
3. In your router, forward external UDP 27960 to that computer’s UDP 27960.
4. Players on the LAN use the computer’s LAN address. Friends elsewhere use your public address or dynamic-DNS hostname.
5. Test with a friend outside your home network or a client on another connection.

If the router’s WAN address differs from the address visible on the Internet, investigate double NAT or carrier-grade NAT with your ISP. A home connection behind CGNAT generally needs an ISP-provided public address or a UDP-capable tunnel/relay. Ordinary TCP web tunnels do not carry the game’s UDP traffic. Routers with no hairpin NAT may require the LAN address for people inside the house.

ENet gameplay uses UDP. A TCP-only port check does not demonstrate whether a player can connect. [Godot hosting considerations](https://docs.godotengine.org/en/stable/tutorials/networking/high_level_multiplayer.html#hosting-considerations)
