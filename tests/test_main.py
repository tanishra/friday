"""main.py argv handling — LiveKit subcommand passthrough, flag stripping."""
import sys
from unittest.mock import MagicMock


def _run_worker_with_argv(monkeypatch, argv):
    """Run run_worker_sync with fake argv; capture final argv handed to cli."""
    import main
    captured = {}

    fake_cli = MagicMock()
    def fake_run_app(opts):
        captured["argv"] = list(sys.argv)
    fake_cli.run_app = fake_run_app
    monkeypatch.setitem(sys.modules, "livekit.agents", MagicMock(
        WorkerOptions=MagicMock(), cli=fake_cli,
    ))

    monkeypatch.setattr(sys, "argv", list(argv))
    main.run_worker_sync()
    return captured.get("argv")


def test_plain_defaults_to_dev(monkeypatch):
    assert _run_worker_with_argv(monkeypatch, ["main.py"]) == ["main.py", "dev"]


def test_our_flags_stripped(monkeypatch):
    assert _run_worker_with_argv(monkeypatch, ["main.py", "--worker"]) == ["main.py", "dev"]


def test_livekit_subcommand_passthrough(monkeypatch):
    assert _run_worker_with_argv(monkeypatch, ["main.py", "start"]) == ["main.py", "start"]
    assert _run_worker_with_argv(monkeypatch, ["main.py", "dev", "--log-level", "debug"]) == \
        ["main.py", "dev", "--log-level", "debug"]
