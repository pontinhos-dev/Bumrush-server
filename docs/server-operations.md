# Operate a Bumrush server

[Hosting](server-hosting.md) · [Configuration](server-configuration.md) · [Commands](server-commands.md)

Each process hosts one eight-player deathmatch on its configured map. Keep its binary/PCK/native-extension set, configuration, credentials, and state together as an identifiable release and instance. Match scores are session state. Bans, administrator identities, and configuration are durable.

## Native service lifecycle

```sh
sudo systemctl start bumrush-main
sudo systemctl status bumrush-main
sudo systemctl restart bumrush-main
sudo systemctl stop bumrush-main
sudo systemctl enable bumrush-main
sudo journalctl -u bumrush-main --since '1 hour ago'
sudo journalctl -u bumrush-main -f
```

The unit restarts after failures and waits three seconds between attempts. Repeated failures hit a start limit. Correct the problem, then use `sudo systemctl reset-failed bumrush-main` followed by `start`. Its stop wrapper requests shutdown through the local owner profile and waits for the main process to exit before returning to systemd. The ten-second stop timeout allows a final forced termination if administration is unavailable.

## Container lifecycle

For a generated Docker instance rooted at `/srv/bumrush`, use its Compose project and file.

```sh
docker compose --project-name bumrush-main -f /srv/bumrush/instances/main/compose.yaml ps
docker compose --project-name bumrush-main -f /srv/bumrush/instances/main/compose.yaml logs --tail 100 server
docker compose --project-name bumrush-main -f /srv/bumrush/instances/main/compose.yaml restart server
docker compose --project-name bumrush-main -f /srv/bumrush/instances/main/compose.yaml stop server
docker compose --project-name bumrush-main -f /srv/bumrush/instances/main/compose.yaml up -d
```

The entrypoint handles termination by requesting a TLS admin shutdown, then waiting for the server. If the profile is unavailable or authentication fails, it falls back to terminating the process. Keep the local owner valid or set `BUMRUSH_ADMIN_PROFILE` to another working owner profile. Docker’s restart policy starts a stopped-by-failure container again. `compose stop` explicitly stops it.

Generated instances keep their data in `instances/main/data` on the host. Back up that directory with `config/` and `instance.json`. The hand-managed example uses a named volume that survives `compose down`. The `-v` option deletes named volumes, including this instance’s credentials and bans. Use it only when deliberately discarding an instance after backing it up.

The image health check makes a real certificate-validated TLS `status` request through the local owner profile. It allows a 15-second startup grace period, uses a 30-second interval, and marks the container unhealthy after three failed checks. Health status appears in `compose ps`. Docker restart policy responds to process exits, so inspect an unhealthy running process and its logs before restarting it. If you replace the local owner profile, update both the shutdown wrapper’s profile and the container health-check command.

## Logs and performance

The server prints lifecycle and administration events to standard output. Native deployments use journald. Compose limits its JSON logs to three 10 MB files. Inspect `status` for uptime, player count, memory, physics processing time, tick and snapshot rates, aggregate ENet traffic, and per-stream serialized snapshot/recording byte counters. Without recording subscribers there are no detailed POV uploads or distribution.

```sh
sudo -u bumrush python3 /opt/bumrush/instances/main/current/tools/bumrushctl.py --profile /opt/bumrush/instances/main/data/owner.profile.json --json status
ss -lunp | grep 27960
ss -ltnp | grep 27961
ps -o pid,%cpu,%mem,rss,etime,cmd -C bumrush-server
```

At 120 physics ticks per second, each tick has about 8.33 ms available. Measure under a full match, including voice and projectiles. Status exposes `memory_bytes` from Godot’s static-allocation monitor, which can report zero in a release build. On Linux, `rss_bytes` reads the process resident-set size from `/proc/self/status`, and reports `-1` when unavailable. Network counters cover ENet gameplay traffic. Use OS measurements alongside game diagnostics before selecting VM size.

A short protocol-11 eight-player check on 12 November 2026 used one native moving client and seven headless clients on a Windows localhost server, while other integration checks also ran. Five instantaneous samples reported mean physics time 2.60 ms, maximum 2.80 ms, maximum Godot static allocation 31.96 MiB, mean outgoing ENet traffic 1.38 MB/s, and incoming 0.34 MB/s. That is roughly 11.0 Mb/s outgoing and 2.7 Mb/s incoming before link overhead. This smoke profile helps identify upload requirements. It is a short local profile and provides no sustained WAN or Linux capacity guarantee. Provision additional bandwidth for variance, voice, and operating-system traffic.

A protocol-12 local eight-client sample measured about 218 KB/s outgoing with no recorders, 294 KB/s with one recorder, and 831 KB/s with eight recorders. The zero-recorder sample was about 84% below the earlier protocol-11 short baseline. Recorder baselines refreshed after map restart, and detailed stream counters stopped after the final unsubscribe. These short local samples characterize this workload; sustained WAN capacity still needs measurement.

## Back up and restore

Stop the instance, then back up configuration and the entire data directory to a protected location. The data backup contains reusable administrator credentials and the private TLS identity.

```sh
sudo systemctl stop bumrush-main
sudo tar -czf /root/bumrush-instance-backup.tar.gz -C /opt/bumrush/instances/main config data instance.json
sudo chmod 0600 /root/bumrush-instance-backup.tar.gz
sudo systemctl start bumrush-main
```

For Docker, stop the instance and use a container volume backup workflow to preserve `server-data`, plus the host’s `deploy/server/config` directory. Restore into a stopped instance with the same ownership and private permissions. Restoring the old TLS identity lets existing administrator profiles continue to validate it.

## Updates, rollback and multiple instances

Use the [release workflow](server-release-workflow.md) to verify/install, stage updates, explicitly restart, recover failed startup and roll back. Named instances generate independent ports, paths, service/Compose names and shutdown identities. Existing hand-managed units retain their original paths.

## Troubleshooting

| Symptom | Inspect and resolve |
| --- | --- |
| Startup reports missing state | Initialize a fresh instance, or correct `--data-dir` to the existing initialized directory |
| Initialization refuses to overwrite | Use the existing instance state or choose a new directory |
| Port bind fails | Check `ss`, another instance, bind address, and whether the port is already occupied |
| Clients time out | Check process logs, UDP host/provider/router rules, public address, CGNAT, and a real external client |
| Version rejected | Install the same client/server release and protocol |
| TLS certificate error | Use the instance’s actual public certificate and expected name, check clock/date, and verify profile paths |
| Administration connection refused | Check listener bind, profile port, SSH tunnel, and Docker host-loopback publication |
| Owner authentication fails | Check credential-file path, revocation, private-file access, and the intended instance |
| Configuration will not save | Check that the configuration directory and file are writable by the service account, or UID 10001 for Compose |
| Reload requests a restart | An address, port, capacity, or data-directory setting changed |
| Players are unexpectedly IP-banned | Check `bans` and shared home-router/NAT addresses |
| Lag or large corrections | Check CPU/tick timing, packet loss, latency, input limits, and server/client release consistency |
| Container exits and starts again | Inspect logs and the `unless-stopped` policy. Use `compose stop` for an intentional stop |

Public hosting also requires ordinary OS updates, restricted SSH access, and appropriate provider network protection. Application admission/rate limits bound game work. They cannot absorb traffic that saturates the host’s network link.
