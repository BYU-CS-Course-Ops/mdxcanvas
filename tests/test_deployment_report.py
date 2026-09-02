import json

from mdxcanvas.deployment_report import DeploymentReport


def test_url_less_navigation_is_stored_saved_and_printed_without_literal_none(tmp_path, capsys):
    output = tmp_path / "report.json"
    report = DeploymentReport(str(output))

    report.add_deployed_content("navigation", "navigation", None)
    report.save_report()
    report.print_report()

    assert report.get_deployed_content() == [("navigation", "navigation", None)]
    assert json.loads(output.read_text())["deployed_content"] == [
        ["navigation", "navigation", None]
    ]
    printed = capsys.readouterr().out
    assert "navigation" in printed
    assert "None" not in printed
