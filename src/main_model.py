"""Main model for processing video frames"""
import queue
import threading
import time
import traceback

from .config import (
    CAMERA_FACE_ROI_ENABLED,
    CAMERA_FACE_ROI_FULL_FRAME_INTERVAL,
    CAMERA_FACE_ROI_MARGIN,
    CAMERA_FACE_ROI_MIN_SIZE,
    CAMERA_FACE_ROI_SHOW,
    CAMERA_FACE_ROI_SMOOTHING_ALPHA,
)
from .image_processor import ImageProcessor
from .screen_state import is_screen_on

class MainModel:
    """Model for processing video frames and managing processing thread"""
    def __init__(self, app, modules, cap, mp_face_mesh, refresh_delay_ms):
        self.app = app  # Reference to main app for UI elements
        self.modules = modules
        self.cap = cap
        self.mp_face_mesh = mp_face_mesh
        self.refresh_delay_ms = refresh_delay_ms

        # Thread control
        self.process_queue = queue.Queue(maxsize=1)
        self.processing_thread = None
        self.should_process = True

        # Create image processor
        self.image_processor = ImageProcessor(self.app, self.modules)

        # Screen state caching
        self._last_screen_check = 0
        self._screen_state = True

        # ROI coordinates always refer to the full camera frame. Keeping this
        # state here separates detection input geometry from display smoothing.
        self._face_roi = None
        self._face_roi_age = 0

    def start(self):
        """Start processing thread"""
        self.should_process = True
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def stop(self):
        """Stop processing thread"""
        self.should_process = False
        if self.processing_thread is not None:
            self.processing_thread.join(timeout=1.0)

    def get_next_result(self):
        """Get next processing result if available"""
        try:
            return self.process_queue.get_nowait()
        except queue.Empty:
            return None

    def _publish_latest_result(self, results):
        """Publish without blocking and discard an obsolete queued frame."""
        try:
            self.process_queue.put_nowait(results)
            return
        except queue.Full:
            pass

        try:
            self.process_queue.get_nowait()
        except queue.Empty:
            pass

        try:
            self.process_queue.put_nowait(results)
        except queue.Full:
            # The UI/producer raced with us. Keeping either frame is safe; the
            # next processing iteration will publish a newer one.
            pass

    def _face_mesh_input(self, frame):
        """Return the current FaceMesh input and its full-frame ROI."""
        if not CAMERA_FACE_ROI_ENABLED or self._face_roi is None:
            return frame, None

        if (
            CAMERA_FACE_ROI_FULL_FRAME_INTERVAL > 0
            and self._face_roi_age >= CAMERA_FACE_ROI_FULL_FRAME_INTERVAL
        ):
            self._face_roi_age = 0
            return frame, None

        x1, y1, x2, y2 = self._face_roi
        if x2 <= x1 or y2 <= y1:
            self._face_roi = None
            return frame, None

        self._face_roi_age += 1
        return frame[y1:y2, x1:x2], self._face_roi

    @staticmethod
    def _remap_landmarks_to_full_frame(mesh_results, roi, frame_shape):
        """Map normalized crop landmarks back to normalized frame space."""
        if roi is None or not mesh_results.multi_face_landmarks:
            return

        frame_h, frame_w = frame_shape[:2]
        x1, y1, x2, y2 = roi
        roi_w = x2 - x1
        roi_h = y2 - y1

        for face_landmarks in mesh_results.multi_face_landmarks:
            for point in face_landmarks.landmark:
                point.x = (x1 + point.x * roi_w) / frame_w
                point.y = (y1 + point.y * roi_h) / frame_h
                # MediaPipe documents normalized z on approximately the same
                # scale as x, so account for the crop-to-frame width ratio.
                point.z *= roi_w / frame_w

    @staticmethod
    def _target_face_roi(mesh_results, frame_shape):
        """Build a clamped square ROI around full-frame face landmarks."""
        if not mesh_results.multi_face_landmarks:
            return None

        frame_h, frame_w = frame_shape[:2]
        landmarks = mesh_results.multi_face_landmarks[0].landmark
        if not landmarks:
            return None

        xs = [point.x * frame_w for point in landmarks]
        ys = [point.y * frame_h for point in landmarks]
        face_w = max(xs) - min(xs)
        face_h = max(ys) - min(ys)
        if face_w <= 1.0 or face_h <= 1.0:
            return None

        center_x = (min(xs) + max(xs)) * 0.5
        center_y = (min(ys) + max(ys)) * 0.5
        side = max(face_w, face_h) * (1.0 + 2.0 * CAMERA_FACE_ROI_MARGIN)
        side = min(max(side, CAMERA_FACE_ROI_MIN_SIZE), frame_w, frame_h)

        x1 = min(max(center_x - side * 0.5, 0.0), frame_w - side)
        y1 = min(max(center_y - side * 0.5, 0.0), frame_h - side)
        return (
            int(round(x1)),
            int(round(y1)),
            int(round(x1 + side)),
            int(round(y1 + side)),
        )

    def _update_face_roi(self, mesh_results, frame_shape):
        """Update the ROI without affecting distance/alert measurements."""
        target = self._target_face_roi(mesh_results, frame_shape)
        if target is None:
            self._face_roi = None
            self._face_roi_age = 0
            return

        if self._face_roi is None:
            self._face_roi = target
        else:
            alpha = CAMERA_FACE_ROI_SMOOTHING_ALPHA
            self._face_roi = tuple(
                int(round(old + alpha * (new - old)))
                for old, new in zip(self._face_roi, target)
            )

    def _draw_face_roi(self, frame):
        """Optionally draw the current ROI for tuning and diagnostics."""
        if not CAMERA_FACE_ROI_SHOW or self._face_roi is None:
            return
        cv = self.modules['cv2']
        x1, y1, x2, y2 = self._face_roi
        cv.rectangle(frame, (x1, y1), (x2, y2), (140, 180, 190), 1)

    def _processing_loop(self):
        """Background thread for continuous frame processing"""
        while self.should_process:
            try:
                # Check if screen is on (caching with 1 second update)
                current_time = time.time()
                if current_time - self._last_screen_check >= 1.0:
                    self._screen_state = is_screen_on()
                    self._last_screen_check = current_time

                # Use cached screen state
                if self._screen_state:
                    # Get required modules
                    cv = self.modules['cv2']
                    # Image = self.modules['PIL']

                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        # Apply mirror effect if enabled
                        if self.app.app_state.mirror_effect.get():
                            frame = cv.flip(frame, 1)

                        # Use one geometry-preserving enhanced frame both for
                        # FaceMesh and, when enabled, the Camera Image view.
                        # Its dimensions come directly from VideoCapture.
                        frame = self.image_processor.enhance_image(frame)

                        # Use the previous detection to give FaceMesh a larger
                        # effective face image without resizing/distorting it.
                        mesh_input, face_roi = self._face_mesh_input(frame)
                        frame_rgb = cv.cvtColor(mesh_input, cv.COLOR_BGR2RGB)

                        # Process frame using FaceMesh
                        mesh_results = self.mp_face_mesh.process(frame_rgb)
                        self._remap_landmarks_to_full_frame(
                            mesh_results,
                            face_roi,
                            frame.shape,
                        )
                        self._update_face_roi(mesh_results, frame.shape)
                        self._draw_face_roi(frame)

                        results = self.image_processor.process_face_mesh(
                            frame,
                            mesh_results,
                        )
                        results['mesh_results'] = mesh_results
                        results['threshold_value'] = self.app.app_state.threshold_value.get()
                        self._publish_latest_result(results)

                # Wait for next frame
                time.sleep(self.refresh_delay_ms / 1000)

            except Exception as e:
                print(f"Error in processing loop: {e}")
                traceback.print_exc()
                time.sleep(self.refresh_delay_ms / 1000)
