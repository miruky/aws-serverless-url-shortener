"""Pytest結果を、起動失敗とアサーション失敗を区別して記録する。"""

import json
import os
from pathlib import Path

import pytest

_reports: list[dict[str, object]] = []


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):  # type: ignore[no-untyped-def]
    outcome = yield
    report = outcome.get_result()
    _reports.append(
        {
            "id": report.nodeid,
            "when": report.when,
            "outcome": report.outcome,
            "exception": call.excinfo.typename if call.excinfo else None,
        }
    )


def pytest_sessionfinish(session, exitstatus):  # type: ignore[no-untyped-def]
    target = os.environ.get("HARNESS_PYTEST_REPORT")
    if target:
        Path(target).write_text(json.dumps({"exitstatus": int(exitstatus), "reports": _reports}))
