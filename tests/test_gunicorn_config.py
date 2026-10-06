import runpy
import sys
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from flask import Flask

from app.activity.monitoring.monitor import WebSocketMonitor
from app.activity.tracking import ACTIVITY_MONITOR_EXTENSION

CONFIG_PATH = Path(__file__).resolve().parents[1] / "gunicorn.conf.py"


def test_gunicorn_uses_one_threaded_worker_by_default(monkeypatch):
    monkeypatch.delenv("GUNICORN_WORKERS", raising=False)
    monkeypatch.delenv("GUNICORN_THREADS", raising=False)

    config = runpy.run_path(str(CONFIG_PATH))

    assert config["workers"] == 1
    assert config["threads"] == 4
    assert config["worker_class"] == "gthread"


def test_gunicorn_worker_and_thread_counts_remain_configurable(monkeypatch):
    monkeypatch.setenv("GUNICORN_WORKERS", "2")
    monkeypatch.setenv("GUNICORN_THREADS", "6")

    config = runpy.run_path(str(CONFIG_PATH))

    assert config["workers"] == 2
    assert config["threads"] == 6


@pytest.mark.parametrize("hook", ["on_exit", "worker_exit"])
def test_gunicorn_shutdown_joins_activity_executor(monkeypatch, hook):
    application = Flask("gunicorn-shutdown-test")
    monitor = WebSocketMonitor(application)
    started = threading.Event()
    monkeypatch.setattr(monitor, "_update_collectors", started.set)
    application.extensions[ACTIVITY_MONITOR_EXTENSION] = monitor
    monkeypatch.setitem(sys.modules, "run", SimpleNamespace(app=application))
    scheduler = Mock(running=True)
    monkeypatch.setattr("app.extensions.scheduler", scheduler)
    config = runpy.run_path(str(CONFIG_PATH))

    monitor.start_monitoring()
    executor = monitor.executor
    try:
        assert started.wait(5)
        arguments = (None, SimpleNamespace(pid=1, age=1)) if hook == "worker_exit" else (None,)
        config[hook](*arguments)
        assert not monitor.monitoring
        assert monitor.executor is None
        assert ACTIVITY_MONITOR_EXTENSION not in application.extensions
        assert all(not thread.is_alive() for thread in executor._threads)
        scheduler.shutdown.assert_called_once_with(wait=False)
    finally:
        monitor.stop_monitoring()


def test_shutdown_does_not_create_an_application_that_never_started(monkeypatch):
    monkeypatch.delitem(sys.modules, "run", raising=False)
    stop = Mock()
    monkeypatch.setattr("app.activity.tracking.stop_activity_tracking", stop)
    config = runpy.run_path(str(CONFIG_PATH))

    config["on_exit"](None)

    stop.assert_not_called()
