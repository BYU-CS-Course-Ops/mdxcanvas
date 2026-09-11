import json

from mdxcanvas.deploy.canvas_deploy import deploy_to_canvas
from mdxcanvas.deployment_report import DeploymentReport
from mdxcanvas.resources import CanvasResource


class ReadLedgerOnlyCourse:
    def __init__(self, envelope):
        self.envelope = envelope

    def get_files(self):
        response = type("LedgerFile", (), {
            "display_name": "_md5sums.json",
            "url": "https://safe.invalid/_md5sums.json",
        })
        return [response()]

    def __getattr__(self, name):
        raise AssertionError(f"unexpected resource-specific Canvas access: {name}")


def install_ledger(monkeypatch, envelope):
    monkeypatch.setattr(
        "mdxcanvas.deploy.checksums.requests.get",
        lambda _url: type("Response", (), {"text": json.dumps(envelope)})(),
    )
    return ReadLedgerOnlyCourse(envelope)


def envelope(resources):
    return {"mdxcanvas_version": "0.8.0", "resources": resources}


def tracked(canvas_id="1", *, parent=None):
    canvas_info = {"id": canvas_id}
    if parent is not None:
        canvas_info["parent"] = parent
    return {"checksum": "old", "canvas_info": canvas_info}


def test_default_cleanup_plans_delete_and_untrack_for_all_stale_resources(monkeypatch, tmp_path):
    course = install_ledger(monkeypatch, envelope({
        "page|stale-page": tracked("10"),
        "course_settings|": tracked("course"),
    }))
    report = DeploymentReport()

    deploy_to_canvas(course, "UTC", {}, report, tmp_path, dryrun=True)

    assert report.report["deployment"]["cleanup"] == "enabled"
    assert report.report["deployment"]["expected_changes"] == [
        {"change": "stale", "resource_type": "course_settings", "resource_id": ""},
        {"change": "stale", "resource_type": "page", "resource_id": "stale-page"},
    ]


def test_no_cleanup_suppresses_delete_and_untrack_stale_resources(monkeypatch, tmp_path):
    course = install_ledger(monkeypatch, envelope({
        "page|stale-page": tracked("10"),
        "course_settings|": tracked("course"),
    }))
    report = DeploymentReport()

    deploy_to_canvas(
        course, "UTC", {}, report, tmp_path, dryrun=True, no_cleanup=True
    )

    assert report.report["deployment"]["cleanup"] == "disabled"
    assert report.report["deployment"]["expected_changes"] == []


def test_ledger_only_explicit_reference_is_retained_and_not_stale(monkeypatch, tmp_path):
    course = install_ledger(monkeypatch, envelope({
        "page|retained": tracked("10"),
        "page|actually-stale": tracked("11"),
    }))
    referring = CanvasResource(
        type="assignment",
        id="referrer",
        data={"name": "Referrer", "description": "__@@page||retained||id@@__"},
        content_path="course.md",
    )
    report = DeploymentReport()

    deploy_to_canvas(
        course,
        "UTC",
        {("assignment", "referrer"): referring},
        report,
        tmp_path,
        dryrun=True,
    )

    assert report.report["deployment"]["expected_changes"] == [
        {"change": "new", "resource_type": "assignment", "resource_id": "referrer"},
        {"change": "stale", "resource_type": "page", "resource_id": "actually-stale"},
    ]


def test_missing_ledger_only_reference_field_is_contextual_planning_error(monkeypatch, tmp_path):
    course = install_ledger(monkeypatch, envelope({
        "page|retained": tracked("10"),
    }))
    referring = CanvasResource(
        type="assignment",
        id="referrer",
        data={"name": "Referrer", "description": "__@@page||retained||url@@__"},
        content_path="source/course.md",
    )
    report = DeploymentReport()

    deploy_to_canvas(
        course,
        "UTC",
        {("assignment", "referrer"): referring},
        report,
        tmp_path,
        dryrun=True,
    )

    assert report.report["processing"]["error"] == ""
    assert report.report["deployment"]["changes_made"] == []
    [error] = report.report["deployment"]["errors"]
    assert error["stage"] == "planning"
    assert error["resource_type"] == "assignment"
    assert error["resource_id"] == "referrer"
    assert error["source"] == "source/course.md"
    assert "url" in error["error"]
