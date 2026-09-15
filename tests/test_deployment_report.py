import json
from types import SimpleNamespace

from mdxcanvas.deploy.planner import PlanningError
from mdxcanvas.deployment_report import DeploymentReport


def test_default_report_uses_nested_deployment_contract(tmp_path):
    output = tmp_path / "report.json"
    report = DeploymentReport(str(output))

    report.save_report()

    expected = {
        "processing": {"error": ""},
        "deployment": {
            "mode": "deploy",
            "cleanup": "enabled",
            "expected_changes": [],
            "changes_made": [],
            "errors": [],
        },
        "deployed_content": [],
        "content_to_review": [],
        "error": "",
    }
    assert report.report == expected
    assert json.loads(output.read_text()) == expected
    assert report.has_errors is False


def test_report_error_status_keeps_processing_and_deployment_errors_separate():
    report = DeploymentReport()
    report.report["processing"]["error"] = "ValueError: bad source"

    assert report.has_errors is True

    report.report["processing"]["error"] = ""
    report.report["deployment"]["errors"].append({
        "stage": "deployment",
        "error": "RuntimeError: Canvas failed",
        "change": "modified",
        "resource_type": "page",
        "resource_id": "welcome",
        "source": "course.md",
    })

    assert report.has_errors is True


def test_errors_retain_bounded_useful_type_and_message_diagnostics():
    report = DeploymentReport()
    report.add_error(ValueError("source document is malformed"))
    report.add_deployment_error("planning", PlanningError("missing referenced field url"))
    report.add_deployment_error("deployment", RuntimeError("Canvas rejected the update"))
    report.add_deployment_error("ledger_persistence", OSError("ledger upload was refused"))

    messages = [
        report.report["processing"]["error"],
        *(error["error"] for error in report.report["deployment"]["errors"]),
    ]
    assert messages == [
        "ValueError: source document is malformed",
        "PlanningError: missing referenced field url",
        "RuntimeError: Canvas rejected the update",
        "OSError: ledger upload was refused",
    ]
    assert report.report["error"] == "\n".join(messages)

    blocked_report = DeploymentReport()
    blocked_report.add_deployment_error(
        "deployment", RuntimeError("prerequisite action failed"),
        {"resource_type": "page", "resource_id": "child"},
        status="blocked", action="create",
    )
    blocked_report.add_deployment_error(
        "deployment", RuntimeError("Canvas rejected the parent"),
        {"resource_type": "page", "resource_id": "parent"},
        status="failed", action="create",
    )
    assert blocked_report.report["error"] == "RuntimeError: Canvas rejected the parent"
    assert blocked_report.report["deployment"]["errors"][0]["error"] == \
        "RuntimeError: prerequisite action failed"

    long_report = DeploymentReport()
    long_report.add_error(RuntimeError("line one\n" + "x" * 500))
    error = long_report.report["processing"]["error"]
    assert "\n" not in error
    assert error.startswith("RuntimeError: line one ")
    assert len(error.removeprefix("RuntimeError: ")) <= 300


def test_error_serialization_redacts_untrusted_urls_credentials_bodies_and_student_data():
    report = DeploymentReport()
    leaked = (
        "Could not deploy page; POST https://canvas.example/api?access_token=TOPSECRET; "
        "authorization=Bearer-SECRET; password=hunter2; api_key=KEY; "
        "access_token=ACCESS; api_token: API; \"client_secret\": \"CLIENT\"; "
        "\"refresh_token\": \"REFRESH\"; signed_url=https://private.example/file?signature=SIGNED; "
        "body: student_name=Alice; response=private-answer"
    )

    report.add_error(RuntimeError(leaked))
    report.add_deployment_error("deployment", RuntimeError(leaked))
    serialized = json.dumps(report.report)

    for sensitive in (
        "TOPSECRET", "Bearer-SECRET", "hunter2", "KEY", "ACCESS", "API", "CLIENT",
        "REFRESH", "SIGNED", "Alice", "private-answer", "canvas.example", "private.example",
    ):
        assert sensitive not in serialized
    assert "Could not deploy page" in serialized
    assert "RuntimeError" in serialized
    assert "[redacted" in serialized


def all_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from all_keys(child)


def test_public_report_shape_has_legacy_compatibility_without_private_fields():
    report = DeploymentReport()

    keys = set(all_keys(report.report))
    assert keys == {
        "processing",
        "error",
        "deployment",
        "mode",
        "cleanup",
        "expected_changes",
        "changes_made",
        "content_to_review",
        "errors",
        "deployed_content",
    }
    assert keys.isdisjoint({
        "review_required",
        "planned_changes",
        "checksum",
        "predecessors",
        "scheduler_key",
    })


