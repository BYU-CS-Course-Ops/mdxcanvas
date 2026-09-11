import copy

from mdxcanvas.deploy.canvas_deploy import deploy_to_canvas
from mdxcanvas.deployment_report import DeploymentReport
from mdxcanvas.resources import CanvasResource


class LedgerReadOnlyCourse:
    def get_files(self):
        return []

    def __getattr__(self, name):
        raise AssertionError(f"dry-run performed resource-specific Canvas access: {name}")


def test_dry_run_is_read_only_and_reports_only_safe_planned_transitions(tmp_path):
    resource = CanvasResource(
        type="assignment",
        id="new-assignment",
        data={"name": "New", "description": "secret body"},
        content_path="course.md",
    )
    resources = {("assignment", "new-assignment"): resource}
    original = copy.deepcopy(resources)
    report = DeploymentReport()

    deploy_to_canvas(
        course=LedgerReadOnlyCourse(),
        timezone="America/Denver",
        resources=resources,
        report=report,
        deploy_root=tmp_path,
        dryrun=True,
    )

    assert resources == original
    assert report.report == {
        "processing": {"error": ""},
        "deployment": {
            "mode": "dry_run",
            "cleanup": "enabled",
            "expected_changes": [{
                "change": "new",
                "resource_type": "assignment",
                "resource_id": "new-assignment",
            }],
            "changes_made": [],
            "content_to_review": [],
            "errors": [],
        },
    }
    serialized = repr(report.report)
    assert "secret body" not in serialized
    assert "checksum" not in serialized


def test_no_cleanup_suppresses_all_stale_transitions_in_dry_run(tmp_path, monkeypatch):
    # The ledger transport itself is the only Canvas read dry-run may perform.
    ledger = {
        "mdxcanvas_version": "0.8.0",
        "resources": {
            "page|old-page": {
                "checksum": "old",
                "canvas_info": {"id": "10"},
            },
            "navigation|navigation": {
                "checksum": "old",
                "canvas_info": {"id": "course"},
            },
        },
    }

    class LedgerFile:
        url = "https://safe.invalid/ledger"

    course = LedgerReadOnlyCourse()
    course.get_files = lambda: [type("File", (), {"display_name": "_md5sums.json", "url": LedgerFile.url})()]
    monkeypatch.setattr(
        "mdxcanvas.deploy.checksums.requests.get",
        lambda _url: type("Response", (), {"text": __import__("json").dumps(ledger)})(),
    )
    report = DeploymentReport()

    deploy_to_canvas(
        course=course,
        timezone="America/Denver",
        resources={},
        report=report,
        deploy_root=tmp_path,
        dryrun=True,
        no_cleanup=True,
    )

    assert report.report["deployment"]["cleanup"] == "disabled"
    assert report.report["deployment"]["expected_changes"] == []
    assert report.report["deployment"]["changes_made"] == []
