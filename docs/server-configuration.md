# Dedicated server configuration

[Hosting](server-hosting.md) · [Administration](server-commands.md) · [Operations](server-operations.md)

Server configuration uses Godot ConfigFile syntax. Strings are quoted, booleans are `true`/`false`, and numbers are unquoted. The supplied native and Docker examples are in `deploy/server/`. Client graphics, controls, microphone settings, and console preferences remain in each client’s own user-data directory.

## Startup arguments

Godot options go before `--`. Bumrush server options go after it. A dedicated export starts the server automatically, and `--server` also enables dedicated startup when running the source project.

```sh
./bumrush-server --headless --audio-driver Dummy -- --server --config /etc/bumrush/server.cfg --data-dir /var/lib/bumrush
godot --headless --path . -- --server --config ./server.cfg
```

| Argument | Behavior |
| --- | --- |
| `--server` | Start dedicated mode explicitly |
| `--init-server` | Create a fresh TLS identity, owner credential/profile, administrator registry, and bans file, then exit |
| `--config PATH` | Read configuration at PATH, default `server.cfg` relative to the process working directory |
| `--data-dir PATH` | Override durable-state location |
| `--bind ADDRESS` | Override gameplay listen address |
| `--port N` | Override gameplay UDP port |
| `--server-help` | Print supported server arguments and exit |

Both `--port 27960` and `--port=27960` are accepted. Defaults are applied first, then configuration keys, then explicit command-line overrides. Unknown arguments, sections, keys, or invalid values fail startup. A missing configuration file is allowed only during initialization.

Relative configuration paths are resolved against the process working directory. Relative `data_dir` paths are resolved against the configuration file’s directory. Use absolute paths in service units. Reload preserves command-line overrides.

## Supported keys

<!-- server-catalog:start -->
| Setting | Default | Bounds | Apply |
| --- | --- | --- | --- |
| `admin.bind` (`admin_bind`) | `"127.0.0.1"` | IP address | Restart |
| `admin.port` (`admin_port`) | `27961` | 1024 to 65535 | Restart |
| `server.bind` (`bind`) | `"0.0.0.0"` | IP address | Restart |
| `paths.data_dir` (`data_dir`) | `"server-data"` |  | Restart |
| `server.map` (`map`) | `"switchyard"` |  | Restart |
| `server.max_players` (`max_players`) | `8` | 1 to 8 | Restart |
| `server.max_unlag` (`max_unlag`) | `0.2` | 0.0 to 0.2 | Live |
| `server.motd` (`motd`) | `"Welcome to Switchyard"` | 512 UTF-8 bytes | Live |
| `server.port` (`port`) | `27960` | 1024 to 65535 | Restart |
| `server.server_name` (`server_name`) | `"Bumrush dedicated server"` | 96 UTF-8 bytes | Live |
| `server.sv_cheats` (`sv_cheats`) | `false` |  | Live |
| `server.voice_enabled` (`voice_enabled`) | `true` |  | Live |
<!-- server-catalog:end -->


`max_unlag` bounds server hit-history rewind. The fixed simulation rate is 120 Hz and snapshots are sent at 30 Hz. Set `[server] map` to `"switchyard"` (default), `"furnace"` or `"fy_snow"`. Each map runs endless deathmatch with a two-second respawn. There is one instance per process.

Named native installations write an absolute instance data path; the generated defaults example uses `server-data` relative to the config directory. The generated owner profile uses the configured admin port, loopback host, and TLS name `bumrush-server`. Customize the client profile’s host for remote connections.

## Durable files

| File in data directory | Purpose |
| --- | --- |
| `server.key` | Private TLS identity key |
| `server.crt` | Public certificate distributed to administrators |
| `admins.json` | Administrator roles and credential hashes |
| `bans.json` | Persistent IP ban list |
| `owner.key` | Initial owner credential |
| `owner.profile.json` | Initial local administration profile |

Initialization refuses to replace any existing identity or initial-owner file. To prepare another instance, use another configuration and state directory. Back up an instance before deliberately replacing an identity. Copying a server certificate to an admin client is safe. The private server key stays on the host.

Linux initialization protects the state directory and private files with restrictive owner permissions. An administrator profile contains filesystem paths to the trusted certificate and credential. Relative profile paths are relative to the profile’s directory. Keep profile and credential files out of source control, container images, and deployment archives.

## Direct remote administration

Change `[admin] bind` to the interface that should accept administrators, restart the process, and allow TCP 27961 from administrator addresses in your firewall. With Docker, change the host publish rule deliberately, for example `"192.0.2.10:27961:27961/tcp"`, using the host’s actual interface address.

The administration channel requires TLS and server-certificate validation. The public game port alone does not expose owner credentials. You can keep the administration listener on loopback and use an SSH tunnel from the game client instead. [Profiles and SSH forwarding](server-commands.md)


Live `config` changes validate the entire persisted configuration before saving or applying. Unknown sections/keys and invalid restart-only disk settings must be repaired first. Invalid candidates leave disk and live values unchanged.
