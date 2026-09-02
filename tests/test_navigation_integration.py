from pathlib import Path

from mdxcanvas.deploy.canvas_deploy import deploy_to_canvas
from mdxcanvas.deploy.checksums import compute_md5
from mdxcanvas.deployment_report import DeploymentReport


class FakeMD5Sums:
    current = None

    def __init__(self, *_args):
        self.data = dict(type(self).current or {})
        type(self).last = self

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def items(self):
        return self.data.items()

    def get(self, item, default=None):
        return self.data.get(item, default)

    def get_checksum(self, item):
        return self.get(item, {}).get("checksum")

    def get_canvas_info(self, item):
        return self.get(item, {}).get("canvas_info")

    def has_canvas_info(self, item):
        return self.get_canvas_info(item) is not None

    def __setitem__(self, item, value):
        self.data[item] = value


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
    FakeMD5Sums.current = entries
    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.MD5Sums", FakeMD5Sums)
    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.migrate", lambda *_args: None)


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
    assert list(FakeMD5Sums.last.data) == [("navigation", "navigation")]
    assert FakeMD5Sums.last.data[("navigation", "navigation")]["canvas_info"] == {"id": "9"}
    assert report.get_deployed_content() == [("navigation", "navigation", None)]
