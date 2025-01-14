import customtkinter as ctk
import importlib
import queue
import threading

from app_types import Size
from config import *
from settings import Settings
from tkinter import messagebox

class ComponentLoader:
    """Class for managing application component loading"""
    def __init__(self, parent_window):
        self.parent = parent_window
        self.load_queue = queue.Queue()
        self.is_loaded = False
        self.modules = {}
        self.on_complete_callback = None  # Add field for callback
        
        # Flags for tracking component loading
        self.components_loaded = {
            'camera': False,
            'mediapipe': False,
            'other_modules': False
        }
        
        # UI components
        self.loading_frame = None
        self.progress_bars = {}
        self.status_labels = {}
        
        # Loading results
        self.cap = None
        self.mp_face_mesh = None
        self.settings = None
        
        # Load settings for UI
        self.settings = Settings()
        self.default_font = self.settings.get(APP_FONT_KEY, APP_FONT)
        
        # Create loading UI
        self._create_loading_ui()
        
    def start_loading(self, on_complete_callback):
        """Starts the component loading process"""
        self.on_complete_callback = on_complete_callback  # Save callback
        
        # First load core modules and settings
        other_thread = threading.Thread(target=self._load_other_modules, daemon=True)
        other_thread.start()
        
        # Wait for settings to load
        while not self.components_loaded.get('other_modules', False):
            self.parent.update()
        
        # Then start other threads
        camera_thread = threading.Thread(target=self._load_camera, daemon=True)
        mediapipe_thread = threading.Thread(target=self._load_mediapipe, daemon=True)
        
        camera_thread.start()
        mediapipe_thread.start()
        
        # Start status checking
        self._check_loading_status()  

    def _load_camera(self):
        """Camera loading and initialization"""
        try:
            self.load_queue.put(("message", "Initializing camera..."))
            self.load_queue.put(("progress_update", "camera", 0.2))
            
            cv = importlib.import_module('cv2')
            self.modules['cv2'] = cv
            self.load_queue.put(("progress_update", "camera", 0.4))
            
            self.cap = cv.VideoCapture(DEFAULT_WEBCAM)
            if not self.cap.isOpened():
                raise Exception("Failed to connect to camera")
            self.load_queue.put(("progress_update", "camera", 0.6))
            
            # Set camera parameters
            self.cap.set(cv.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv.CAP_PROP_FPS, 30)
            self.load_queue.put(("progress_update", "camera", 0.8))
            
            self.components_loaded['camera'] = True
            self.load_queue.put(("progress_update", "camera", 1.0))
        except Exception as e:
            self.load_queue.put(("error", f"Camera initialization error: {str(e)}"))
    
    def _load_mediapipe(self):
        """Loading MediaPipe and initializing FaceMesh"""
        try:
            self.load_queue.put(("message", "Loading MediaPipe..."))
            self.load_queue.put(("progress_update", "mediapipe", 0.1))
            
            mp = importlib.import_module('mediapipe')
            self.modules['mediapipe'] = mp
            self.load_queue.put(("progress_update", "mediapipe", 0.4))
            
            self.mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=self.settings.get(MIN_DETECTION_CONFIDENCE_KEY, MIN_DETECTION_CONFIDENCE),
                min_tracking_confidence=self.settings.get(MIN_TRACKING_CONFIDENCE_KEY, MIN_TRACKING_CONFIDENCE),
            )
            self.load_queue.put(("progress_update", "mediapipe", 0.7))
            
            self.components_loaded['mediapipe'] = True
            self.load_queue.put(("progress_update", "mediapipe", 1.0))
        except Exception as e:
            self.load_queue.put(("error", f"MediaPipe initialization error: {str(e)}"))
    
    def _load_other_modules(self):
        """Loading other modules"""
        try:
            # Load settings
            self.load_queue.put(("message", "Loading settings..."))
            self.settings = Settings()
            self.load_queue.put(("progress_update", "other_modules", 0.2))
            
            # Load additional modules
            self.load_queue.put(("message", "Loading additional modules..."))
            self.modules['numpy'] = importlib.import_module('numpy')
            self.load_queue.put(("progress_update", "other_modules", 0.4))
            
            self.modules['PIL'] = importlib.import_module('PIL.Image')
            self.load_queue.put(("progress_update", "other_modules", 0.5))
            
            # Import local modules
            self.load_queue.put(("message", "Loading image processor..."))
            self.modules['image_processor'] = importlib.import_module('image_processor')
            self.load_queue.put(("progress_update", "other_modules", 0.7))
            
            self.components_loaded['other_modules'] = True
            self.load_queue.put(("progress_update", "other_modules", 1.0))

        except Exception as e:
            self.load_queue.put(("error", f"Module loading error: {str(e)}"))
    
    def _create_loading_ui(self):
        """Creates loading indicator UI"""
        # Central loading frame
        self.loading_frame = ctk.CTkFrame(self.parent, width=LOADING_WINDOW_WIDTH, height=LOADING_WINDOW_HEIGHT)
        self.loading_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.loading_frame.pack_propagate(False)  # Prevent frame size changes
        
        # Add inner padding
        content_frame = ctk.CTkFrame(self.loading_frame)
        content_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Add title
        title_label = ctk.CTkLabel(
            content_frame, 
            text="Loading Components",
            font=(self.default_font, 16, "bold")
        )
        title_label.pack(pady=(5, 10), padx=15)
        
        # Create frames for each component
        components = {
            'camera': 'Camera',
            'mediapipe': 'MediaPipe',
            'other_modules': 'Additional Modules'
        }
        
        for component_id, component_name in components.items():
            # Create component frame
            component_frame = ctk.CTkFrame(content_frame)
            component_frame.pack(fill='x', padx=15, pady=2)
            
            # Add component name label
            component_label = ctk.CTkLabel(
                component_frame, 
                text=component_name,
                anchor='w',
                font=(self.default_font, 12)
            )
            component_label.pack(side='left', padx=8, pady=4)
            
            # Add status
            status_label = ctk.CTkLabel(
                component_frame, 
                text="Waiting...",
                text_color='gray',
                anchor='e',
                font=(self.default_font, 11)
            )
            status_label.pack(side='right', padx=8, pady=4)
            self.status_labels[component_id] = status_label
            
            # Create progress bar
            progress_bar = ctk.CTkProgressBar(content_frame, width=340)
            progress_bar.pack(padx=15, pady=(0, 6))
            progress_bar.set(0)
            self.progress_bars[component_id] = progress_bar
        
    def _check_loading_status(self):
        """Checks background loading status"""
        try:
            while True:  # Process all messages in queue
                msg_type, *msg_data = self.load_queue.get_nowait()
                
                if msg_type == "progress_update":
                    component, value = msg_data
                    # Update progress of specific component
                    if component in self.progress_bars:
                        self.progress_bars[component].set(value)
                        if value >= 1.0:
                            self.status_labels[component].configure(
                                text="Done",
                                text_color='green'
                            )
                            self.progress_bars[component].lower()
                        else:
                            self.status_labels[component].configure(
                                text=f"{int(value * 100)}%",
                                text_color='gray'
                            )
                elif msg_type == "message":
                    # Update status of component related to message
                    for component_id, component_name in {
                        'camera': 'Camera',
                        'mediapipe': 'MediaPipe',
                        'other_modules': 'Additional Modules'
                    }.items():
                        if component_name.lower() in msg_data[0].lower():
                            self.status_labels[component_id].configure(text=msg_data[0])
                            break
                elif msg_type == "error":
                    messagebox.showerror("Error", msg_data[0])
                    self.parent.quit()
                    return
                
                # Check if all components are loaded
                if all(self.components_loaded.values()):
                    self.is_loaded = True
                    # Call the completion callback
                    self.on_complete_callback(
                        self.modules,
                        self.cap,
                        self.mp_face_mesh,
                        self.settings,
                    )
                    return
                
                self.load_queue.task_done()
                
        except queue.Empty:
            # If queue is empty, check again after 100ms
            if not self.is_loaded:
                self.parent.after(100, self._check_loading_status)
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            self.parent.quit()
