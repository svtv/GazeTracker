import matplotlib
matplotlib.use('Agg')  # Use Agg backend which doesn't require GUI

import collections
import ctkchart
import customtkinter as ctk
import tkinter as tk
import traceback

from settings_window import SettingsWindow
from app_types import Size
from component_loader import ComponentLoader
from config import *
from CTkColorPicker import *
from overlay import OverlayWindow
from widgets.imageknobex import ImageKnobEx

class App(ctk.CTk):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.resizable(False, False)
        
        # Set window title
        self.title(APP_TITLE)
        
        # Set loading window dimensions
        self.geometry(LOADING_WINDOW_GEOMETRY)
        # Minimum window dimensions
        self.minsize(LOADING_WINDOW_WIDTH, LOADING_WINDOW_HEIGHT)

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create component loader
        self.loader = ComponentLoader(self)
        
        # Start loading process        
        self.loader.start_loading(self._on_components_loaded)

    def _on_components_loaded(self, modules, cap, mp_face_mesh, settings):
        """Callback called after all components are loaded"""
        # Save loading results
        self.modules = modules
        self.cap = cap
        self.mp_face_mesh = mp_face_mesh
        self.settings = settings
        self.face_detected = False
        
        # Initialize main UI
        self._initialize_main_ui()

    def _initialize_main_ui(self):
        """Initialize main interface after loading"""
        # Set main window dimensions
        self.app_geometry = self.settings.get(APP_GEOMETRY_KEY, APP_GEOMETRY)
        
        # Restore window position if saved
        settings_pos = self.settings.get(MAIN_WINDOW_POSITION_KEY, None)
        if settings_pos:
            x, y = settings_pos
            width, height = map(int, self.app_geometry.split('x'))
            self.app_geometry = f"{width}x{height}+{x}+{y}"
            
        self.geometry(self.app_geometry)
        self.minsize(APP_MINSIZE_WIDTH, APP_MINSIZE_HEIGHT)
        
        # Set font
        ctk.ThemeManager.theme["CTkFont"]["family"] = self.settings.get(APP_FONT_KEY, APP_FONT)
        
        # Bind window resize handler
        self.bind('<Configure>', self._on_window_configure)
        
        # Create overlay
        self.overlay = OverlayWindow()
        self.overlay.set_color_hex(self.settings.get(OVERLAY_COLOR_KEY, OVERLAY_COLOR))
        self.overlay.set_opacity(self.settings.get(OVERLAY_OPACITY_KEY, OVERLAY_OPACITY))

        # Initialize variables
        self.eye_distance = ctk.StringVar()
        self.threshold_mutex = False
        self.threshold_value = ctk.DoubleVar(value=self.settings.get(STRABISMUS_THRESHOLD_KEY, STRABISMUS_THRESHOLD))
        self.threshold_value.trace_add("write", self._update_threshold_by_entry)  
        self.show_camera = ctk.BooleanVar(value=self.settings.get(SHOW_CAMERA_KEY, SHOW_CAMERA))
        self.mirror_effect = ctk.BooleanVar(value=self.settings.get(MIRROR_EFFECT_KEY, MIRROR_EFFECT_ENABLED))
        self.fullscreen_alert = ctk.BooleanVar(value=self.settings.get(FULLSCREEN_ALERT_KEY, FULLSCREEN_ALERT_ENABLED))
        self.overlay_color = ctk.StringVar(value=self.settings.get(OVERLAY_COLOR_KEY, OVERLAY_COLOR))
        self.overlay_opacity = ctk.IntVar(value=self.settings.get(OVERLAY_OPACITY_KEY, OVERLAY_OPACITY))

        # Create main UI
        self._create_main_ui()

        # Create line chart
        self.chart_line = ctkchart.CTkLine(
            master=self.chart,
            fill="enabled",
        )
        self.chart_threshold_line = ctkchart.CTkLine(
            master=self.chart,
            color="red",
        )

        # Update threshold value
        self.threshold_knob.set(self.threshold_value.get())
        self.chart_data = collections.deque([0.] * CHART_BUFFER_SIZE, maxlen=CHART_BUFFER_SIZE)
        self.chart_threshold_data = collections.deque([self.threshold_value.get()] * CHART_BUFFER_SIZE, maxlen=CHART_BUFFER_SIZE)
        
        # Start video update
        self.update_video()

    def _create_main_ui(self):
        """Create main application interface"""

        is_dark_mode = ctk.get_appearance_mode().lower() == "dark"

        app_font = self.settings.get(APP_FONT_KEY, APP_FONT)
        app_font_small = (app_font, APP_FONT_SIZE)

        # Create video frame
        self.video_frame = ctk.CTkFrame(self)
        
        # Create video label
        self.video_label = ctk.CTkLabel(self.video_frame, text="")
        
        # Create threshold frame
        threshold_frame = ctk.CTkFrame(self)

        threshold_inner_frame1 = ctk.CTkFrame(
            master=threshold_frame,
            fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1 if is_dark_mode else 0],
        )

        chart_label = ctk.CTkLabel(
            threshold_inner_frame1, 
            text="Eye Distance",
            font=app_font_small
        )

        self.eye_distance_entry = ctk.CTkEntry(
            threshold_inner_frame1, 
            width=60,
            height=20,
            border_width=0,
            fg_color=ctk.ThemeManager.theme["CTk"]["fg_color"][1 if is_dark_mode else 0],
            text_color="#768df1", # Default color of CTkLine
            textvariable=self.eye_distance,
            font=app_font_small,
            justify=tk.CENTER,
            state=ctk.DISABLED
        )

        # Create line chart widget
        self.chart = ctkchart.CTkLineChart(
            master=threshold_frame,
            width=200,
            height=60,
            axis_size=0,

            axis_color=ctk.ThemeManager.theme["CTk"]["fg_color"][1 if is_dark_mode else 0],
            bg_color=ctk.ThemeManager.theme["CTk"]["fg_color"][1 if is_dark_mode else 0],
            fg_color=ctk.ThemeManager.theme["CTk"]["fg_color"][1 if is_dark_mode else 0],

            x_axis_data="",
            x_axis_values=tuple([0] * CHART_BUFFER_SIZE),
            x_axis_label_count=0,
            x_axis_section_count=0,
            x_space=0,

            y_axis_data="",
            y_axis_values=(0, 100), # range from 0 to 100%
            y_axis_label_count=0,
            y_axis_section_count=0,
            y_space=0,
        )

        threshold_inner_frame2 = ctk.CTkFrame(
            master=threshold_frame,
            fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1 if is_dark_mode else 0],
        )

        threshold_label = ctk.CTkLabel(
            threshold_inner_frame2, 
            text="Alert Threshold",
            font=app_font_small
        )

        threshold_entry = ctk.CTkEntry(
            threshold_inner_frame2, 
            width=60,
            height=20,
            border_width=0,
            fg_color=ctk.ThemeManager.theme["CTk"]["fg_color"][1 if is_dark_mode else 0],
            text_color="red",
            textvariable=self.threshold_value,
            font=app_font_small,
            justify=tk.CENTER,
        )
        
        # Use mouse wheel to adjust Alert Threshold. Hold Ctrl for fine-tuning
        # Knob control
        self.threshold_knob = ImageKnobEx(
            threshold_frame, 
            image="assets/knob4.png",
            scale_image="assets/knob4_scale.png" if is_dark_mode else "assets/knob4_scale_light.png",
            start=STRABISMUS_RANGE_MIN,
            end=STRABISMUS_RANGE_MAX,
            scroll_steps=THRESHOLD_KNOB_STEP,
            scroll_steps_precise=THRESHOLD_KNOB_STEP_PRECISE,
            start_angle=60, end_angle=-300,
            radius=180,
            text=None,
            command=self._update_threshold_by_knob
        )
        
        threshold_knob_label = ctk.CTkLabel(
            threshold_frame, 
            text="Use mouse wheel to adjust\nAlert Threshold.\nHold Ctrl for fine-tuning",
            font=app_font_small,
            text_color=ctk.ThemeManager.theme["CTkButton"]["text_color_disabled"][1],
            wraplength=200,
        )
        
        # Create misc frame
        # misc_frame = ctk.CTkFrame(self)
        misc_frame = ctk.CTkTabview(self, width=200)
        options_tab = misc_frame.add("Options")
        more_tab = misc_frame.add("More")

        # Create show camera switch
        show_camera_switch = ctk.CTkSwitch(
            master=options_tab,
            text="Camera Image",
            variable=self.show_camera,
            command=self._on_show_camera_toggle
        )
        
        # Create mirror effect switch
        mirror_effect_switch = ctk.CTkSwitch(
            master=options_tab,
            text="Mirror Effect",
            variable=self.mirror_effect,
            command=self._on_mirror_toggle
        )

        # Create fullscreen alert switch
        fullscreen_alert_switch = ctk.CTkSwitch(
            master=more_tab,
            text="Fullscreen Alert",
            variable=self.fullscreen_alert,
            command=self._on_fullscreen_alert_toggle
        )
        fullscreen_alert_switch.pack(anchor='w', padx=10, pady=10)
        
        # Color controls
        color_frame = ctk.CTkFrame(more_tab)
        color_frame.pack(fill="x", pady=10)
        
        overlay_color_label = ctk.CTkLabel(
            master=color_frame,
            text="Color:",
            font=app_font_small,
        )
        overlay_color_label.pack(side="left", padx=10)
        
        overlay_color_entry = ctk.CTkEntry(
            master=color_frame,
            width=60,
            height=20,
            border_width=0,
            fg_color=ctk.ThemeManager.theme["CTk"]["fg_color"][1 if is_dark_mode else 0],
            textvariable=self.overlay_color,
            font=app_font_small,
            justify=tk.CENTER
        )
        overlay_color_entry.pack(side="left", padx=5)
        
        overlay_color_button = ctk.CTkButton(
            master=color_frame,
            text="...",
            width=20,
            height=20,
            fg_color=self.overlay_color.get(),
            command=self._on_color_picker_click
        )
        overlay_color_button.pack(side="left")
        
        # Opacity controls
        opacity_frame = ctk.CTkFrame(more_tab)
        opacity_frame.pack(fill="x", pady=10)
        
        overlay_opacity_label = ctk.CTkLabel(
            master=opacity_frame,
            text="Opacity:",
            font=app_font_small,
        )
        overlay_opacity_label.pack(side="left", padx=10)
        
        overlay_opacity_entry = ctk.CTkEntry(
            master=opacity_frame,
            width=60,
            height=20,
            border_width=0,
            fg_color=ctk.ThemeManager.theme["CTk"]["fg_color"][1 if is_dark_mode else 0],
            textvariable=self.overlay_opacity,
            font=app_font_small,
            justify=tk.CENTER
        )
        overlay_opacity_entry.pack(side="left", padx=5)
        
        overlay_opacity_slider = ctk.CTkSlider(
            master=opacity_frame,
            from_=0,
            to=255,
            variable=self.overlay_opacity,
            command=self._on_opacity_change,
            width=150
        )
        overlay_opacity_slider.pack(side="left")
        
        # Pack controls
        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        self.video_label.pack(expand=True, fill=tk.BOTH)
        
        # Pack threshold controls
        threshold_frame.pack(fill='x', padx=5, pady=(5, 0))
        
        threshold_inner_frame1.pack(fill='x', padx=5, pady=5)
        threshold_inner_frame1.grid_columnconfigure((0, 1), weight=1)
        chart_label.grid(row=0, column=0, sticky='w')
        self.eye_distance_entry.grid(row=0, column=1, sticky='e')

        self.chart.pack(pady=0, padx=5, anchor="center")

        threshold_inner_frame2.pack(fill='x', padx=5, pady=5)
        threshold_inner_frame2.grid_columnconfigure((0, 1), weight=1)
        threshold_label.grid(row=0, column=0, sticky='w')
        threshold_entry.grid(row=0, column=1, sticky='e')

        self.threshold_knob.pack(pady=(0, 5), anchor="center")
        threshold_knob_label.pack(pady=(0, 10), anchor="center")
        
        # Pack misc controls
        misc_frame.pack(fill='x', padx=5, pady=5)
        
        # Grid controls in options_tab
        show_camera_switch.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        mirror_effect_switch.grid(row=1, column=0, padx=5, pady=5, sticky="w")

    def update_video(self):
        """Update video in real-time"""
        try:
            # Get frame from camera
            ret, frame = self.cap.read()
            if not ret:
                raise Exception("Failed to get frame from camera")
            
            # Process frame
            cv = self.modules['cv2']
            np = self.modules['numpy']
            Image = self.modules['PIL']
            ImageProcessor = self.modules['image_processor'].ImageProcessor
            
            # Apply mirror effect if enabled
            if self.mirror_effect.get():
                frame = cv.flip(frame, 1)
            
            # Process frame using FaceMesh
            frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            mesh_results = self.mp_face_mesh.process(frame_rgb)
            
            # Process frame            
            results = ImageProcessor.process_face_mesh(
                self,
                frame,
                mesh_results,
            )

            # Process results
            self.face_detected = bool(mesh_results.multi_face_landmarks)
            eye_distance_raw = results['normalized_eye_distance']
            self.eye_distance.set(self.format_eye_distance(eye_distance_raw))
            strabismus_detected = eye_distance_raw  > self.threshold_value.get()
            self.overlay.show(strabismus_detected and self.fullscreen_alert.get())  # Show/hide overlay based on strabismus detection
            
            eye_distance_percent = (eye_distance_raw - STRABISMUS_RANGE_MIN) / (STRABISMUS_RANGE_MAX - STRABISMUS_RANGE_MIN)

            # Create a line for the line chart
            self.chart_data.append(100 * eye_distance_percent)
            self.chart_threshold_data.append(100 * (self.threshold_value.get() - STRABISMUS_RANGE_MIN) / (STRABISMUS_RANGE_MAX - STRABISMUS_RANGE_MIN))
            self.chart.show_data(line=self.chart_line, data=list(self.chart_data))
            self.chart.show_data(line=self.chart_threshold_line, data=list(self.chart_threshold_data))

            # Get processed frame            
            frame = results['frame']
            
            # Get video frame dimensions
            video_width = self.video_frame.winfo_width()
            video_height = self.video_frame.winfo_height()
            
            if video_width > 1 and video_height > 1:  # Check if dimensions are valid
                # Convert frame to PIL format
                image = Image.fromarray(cv.cvtColor(frame, cv.COLOR_BGR2RGB))
                
                # Resize image to match video frame dimensions
                image = image.resize((video_width, video_height))
                
                # Convert to CTk format
                ctk_image = ctk.CTkImage(image, size=(video_width, video_height))
                
                # Update video label
                self.video_label.configure(image=ctk_image)
                self.video_label.image = ctk_image

        except Exception as e:
            print(f"Error updating video: {e}")
            print(traceback.format_exc())

        finally:
            # Allow time for background tasks
            self.update_idletasks()
            # Schedule next video update
            self.after(REFRESH_DELAY_MS, self.update_video)
        
    def destroy(self):
        # Save window position before closing
        x = self.winfo_x()
        y = self.winfo_y()
        self.settings.set(MAIN_WINDOW_POSITION_KEY, (x, y))
        super().destroy()
        
    def on_closing(self):
        """Handle window close"""
        if hasattr(self, 'overlay') and self.overlay:
            self.overlay.close()
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
        self.quit()
        self.destroy()

    def _on_window_configure(self, event):
        """Save new window size when it changes"""
        # Check if event came from main window
        if event.widget is not self:
            return
            
        # Check if size actually changed
        new_geometry = Size(event.width, event.height)
        if new_geometry == self.app_geometry:
            return
            
        # Update saved size
        self.app_geometry = new_geometry
        # Save to settings
        self.settings.set(APP_GEOMETRY_KEY, str(new_geometry))
            
    def _update_threshold_by_entry(self, *args):
        try:
            self.threshold_mutex = True
            value = max(
                self.threshold_knob.start,
                min(
                    self.threshold_knob.max,
                    float(self.threshold_value.get())))
            self.threshold_knob.set(value)
            # Save value to settings
            self.settings.set(STRABISMUS_THRESHOLD_KEY, value)
        except ValueError:
            pass  
        finally:
            self.threshold_mutex = False

    def _update_threshold_by_knob(self):
        if not self.threshold_mutex:
            value = self.threshold_knob.get()
            self.threshold_value.set( self.format_eye_distance(value)) 

    def _on_show_camera_toggle(self):
        """Handle show image toggle"""
        # Save value to settings
        self.settings.set(SHOW_CAMERA_KEY, self.show_camera.get())

    def _on_mirror_toggle(self):
        """Handle mirror effect toggle"""
        # Save value to settings
        self.settings.set(MIRROR_EFFECT_KEY, self.mirror_effect.get() == 1)

    def _on_color_picker_click(self):
        """Handle color picker button click"""
        pick_color = AskColor(initial_color=self.overlay.get_color_hex())
        color = pick_color.get()
        if color:  # If color was selected (not cancelled)
            self.overlay.set_color_hex(color)
            # Update button color
            self.overlay_color.set(color)  
        
            # Save value to settings
            self.settings.set(OVERLAY_COLOR_KEY, color)

    def _on_fullscreen_alert_toggle(self):
        """Handle fullscreen alert toggle"""
        is_fullscreen_alert = self.fullscreen_alert.get() == 1
        # Update alert settings button state
        state = ctk.NORMAL if is_fullscreen_alert else ctk.DISABLED
        
        # Save value to settings
        self.settings.set(FULLSCREEN_ALERT_KEY, is_fullscreen_alert)

    def _on_opacity_change(self, value):
        """Handle opacity slider change"""
        opacity = int(float(value))
        self.overlay.set_opacity(opacity)
        self.overlay.show()
        
        # Save value to settings
        self.settings.set(OVERLAY_OPACITY_KEY, opacity)

    @staticmethod
    def format_eye_distance(eye_distance):
        return f"{eye_distance:.3f}".lstrip('0')

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
