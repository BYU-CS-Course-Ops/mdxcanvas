import json
import sys


class DeploymentReport:
    def __init__(self, output_file: str | None = None):
        self.output_file = output_file
        self.report = {
            "deployed_content": [],
            "content_to_review": [],
            "error": ""
        }

    def add_deployed_content(self, rtype: str, content_name: str, content_url: str | None = None):
        self.report["deployed_content"].append((rtype, content_name, content_url))

    def get_deployed_content(self):
        return self.report["deployed_content"]

    def add_content_to_review(self, rtype: str, content_name: str, content_url: str | None = None):
        if [content_name, content_url] not in self.report["content_to_review"]:
            self.report["content_to_review"].append([rtype, content_name, content_url])

    def get_content_to_review(self):
        return self.report["content_to_review"]

    def add_error(self, error: Exception):
        error_type = type(error).__name__
        error_msg = str(error)
        self.report["error"] = f"{error_type}: {error_msg}"

    def save_report(self):
        if self.output_file:
            with open(self.output_file, 'w') as f:
                f.write(json.dumps(self.report, indent=4))

    def print_report(self):
        if self.report['deployed_content']:
            groups = {}
            for rtype, rid, url in self.report['deployed_content']:
                if url not in groups:
                    groups[url] = []
                groups[url].append((rtype, rid))

            print(' Deployed Content '.center(60, '-'))
            for url, resources in groups.items():
                resources_str = ', '.join(rid for _, rid in resources)
                print(f'{resources_str}: {url}' if url else resources_str)

        if self.report['content_to_review']:
            print(' Content to Review '.center(60, '-'))
            for rtype, name, url in self.report['content_to_review']:
                print(f'{rtype}: {name} ({url})' if url else f'{rtype}: {name}')

        if self.report['error']:
            print(file=sys.stderr)
            print(self.report['error'], file=sys.stderr)
