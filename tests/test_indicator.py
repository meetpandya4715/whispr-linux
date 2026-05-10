from __future__ import annotations

from whisprlinux.indicator import RecordingIndicator


def test_recording_indicator_starts_and_stops_process(monkeypatch) -> None:
    actions = []

    class Process:
        returncode = None

        def terminate(self) -> None:
            actions.append("terminate")

        def wait(self, timeout: float | None = None) -> None:
            actions.append(("wait", timeout))
            self.returncode = 0

    def popen(*args, **kwargs):
        actions.append((args, kwargs))
        return Process()

    monkeypatch.setattr("whisprlinux.indicator.subprocess.Popen", popen)
    monkeypatch.setattr("whisprlinux.indicator.shutil.which", lambda name: None)

    indicator = RecordingIndicator(enabled=True)
    indicator.start()
    indicator.stop()

    assert actions[0][0][0][1:] == ["-m", "whisprlinux.indicator"]
    assert actions[1:] == ["terminate", ("wait", 1)]


def test_recording_indicator_prefers_gjs_when_available(monkeypatch) -> None:
    actions = []

    class Process:
        returncode = 0

    def popen(*args, **kwargs):
        actions.append((args, kwargs))
        return Process()

    monkeypatch.setattr("whisprlinux.indicator.subprocess.Popen", popen)
    monkeypatch.setattr("whisprlinux.indicator.shutil.which", lambda name: "/usr/bin/gjs" if name == "gjs" else None)

    RecordingIndicator(enabled=True).start()

    assert actions[0][0][0][0] == "/usr/bin/gjs"
    assert actions[0][0][0][1].endswith("indicator-gjs.js")


def test_recording_indicator_ignores_startup_failure(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise OSError("no display")

    monkeypatch.setattr("whisprlinux.indicator.subprocess.Popen", fail)

    indicator = RecordingIndicator(enabled=True)
    indicator.start()
    indicator.stop()


def test_recording_indicator_can_be_disabled(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("should not start")

    monkeypatch.setattr("whisprlinux.indicator.subprocess.Popen", fail)

    RecordingIndicator(enabled=False).start()


def test_rounded_rect_draws_smooth_canvas_shape() -> None:
    calls = []

    class Canvas:
        def create_arc(self, *args, **kwargs):
            calls.append(("arc", args, kwargs))

        def create_rectangle(self, *args, **kwargs):
            calls.append(("rectangle", args, kwargs))

    from whisprlinux.indicator import rounded_rect

    rounded_rect(Canvas(), 0, 0, 100, 40, radius=16, fill="#111111", outline="")

    assert len([call for call in calls if call[0] == "arc"]) == 4
    assert len([call for call in calls if call[0] == "rectangle"]) == 3


def test_indicator_theme_avoids_chroma_key_window_background() -> None:
    from whisprlinux.indicator import indicator_theme

    theme = indicator_theme()

    assert theme["window_background"] != "#ff00ff"
    assert theme["background"] != theme["window_background"]


def test_indicator_asset_exists() -> None:
    from whisprlinux.indicator import gjs_indicator_path, indicator_asset_path

    asset = indicator_asset_path()

    assert asset.exists()
    assert asset.name == "recording-indicator.png"
    assert gjs_indicator_path().exists()
