import json
import re
import sys
from typing import Any

from .deploy.actions import ReviewInfo

_URL = re.compile(r"https?://[^\s\]\[<>{}\"']+", re.IGNORECASE)
_BEARER = re.compile(r"(?i)\bBearer\s+[^,;\s]+")
_SENSITIVE = re.compile(
    r"(?i)(?:[\"']?)\b("
    r"(?:[a-z0-9]+[-_])*(?:token|password|secret|authorization|credential|api[-_]?key|"
    r"signed[-_]?url|private[-_]?url|student(?:[-_]\w+)?|body|response)"
    r"(?:[-_][a-z0-9]+)*)\b(?:[\"']?)\s*[:=]\s*"
    r"(?:\"[^\"]*\"|'[^']*'|[^;]+)"
)


def _redact_error_message(error: Exception) -> str:
    message = " ".join(str(error).replace("\r", " ").replace("\n", " ").split())
    message = _URL.sub("[redacted-url]", message)
    message = _BEARER.sub("Bearer [redacted]", message)
    message = _SENSITIVE.sub(lambda match: f"{match.group(1)}=[redacted]", message)
    return message[:300]


def _safe_error(error: Exception) -> str:
    message = _redact_error_message(error)
    error_type = type(error).__name__
    return f"{error_type}: {message}" if message else error_type


class DeploymentReport:
    def __init__(self, output_file: str | None = None):
        self.output_file = output_file
        self._course_url: str | None = None
        self.report = {
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

    @property
    def has_errors(self) -> bool:
        return bool(self.report["processing"]["error"] or self.report["deployment"]["errors"])

    def configure(self, *, dryrun: bool, no_cleanup: bool,
                  course_url: str | None = None):
        self.report["deployment"]["mode"] = "dry_run" if dryrun else "deploy"
        self.report["deployment"]["cleanup"] = "disabled" if no_cleanup else "enabled"
        self._course_url = course_url

    def set_course_url(self, course_url: str | None):
        self._course_url = course_url

    def set_expected_changes(self, changes):
        self.report["deployment"]["expected_changes"] = [change.public() if hasattr(change, "public") else dict(change) for change in changes]

    def add_change_made(self, change, outcome: str, *, url: str | None = None,
                        review: ReviewInfo | None = None):
        item = change.public() if hasattr(change, "public") else dict(change)
        outcome = getattr(outcome, "value", outcome)
        item["outcome"] = outcome
        if url:
            item["url"] = url
        if outcome in {"created", "updated"}:
            self.report["deployed_content"].append([
                item["resource_type"], item["resource_id"], url,
            ])
        if review is not None:
            item["review"] = {"name": review.name, "url": review.url}
        self.report["deployment"]["changes_made"].append(item)
        self._derive_content_to_review()

    def _derive_content_to_review(self):
        content = []
        seen = set()
        for change in self.report["deployment"]["changes_made"]:
            review = change.get("review")
            if review is None:
                continue
            key = change["resource_type"], review["name"], review["url"]
            if key in seen:
                continue
            seen.add(key)
            content.append([
                change["resource_type"],
                review["name"],
                review["url"],
            ])
        self.report["content_to_review"] = content

    def add_deployment_error(
            self, stage: str, error: Exception, change=None,
            source: str | None = None, *, status: str | None = None,
            action: str | None = None,
    ):
        item: dict[str, Any] = {"stage": stage, "error": _safe_error(error)}
        if change is not None:
            item.update(change.public() if hasattr(change, "public") else dict(change))
            source = source or getattr(change, "source", None)
        if source:
            item["source"] = source
        if status:
            item["status"] = status
        if action:
            item["action"] = action
        self.report["deployment"]["errors"].append(item)
        self._derive_legacy_error()

    def add_error(self, error: Exception):
        self.report["processing"]["error"] = _safe_error(error)
        self._derive_legacy_error()

    def _derive_legacy_error(self):
        errors = [
            self.report["processing"]["error"],
            *(
                item["error"]
                for item in self.report["deployment"]["errors"]
                if item.get("status") != "blocked"
            ),
        ]
        self.report["error"] = "\n".join(error for error in errors if error)

    def save_report(self):
        if self.output_file:
            with open(self.output_file, "w") as output:
                json.dump(self.report, output, indent=4)

    def print_report(self):
        deployment = self.report["deployment"]
        print(f"Cleanup: {deployment['cleanup']}")
        if deployment["mode"] == "dry_run":
            for change in deployment["expected_changes"]:
                print(f"{change['change']:<8} {change['resource_type']} {change['resource_id']}")
        if deployment["changes_made"]:
            print(" Deployed Content ".center(60, "-"))
            groups: dict[str | None, list[str]] = {}
            for change in deployment["changes_made"]:
                url = change.get("url") or self._course_url
                label = f"{change['outcome']} {change['resource_type']} {change['resource_id']}"
                groups.setdefault(url, []).append(label)
            for url, labels in groups.items():
                line = ", ".join(labels)
                print(f"{line}: {url}" if url else line)
        if self.report["content_to_review"]:
            print(" Content to Review ".center(60, "-"))
            for resource_type, name, url in self.report["content_to_review"]:
                suffix = f" ({url})" if url else ""
                print(f"{resource_type}: {name}{suffix}")
        if self.report["processing"]["error"]:
            print(self.report["processing"]["error"], file=sys.stderr)
        blocked_resources = set()
        for error in deployment["errors"]:
            if error.get("status") == "blocked":
                blocked_resources.add((error.get("resource_type"), error.get("resource_id")))
                continue
            context = " ".join(filter(None, (
                error.get("action") or error.get("change"),
                error.get("resource_type"),
                error.get("resource_id"),
            )))
            if error.get("source"):
                context = f"{context} ({error['source']})" if context else error["source"]
            prefix = f"{context}: " if context else f"{error['stage']}: "
            print(f"{prefix}{error['error']}", file=sys.stderr)
        if blocked_resources:
            print(f"{len(blocked_resources)} resources not deployed", file=sys.stderr)
