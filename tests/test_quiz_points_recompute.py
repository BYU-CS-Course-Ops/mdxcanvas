from copy import deepcopy
from pathlib import Path

import pytest

import mdxcanvas
from mdxcanvas.deploy.canvas_deploy import deploy_to_canvas
from mdxcanvas.deploy.checksums import compute_md5
from mdxcanvas.deploy.quiz import deploy_quiz_question, deploy_quiz_question_order
from mdxcanvas.deployment_report import DeploymentReport
from mdxcanvas.resources import CanvasResource, get_key


class FakeQuestion:
    def __init__(self, quiz: "FakeQuiz", question_id: str, points: float):
        self.quiz = quiz
        self.id = question_id
        self.points = points

    def edit(self, *, question: dict):
        self.points = question["points_possible"]
        self.quiz.events.append(("question.edit", self.id))

    def delete(self):
        del self.quiz.questions[self.id]
        self.quiz.events.append(("question.delete", self.id))


class FakeQuiz:
    def __init__(self, *, published: bool, submissions: bool = False):
        self.id = "quiz"
        self.title = "Quiz"
        self.html_url = "https://canvas.example/quizzes/quiz"
        self.published = published
        self.submissions = submissions
        self.events: list[tuple[str, object]] = []
        self.questions = {
            key: FakeQuestion(self, key, points) for key, points in [("q1", 1), ("q2", 2)]
        }
        self.points_possible = 3

    def get_submissions(self) -> list[object]:
        return [object()] if self.submissions else []

    def get_question(self, question_id: str) -> FakeQuestion:
        return self.questions[question_id]

    def create_question(self, *, question: dict) -> FakeQuestion:
        question_id = question["question_name"]
        created = FakeQuestion(self, question_id, question["points_possible"])
        self.questions[question_id] = created
        self.events.append(("question.create", question_id))
        return created

    def edit(self, *, quiz: dict):
        self.events.append(("quiz.edit", dict(quiz)))
        # Model Canvas's stored total: published no-op saves do not recompute it.
        if not self.published or quiz.get("published") is False:
            self.points_possible = sum(question.points for question in self.questions.values())
        self.published = quiz.get("published", self.published)


class FakeCourse:
    def __init__(self, quiz: FakeQuiz):
        self.id = "course"
        self.quiz = quiz
        self._requester = self

    def get_quiz(self, quiz_id: str) -> FakeQuiz:
        assert quiz_id == self.quiz.id
        return self.quiz

    def request(self, method: str, path: str, **kwargs):
        assert method == "POST"
        assert path == "courses/course/quizzes/quiz/reorder"
        self.quiz.events.append(("reorder", kwargs["_kwargs"]))


def question_data(question_id: str, points: float) -> dict:
    return {
        "quiz_id": "quiz",
        "question_name": question_id,
        "question_text": question_id,
        "points_possible": points,
    }


@pytest.mark.parametrize("published", [False, True])
@pytest.mark.parametrize("submissions", [False, True])
def test_individual_question_writes_do_not_change_quiz_publication(tmp_path, published, submissions):
    quiz = FakeQuiz(published=published, submissions=submissions)
    course = FakeCourse(quiz)

    _, review = deploy_quiz_question(course, dict(question_data("q1", 4), canvas_id="q1"), tmp_path)
    deploy_quiz_question(course, question_data("q3", 5), tmp_path)

    assert quiz.events == [("question.edit", "q1"), ("question.create", "q3")]
    assert quiz.published is published
    assert review == ((quiz.title, quiz.html_url) if submissions else None)


