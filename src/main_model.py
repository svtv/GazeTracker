"""Main model for processing video frames"""
import queue
import threading
import time
import traceback

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
        self.process_queue = queue.Queue()
        self.processing_thread = None
        self.should_process = True

        # Create image processor
        self.image_processor = ImageProcessor(self.app, self.modules)

        # Screen state caching
        self._last_screen_check = 0
        self._screen_state = True

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
                    if ret and not frame is None:
                        # Apply mirror effect if enabled
                        if self.app.app_state.mirror_effect.get():
                            frame = cv.flip(frame, 1)

                        # Convert frame for FaceMesh
                        frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

                        # Process frame using FaceMesh
                        mesh_results = self.mp_face_mesh.process(frame_rgb)

                        results = self.image_processor.process_face_mesh(
                            frame,
                            mesh_results,
                        )
                        results['mesh_results'] = mesh_results
                        results['threshold_value'] = self.app.app_state.threshold_value.get()
                        self.process_queue.put(results)

                # Wait for next frame
                time.sleep(self.refresh_delay_ms / 1000)

            except Exception as e:
                print(f"Error in processing loop: {e}")
                traceback.print_exc()
                time.sleep(self.refresh_delay_ms / 1000)
