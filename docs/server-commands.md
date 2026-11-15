# Server administration

[Hosting](server-hosting.md) · [Configuration](server-configuration.md) · [Operations](server-operations.md)

Bumrush uses one authority-owned command policy for cloud servers and listen servers. Menu controls, console commands, chat commands and the TLS operator helper share permissions. A player name or IP address never grants staff access. Verified Steam identities are not implemented yet.

## Join your own server as Owner

New interactive server installation asks twice for an Owner passkey of 12–128 printable characters. The listen-host menu has matching masked passkey fields; its local player is automatically Owner. Each remote staff member should have a separate named account and passkey.

For a standalone cloud instance, the setup helper creates its configuration, certificate and private client enrollment files:

```sh
python3 tools/admin_setup.py --server ./bumrush-server --config ./server.cfg --data-dir ./server-data --client-dir ./private-client-export --host game.example.com --remote-admin
```

The helper prompts privately. It never takes a raw passkey as a process argument. `--passkey-file` supports a protected unattended input file with no trailing newline. Setup refuses existing configuration or credentials. It exports `admin.cfg` and the public certificate into the private client directory. Transfer those files using trusted SSH/SCP, then place them in `cfg/` beside `Bumrush.exe`.

Installed services can use `bumrushctl.py local install` with its masked prompt or `--owner-passkey-file`. Noninteractive legacy installation without a passkey file still creates the original random-token owner profile; enroll passkey staff through an authenticated Owner before using saved CFG login. Existing instances and credential files are preserved when updating.

An example client CFG entry follows. Replace the passkey placeholder locally; never post your actual file publicly.

```ini
[my-cloud]
host="game.example.com"
game_port=27960
admin_host="game.example.com"
admin_port=27961
username="owner"
passkey="REPLACE-WITH-YOUR-PRIVATE-PASSKEY"
certificate="server-my-cloud.crt"
expected_name="bumrush-server"
```

The client automatically authenticates for a matching server on join. The Credentials dialog can save or select an entry and displays its active file path. A per-user `user://cfg/admin.cfg` overrides the portable file when present, including when the executable directory is unwritable. CFG files are data; they are never executed as console scripts. The server stores Argon2id passkey verifiers. Client CFG files contain the actual secret and must remain private.

Administration uses certificate-validated TLS TCP, normally on port 27961. Gameplay uses UDP, normally 27960. The certificate must come from your trusted setup/SSH transfer, never an unauthenticated gameplay message. Existing loopback-only deployments remain loopback-only unless you explicitly enable direct administration and firewall its TCP port. For an SSH tunnel use `ssh -N -L 27961:127.0.0.1:27961 your-user@game.example.com` and set `admin_host="127.0.0.1"` in the CFG. The gameplay host stays unchanged.

Authentication is bound to the current gameplay connection using a 30-second single-use challenge. Reconnect requires rebinding; map changes keep access. Credential rotation, revocation, disconnect and changing servers invalidate the old binding. An Owner can also connect from the main menu when the game is full and moderate before joining.

## Commands from the menu, console and chat

Enter `admin` in the console or `/admin` in chat to open the administration menu. Its sections are Players, Moderation, Reports, Server, Votes, Fun, Staff and History. Permissions filter available actions; the server rechecks permissions and target connections at execution.

```text
admin players
admin kick "Player Name" "Repeated disruption"
admin ban #42 60 "Repeated disruption"
admin slay #42
admin changelevel fy_snow
```

In chat, use `/kick`, `/ban`, `/slay`, and so on, without the console's `admin` prefix. `/kill <target>` aliases administrative `slay`. Plain console `kill` remains self-suicide and refuses extra arguments.

Slash command text is never broadcast, added to normal chat history, or recorded as demo chat. Unknown and denied commands stay private too. Results appear in the private administration feed. Successful moderation and fun actions show a public notice identifying the staff member, action and target. Staff messages, reports and private replies are not part of public demo chat; public action notices remain ordinary visible notices.

Targets can be `#connection_id`, a quoted exact name, a unique partial name, or `@me`. Ambiguous names return candidates. `#@all` targets a player literally named `@all`; `@all` is a selector. Owner-only bulk selectors include `@all`, `@alive`, `@dead`, and `@others` on supported actions. Bulk actions return a confirmation token; `admin confirm <token>` must execute within 30 seconds. Reconnected or changed targets invalidate confirmation. Bulk bans are unavailable.

## Roles and protection

- **Player:** public information, reports, vote responses and ordinary self-suicide.
- **Moderator:** warnings, chat/voice sanctions, kicks, temporary bans up to 24 hours, reports, staff messages, self-spectating and kick votes.
- **Admin:** Moderator powers plus permanent sanctions, unbanning, slay, respawn, maps, match restart and map/restart votes.
- **Owner:** Admin powers plus staff accounts, credentials, protected settings, shutdown and fun commands.

Equal- and higher-ranked staff are protected from administrative targeting. Explicit self-actions remain available where applicable. This protection does not affect normal combat. The listen host cannot be kicked and the final persistent Owner cannot be revoked or demoted. `grant_admin <id>` is a temporary **Admin** role, not Owner; only Owner controls `sv_cheats` and `sv_autobunnyhopping`.