@pytest.mark.parametrize("published", [False, True])
@pytest.mark.parametrize("submissions", [False, True])
def test_order_postprocessing_recomputes_totals_unless_submissions_exist(tmp_path, published, submissions):
    quiz = FakeQuiz(published=published, submissions=submissions)
    quiz.questions["q1"].points = 4
    order = {"quiz_id": "quiz", "order": [{"id": "q1", "type": "question"}, {"id": "q2", "type": "question"}]}

    _, review = deploy_quiz_question_order(FakeCourse(quiz), order, tmp_path)

    assert quiz.events[0] == ("reorder", [
        ("order[][id]", "q1"), ("order[][type]", "question"),
        ("order[][id]", "q2"), ("order[][type]", "question"),
    ])
    expected_saves = [] if submissions else (
        [("quiz.edit", {"published": False}), ("quiz.edit", {"published": True})]
        if published else [("quiz.edit", {"notify_of_update": False})]
    )
    assert quiz.events[1:] == expected_saves
    assert quiz.points_possible == (3 if submissions else 6)
    assert quiz.published is published
    assert review == ((quiz.title, quiz.html_url) if submissions else None)


def quiz_resources(points: dict[str, float]) -> dict[tuple[str, str], CanvasResource]:
    resources = {("quiz", "quiz"): CanvasResource(
        type="quiz", id="quiz", data={"title": "Quiz"}, content_path="quiz.md",
    )}
    for question_id, value in points.items():
        data = question_data(question_id, value)
        data["quiz_id"] = get_key("quiz", "quiz", "id")
        resources[("quiz_question", question_id)] = CanvasResource(
            type="quiz_question", id=question_id, data=data, content_path="quiz.md",
        )
    resources[("quiz_question_order", "order")] = CanvasResource(
        type="quiz_question_order", id="order", reapply_on_update=True,
        data={
            "quiz_id": get_key("quiz", "quiz", "id"),
            "order": [{"id": get_key("quiz_question", key, "id"), "type": "question"} for key in points],
        },
        content_path="quiz.md",
    )
    return resources


@pytest.mark.parametrize("published", [False, True])
@pytest.mark.parametrize("change, points, expected_total", [
    ("update", {"q1": 3, "q2": 4}, 7),
    ("add", {"q1": 1, "q2": 2, "q3": 4}, 7),
    ("delete", {"q1": 1}, 1),
    ("unchanged", {"q1": 1, "q2": 2}, 3),
])
def test_deployment_recomputes_once_after_all_question_actions(
        monkeypatch, tmp_path: Path, published: bool, change: str, points: dict[str, float], expected_total: float):
    previous = quiz_resources({"q1": 1, "q2": 2})
    entries = {}
    for (resource_type, resource_id), resource in previous.items():
        info = {"id": resource_id if resource_type == "quiz_question" else "quiz"}
        if resource_type == "quiz_question":
            info["parent"] = {"type": "quiz", "id": "quiz"}
        entries[f"{resource_type}|{resource_id}"] = {
            "checksum": compute_md5(resource["data"], tmp_path), "canvas_info": info,
        }
    entries["quiz_question_order|order"]["dependencies"] = [
        ["quiz", "quiz"], ["quiz_question", "q1"], ["quiz_question", "q2"],
    ]
    envelope = {"mdxcanvas_version": mdxcanvas.__version__, "resources": entries}

    class Store:
        def load(self) -> dict:
            return deepcopy(envelope)

        def save(self, value: dict):
            envelope.clear()
            envelope.update(deepcopy(value))

    monkeypatch.setattr("mdxcanvas.deploy.canvas_deploy.MD5Sums", lambda *_args: Store())
    quiz = FakeQuiz(published=published)

    report = deploy_to_canvas(
        FakeCourse(quiz), "UTC", quiz_resources(points), DeploymentReport(), tmp_path,
    )

    assert not report.report["deployment"]["errors"]
    assert quiz.points_possible == expected_total
    assert quiz.published is published
    if change == "unchanged":
        assert not quiz.events
        return
    operations = [event[0] for event in quiz.events]
    assert operations.count("reorder") == 1
    reorder_index = operations.index("reorder")
    assert all(operation.startswith("question.") for operation in operations[:reorder_index])
    assert operations[reorder_index + 1:] == ["quiz.edit"] * (2 if published else 1)
    if change == "update":
        assert set(quiz.events[:reorder_index]) == {("question.edit", "q1"), ("question.edit", "q2")}
    if change == "delete":
        assert quiz.events[0] == ("question.delete", "q2")
