from pathlib import Path

from mdxcanvas.deploy.canvas_deploy import deploy_to_canvas
from mdxcanvas.deploy.checksums import compute_md5
from mdxcanvas.deployment_report import DeploymentReport


class FakeMD5Sums:
    current = None

    def __init__(self, *_args):
        self.data = {
            "mdxcanvas_version": "0.8.0",
            "resources": dict(type(self).current or {}),
        }
        type(self).last = self

    def load(self):
        return self.data

    def save(self, envelope):
        self.data = envelope


class FakeTab:
    def __init__(self, tab_id, label, position, hidden=False):
        self.id = tab_id
        self.label = label
        self.position = position
        self.hidden = hidden
        self.updates = []

    def update(self, **changes):
        self.updates.append(changes)
        return self


class FakeCourse:
    id = 9

    def __init__(self):
        self.get_tabs_calls = 0
        self.tabs = [
            FakeTab("home", "Home", 1),
            FakeTab("assignments", "Assignments", 2),
            FakeTab("settings", "Settings", 3),
        ]

    def get_tabs(self):
        self.get_tabs_calls += 1
        return self.tabs


def navigation_resource(names):
    return {
        ("navigation", "navigation"): {
            "type": "navigation",
            "id": "navigation",
            "data": {"tabs": names},
            "content_path": "course.xml",
        }
    }


def configure_ledger(monkeypatch, entries):
    FakeMD5Sums.current = {"|".join(key): value for key, value in entries.items()}
    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.MD5Sums", FakeMD5Sums)


def test_unchanged_navigation_checksum_performs_no_canvas_tab_api_work(monkeypatch, tmp_path):
    resources = navigation_resource(["Assignments"])
    checksum = compute_md5(resources[("navigation", "navigation")]["data"], tmp_path)
    configure_ledger(
        monkeypatch,
        {
            ("navigation", "navigation"): {
                "checksum": checksum,
                "canvas_info": {"id": "9"},
            }
        },
    )
    course = FakeCourse()

    deploy_to_canvas(
        course,
        "America/Denver",
        resources,
        DeploymentReport(),
        tmp_path,
    )

    assert course.get_tabs_calls == 0
    assert all(tab.updates == [] for tab in course.tabs)


def test_changed_navigation_records_one_checksum_and_one_url_less_report_entry(monkeypatch, tmp_path):
    configure_ledger(monkeypatch, {})
    course = FakeCourse()
    resources = navigation_resource(["Assignments"])
    report = DeploymentReport()

    deploy_to_canvas(course, "America/Denver", resources, report, tmp_path)

    assert course.get_tabs_calls == 1
    assert list(FakeMD5Sums.last.data["resources"]) == ["navigation|navigation"]
    assert FakeMD5Sums.last.data["resources"]["navigation|navigation"]["canvas_info"] == {"id": "9"}
    assert report.report["deployment"]["changes_made"] == [{
        "change": "new",
        "resource_type": "navigation",
        "resource_id": "navigation",
        "outcome": "created",
    }]
    assert report.report["deployment"]["content_to_review"] == []
