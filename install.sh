#!/usr/bin/env bash
# Public bootstrap; the game runtime comes from a verified GitHub Release.
set -euo pipefail
umask 077

repo=pontinhos-dev/Bumrush-server
version=latest
host=
confirmed=false
usage() {
    echo 'Usage: bash install.sh --quickstart [--host PUBLIC_IP_OR_DNS] [--version TAG] [--repo OWNER/REPO]'
    echo 'Requires Ubuntu 24.04 x86_64 with systemd and root/sudo access.'
}
while (($#)); do
    case "$1" in
        --quickstart) confirmed=true; shift ;;
        --host|--version|--repo)
            if (($# < 2)) || [[ "$2" == --* ]]; then usage >&2; exit 2; fi
            case "$1" in --host) host=$2 ;; --version) version=$2 ;; --repo) repo=$2 ;; esac
            shift 2 ;;
        --help|-h) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
done
if [[ "$confirmed" != true ]]; then usage >&2; exit 2; fi
if [[ ! "$repo" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$ ]] ||
   [[ ! "$version" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$ ]] ||
   { [[ -n "$host" ]] && [[ ! "$host" =~ ^[A-Za-z0-9][A-Za-z0-9.-]*$ ]]; }; then
    echo 'Invalid repository, version, or host.' >&2; exit 2
fi
if [[ $(uname -s) != Linux || $(uname -m) != x86_64 ]]; then
    echo 'This quick start supports Linux x86_64 only.' >&2; exit 1
fi
# shellcheck source=/dev/null
source /etc/os-release
if [[ "$ID" != ubuntu || "$VERSION_ID" != 24.04 || ! -d /run/systemd/system ]]; then
    echo 'Use an Ubuntu 24.04 x86_64 server booted with systemd.' >&2; exit 1
fi
elevate=()
if ((EUID != 0)); then elevate=(sudo); fi
echo 'Installing the headless server dependencies...'
"${elevate[@]}" env DEBIAN_FRONTEND=noninteractive apt-get update </dev/null
"${elevate[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ca-certificates curl python3 libstdc++6 libfontconfig1 </dev/null

temporary=$(mktemp -d)
trap 'rm -rf -- "$temporary"' EXIT
curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
    --connect-timeout 20 --max-time 120 \
    "https://raw.githubusercontent.com/$repo/main/tools/quickstart.py" -o "$temporary/quickstart.py"
arguments=(--quickstart --repo "$repo" --version "$version")
if [[ -n "$host" ]]; then arguments+=(--host "$host"); fi
# Keep pipe input away from apt and Python; sudo uses the SSH terminal for its prompt.
"${elevate[@]}" env "BUMRUSH_SSH_CONNECTION=${SSH_CONNECTION:-}" \
    "BUMRUSH_SSH_USER=${SUDO_USER:-$(id -un)}" \
    python3 "$temporary/quickstart.py" "${arguments[@]}" </dev/null
