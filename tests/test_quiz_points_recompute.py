"""A quiz's point total is recomputed once, after all of its questions are written.

Canvas stores points_possible and recomputes it only on a save. On a published
quiz a save that changes nothing is ignored, so only unpublishing and
republishing recomputes. Questions deploy concurrently, so the recompute is
the job of the question-order step. A changed question is a replacement, edited
in place, so the planner reapplies the order step after it.
"""
from mdxcanvas.deploy.actions import Create, Update
from mdxcanvas.deploy.checksums import compute_md5
from mdxcanvas.deploy.handlers import build_builtin_handlers
from mdxcanvas.deploy.planner import plan_deployment
from mdxcanvas.deploy.quiz import deploy_quiz_question, deploy_quiz_question_order


def resource(resource_type, resource_id, data):
    return {"type": resource_type, "id": resource_id, "data": data, "content_path": "hw.md"}


def quiz_with_two_questions():
    return {
        ("quiz", "hw"): resource("quiz", "hw", {"title": "HW"}),
        ("quiz_question", "hw|q1"): resource("quiz_question", "hw|q1", {
            "quiz_id": "__@@quiz||hw||id@@__", "question_text": "one", "points_possible": 1,
        }),
        ("quiz_question", "hw|q2"): resource("quiz_question", "hw|q2", {
            "quiz_id": "__@@quiz||hw||id@@__", "question_text": "two", "points_possible": 2,
        }),
        ("quiz_question_order", "hw|order"): resource("quiz_question_order", "hw|order", {
            "quiz_id": "__@@quiz||hw||id@@__",
            "order": [
                {"id": "__@@quiz_question||hw|q1||id@@__", "type": "question"},
                {"id": "__@@quiz_question||hw|q2||id@@__", "type": "question"},
            ],
        }),
    }


def tracked(resources, tmp_path):
    return {
        "mdxcanvas_version": "0.8.14",
        "resources": {
            f"{rtype}|{rid}": {
                "checksum": compute_md5(value["data"], tmp_path),
                "canvas_info": {"id": f"canvas-{rid}"},
            }
            for (rtype, rid), value in resources.items()
        },
    }


def node(plan, resource_type, resource_id):
    return next(n for n in plan.nodes if n.key == f"action:{resource_type}|{resource_id}")


def test_a_changed_question_replans_the_order_step_after_it(tmp_path):
    resources = quiz_with_two_questions()
    ledger = tracked(resources, tmp_path)
    ledger["resources"]["quiz_question|hw|q1"]["checksum"] = "old"

    plan = plan_deployment(resources, ledger, build_builtin_handlers(), tmp_path)

    assert [c.public() for c in plan.expected_changes] == [
        {"change": "modified", "resource_type": "quiz_question", "resource_id": "hw|q1"},
        {"change": "modified", "resource_type": "quiz_question_order", "resource_id": "hw|order"},
    ]
    order = node(plan, "quiz_question_order", "hw|order")
    assert isinstance(order.action, Update)
    assert order.predecessors == {"action:quiz_question|hw|q1"}


def test_a_changed_question_is_rewritten_in_place(tmp_path):
    resources = quiz_with_two_questions()
    ledger = tracked(resources, tmp_path)
    ledger["resources"]["quiz_question|hw|q1"]["checksum"] = "old"

    plan = plan_deployment(resources, ledger, build_builtin_handlers(), tmp_path)

    question = node(plan, "quiz_question", "hw|q1").action
    assert isinstance(question, Create)
    assert question.resource["data"]["canvas_id"] == "canvas-hw|q1"
    assert "canvas_id" not in resources[("quiz_question", "hw|q1")]["data"]


def test_a_new_question_has_no_canvas_id(tmp_path):
    resources = quiz_with_two_questions()
    ledger = tracked(resources, tmp_path)
    del ledger["resources"]["quiz_question|hw|q1"]

    plan = plan_deployment(resources, ledger, build_builtin_handlers(), tmp_path)

    assert "canvas_id" not in node(plan, "quiz_question", "hw|q1").action.resource["data"]


def test_an_unchanged_quiz_plans_nothing(tmp_path):
    resources = quiz_with_two_questions()

    plan = plan_deployment(resources, tracked(resources, tmp_path), build_builtin_handlers(), tmp_path)

    assert plan.expected_changes == ()


class FakeQuestion:
    def __init__(self, log):
        self.id = "77"
        self._log = log

    def edit(self, *, question):
        self._log.append(("question.edit", question["question_text"]))


class FakeQuiz:
    def __init__(self, log, *, published, submissions=()):
        self.id = "10"
        self.title = "HW"
        self.html_url = "https://canvas/quizzes/10"
        self.published = published
        self._log = log
        self._submissions = list(submissions)

    def get_submissions(self):
        return iter(self._submissions)

    def get_question(self, question_id):
        return FakeQuestion(self._log)

    def create_question(self, *, question):
        self._log.append(("question.create", question["question_text"]))
        return FakeQuestion(self._log)

    def edit(self, *, quiz):
        self._log.append(("quiz.edit", quiz))
        if "published" in quiz:
            self.published = quiz["published"]


class FakeCourse:
    def __init__(self, quiz, log):
        self.id = "20"
        self._quiz = quiz
        self._log = log
        self._requester = self

    def get_quiz(self, quiz_id):
        return self._quiz

    def request(self, method, path, **kwargs):
        self._log.append(("request", method, path))


ORDER = {"quiz_id": "10", "order": [{"id": "77", "type": "question"}]}


def test_writing_a_question_leaves_the_quiz_published_state_alone(tmp_path):
    log = []
    quiz = FakeQuiz(log, published=True)
    course = FakeCourse(quiz, log)

    deploy_quiz_question(course, {"quiz_id": "10", "canvas_id": "77", "question_text": "one"}, tmp_path)
    deploy_quiz_question(course, {"quiz_id": "10", "question_text": "new"}, tmp_path)

    assert log == [("question.edit", "one"), ("question.create", "new")]
    assert quiz.published is True


def test_order_step_republishes_a_published_quiz_after_reordering(tmp_path):
    log = []
    quiz = FakeQuiz(log, published=True)

    _, review = deploy_quiz_question_order(FakeCourse(quiz, log), ORDER, tmp_path)

    assert log == [
        ("request", "POST", "courses/20/quizzes/10/reorder"),
        ("quiz.edit", {"published": False}),
        ("quiz.edit", {"published": True}),
    ]
    assert quiz.published is True
    assert review is None


def test_order_step_saves_an_unpublished_quiz_once(tmp_path):
    log = []
    quiz = FakeQuiz(log, published=False)

    deploy_quiz_question_order(FakeCourse(quiz, log), ORDER, tmp_path)

    assert log == [
        ("request", "POST", "courses/20/quizzes/10/reorder"),
        ("quiz.edit", {"notify_of_update": False}),
    ]
    assert quiz.published is False


def test_order_step_leaves_a_quiz_with_submissions_for_the_user(tmp_path):
    log = []
    quiz = FakeQuiz(log, published=True, submissions=[object()])

    _, review = deploy_quiz_question_order(FakeCourse(quiz, log), ORDER, tmp_path)

    assert log == [("request", "POST", "courses/20/quizzes/10/reorder")]
    assert review == ("HW", "https://canvas/quizzes/10")
