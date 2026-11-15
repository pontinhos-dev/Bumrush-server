# Security and privacy

[Documentation](README.md) · [Administration](server-commands.md) · [Operations](server-operations.md) · [Security reporting](../SECURITY.md)

## Network boundary

| Endpoint | Default | Exposure |
| --- | --- | --- |
| Gameplay | UDP 27960 | Reachable by admitted players |
| Administration | TLS TCP 27961 on 127.0.0.1 | Local server and trusted SSH tunnels |
| SSH | Your existing SSH TCP port | Your host/provider access policy |

Quick start keeps administration on loopback. It adds the game UDP rule only with active UFW, preserves SSH rules, and leaves other firewalls, security groups, and routers under your control.

Use SSH keys and maintain OS updates according to your hosting policy. Verify new SSH host keys through a trusted route. Test a second working connection before changing SSH authentication or firewall policy.

## Owner credentials

The generated 16-character passkey grants Owner administration. It is not a join password. The server checks permissions for menu, console, chat, and TLS commands.

The server stores an Argon2id verifier for passkey authentication. Setup passes the key through a protected temporary file, rather than a raw process argument or environment variable. Live login uses certificate-validated TLS.

Give staff separate identities with the least role required. Credential rotation/revocation invalidates access. The current gameplay connection must also bind to the authenticated identity.

## Private files

| File or directory | Why it matters |
| --- | --- |
| Client `cfg/admin.cfg` | Contains the actual passkey |
| Enrollment ZIP | Contains that CFG and trusted server certificate |
| `quickstart/main/owner-passkey` | Root-only copy of the initial generated key |
| Server `owner.key` | Legacy Owner token |
| Server `server.key` | Private TLS key |
| Server `admins.json` | Account records and passkey verifiers |
| Server data/backups | May contain credentials, player identities/IPs, bans, and audit logs |

Quick-start receipts are root-only. The ZIP is mode 0600 and belongs to the SSH account used for setup. The game service has a separate account and does not need the plaintext receipt.

The certificate (`server.crt` or `server-main.crt`) is public, but its authenticity matters. Transfer it through SSH or another trusted channel; never replace it from an unauthenticated gameplay message.

Do not place private files in public repositories, shared drives, screenshots, game releases, or support attachments. Ignore rules do not remove tracked files or clean Git history.

## Download trust

The bootstrap and helper come from the selected GitHub repository over HTTPS. Review them before granting root access. `--version TAG` pins the runtime release; bootstrap code still comes from `main`.

The helper checks GitHub's SHA256 digest and advertised size, rejects unsafe archive entries, and verifies the internal manifest before executing package code. These checks establish integrity relative to the trusted publisher; they do not protect against a compromised publisher account.

The release contains the executable, PCK, native library, operator tools, notices, and docs. Compiled game scripts and runtime assets remain inspectable/recoverable. It should never contain editable source art, private instance state, or project build-machine home paths.

## Recovery and rotation

Restore a coherent private backup. Do not mix a different server's TLS key, certificate, account database, and token profile.

The setup receipt is the original generated key. After an Owner changes the active key, update client CFGs and securely retire old copies. Rerunning setup does not reset accounts to old receipts or rewrite existing enrollment ZIPs.

If a credential is exposed, revoke/rotate it first through an authorized Owner or documented recovery route. Deleting a file does not invalidate copies in Git history, logs, downloads, or other computers. Reissue client trust if the server's TLS identity changes.

## Logs and backups

Keep backups private and outside the published repository. Store disaster-recovery backups outside the live VM and test restoration.

Logs may contain names, IDs, addresses, moderation reasons, and account activity even without passkeys. Share only a sanitized excerpt. Never upload full server data to demonstrate a bug.

## Publication review

Scan reachable Git history, tracked files, release archives including PCK resources, commit metadata, and CI logs. A clean working tree alone is insufficient. See [Release readiness](release-readiness.md) and the [maintainer guide](server-development.md).

Scans reduce risk; they cannot prove every possible secret encoding absent or erase copies made during a previous public period.
