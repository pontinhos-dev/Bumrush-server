# Release readiness and publication review

[Documentation](README.md) · [Maintainer guide](server-development.md) · [Security](security.md)

## Review scope — 2026-11-15

The pre-publication review covered the distribution's tracked files and reachable Git history, commit author/committer metadata, GitHub release assets, ignore rules, workflow permissions, and the successful installation workflow's logs.

The initial runtime audit verified the remote archive's SHA256 against the local artifact and inspected all 42 archive files, 2,376 PCK entries, 85 decompressed compiled scripts, 346 decompressed resources, and both stripped Linux binaries. This distinguishes actual private keys from the engine's generic PEM parser strings. Upstream engine build paths are vendor metadata, not this project's developer home directories.

Gitleaks 8.30.1, obtained from its official release and checksum-verified, scanned complete Git history and the working directory with fully redacted reporting. Neither scan found live credentials. Documentation passkeys are explicit replacement placeholders, not usable credentials.

## Corrections

- Replaced personal author/committer email metadata with the account's GitHub noreply identity throughout published history and configured future commits the same way.
- Changed release provenance to record a project-relative gate-evidence path instead of an absolute developer workstation path. A regression test protects this boundary.
- Reissued the SHA256 sidecar with POSIX LF line endings so GNU checksum verification works on Linux.
- Restricted packaged documentation to the operator guides instead of distributing unrelated game-development notes.
- Expanded ignores for environment files, private key formats, SSH keys, password databases, private CFGs, data directories, enrollment ZIPs, and backups.
- Added a full-history secret-scanning workflow with read-only permissions, pinned official actions, redacted output, and no report-artifact uploads.
- Reworked hosting, configuration, administration, backup, restore, update, and troubleshooting documentation. Removed obsolete protocol claims and unverified performance figures.

The release archive and checksum must be regenerated after packaging changes. Maintainers verify the uploaded digest matches the reviewed local artifact before completing the review.

## Validation record

The game regression gate runs before exporting the runtime. The Linux workflow checks native startup, loopback-only administration, private enrollment, live Owner passkey authentication, and unchanged credentials/configuration on repeat installation.

Public repositories exercise the anonymous curl path. A private preview uses a read-only CI token only to download the release, verifies its checksum, and provisions the package without passing that token into the installer. Anonymous users cannot install from a private repository.

Documentation checks cover local Markdown links/anchors, shell-block syntax, and consistency of generated command/configuration reference tables. Secret scanning supplements these checks; it does not validate command semantics or replace the native smoke test.

## Before making the repository public

1. Keep the repository private while addressing findings and reviewing the final diff.
2. Scan all reachable refs, files, release archives, and workflow output again after the final changes.
3. Confirm no runtime credentials, private keys, client CFGs, enrollment ZIPs, logs with private player data, or local backup refs are published.
4. Verify the release manifest, matching SHA256 sidecar, compatibility notes, and required license notices.
5. Require successful secret-scanning and Linux installation checks. Treat multiplayer load and external connectivity as separate tests.
6. Make the visibility decision deliberately, then verify the anonymous download path after publication.

## Limits

No live credentials were identified by this review. Pattern scans and binary inspection cannot prove every possible encoding of a secret absent. Normal Godot packaging leaves compiled scripts and runtime assets inspectable; it is not source or asset obfuscation.

The repository was briefly public before this review. Changing visibility and rewriting reachable history cannot establish that no outside copies or cached metadata exist. No forks were reported at the start of the review. Do not treat Git history rewriting as credential revocation if a real credential is ever exposed. [GitHub's history-cleanup guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) explains these limits.

Installation/startup checks do not establish provider-specific WAN behavior, sustained eight-player capacity, or bandwidth cost.
