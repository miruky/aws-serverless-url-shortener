"""CognitoのパスワードポリシーをIAMのポリシー配列と混同しない。"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_complete_name_inventory_accepts_cognito_password_policies(tmp_path):
    project = tmp_path / "fixture"
    for directory in ["src", "web", "infrastructure"]:
        shutil.copytree(
            ROOT / directory,
            project / directory,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    (project / "tools/vendor").mkdir(parents=True)
    for filename in [
        "tools/prepare_deployment.py",
        "tools/vendor/aws_resource_names.py",
        "uv.lock",
    ]:
        shutil.copyfile(ROOT / filename, project / filename)
    # This fixture checks parameter inventory, not the executable package (tested separately).
    destination = project / "dist"
    destination.mkdir()
    (destination / "lambda-package.zip").write_bytes(b"inventory-fixture")
    (destination / "product.json").write_text("{}")
    sources = [p for p in (project / "src").rglob("*.py") if p.name != "local_server.py"]
    sources += [
        project / "web" / name for name in ["index.html", "app.js", "auth.js", "style.css"]
    ]

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    manifest = {
        "source_hashes": {str(p.relative_to(project)): digest(p) for p in sources},
        "sha256": digest(destination / "lambda-package.zip"),
        "lock_sha256": digest(project / "uv.lock"),
        "template_sha256": digest(destination / "product.json"),
        "template_source_sha256": digest(project / "infrastructure/product.yaml"),
    }
    (destination / "manifest.json").write_text(json.dumps(manifest))
    result = subprocess.run(
        [sys.executable, "tools/prepare_deployment.py", "--region", "ap-northeast-1"],
        cwd=project,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr.replace(str(project), "<fixture>")
    ledger = json.loads((project / ".harness/deployment/ledger.json").read_text())
    names = [item["resource_name"] for item in ledger["resources"]]
    assert len(names) == len(set(names)) == 36
    assert all(item["generated_by"] == "aws-resource-name-v1" for item in ledger["resources"])
    assert any(item["logical_label"] == "UserPoolName" for item in ledger["resources"])
    assert any(item["logical_label"] == "CreatePolicyName" for item in ledger["resources"])
