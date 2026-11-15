"""Provision one Ubuntu dedicated server from a checksum-verified GitHub Release."""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import secrets
import shlex
import shutil
import stat
import string
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile

REPOSITORY = "pontinhos-dev/Bumrush-server"
ASSET = "server-linux-x86_64.tar.gz"
ROOT = Path("/opt/bumrush")


def generate_passkey() -> str:
    return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "Bumrush-Quickstart", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if not response.geturl().startswith("https://"):
            raise ValueError("Release metadata redirected outside HTTPS")
        data = response.read(2 * 1024 * 1024 + 1)
    if len(data) > 2 * 1024 * 1024:
        raise ValueError("Release metadata is too large")
    return json.loads(data)


def download_asset(url: str, target: Path, digest: str, size: int) -> None:
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ValueError("Release asset needs GitHub's SHA256 digest; re-upload legacy assets")
    if type(size) is not int or not 0 < size <= 1024 * 1024 * 1024:
        raise ValueError("Invalid release size")
    checksum = hashlib.sha256()
    received = 0
    request = urllib.request.Request(url, headers={"User-Agent": "Bumrush-Quickstart"})
    with urllib.request.urlopen(request, timeout=60) as response, target.open("xb") as output:
        if not response.geturl().startswith("https://"):
            raise ValueError("Asset redirected outside HTTPS")
        while chunk := response.read(1024 * 1024):
            received += len(chunk)
            if received > size:
                raise ValueError("Release exceeds its advertised size")
            checksum.update(chunk)
            output.write(chunk)
    if received != size or checksum.hexdigest() != digest.removeprefix("sha256:"):
        raise ValueError("Release checksum or size mismatch; nothing was installed")


def download_release(repo: str, version: str, target: Path) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", repo):
        raise ValueError("Invalid GitHub repository")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", version):
        raise ValueError("Invalid release tag")
    endpoint = "latest" if version == "latest" else "tags/" + version
    release = fetch_json(f"https://api.github.com/repos/{repo}/releases/{endpoint}")
    assets = [asset for asset in release.get("assets", []) if asset.get("name") == ASSET]
    if release.get("draft") or len(assets) != 1:
        raise ValueError(f"Publish a release containing exactly one {ASSET}")
    asset = assets[0]
    url = asset.get("browser_download_url", "")
    expected = f"https://github.com/{repo}/releases/download/"
    if not url.startswith(expected) or urllib.parse.urlsplit(url).query:
        raise ValueError("Release asset URL does not belong to the selected GitHub repository")
    print(f"Downloading {release.get('tag_name', version)} ({asset.get('size', 0) // 1048576} MiB)...", flush=True)
    archive = target / ASSET
    download_asset(url, archive, asset.get("digest", ""), asset.get("size"))
    return archive


def extract_release(archive: Path, target: Path) -> Path:
    # The outer digest must pass before any code from the release is imported/executed.
    with tarfile.open(archive, "r:gz") as package:
        members = package.getmembers()
        names, roots, total = set(), set(), 0
        for member in members:
            path = PurePosixPath(member.name)
            if (path.is_absolute() or ".." in path.parts or "\\" in member.name or ":" in member.name
                    or not path.parts or not (member.isfile() or member.isdir()) or member.name in names):
                raise ValueError("Unsafe release archive entry")
            names.add(member.name)
            roots.add(path.parts[0])
            total += member.size
        if len(roots) != 1 or len(members) > 10000 or total > 3 * 1024**3:
            raise ValueError("Invalid release archive layout or size")
        package.extractall(target, members=members, filter="data")
    result = target / roots.pop()
    manifest = json.loads((result / "manifest.json").read_text(encoding="utf-8"))
    files = manifest.get("files")
    actual = {p.relative_to(result).as_posix() for p in result.rglob("*")
              if p.is_file() and p.relative_to(result).as_posix() != "manifest.json"}
    if not isinstance(files, dict) or actual != set(files):
        raise ValueError("Release manifest file list mismatch")
    for name, digest in files.items():
        with (result / name).open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                raise ValueError(f"Release manifest checksum mismatch: {name}")
    for name in ("bumrush-server", "bumrush-server.pck", "admin_crypto.linux.x86_64.so", "tools/bumrushctl.py"):
        if name not in files:
            raise ValueError(f"Incomplete dedicated server release: {name}")
    return result


