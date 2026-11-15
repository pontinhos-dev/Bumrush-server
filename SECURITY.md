# Security policy

## Report a vulnerability

Do not open a public issue containing credentials, private keys, a working exploit, private configuration, or player data.

When GitHub private vulnerability reporting is available, use **Security → Advisories → Report a vulnerability**. If unavailable, use a private channel already established with the maintainer before sending sensitive material. No public support email is designated here.

Include the affected release, attack requirements, expected impact, and minimal reproduction with secrets removed. Reports never need an actual Owner passkey, enrollment ZIP, data directory, or private backup.

## Exposed credentials

Revoke/rotate an exposed credential promptly. Deleting a file or changing repository visibility does not invalidate downloaded secrets. Distribute updated enrollment through a trusted route when necessary.

## Supported releases

Use the latest published release unless maintainers document a compatibility reason otherwise. Gameplay protocols must be compatible. Quick start does not update an existing installation automatically.

There is no published long-term-support or response-time guarantee. Installation tests do not replace operational monitoring or provider-specific load testing.

Read [Security and privacy](docs/security.md) for credentials, TLS trust, and safe diagnostics.
