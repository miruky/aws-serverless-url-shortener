"""製品の信頼境界と配布契約。実AWSに対する検査ではない。"""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_all_management_methods_require_the_scoped_authorizer():
    resources = yaml.safe_load((ROOT / "infrastructure/product.yaml").read_text())["Resources"]
    checked = 0
    for value in resources.values():
        if value["Type"] != "AWS::ApiGateway::Method":
            continue
        method = value["Properties"]
        if method["ResourceId"]["Ref"] in {"UrlsResource", "UrlResource"}:
            checked += 1
            assert method["AuthorizationType"] == "COGNITO_USER_POOLS"
            assert method["AuthorizerId"] == {"Ref": "ManagementAuthorizer"}
    assert checked == 5
    assert resources["ManagementAuthorizer"]["Properties"]["IdentityValidationExpression"] == {
        "Fn::Sub": "^${UserPoolClient}$"
    }
    assert resources["RedirectMethod"]["Properties"]["AuthorizationType"] == "NONE"
    assert resources["HeadMethod"]["Properties"]["AuthorizationType"] == "NONE"


def test_each_function_has_only_its_domain_permissions():
    resources = yaml.safe_load((ROOT / "infrastructure/product.yaml").read_text())["Resources"]
    expected = {
        "CreateRole": {"dynamodb:PutItem"},
        "ManageRole": {"dynamodb:GetItem", "dynamodb:Scan", "dynamodb:UpdateItem"},
        "RedirectRole": {"dynamodb:GetItem", "dynamodb:UpdateItem"},
        "WebRole": set(),
    }
    for role, actions in expected.items():
        statements = resources[role]["Properties"]["Policies"][0]["PolicyDocument"]["Statement"]
        actual = {
            action
            for statement in statements
            for action in statement["Action"]
            if action.startswith("dynamodb:")
        }
        assert actual == actions
        for statement in statements:
            assert statement["Resource"] != "*"


def test_identity_and_link_data_are_not_silently_destroyed():
    resources = yaml.safe_load((ROOT / "infrastructure/product.yaml").read_text())["Resources"]
    for key in ["UrlsTable", "UserPool"]:
        assert resources[key]["DeletionPolicy"] == "Retain"
        assert resources[key]["UpdateReplacePolicy"] == "Retain"
    assert "TimeToLiveSpecification" not in resources["UrlsTable"]["Properties"]
    assert resources["UserPool"]["Properties"]["MfaConfiguration"] == "ON"
    assert resources["UserPool"]["Properties"]["AdminCreateUserConfig"]["AllowAdminCreateUserOnly"]
    client = resources["UserPoolClient"]["Properties"]
    assert client["GenerateSecret"] is False
    assert client["AllowedOAuthFlows"] == ["code"]


def test_api_shape_changes_force_a_new_deployment():
    import copy

    from tools.package import render_template

    template = yaml.safe_load((ROOT / "infrastructure/product.yaml").read_text())
    original = render_template(copy.deepcopy(template))
    same = render_template(copy.deepcopy(template))
    assert original == same
    template["Resources"]["CreateMethod"]["Properties"]["AuthorizationType"] = "NONE"
    changed = render_template(template)
    assert (
        original["Resources"]["ApiStage"]["Properties"]["DeploymentId"]
        != changed["Resources"]["ApiStage"]["Properties"]["DeploymentId"]
    )
