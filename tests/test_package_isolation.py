"""開発用venvの依存が、配布ZIPの不足を隠さない。"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from tools import package


def test_package_smoke_rejects_a_dependency_available_only_in_development(tmp_path, monkeypatch):
    project = tmp_path / "project"
    handlers = project / "src/handlers"
    handlers.mkdir(parents=True)
    (project / "src/__init__.py").write_text("")
    (handlers / "__init__.py").write_text("")
    for name in [
        "create_url",
        "redirect_url",
        "get_url_stats",
        "delete_url",
        "list_urls",
        "update_url",
    ]:
        (handlers / f"{name}.py").write_text("import moto\n")
    (handlers / "web.py").write_text("def handler(event, context): return {'statusCode': 200}\n")
    (project / "web").mkdir()
    for name in ["index.html", "app.js", "auth.js", "style.css"]:
        (project / "web" / name).write_text("")
    (project / "infrastructure").mkdir()
    shutil.copyfile(
        package.ROOT / "infrastructure/product.yaml", project / "infrastructure/product.yaml"
    )
    shutil.copyfile(package.ROOT / "uv.lock", project / "uv.lock")
    actual_run = subprocess.run

    def without_runtime_dependencies(command, **kwargs):
        if command[0] == "uv":
            if command[1] == "export":
                Path(command[command.index("--output-file") + 1]).write_text("# empty package\n")
            return subprocess.CompletedProcess(command, 0)
        return actual_run(command, **kwargs)

    monkeypatch.setattr(package, "ROOT", project)
    monkeypatch.setattr(package.subprocess, "run", without_runtime_dependencies)
    with pytest.raises(subprocess.CalledProcessError):
        package.main()
