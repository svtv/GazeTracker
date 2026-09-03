"""Tests for camera preprocessing; skipped when OpenCV is not installed."""
import pytest

cv = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")

from src.config import CAMERA_CLAHE_CLIP_LIMIT, CAMERA_CLAHE_GRID_SIZE  # noqa: E402
from src.image_processor import ImageProcessor  # noqa: E402
from src.main_model import MainModel  # noqa: E402


def make_processor():
    processor = ImageProcessor.__new__(ImageProcessor)
    processor._camera_clahe = cv.createCLAHE(
        clipLimit=CAMERA_CLAHE_CLIP_LIMIT,
        tileGridSize=CAMERA_CLAHE_GRID_SIZE,
    )
    processor._smoothed_camera_luminance = None
    processor._gamma_lut_value = None
    processor._gamma_lut = None
    return processor


def test_enhancement_preserves_actual_camera_geometry():
    processor = make_processor()
    frame = np.full((137, 251, 3), 45, dtype=np.uint8)

    enhanced = processor.enhance_image(frame)

    assert enhanced.shape == frame.shape
    assert enhanced.dtype == frame.dtype


def test_dark_frame_gets_stronger_gamma_than_bright_frame():
    assert ImageProcessor._adaptive_camera_gamma(30.0) > 1.0
    assert ImageProcessor._adaptive_camera_gamma(200.0) == 1.0


class Landmark:
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z


class FaceLandmarks:
    def __init__(self, landmarks):
        self.landmark = landmarks


class MeshResults:
    def __init__(self, landmarks):
        self.multi_face_landmarks = [FaceLandmarks(landmarks)]


def test_roi_is_square_clamped_and_uses_actual_frame_size():
    results = MeshResults([
        Landmark(0.40, 0.20),
        Landmark(0.60, 0.70),
    ])

    x1, y1, x2, y2 = MainModel._target_face_roi(results, (720, 1280, 3))

    assert x2 - x1 == y2 - y1
    assert 0 <= x1 < x2 <= 1280
    assert 0 <= y1 < y2 <= 720


def test_crop_landmarks_are_mapped_back_to_full_frame():
    results = MeshResults([Landmark(0.5, 0.5, 0.2)])

    MainModel._remap_landmarks_to_full_frame(
        results,
        roi=(100, 50, 300, 250),
        frame_shape=(400, 800, 3),
    )

    point = results.multi_face_landmarks[0].landmark[0]
    assert point.x == pytest.approx(0.25)
    assert point.y == pytest.approx(0.375)
    assert point.z == pytest.approx(0.05)
