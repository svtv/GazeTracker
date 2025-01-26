# Standard library imports
import importlib
import queue
import threading
from tkinter import messagebox

# Third-party imports
import customtkinter as ctk

# Local imports
from .config import (
    APP_FONT, APP_FONT_KEY, APP_FONT_SIZE_TITLE,
    MIN_DETECTION_CONFIDENCE, MIN_DETECTION_CONFIDENCE_KEY,
    MIN_TRACKING_CONFIDENCE, MIN_TRACKING_CONFIDENCE_KEY,
    DEFAULT_WEBCAM
)
from .settings import Settings

class LoadingUIComponents:
    """Class for managing loading UI components"""
    def __init__(self, parent):
        self.frame = None
        self.progress_bars = {}
        self.status_labels = {}
        self.default_font = Settings.get(APP_FONT_KEY, APP_FONT)
        self.parent = parent


class LoadingState:
    """Class for managing loading state"""
    def __init__(self):
        self.is_loaded = False
        self.components_loaded = {
            'camera': False,
            'mediapipe': False,
            'other_modules': False
        }
        self.load_queue = queue.Queue()


class LoadedComponents:
    """Class for managing loaded components"""
    def __init__(self):
        self.modules = {}
        self.cap = None
        self.mp_face_mesh = None


class ComponentLoader:
    """Class for managing application component loading"""
    def __init__(self, parent):
        self.parent = parent

        # Initialize component groups
        self.ui = LoadingUIComponents(parent)
        self.state = LoadingState()
        self.loaded = LoadedComponents()
        self.on_complete_callback = None

        # Create loading UI
        self._create_loading_ui()

    def start_loading(self, on_complete_callback):
        """Starts the component loading process"""
        self.on_complete_callback = on_complete_callback

        # Start loading components in background threads
        for loader in [self._load_camera, self._load_mediapipe, self._load_other_modules]:
            thread = threading.Thread(target=loader)
            thread.daemon = True
            thread.start()

        # Start checking loading status
        self._check_loading_status()

    def _load_camera(self):
        """Camera loading and initialization"""
        try:
            self.state.load_queue.put(("message", "Initializing camera..."))
            self.state.load_queue.put(("progress_update", "camera", 0.2))

            # Import OpenCV
            cv = importlib.import_module('cv2')
            self.loaded.modules['cv2'] = cv
            self.state.load_queue.put(("progress_update", "camera", 0.4))

            # Initialize camera
            self.loaded.cap = cv.VideoCapture(DEFAULT_WEBCAM)
            if not self.loaded.cap.isOpened():
                raise RuntimeError("Failed to connect to camera")
            self.state.load_queue.put(("progress_update", "camera", 0.6))

            # Set camera parameters
            ret1 = self.loaded.cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
            ret2 = self.loaded.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 720)
            ret3 = self.loaded.cap.set(cv.CAP_PROP_FPS, 30)

            # Verify camera settings
            if not all([ret1, ret2, ret3]):
                raise RuntimeError("Failed to set camera parameters")

            # Test camera capture
            ret, frame = self.loaded.cap.read()
            if not ret or frame is None:
                raise RuntimeError("Failed to capture frame from camera")

            self.state.load_queue.put(("progress_update", "camera", 0.8))

            self.state.components_loaded['camera'] = True
            self.state.load_queue.put(("progress_update", "camera", 1.0))

        except ImportError as e:
            self.state.load_queue.put(("error", f"Failed to import OpenCV: {str(e)}"))
        except (cv.error, OSError) as e:
            self.state.load_queue.put(("error", f"Camera hardware error: {str(e)}"))
        except RuntimeError as e:
            self.state.load_queue.put(("error", f"Camera initialization error: {str(e)}"))

    def _load_mediapipe(self):
        """Loading MediaPipe and initializing FaceMesh"""
        try:
            self.state.load_queue.put(("message", "Loading MediaPipe..."))
            self.state.load_queue.put(("progress_update", "mediapipe", 0.1))

            # Import MediaPipe
            mp = importlib.import_module('mediapipe')
            self.loaded.modules['mediapipe'] = mp
            self.state.load_queue.put(("progress_update", "mediapipe", 0.4))

            # Initialize FaceMesh
            self.loaded.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=Settings.get(MIN_DETECTION_CONFIDENCE_KEY, MIN_DETECTION_CONFIDENCE),
                min_tracking_confidence=Settings.get(MIN_TRACKING_CONFIDENCE_KEY, MIN_TRACKING_CONFIDENCE),
            )
            self.state.load_queue.put(("progress_update", "mediapipe", 0.7))

            self.state.components_loaded['mediapipe'] = True
            self.state.load_queue.put(("progress_update", "mediapipe", 1.0))

        except ImportError as e:
            self.state.load_queue.put(("error", f"Failed to import MediaPipe: {str(e)}"))
        except ValueError as e:
            self.state.load_queue.put(("error", f"Invalid MediaPipe configuration: {str(e)}"))
        except RuntimeError as e:
            self.state.load_queue.put(("error", f"MediaPipe initialization error: {str(e)}"))

    def _load_other_modules(self):
        """Loading other modules"""
        try:
            # Load additional modules
            self.state.load_queue.put(("message", "Loading additional modules..."))
            self.loaded.modules['numpy'] = importlib.import_module('numpy')
            self.state.load_queue.put(("progress_update", "other_modules", 0.4))

            self.loaded.modules['PIL'] = importlib.import_module('PIL.Image')
            self.state.load_queue.put(("progress_update", "other_modules", 0.5))

            # Import local modules
            self.state.load_queue.put(("message", "Loading image processor..."))
            self.loaded.modules['image_processor'] = importlib.import_module('src.image_processor')
            self.state.load_queue.put(("progress_update", "other_modules", 0.7))

            self.state.components_loaded['other_modules'] = True
            self.state.load_queue.put(("progress_update", "other_modules", 1.0))

        except ModuleNotFoundError as e:
            self.state.load_queue.put(("error", f"Required module not found: {str(e)}"))
        except ImportError as e:
            self.state.load_queue.put(("error", f"Failed to import module: {str(e)}"))
        except AttributeError as e:
            self.state.load_queue.put(("error", f"Module missing required attributes: {str(e)}"))
        except RuntimeError as e:
            self.state.load_queue.put(("error", f"Settings initialization error: {str(e)}"))

    def _create_loading_ui(self):
        """Creates loading indicator UI"""
        # Create and configure loading frame
        self.ui.frame = ctk.CTkFrame(self.parent)
        self.ui.frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Create loading indicators for each component
        for idx, (component_id, component_name) in enumerate({
            'camera': 'Camera',
            'mediapipe': 'MediaPipe',
            'other_modules': 'Additional Modules'
        }.items()):
            component_frame = ctk.CTkFrame(self.ui.frame)
            component_frame.pack(fill='x', padx=15, pady=(20 if idx == 0 else 10, 0))

            # Create label
            component_label = ctk.CTkLabel(
                component_frame,
                text=component_name,
                anchor="w",
                font=(self.ui.default_font, APP_FONT_SIZE_TITLE)
            )
            component_label.pack(side='left', padx=8, pady=4)

            # Add status
            status_label = ctk.CTkLabel(
                component_frame,
                text="Waiting...",
                text_color='gray',
                anchor='e',
                font=(self.ui.default_font, 13)
            )
            status_label.pack(side='right', padx=8, pady=4)
            self.ui.status_labels[component_id] = status_label

            # Create progress bar
            progress = ctk.CTkProgressBar(self.ui.frame, width=340)
            progress.set(0)
            progress.pack(padx=15, pady=(0, 6))
            self.ui.progress_bars[component_id] = progress

    def _handle_progress_update(self, component, value):
        """Handle progress update message"""
        if component in self.ui.progress_bars:
            self.ui.progress_bars[component].set(value)
            # Update status text based on progress
            if value >= 1.0:
                self.ui.status_labels[component].configure(
                    text="Done",
                    text_color="green"
                )
            else:
                self.ui.status_labels[component].configure(
                    text=f"{int(value * 100)}%",
                    text_color="gray"
                )

    def _handle_status_message(self, message):
        """Handle status message"""
        # Find the component this message relates to
        for component_id, label in self.ui.status_labels.items():
            if component_id.lower() in message.lower():
                label.configure(
                    text=message,
                    text_color="gray"
                )
                break

    def _handle_error(self, error_message):
        """Handle error message"""
        messagebox.showerror("Error", error_message)
        self.parent.quit()

    def _handle_loading_complete(self):
        """Handle completion of loading"""
        # Destroy loading UI
        if self.ui.frame:
            self.ui.frame.destroy()
            self.ui.frame = None

        # Call the completion callback
        self.on_complete_callback(
            self.loaded.modules,
            self.loaded.cap,
            self.loaded.mp_face_mesh,
        )

    def _check_loading_status(self):
        """Checks background loading status"""
        try:
            while True:
                # Get message from queue
                msg_type, *msg_data = self.state.load_queue.get_nowait()

                # Process message based on type
                if msg_type == "progress_update":
                    self._handle_progress_update(msg_data[0], msg_data[1])
                elif msg_type == "message":
                    self._handle_status_message(msg_data[0])
                elif msg_type == "error":
                    self._handle_error(msg_data[0])
                    return

                # Check if all components are loaded
                if all(self.state.components_loaded.values()):
                    self.state.is_loaded = True
                    self._handle_loading_complete()
                    return

                self.state.load_queue.task_done()

        except queue.Empty:
            # If queue is empty, check again after 100ms
            if not self.state.is_loaded:
                self.parent.after(100, self._check_loading_status)

        except (AttributeError, TypeError) as e:
            self._handle_error(f"UI component error: {str(e)}")

        except RuntimeError as e:
            self._handle_error(f"Callback error: {str(e)}")
