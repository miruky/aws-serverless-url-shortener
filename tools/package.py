"""ロック済み依存と製品コードだけを決定的なLambda ZIPへまとめる。AWS操作はしない。"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def render_template(template: dict) -> dict:
    """API定義の変更時に新しいDeploymentを作り、Stageが古い設定を参照するのを防ぐ。"""
    resources = template["Resources"]
    shape = {
        key: value
        for key, value in resources.items()
        if value["Type"].startswith("AWS::ApiGateway::")
        and key not in {"ApiStage", "ApiDeployment"}
    }
    digest = hashlib.sha256(json.dumps(shape, sort_keys=True).encode()).hexdigest()[:16]
    logical_id = "ApiDeployment" + digest
    resources[logical_id] = resources.pop("ApiDeployment")
    resources["ApiStage"]["Properties"]["DeploymentId"] = {"Ref": logical_id}
    return template


def main() -> None:
    destination = ROOT / "dist"
    destination.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="shortener-package-") as temp:
        stage = Path(temp) / "package"
        stage.mkdir()
        requirements = Path(temp) / "requirements.txt"
        subprocess.run(
            [
                "uv",
                "export",
                "--locked",
                "--no-dev",
                "--no-emit-project",
                "--output-file",
                str(requirements),
            ],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--require-hashes",
                "--target",
                str(stage),
                "--python-version",
                "3.12",
                "--python-platform",
                "aarch64-manylinux_2_17",
                "--only-binary",
                ":all:",
                "-r",
                str(requirements),
            ],
            cwd=ROOT,
            check=True,
        )
        source_hashes = {}
        source_files = [
            p
            for p in (ROOT / "src").rglob("*.py")
            if "__pycache__" not in p.parts and p.name != "local_server.py"
        ]
        source_files += [
            ROOT / "web" / name for name in ["index.html", "app.js", "auth.js", "style.css"]
        ]
        for source in source_files:
            relative = source.relative_to(ROOT)
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            source_hashes[str(relative)] = hashlib.sha256(source.read_bytes()).hexdigest()
        archive_path = destination / "lambda-package.zip"
        with zipfile.ZipFile(
            archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for path in sorted(stage.rglob("*")):
                if (
                    not path.is_file()
                    or "__pycache__" in path.parts
                    or path.suffix == ".pyc"
                    or path.name in {"uv_cache.json", "uv_build.json", "direct_url.json"}
                ):
                    continue
                info = zipfile.ZipInfo(
                    str(path.relative_to(stage)), date_time=(1980, 1, 1, 0, 0, 0)
                )
                info.external_attr = 0o644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes(), compresslevel=9)
        # Lambda extracts the ZIP. Test the packaged tree, not editable imports from the workspace.
        smoke = (
            "import sys,importlib;from pathlib import Path;"
            "sys.path.insert(0,sys.argv[1]);import src;"
            "assert Path(src.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve()), "
            "'import outside package';"
            "[importlib.import_module('src.handlers.'+name) for name in "
            "['create_url','redirect_url','get_url_stats','delete_url','list_urls','update_url','web']];"
            "from src.handlers.web import handler;assert handler({},None)['statusCode']==200;"
            "assert not (Path(sys.argv[1])/'moto').exists();print('Packaged handlers and UI: OK')"
        )
        with tempfile.TemporaryDirectory(prefix="shortener-smoke-") as extracted:
            with zipfile.ZipFile(archive_path) as archive:
                archive.extractall(extracted)
            subprocess.run(
                [sys.executable, "-I", "-S", "-c", smoke, extracted],
                cwd=extracted,
                env={**os.environ, "AWS_EC2_METADATA_DISABLED": "true"},
                check=True,
            )
    template = render_template(yaml.safe_load((ROOT / "infrastructure/product.yaml").read_text()))
    (destination / "product.json").write_text(
        json.dumps(template, ensure_ascii=False, indent=2) + "\n"
    )
    package_hash = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    (destination / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package": archive_path.name,
                "sha256": package_hash,
                "source_hashes": dict(sorted(source_hashes.items())),
                "lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
                "template_sha256": hashlib.sha256(
                    (destination / "product.json").read_bytes()
                ).hexdigest(),
                "template_source_sha256": hashlib.sha256(
                    (ROOT / "infrastructure/product.yaml").read_bytes()
                ).hexdigest(),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"dist/lambda-package.zip: {package_hash}")


if __name__ == "__main__":
    main()