<!-- server-catalog:start -->
| Command | Required role |
| --- | --- |
| `access` | player |
| `admin_add <name> <owner&#124;admin&#124;moderator>` | owner |
| `admin_revoke <name>` | owner |
| `adminmenu` | moderator |
| `admins` | owner |
| `armor <target> <amount>` | owner |
| `asay <message>` | moderator |
| `ban <target> <minutes&#124;0> [reason]` | moderator |
| `banip <address> <minutes&#124;0> [reason]` | owner |
| `bans [offset] [limit]` | moderator |
| `beacon <target> [0&#124;1]` | owner |
| `bring <target>` | owner |
| `cancelvote` | admin |
| `changelevel <map>` | admin |
| `config [key [value]]` | owner |
| `confirm <token>` | player |
| `execpreset <name>` | owner |
| `freeze <target> [seconds]` | owner |
| `gag <target> [minutes] [reason]` | moderator |
| `give <target> <weapon&#124;ammo&#124;health&#124;armor>` | owner |
| `god <target> [0&#124;1]` | owner |
| `goto <target>` | owner |
| `health <target> <amount>` | owner |
| `help [command]` | player |
| `history [target]` | moderator |
| `kick <target> [reason]` | moderator |
| `map_restart` | admin |
| `maplist` | admin |
| `motd` | player |
| `mute <target> [minutes] [reason]` | moderator |
| `mutelist` | moderator |
| `noclip <target> [0&#124;1]` | owner |
| `players` | moderator |
| `psay <target> <message>` | moderator |
| `quit` | owner |
| `reload_config` | owner |
| `report <target> <reason>` | player |
| `reports [open&#124;all]` | moderator |
| `resolve <report_id> [note]` | moderator |
| `respawn <target>` | admin |
| `rules` | player |
| `say <message>` | moderator |
| `shutdown [seconds] [reason]` | owner |
| `silence <target> [minutes] [reason]` | moderator |
| `slap <target> [damage]` | owner |
| `slay <target> [reason]` | admin |
| `spectate [target&#124;off]` | moderator |
| `status` | player |
| `sv_autobunnyhopping [0&#124;1]` | owner |
| `sv_cheats [0&#124;1]` | owner |
| `teleport <target> <x> <y> <z>` | owner |
| `unbanip <address>` | admin |
| `unfreeze <target>` | owner |
| `ungag <target>` | moderator |
| `unmute <target>` | moderator |
| `unsilence <target>` | moderator |
| `vote <yes&#124;no>` | player |
| `vote_status` | player |
| `votekick <target> [reason]` | moderator |
| `votemap <map>` | admin |
| `voterestart` | admin |
| `warn <target> [reason]` | moderator |
| `who <target>` | moderator |
<!-- server-catalog:end -->

## Moderation, reports and votes

`mute` blocks voice, `gag` blocks text chat and `silence` blocks both. Their undo commands restore the selected channel. Communication sanctions default to 30 minutes. Ban commands require an explicit duration in minutes; `0` means permanent and requires Admin. Legacy `mute <id> voice|chat|all` and equivalent unmute forms remain accepted.

Until Steam authentication exists, bans and timed communication sanctions follow the target's exact IP address. They survive reconnect, map changes and restart, and expire using UTC. People sharing a router may be affected together. The menu identifies this consequence; sanctions that would also affect protected connected staff are rejected. Names are not durable identity. History matches associated addresses and recorded names, not a verified account history.

Reports have a 60-second submission cooldown and an open/resolved workflow. Gagged players can still submit reports and ask for help. Staff can use `asay <message>` for private staff chat and `psay <target> <message>` for a private message. Audit history records successful and failed administrative requests, without passkeys. Storage is bounded and audit files rotate.

Only staff start votes. Votes last 30 seconds with a fixed starting electorate; late joiners do not enter that vote. They require at least two eligible voters, turnout from at least half, and 60% yes among votes cast. The server cooldown is two minutes, with a five-minute cooldown for the same kick-vote target. Players respond with `/vote yes` or `/vote no`. Permissions and target protection are checked again before an approved action executes.

## Gameplay administration

`slay` follows administrative death policy without weapon frag credit, bonuses or score rewards. `respawn` restores normal participation. `spectate [target|off]` removes the staff member from play until they leave spectating: no collisions, firing or automatic respawn. Primary/secondary attack cycle living targets.

Owner fun commands work with `sv_cheats 0` and do not enable ordinary player cheats. Freeze defaults to 30 seconds and caps at 600. Teleport destinations must be finite, outside the kill region and clear of world geometry and other players. Health and armor range from 0 to 100. `give` accepts a stable weapon ID, `ammo`, `health` or `armor`. Temporary effects clear on respawn and session changes. Beacon and spectator visuals are preserved in new demos; historical demos without those fields still play.

## Staff accounts and legacy operator profiles

Use the Staff menu to create an account, change its role, rotate its passkey or revoke it. Secret fields are masked and are never sent through console/chat commands. The final Owner is protected. Revocation and credential/role changes invalidate existing sessions.

Existing random-token profiles remain supported:

```text
admin_connect "C:/Private/Bumrush/owner.profile.json"
admin status
admin players
admin_disconnect
```

The CLI operator helper also remains available:

```sh
python3 tools/bumrushctl.py --profile server-data/owner.profile.json status
python3 tools/bumrushctl.py --profile server-data/owner.profile.json console
```

`admin_add <name> <role>` preserves legacy token enrollment; transfer its named profile, key and public certificate securely. Passkey enrollment through the Staff menu is the preferred in-game workflow. Do not revoke the local token identity used by service health/shutdown wrappers without updating their selected profile.

Administration protocol 2 supports passkey authentication, gameplay binding and typed account requests while retaining version-1 token authentication. Live game protocol 26 requires matching clients and servers. Administration versions remain independent of game and demo versions. Requests, queues, authentication attempts, responses and password work are bounded. Neither console nor chat administration supports shell execution or arbitrary script commands.
