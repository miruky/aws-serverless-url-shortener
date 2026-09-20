"""新規スタック用の名前とパラメータを生成する。AWSへは一切接続しない。"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", required=True)
    parser.add_argument(
        "--generator", type=Path, default=ROOT / "tools/vendor/aws_resource_names.py"
    )
    args = parser.parse_args()
    target = ROOT / ".harness/deployment"
    if target.exists():
        raise SystemExit(
            "Deployment plan already exists; reuse it. "
            "Archive it before preparing a different stack."
        )
    template = yaml.safe_load((ROOT / "infrastructure/product.yaml").read_text())
    manifest = json.loads((ROOT / "dist/manifest.json").read_text())
    sources = [
        p
        for p in (ROOT / "src").rglob("*.py")
        if "__pycache__" not in p.parts and p.name != "local_server.py"
    ]
    sources += [ROOT / "web" / name for name in ["index.html", "app.js", "auth.js", "style.css"]]
    current = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources
    }
    if current != manifest["source_hashes"]:
        raise SystemExit(
            "Source changed after packaging. Run ./dev check before preparing deployment."
        )
    for path, field in [
        ("dist/lambda-package.zip", "sha256"),
        ("uv.lock", "lock_sha256"),
        ("dist/product.json", "template_sha256"),
        ("infrastructure/product.yaml", "template_source_sha256"),
    ]:
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != manifest.get(field):
            raise SystemExit(f"Stale package input: {path}. Run ./dev check again.")
    keys = [p for p in template["Parameters"] if p.endswith("Name")]
    artifacts = yaml.safe_load((ROOT / "infrastructure/artifacts.yaml").read_text())
    artifact_keys = ["ArtifactBucketName"]
    extras = [
        "ProductStackName",
        "ArtifactsStackName",
        "ProductChangeSetName",
        "ArtifactsChangeSetName",
        "AdministratorName",
    ]
    generated = json.loads(
        subprocess.check_output(
            [
                sys.executable,
                str(args.generator),
                "generate",
                "--count",
                str(len(keys) + len(artifact_keys) + len(extras)),
                "--json",
            ],
            text=True,
        )
    )
    names = {
        key: entry["name"]
        for key, entry in zip(keys + artifact_keys + extras, generated["names"], strict=True)
    }
    inventory = []
    exemptions = []
    for logical, resource in {**template["Resources"], **artifacts["Resources"]}.items():
        properties = resource.get("Properties", {})
        found = []
        for field, value in properties.items():
            if (
                isinstance(value, dict)
                and value.get("Ref") in names
                and field
                in {
                    "BucketName",
                    "TableName",
                    "Name",
                    "StageName",
                    "RoleName",
                    "FunctionName",
                    "LogGroupName",
                    "UserPoolName",
                    "ClientName",
                    "Domain",
                    "AlarmName",
                }
            ):
                found.append((field, value["Ref"]))
        policies = properties.get("Policies", []) if resource["Type"] == "AWS::IAM::Role" else []
        for i, policy in enumerate(policies):
            value = policy.get("PolicyName", {})
            if isinstance(value, dict) and value.get("Ref") in names:
                found.append((f"Policies[{i}].PolicyName", value["Ref"]))
        for field, key in found:
            inventory.append((key, resource["Type"], f"{logical}.{field}"))
        if not found:
            exemptions.append(
                {
                    "logical_label": logical,
                    "service": resource["Type"],
                    "region": args.region,
                    "identifier_kind": "CloudFormation-assigned identifier; no Name property",
                    "exemption_reason": "no-supported-user-name-field",
                }
            )
    inventory += [
        (
            key,
            "cloudformation"
            if "Stack" in key or "ChangeSet" in key
            else "s3"
            if key == "ArtifactBucketName"
            else "cognito-idp",
            key,
        )
        for key in extras
    ]
    if set(key for key, _, _ in inventory) != set(names):
        raise SystemExit("Name inventory is incomplete")
    records = [
        {
            "logical_label": key,
            "service": service,
            "region": args.region,
            "resource_name": names[key],
            "name_core": names[key],
            "generated_by": "aws-resource-name-v1",
            "create_target": path,
            "cleanup_target": "Not created; retained data requires a cleanup decision.",
            "absence_check": "Prepared input only; no AWS call. Not live absence evidence.",
            "final_state": "not-created-and-absent",
        }
        for key, service, path in inventory
    ]
    ledger = {
        "schema_version": 1,
        "inventory_complete": "PASS",
        "name_field_inventory_complete": "PASS",
        "resources": records,
        "aws_generated_identifiers": exemptions,
    }
    parameters = [{"ParameterKey": key, "ParameterValue": names[key]} for key in keys]
    parameters += [
        {"ParameterKey": "LambdaS3Bucket", "ParameterValue": names["ArtifactBucketName"]},
        {"ParameterKey": "LambdaS3Key", "ParameterValue": f"packages/{manifest['sha256']}.zip"},
    ]
    target.mkdir(parents=True)
    for file, payload in {
        "names.json": names,
        "ledger.json": ledger,
        "parameters.json": parameters,
        "artifacts-parameters.json": [
            {"ParameterKey": "ArtifactBucketName", "ParameterValue": names["ArtifactBucketName"]}
        ],
        "plan.json": {
            "region": args.region,
            "package_sha256": manifest["sha256"],
            "status": "prepared-not-deployed",
        },
    }.items():
        (target / file).write_text(json.dumps(payload, indent=2) + "\n")
    subprocess.run(
        [
            sys.executable,
            str(args.generator),
            "audit-ledger",
            str(target / "ledger.json"),
            "--final",
        ],
        check=True,
    )
    print("Prepared .harness/deployment. No AWS requests were sent.")


if __name__ == "__main__":
    main()
