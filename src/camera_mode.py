"""Helpers for requesting and reporting the actual camera capture mode."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class CameraMode:
    """Camera settings requested by the app and observed after the first read."""
    requested_width: int
    requested_height: int
    requested_fps: float
    actual_width: int
    actual_height: int
    actual_fps: float
    accepted: tuple

    @property
    def matches_request(self):
        """Whether resolution matches exactly and FPS is close when reported."""
        resolution_matches = (
            self.actual_width == self.requested_width
            and self.actual_height == self.requested_height
        )
        fps_matches = (
            self.actual_fps <= 0
            or math.isclose(self.actual_fps, self.requested_fps, rel_tol=0.05)
        )
        return resolution_matches and fps_matches

    def describe(self):
        """Return a compact human-readable description of the active mode."""
        fps = f"{self.actual_fps:.1f} FPS" if self.actual_fps > 0 else "FPS unknown"
        return f"{self.actual_width}x{self.actual_height} @ {fps}"


def configure_and_probe_camera(cap, cv, width, height, fps):
    """Request a mode, capture one frame, and return the frame and actual mode.

    OpenCV's ``VideoCapture.set`` result is advisory: a backend may return False
    while continuing with a usable fallback.  The captured frame dimensions are
    therefore authoritative; FPS is read from the backend when it is available.
    """
    requests = (
        (cv.CAP_PROP_FRAME_WIDTH, float(width)),
        (cv.CAP_PROP_FRAME_HEIGHT, float(height)),
        (cv.CAP_PROP_FPS, float(fps)),
    )
    accepted = tuple(bool(cap.set(prop, value)) for prop, value in requests)

    ok, frame = cap.read()
    if not ok or frame is None:
        raise RuntimeError("Failed to capture frame from camera")

    actual_height, actual_width = frame.shape[:2]
    actual_fps = float(cap.get(cv.CAP_PROP_FPS))
    if not math.isfinite(actual_fps) or actual_fps < 0:
        actual_fps = 0.0

    return frame, CameraMode(
        requested_width=int(width),
        requested_height=int(height),
        requested_fps=float(fps),
        actual_width=int(actual_width),
        actual_height=int(actual_height),
        actual_fps=actual_fps,
        accepted=accepted,
    )
