# Getting started

[Documentation](README.md) · [Configuration](server-configuration.md) · [Troubleshooting](troubleshooting.md)

This walkthrough is for a first-time server owner with SSH access to Ubuntu 24.04 on an Intel/AMD x86_64 machine. **Server** commands run in your SSH session. **Gaming PC** commands run on the computer where you play.

## Before you begin

- Use Ubuntu 24.04 x86_64 with systemd. ARM requires a different runtime and is not supported by this release.
- Start with two modern CPU cores and 2 GB RAM, then measure real player load. These are estimates.
- Have a public IPv4 address or a DNS name resolving to it. Home hosting also requires UDP forwarding; see [Hosting](server-hosting.md).
- Keep SSH access available. Do not change its firewall rule while setting up gameplay.
- Use a client compatible with the server's game protocol, recorded in the release manifest.

## 1. SSH into the server

**Gaming PC:**

```sh
ssh YOUR_SSH_USER@YOUR_SERVER_ADDRESS
```

For a custom SSH port:

```sh
ssh -p 2222 YOUR_SSH_USER@YOUR_SERVER_ADDRESS
```

Verify a new SSH host key through your provider or another trusted route. Use a normal account with `sudo` when available; the game service runs as the separate `bumrush` account.

## 2. Install the server

**Server:** install the initial download tool if it is missing:

```sh
sudo apt-get update
sudo apt-get install -y curl ca-certificates
```

Then run:

```sh
curl -fsSL https://raw.githubusercontent.com/pontinhos-dev/Bumrush-server/main/install.sh | bash -s -- --quickstart --host YOUR_SERVER_ADDRESS
```

`--host` is optional. Supplying it avoids a public-IP lookup and makes the address saved in your client CFG explicit. Use a public IPv4 address or IPv4 DNS name. The script installs dependencies, downloads and verifies the runtime, initializes Owner credentials, enables `bumrush-main`, and starts it.

The generated passkey has 16 cryptographically selected letters/digits. It is displayed when output goes to a terminal, saved privately on the server, and included in the private enrollment ZIP. It grants Owner administration; it does not restrict ordinary players from joining.

If setup fails, read the error and [Troubleshooting](troubleshooting.md) before retrying. A retry preserves the setup key and enrolled accounts. Do not delete configuration or data to get past an error.

## 3. Check the service

**Server:**

```sh
sudo systemctl is-active bumrush-main
sudo systemctl status bumrush-main --no-pager
sudo journalctl -u bumrush-main -n 50 --no-pager
sudo ss -lunp
```

Expect an active service and a UDP listener on port 27960. The installer's health check also verifies a certificate-validated administration response on loopback. This does not prove the provider allows external gameplay traffic.

## 4. Allow gameplay traffic

In your provider's firewall or security group, allow inbound **UDP 27960** from the players you want to admit. Preserve SSH access. With active UFW, quick start adds the game rule. It does not enable inactive UFW or configure another firewall system.

Inspect an existing UFW policy with:

```sh
sudo ufw status verbose
```

For a custom gameplay port, allow that UDP port in every firewall and use it when joining. A successful TCP test does not test ENet's UDP gameplay. Keep TCP 27961 closed to the public Internet; use SSH for administration.

## 5. Join as a player

**Gaming PC:** open a compatible client. Use Multiplayer, or enter in the game console:

```text
connect YOUR_SERVER_ADDRESS 27960
```

Join using the same address saved in your admin CFG for automatic administration login. Ordinary players do not need the Owner ZIP or passkey.

## 6. Transfer your Owner enrollment

**Gaming PC:** use the SCP command printed by setup, or:

```sh
scp YOUR_SSH_USER@YOUR_SERVER_ADDRESS:/opt/bumrush/bumrush-main-admin.zip .
```

For a custom SSH port, SCP uses uppercase `-P`:

```sh
scp -P 2222 YOUR_SSH_USER@YOUR_SERVER_ADDRESS:/opt/bumrush/bumrush-main-admin.zip .
```

The ZIP is private to the SSH account used during setup. If a different account installed it, retrieve it with that account or have the server owner arrange a protected transfer. Do not make it world-readable.

Extract the ZIP. It contains:

```text
cfg/
  admin.cfg
  server-main.crt
```

Place both files in `cfg/` beside `Bumrush.exe`. If `admin.cfg` already contains other servers, append the new section under a unique section name rather than replacing the file. Preserve each entry's certificate filename. The Credentials dialog shows the active CFG path; a per-user CFG can override the portable one.

The CFG contains the actual passkey. Keep it and the ZIP out of shared folders, public repositories, screenshots, and issue reports. The certificate is public information, but SSH transfer establishes its authenticity.

## 7. Open the administration tunnel

**Gaming PC:**

```sh
ssh -N -L 127.0.0.1:27961:127.0.0.1:27961 YOUR_SSH_USER@YOUR_SERVER_ADDRESS
```

For a custom SSH port:

```sh
ssh -N -p 2222 -L 127.0.0.1:27961:127.0.0.1:27961 YOUR_SSH_USER@YOUR_SERVER_ADDRESS
```

An idle terminal is normal: `-N` runs only the tunnel. Leave it open while moderating. The local end binds to 127.0.0.1 so other computers cannot use your forwarded endpoint.

If local port 27961 is occupied, choose another local port:

```sh
ssh -N -L 127.0.0.1:27962:127.0.0.1:27961 YOUR_SSH_USER@YOUR_SERVER_ADDRESS
```

Set `admin_port=27962` in this server's client CFG entry. Leave the server's actual administration port at 27961. Keep `admin_host="127.0.0.1"` and the gameplay host unchanged.

## 8. Moderate from the game

Join, then enter `admin` in the console or `/admin` in chat. The game authenticates the saved credentials over trusted TLS and binds permissions to your current player connection. You can play normally while moderating.

Use Staff to create separate Moderator/Admin identities. Do not share your Owner ZIP with every staff member. See [Administration](server-commands.md) for permissions and commands.

## Next steps

- Configure maps, name, player cap, and voice using [Configuration](server-configuration.md).
- Create a protected [backup](server-operations.md) before adding staff or updating.
- Learn [updates and rollback](server-release-workflow.md); quick start does not upgrade an existing instance.
- Review [security and privacy](security.md) before sharing logs or exposing administration directly.
