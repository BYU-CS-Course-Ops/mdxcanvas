import inspect
import subprocess
import sys
from pathlib import Path

import pytest

from mdxcanvas.deployment_report import DeploymentReport
from mdxcanvas.main import entry, main


def run_help():
    return subprocess.run(
        [sys.executable, "-m", "mdxcanvas.main", "--help"],
        capture_output=True,
        text=True,
    )


def test_callable_main_uses_no_cleanup_without_cleanup_alias():
    parameters = inspect.signature(main).parameters

    assert parameters["no_cleanup"].default is False
    assert "cleanup" not in parameters


def test_deployment_cli_exposes_new_cleanup_and_both_dry_run_spellings():
    result = run_help()

    assert result.returncode == 0
    assert "--no-cleanup" in result.stdout
    assert "--dryrun" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--cleanup" not in result.stdout


def test_help_does_not_require_runtime_canvas_or_rendering_dependencies():
    result = subprocess.run(
        [sys.executable, "-S", "-m", "mdxcanvas.main", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--no-cleanup" in result.stdout


def test_removed_cleanup_flag_is_rejected():
    result = subprocess.run(
        [sys.executable, "-m", "mdxcanvas.main", "course.md", "--cleanup"],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "unrecognized arguments: --cleanup" in result.stderr


def test_newer_ledger_planning_error_causes_cli_exit_one(monkeypatch):
    report = DeploymentReport()
    report.add_deployment_error(
        "planning",
        ValueError(
            "Ledger version 0.9.0 is newer than running MDXCanvas 0.8.7; "
            "upgrade MDXCanvas to at least 0.9.0."
        ),
    )
    monkeypatch.setattr("mdxcanvas.main.main", lambda **_kwargs: report)
    monkeypatch.setattr(sys, "argv", ["mdxcanvas", "course.md"])
    monkeypatch.setenv("CANVAS_API_TOKEN", "test-token")

    with pytest.raises(SystemExit) as raised:
        entry()

    assert raised.value.code == 1


def test_skilldir_prints_packaged_skills_directory():
    result = subprocess.run(
        [sys.executable, "-m", "mdxcanvas.cli", "skilldir"],
        check=True,
        capture_output=True,
        text=True,
    )

    skill_directory = Path(result.stdout.strip())
    assert skill_directory == Path(__file__).parents[1] / "mdxcanvas" / "skills"
    assert skill_directory.is_dir()
