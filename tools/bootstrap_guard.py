"""公式リリースのSHA-256を確認し、プロジェクト内にGuardを導入する。"""

from __future__ import annotations

import hashlib
import io
import json
import platform
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    config = json.loads((ROOT / "tools/toolchain.json").read_text())["guard"]
    installed = shutil.which("cfn-guard")
    if installed:
        version = subprocess.check_output([installed, "--version"], text=True).strip()
        if version == f"cfn-guard {config['version']}":
            print(version)
            return
    key = f"{platform.system()}-{platform.machine()}"
    if key not in config["assets"]:
        raise SystemExit(
            "Install cfn-guard 3.2.1 for this platform; "
            "automatic setup supports Linux x86_64 and macOS arm64."
        )
    asset = config["assets"][key]
    endpoint = f"https://github.com/aws-cloudformation/cloudformation-guard/releases/download/{config['version']}/{asset['file']}"
    with urllib.request.urlopen(endpoint, timeout=60) as response:
        archive = response.read(32 * 1024 * 1024)
    if hashlib.sha256(archive).hexdigest() != asset["sha256"]:
        raise SystemExit("Guard archive checksum mismatch")
    target = ROOT / ".harness/bin/cfn-guard"
    target.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as contents:
        matches = [
            m for m in contents.getmembers() if m.isfile() and Path(m.name).name == "cfn-guard"
        ]
        if len(matches) != 1:
            raise SystemExit("Unexpected Guard archive layout")
        payload = contents.extractfile(matches[0])
        if payload is None:
            raise SystemExit("Missing Guard executable")
        target.write_bytes(payload.read())
    target.chmod(0o755)
    subprocess.run([str(target), "--version"], check=True)


if __name__ == "__main__":
    main()
