from pathlib import Path

from mdxcanvas.deploy.canvas_deploy import (
    DEFAULT_STALE_RESOURCE_TYPES,
    deploy_to_canvas,
    get_stale_resources,
)


class FakeMD5Sums:
    def __init__(self, data):
        self._data = data

    def items(self):
        return self._data.items()

    def get_canvas_info(self, item):
        return self._data.get(item, {}).get('canvas_info')


def test_get_stale_resources_filters_allowed_types_and_priority():
    resources = {}
    md5s = FakeMD5Sums({
        ('assignment', 'keep-assignment'): {
            'canvas_info': {'id': '10'},
        },
        ('module_item', 'stale-module-item'): {
            'canvas_info': {'id': '20', 'module_id': '200'},
        },
        ('quiz', 'stale-quiz'): {
            'canvas_info': {'id': '30'},
        },
        ('quiz_question', 'stale-question'): {
            'canvas_info': {'id': '40', 'quiz_id': '30'},
        },
        ('syllabus', 'ignored-syllabus'): {
            'canvas_info': {'id': '50'},
        },
    })

    stale = get_stale_resources(
        resources,
        md5s,
        allowed_types=DEFAULT_STALE_RESOURCE_TYPES,
    )

    assert stale == [
        ('module_item', 'stale-module-item', {'id': '20', 'module_id': '200'}),
        ('quiz_question', 'stale-question', {'id': '40', 'quiz_id': '30'}),
    ]


def test_navigation_checksum_is_retained_even_during_full_cleanup():
    entry = {
        'checksum': 'navigation-checksum',
        'canvas_info': {'id': '99'},
    }
    md5s = FakeMD5Sums({
        ('navigation', 'navigation'): entry,
    })

    stale = get_stale_resources({}, md5s, allowed_types=None)

    assert stale == []
    assert md5s.get_canvas_info(('navigation', 'navigation')) == {'id': '99'}
    assert md5s._data[('navigation', 'navigation')] == entry


def test_deploy_to_canvas_applies_default_stale_cleanup(monkeypatch):
    recorded = {}

    class StubMD5Sums:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def fake_remove(_course, _resources, _md5s, allowed_types=None):
        recorded['allowed_types'] = allowed_types
        return 2

    def fake_log_completion(actions, _elapsed):
        recorded['actions'] = actions

    monkeypatch.setattr('mdxcanvas.deploy.canvas_deploy.MD5Sums', StubMD5Sums)
    monkeypatch.setattr('mdxcanvas.deploy.canvas_deploy.migrate', lambda *_args: None)
    monkeypatch.setattr(
        'mdxcanvas.deploy.canvas_deploy._prepare_deployment_order',
        lambda _resources: ({}, []),
    )
    monkeypatch.setattr(
        'mdxcanvas.deploy.canvas_deploy.identify_modified_or_outdated',
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        'mdxcanvas.deploy.canvas_deploy._remove_stale_resources',
        fake_remove,
    )
    monkeypatch.setattr(
        'mdxcanvas.deploy.canvas_deploy._log_completion',
        fake_log_completion,
    )

    deploy_to_canvas(
        course=object(),
        timezone='America/Denver',
        resources={},
        report=object(),
        deploy_root=Path('.'),
        cleanup=False,
    )

    assert recorded['allowed_types'] == DEFAULT_STALE_RESOURCE_TYPES
    assert recorded['actions'] == ['2 stale resources removed']


def test_deploy_to_canvas_cleanup_flag_keeps_full_cleanup(monkeypatch):
    recorded = {}

    class StubMD5Sums:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def fake_remove(_course, _resources, _md5s, allowed_types=None):
        recorded['allowed_types'] = allowed_types
        return 1

    monkeypatch.setattr('mdxcanvas.deploy.canvas_deploy.MD5Sums', StubMD5Sums)
    monkeypatch.setattr('mdxcanvas.deploy.canvas_deploy.migrate', lambda *_args: None)
    monkeypatch.setattr(
        'mdxcanvas.deploy.canvas_deploy._prepare_deployment_order',
        lambda _resources: ({}, []),
    )
    monkeypatch.setattr(
        'mdxcanvas.deploy.canvas_deploy.identify_modified_or_outdated',
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        'mdxcanvas.deploy.canvas_deploy._remove_stale_resources',
        fake_remove,
    )
    monkeypatch.setattr(
        'mdxcanvas.deploy.canvas_deploy._log_completion',
        lambda *_args: None,
    )

    deploy_to_canvas(
        course=object(),
        timezone='America/Denver',
        resources={},
        report=object(),
        deploy_root=Path('.'),
        cleanup=True,
    )

    assert recorded['allowed_types'] is None