def test_review_metadata_is_retained_per_change_and_summary_is_ordered_and_deduplicated(tmp_path):
    output = tmp_path / "review-report.json"
    report = DeploymentReport(str(output))
    reviews = [
        ("page", "one", SimpleNamespace(name="First page", url="https://safe/first")),
        ("page", "duplicate", SimpleNamespace(name="First page", url="https://safe/first")),
        ("quiz", "null-url", SimpleNamespace(name="Submitted quiz", url=None)),
        ("quiz", "same-target-different-type", SimpleNamespace(name="First page", url="https://safe/first")),
    ]

    for resource_type, resource_id, review in reviews:
        report.add_change_made(
            {"change": "new", "resource_type": resource_type, "resource_id": resource_id},
            "created",
            review=review,
        )

    changes = report.report["deployment"]["changes_made"]
    assert [change["review"] for change in changes] == [
        {"name": "First page", "url": "https://safe/first"},
        {"name": "First page", "url": "https://safe/first"},
        {"name": "Submitted quiz", "url": None},
        {"name": "First page", "url": "https://safe/first"},
    ]
    assert report.report["content_to_review"] == [
        ["page", "First page", "https://safe/first"],
        ["quiz", "Submitted quiz", None],
        ["quiz", "First page", "https://safe/first"],
    ]
    assert "review_required" not in set(all_keys(report.report))
    report.save_report()
    assert json.loads(output.read_text()) == report.report


def test_absent_review_adds_no_signal_or_summary_entry():
    report = DeploymentReport()

    report.add_change_made(
        {"change": "modified", "resource_type": "page", "resource_id": "ordinary"},
        "updated",
    )

    change = report.report["deployment"]["changes_made"][0]
    assert "review" not in change
    assert report.report["content_to_review"] == []
    assert "review_required" not in set(all_keys(report.report))


def test_human_report_groups_successes_by_link_with_course_fallback(capsys):
    report = DeploymentReport()
    report.configure(
        dryrun=False,
        no_cleanup=False,
        course_url="https://canvas.example/courses/42",
    )
    report.add_change_made(
        {"change": "new", "resource_type": "quiz", "resource_id": "quiz"},
        "created",
        url="https://canvas.example/courses/42/quizzes/7",
    )
    report.add_change_made(
        {"change": "new", "resource_type": "quiz_question", "resource_id": "q1"},
        "created",
        url="https://canvas.example/courses/42/quizzes/7",
    )
    report.add_change_made(
        {"change": "modified", "resource_type": "navigation", "resource_id": "tabs"},
        "updated",
    )

    report.print_report()

    output = capsys.readouterr().out
    quiz_url = "https://canvas.example/courses/42/quizzes/7"
    course_url = "https://canvas.example/courses/42"
    assert output.count(quiz_url) == 1
    assert "created quiz quiz, created quiz_question q1" in output
    assert output.count(course_url) == 2  # Once alone and once as part of the quiz URL.
    assert "updated navigation tabs: https://canvas.example/courses/42" in output
    assert "url" not in report.report["deployment"]["changes_made"][2]
    assert report.report["deployed_content"] == [
        ["quiz", "quiz", quiz_url],
        ["quiz_question", "q1", quiz_url],
        ["navigation", "tabs", None],
    ]


def test_human_report_shows_contextual_failures_and_one_blocked_count(capsys):
    report = DeploymentReport()
    change = {
        "change": "modified",
        "resource_type": "quiz_question",
        "resource_id": "lab0a|question",
    }
    report.add_deployment_error(
        "deployment", KeyError("canvas_id"), change, "course.md",
        status="failed", action="update",
    )
    for resource_id in ("order", "module-item"):
        report.add_deployment_error(
            "deployment", RuntimeError("prerequisite failed"),
            {"change": "new", "resource_type": "resource", "resource_id": resource_id},
            status="blocked", action="create",
        )

    report.print_report()

    captured = capsys.readouterr()
    assert "update quiz_question lab0a|question (course.md): KeyError: 'canvas_id'" in captured.err
    assert "prerequisite failed" not in captured.err
    assert captured.err.count("2 resources not deployed") == 1
    errors = report.report["deployment"]["errors"]
    assert [error["status"] for error in errors] == ["failed", "blocked", "blocked"]


def test_human_report_renders_nested_review_summary_and_omits_empty_section(capsys):
    empty = DeploymentReport()
    empty.print_report()
    assert "Content to Review" not in capsys.readouterr().out

    report = DeploymentReport()
    for resource_type, resource_id, review in (
        ("page", "one", SimpleNamespace(name="First page", url="https://safe/first")),
        ("page", "duplicate", SimpleNamespace(name="First page", url="https://safe/first")),
        ("quiz", "submitted", SimpleNamespace(name="Submitted quiz", url=None)),
    ):
        report.add_change_made(
            {"change": "new", "resource_type": resource_type, "resource_id": resource_id},
            "created",
            review=review,
        )

    report.print_report()
    output = capsys.readouterr().out
    assert "Content to Review" in output
    assert output.count("page: First page (https://safe/first)") == 1
    assert "quiz: Submitted quiz" in output
    assert "Submitted quiz (None)" not in output
    assert output.index("page: First page") < output.index("quiz: Submitted quiz")
