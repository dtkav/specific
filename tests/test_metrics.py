
import flask

import specific
from mock import MagicMock
from specific.decorators.metrics import UWSGIMetricsCollector


def test_timer(monkeypatch):
    wrapper = UWSGIMetricsCollector('/foo/bar/<param>', 'get')

    def operation(req):
        return specific.problem(418, '', '')

    op = wrapper(operation)
    metrics = MagicMock()
    monkeypatch.setattr('flask.request', MagicMock())
    monkeypatch.setattr('flask.current_app', MagicMock(response_class=flask.Response))
    monkeypatch.setattr('specific.decorators.metrics.uwsgi_metrics', metrics)
    op(MagicMock())
    assert metrics.timer.call_args[0][:2] == ('specific.response',
                                              '418.GET.foo.bar.{param}')
