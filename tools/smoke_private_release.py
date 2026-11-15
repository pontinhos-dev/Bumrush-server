"""CI-only installation check for a release downloaded through authenticated gh."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile

import quickstart


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--login", required=True)
    args = parser.parse_args()
    if os.geteuid() != 0 or "GH_TOKEN" in os.environ or "GITHUB_TOKEN" in os.environ:
        raise ValueError("Run this Linux CI helper as root without GitHub tokens")
    archive = args.archive.resolve()
    if archive.name != quickstart.ASSET:
        raise ValueError("Unexpected release archive name")
    sidecar = archive.with_name(archive.name + ".sha256")
    checksum = sidecar.read_text(encoding="ascii")
    expected = re.fullmatch(r"([0-9a-f]{64})  server-linux-x86_64\.tar\.gz\n?", checksum)
    with archive.open("rb") as source:
        actual = hashlib.file_digest(source, "sha256").hexdigest()
    if expected is None or actual != expected[1]:
        raise ValueError("Private release checksum mismatch; nothing was installed")
    with tempfile.TemporaryDirectory(prefix="bumrush-private-smoke-") as temporary:
        package = quickstart.extract_release(archive, Path(temporary) / "package")
        if subprocess.run(["getent", "passwd", "bumrush"], stdout=subprocess.DEVNULL).returncode:
            subprocess.run(["useradd", "--system", "--user-group", "--home-dir", "/var/lib/bumrush",
                            "--shell", "/usr/sbin/nologin", "bumrush"], check=True)
        quickstart.configure(package, archive, "127.0.0.1", args.login, 22)


if __name__ == "__main__":
    main()
