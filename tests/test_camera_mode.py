"""Unit tests for camera mode negotiation without camera hardware."""
from src.camera_mode import configure_and_probe_camera


class FakeCV:
    CAP_PROP_FRAME_WIDTH = 3
    CAP_PROP_FRAME_HEIGHT = 4
    CAP_PROP_FPS = 5


class FakeFrame:
    shape = (720, 1280, 3)


class FakeCapture:
    def __init__(self, accepted=(True, True, True), fps=30.0, read_ok=True):
        self._accepted = iter(accepted)
        self._fps = fps
        self._read_ok = read_ok
        self.requests = []

    def set(self, prop, value):
        self.requests.append((prop, value))
        return next(self._accepted)

    def get(self, prop):
        assert prop == FakeCV.CAP_PROP_FPS
        return self._fps

    def read(self):
        return self._read_ok, FakeFrame() if self._read_ok else None


def test_reports_mode_from_captured_frame():
    capture = FakeCapture()

    _, mode = configure_and_probe_camera(capture, FakeCV, 1280, 720, 30)

    assert mode.actual_width == 1280
    assert mode.actual_height == 720
    assert mode.actual_fps == 30.0
    assert mode.matches_request
    assert mode.describe() == "1280x720 @ 30.0 FPS"


def test_set_rejection_is_not_a_capture_failure():
    capture = FakeCapture(accepted=(False, False, False), fps=0.0)

    _, mode = configure_and_probe_camera(capture, FakeCV, 1920, 1080, 60)

    assert mode.accepted == (False, False, False)
    assert not mode.matches_request
    assert mode.describe() == "1280x720 @ FPS unknown"


def test_read_failure_is_reported():
    capture = FakeCapture(read_ok=False)

    try:
        configure_and_probe_camera(capture, FakeCV, 1280, 720, 30)
    except RuntimeError as error:
        assert str(error) == "Failed to capture frame from camera"
    else:
        raise AssertionError("A failed camera read must raise RuntimeError")
