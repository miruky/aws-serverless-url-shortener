"""現在のテストをGitの修正前ソースに対して隔離実行する。作業ツリーは変更しない。"""

from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


def main() -> int:
    revision, *tests = sys.argv[1:]
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("Baseline must be a full Git commit SHA")
    root = Path(__file__).resolve().parents[1]
    object_type = subprocess.check_output(["git", "cat-file", "-t", revision], cwd=root, text=True)
    if object_type.strip() != "commit":
        raise ValueError("Baseline must identify a commit, not a tree or blob")
    archive = subprocess.run(
        ["git", "archive", "--format=tar", revision], cwd=root, capture_output=True, check=True
    ).stdout
    with tempfile.TemporaryDirectory(prefix="shortener-baseline-") as temp:
        target = Path(temp)
        with tarfile.open(fileobj=io.BytesIO(archive)) as contents:
            contents.extractall(target, filter="data")
        shutil.copytree(
            root / "tests",
            target / "tests",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        (target / "tools").mkdir(exist_ok=True)
        shutil.copy2(root / "tools/pytest_evidence.py", target / "tools/pytest_evidence.py")
        env = {**os.environ, "PYTHONPATH": temp}
        bootstrap = (
            "from pathlib import Path; import src, pytest, sys; "
            "assert Path(src.__file__).resolve().is_relative_to(Path.cwd()), "
            "'Baseline source was not imported'; raise SystemExit(pytest.main(sys.argv[1:]))"
        )
        result = subprocess.run(
            [sys.executable, "-c", bootstrap, "-p", "tools.pytest_evidence", "-q", *tests],
            cwd=target,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        print((result.stdout + result.stderr).replace(temp, "<baseline>"), end="")
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