def private_write(path: Path, value: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output:
        output.write(value)
        output.flush()
        os.fsync(output.fileno())


def prepare_passkey(instance: Path, saved: Path) -> tuple[str | None, bool]:
    if saved.is_symlink():
        raise ValueError("Saved passkey must not be a symlink")
    if saved.exists():
        info = saved.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.geteuid():
            raise ValueError("Saved passkey must be a private file owned by the installer account")
        password = saved.read_text(encoding="utf-8")
        if not re.fullmatch(r"[A-Za-z0-9]{16}", password):
            raise ValueError("Invalid quick-start passkey receipt")
        return password, False
    if (instance / "data/admins.json").exists():
        return None, False  # Existing installations are never silently re-enrolled.
    password = generate_passkey()
    private_write(saved, password)  # Persist before enrollment so an interrupted setup can resume.
    return password, True


def export_client(instance: Path, state: dict, password: str, host: str, output: Path, uid: int, gid: int) -> bool:
    if output.exists() or output.is_symlink():
        return False
    certificate = instance / "data/server.crt"
    if certificate.is_symlink() or not certificate.is_file() or certificate.stat().st_size > 65536:
        raise ValueError("Invalid server certificate")
    profile = (f'[main]\nhost={json.dumps(host)}\ngame_port={state["game_port"]}\n'
               f'admin_host="127.0.0.1"\nadmin_port={state["admin_port"]}\nusername="owner"\n'
               f'passkey={json.dumps(password)}\ncertificate="server-main.crt"\nexpected_name="bumrush-server"\n')
    descriptor, temporary = tempfile.mkstemp(prefix=".enrollment-", dir=output.parent)
    try:
        with os.fdopen(descriptor, "w+b") as stream:
            with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as bundle:
                bundle.writestr("cfg/admin.cfg", profile)
                bundle.writestr("cfg/server-main.crt", certificate.read_bytes())
            stream.flush()
            os.fsync(stream.fileno())
            os.fchown(stream.fileno(), uid, gid)
        os.link(temporary, output)  # Never replace an existing enrollment or follow its symlink.
    finally:
        Path(temporary).unlink(missing_ok=True)
    return True


def configure(package: Path, archive: Path, host: str, login: str, ssh_port: int, root: Path = ROOT) -> None:
    import pwd
    identity = pwd.getpwnam(login)
    # Public runtime directories must be traversable by the unprivileged service user.
    os.umask(0o022)
    root.mkdir(mode=0o755, parents=True, exist_ok=True)
    if root.is_symlink() or root.stat().st_uid != 0 or root.stat().st_mode & 0o022:
        raise ValueError("Hosting root must be root-owned and not writable by other users")
    root.chmod(root.stat().st_mode | 0o111)
    instance = root / "instances/main"
    if (instance / "instance.json").exists():
        existing = json.loads((instance / "instance.json").read_text(encoding="utf-8"))
        if existing.get("backend") != "native":
            raise ValueError("Quick start cannot change an existing Docker installation; use its current management tools")
    # Separate from service-owned data: the runtime never needs the plaintext receipt.
    receipt = root / "quickstart"
    receipt.mkdir(mode=0o700, exist_ok=True)
    if receipt.is_symlink() or receipt.stat().st_uid != 0 or receipt.stat().st_mode & 0o077:
        raise ValueError("Quick-start credential directory must be private and root-owned")
    with (receipt / "install.lock").open("a") as lock:
        import fcntl
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        credential_dir = receipt / "main"
        credential_dir.mkdir(mode=0o700, exist_ok=True)
        if credential_dir.is_symlink() or credential_dir.stat().st_uid != 0 or credential_dir.stat().st_mode & 0o077:
            raise ValueError("Unsafe quick-start instance directory")
        password, generated = prepare_passkey(instance, credential_dir / "owner-passkey")
        command = [sys.executable, str(package / "tools/bumrushctl.py"), "local", "install", str(archive),
                   "--root", str(root), "--instance", "main", "--register-service", "--start"]
        if password is not None:
            command += ["--owner-passkey-file", str(credential_dir / "owner-passkey")]
        subprocess.run(command, check=True, stdin=subprocess.DEVNULL)
        state = json.loads((instance / "instance.json").read_text(encoding="utf-8"))
        bundle = root / "bumrush-main-admin.zip"
        exported = False
        if password is not None:
            exported = export_client(instance, state, password, host, bundle, identity.pw_uid, identity.pw_gid)
        if shutil.which("ufw"):
            status = subprocess.run(["ufw", "status"], check=True, capture_output=True, text=True, env=dict(os.environ, LC_ALL="C"))
            if "Status: active" in status.stdout:
                subprocess.run(["ufw", "allow", f'{state["game_port"]}/udp', "comment", "Bumrush"], check=True)
        print(f'\nBumrush is running. Players connect to {host}:{state["game_port"]}.')
        print(f'Allow inbound UDP {state["game_port"]} in your cloud provider firewall. SSH rules were preserved.')
        if generated and sys.stdout.isatty():
            print(f"Owner username: owner\nOwner passkey: {password}")
        elif password is not None:
            print("Owner credentials preserved privately; the passkey is included in the admin ZIP.")
        accessible_bundle = bundle.is_file() and not bundle.is_symlink() and bundle.stat().st_uid == identity.pw_uid
        if not exported and bundle.exists() and not accessible_bundle:
            print(f"Existing enrollment belongs to another account. Retrieve {bundle} with its original SSH account or root.")
        if exported or accessible_bundle:
            destination = f"{login}@{host}" if ":" not in host else f"{login}@[{host}]"
            print("\nOn your gaming PC, download the private enrollment:")
            print(f"  scp -P {ssh_port} {shlex.quote(destination + ':' + str(bundle))} .")
            print("Extract it and copy cfg/admin.cfg and cfg/server-main.crt into the game's cfg folder.")
            print("If you already have cfg/admin.cfg, append its [main] entry instead of overwriting other entries.")
            print("Keep this SSH tunnel running on your gaming PC while using administration:")
            print(f"  ssh -N -p {ssh_port} -L 127.0.0.1:{state['admin_port']}:127.0.0.1:{state['admin_port']} {shlex.quote(login + '@' + host)}")
            print("Join the gameplay address in Multiplayer, then open the Admin menu. Keep the ZIP private.")
        else:
            print("Existing Owner account preserved. Use your current admin CFG; no replacement passkey was generated.")
        print(f"\nStatus: sudo systemctl status {state['service']}\nLogs: sudo journalctl -u {state['service']} -f")
        print("Rerunning quick start preserves the installed release and account; use the documented update command for upgrades.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quickstart", action="store_true", required=True)
    parser.add_argument("--repo", default=REPOSITORY)
    parser.add_argument("--version", default="latest")
    parser.add_argument("--host", help="Public gameplay IP/DNS; defaults to the server address used by this SSH session")
    args = parser.parse_args(argv)
    if (sys.platform != "linux" or platform.machine() != "x86_64"
            or not Path("/run/systemd/system").is_dir() or os.geteuid() != 0):
        raise ValueError("Run the Bash quick start on an Ubuntu 24.04 x86_64 systemd host with sudo/root")
    release = platform.freedesktop_os_release()
    if release.get("ID") != "ubuntu" or release.get("VERSION_ID") != "24.04":
        raise ValueError("Quick start supports Ubuntu 24.04 only")
    connection = os.environ.get("BUMRUSH_SSH_CONNECTION", "").split()
    host = args.host or (connection[2] if len(connection) == 4 else None)
    if not args.host and (not host or not ipaddress.ip_address(host).is_global or ":" in host):
        print("Detecting the server's public IP through ipify (use --host to override)...")
        host = str(ipaddress.ip_address(fetch_json("https://api.ipify.org?format=json")["ip"]))
        if not ipaddress.ip_address(host).is_global:
            raise ValueError("Public address lookup failed; provide --host PUBLIC_IP_OR_DNS")
    if not host or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", host):
        raise ValueError("Provide --host PUBLIC_IPV4_OR_DNS; the default gameplay listener uses IPv4")
    login = os.environ.get("BUMRUSH_SSH_USER") or os.environ.get("SUDO_USER") or "root"
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_.-]*\$?", login):
        raise ValueError("Invalid SSH login name")
    ssh_port = int(connection[3]) if len(connection) == 4 else 22
    with tempfile.TemporaryDirectory(prefix="bumrush-quickstart-") as temporary:
        staging = Path(temporary)
        archive = download_release(args.repo, args.version, staging)
        package = extract_release(archive, staging / "package")
        if subprocess.run(["getent", "passwd", "bumrush"], stdout=subprocess.DEVNULL).returncode:
            subprocess.run(["useradd", "--system", "--user-group", "--home-dir", "/var/lib/bumrush", "--shell", "/usr/sbin/nologin", "bumrush"], check=True)
        configure(package, archive, host, login, ssh_port)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, tarfile.TarError, zipfile.BadZipFile) as error:
        raise SystemExit(f"Quick start failed: {error}\nExisting configuration and saved credentials were preserved; correct the issue and rerun.")
