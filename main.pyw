# Standard library imports
import collections
import tkinter as tk
import traceback

# Third-party imports
import ctkchart
import customtkinter as ctk
from CTkColorPicker import AskColor

# Local imports
from src.app_types import Size
from src.component_loader import ComponentLoader
from src.config import (
    APP_TITLE, APP_FONT, APP_FONT_KEY, APP_FONT_SIZE,
    APP_GEOMETRY, APP_GEOMETRY_KEY,
    LOADING_WINDOW_WIDTH, LOADING_WINDOW_HEIGHT, LOADING_WINDOW_GEOMETRY,
    REFRESH_DELAY_MS,
    STRABISMUS_RANGE_MIN, STRABISMUS_RANGE_MAX,
    CHART_BUFFER_SIZE,
    MAIN_WINDOW_POSITION_KEY,
    THRESHOLD_KNOB_STEP, THRESHOLD_KNOB_STEP_PRECISE,
)
from src.main_model import MainModel
from src.overlay import OverlayWindow
from src.widgets.imageknobex import ImageKnobEx
from src.color_settings import ColorSettingsWindow
from src.app_state import AppState
from src.settings import Settings

# Configure matplotlib to use Agg backend which doesn't require GUI
import matplotlib
matplotlib.use('Agg')

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

        # Initialize attributes
        self.modules = None
        self.cap = None
        self.mp_face_mesh = None
        self.face_detected = False
        self.overlay = None
        self.chart = None
        self.chart_data = None
        self.chart_threshold_data = None
        self.chart_line = None
        self.chart_threshold_line = None
        self.threshold_knob = None
        # self.threshold_entry = None
        # self.opacity_slider = None
        self.app_geometry = None
        self.video_frame = None
        self.video_label = None
        self.threshold_inner_frame1 = None
        self.threshold_inner_frame2 = None
        self.threshold_entry = None
        # self.eye_distance_entry = None
        self.model = None

        # Application state initialization
        self.app_state = AppState()

        # Set appearance mode
        ctk.set_appearance_mode("Light" if self.app_state.light_theme.get() else "Dark")

        # Create component loader
        self.loader = ComponentLoader(self)

        # Start loading process
        self.loader.start_loading(self._on_components_loaded)

    def _on_components_loaded(self, modules, cap, mp_face_mesh):
        """Callback called after all components are loaded"""
        self.modules = modules
        self.cap = cap
        self.mp_face_mesh = mp_face_mesh

        self.app_state.threshold_value.trace_add("write", self._update_threshold_by_entry)

        # Create main model
        self.model = MainModel(self, modules, cap, mp_face_mesh, REFRESH_DELAY_MS)

        # Initialize window
        self._initialize_main_ui()

        # Create overlay
        self.overlay = OverlayWindow()
        self.overlay.set_color_hex(self.app_state.overlay_color.get())
        self.overlay.set_opacity(self.app_state.overlay_opacity.get())

        # Create main UI components
        self._create_main_ui()

        # Create chart
        self.chart_data = collections.deque(
            [0.] * CHART_BUFFER_SIZE,
            maxlen=CHART_BUFFER_SIZE
        )
        self.chart_threshold_data = collections.deque(
            [0.] * CHART_BUFFER_SIZE,
            maxlen=CHART_BUFFER_SIZE
        )

        # Create chart lines
        self.chart_line = ctkchart.CTkLine(
            master=self.chart,
            fill="enabled",
        )
        self.chart_threshold_line = ctkchart.CTkLine(
            master=self.chart,
            color="red",
        )

        # Set threshold knob value
        self.threshold_knob.set(self.app_state.threshold_value.get())

        # Start processing
        self.model.start()

        # Start checking for results
        self.check_results()

    def _initialize_main_ui(self):
        """Initialize main interface after loading"""
        # Set main window dimensions
        self.geometry(APP_GEOMETRY)

        # Get saved window position
        if MAIN_WINDOW_POSITION_KEY in Settings.all():
            window_position = Settings.get(MAIN_WINDOW_POSITION_KEY)
            if window_position:
                x, y = window_position
                self.geometry(f"+{x}+{y}")

    def _create_main_ui(self):
        """Create main application interface"""

        is_dark_mode = ctk.get_appearance_mode().lower() == "dark"

        app_font = Settings.get(APP_FONT_KEY, APP_FONT)
        app_font_small = (app_font, APP_FONT_SIZE)

        # Create video frame
        self.video_frame = ctk.CTkFrame(self)

        # Create video label
        self.video_label = ctk.CTkLabel(self.video_frame, text="")

        # Create threshold frame
        threshold_frame = ctk.CTkFrame(self)

        self.threshold_inner_frame1 = ctk.CTkFrame(
            master=threshold_frame,
            fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1 if is_dark_mode else 0],
        )

        chart_label = ctk.CTkLabel(
            self.threshold_inner_frame1,
            text="Eye Distance",
            font=app_font_small
        )

        self.eye_distance_entry = ctk.CTkEntry(
            self.threshold_inner_frame1,
            width=60,
            height=26,
            border_width=0,
            fg_color=ctk.ThemeManager.theme["CTk"]["fg_color"][1 if is_dark_mode else 0],
            text_color="#768df1", # Default color of CTkLine
            textvariable=self.app_state.eye_distance,
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

        self.threshold_inner_frame2 = ctk.CTkFrame(
            master=threshold_frame,
            fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1 if is_dark_mode else 0],
        )

        threshold_label = ctk.CTkLabel(
            self.threshold_inner_frame2,
            text="Alert Threshold",
            font=app_font_small
        )

        self.threshold_entry = ctk.CTkEntry(
            self.threshold_inner_frame2,
            width=60,
            height=26,
            border_width=0,
            fg_color=ctk.ThemeManager.theme["CTk"]["fg_color"][1 if is_dark_mode else 0],
            text_color="red",
            textvariable=self.app_state.threshold_value,
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
            variable=self.app_state.threshold_value,
            # command=self._update_threshold_by_knob
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

        self._create_options_tab(options_tab, app_font_small)
        self._create_more_tab(more_tab, app_font_small, is_dark_mode)

        # Pack controls
        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        self.video_label.pack(expand=True, fill=tk.BOTH)

        # Pack threshold controls
        threshold_frame.pack(fill='x', padx=5, pady=(5, 0))

        self.threshold_inner_frame1.pack(fill='x', padx=5, pady=5)
        self.threshold_inner_frame1.grid_columnconfigure((0, 1), weight=1)
        chart_label.grid(row=0, column=0, sticky='w')
        self.eye_distance_entry.grid(row=0, column=1, sticky='e')

        self.chart.pack(pady=0, padx=5, anchor="center")

        self.threshold_inner_frame2.pack(fill='x', padx=5, pady=5)
        self.threshold_inner_frame2.grid_columnconfigure((0, 1), weight=1)
        threshold_label.grid(row=0, column=0, sticky='w')
        self.threshold_entry.grid(row=0, column=1, sticky='e')

        self.threshold_knob.pack(pady=(0, 5), anchor="center")
        threshold_knob_label.pack(pady=(0, 10), anchor="center")

        # Pack misc controls
        misc_frame.pack(fill='x', padx=5, pady=5)

    def _create_options_tab(self, parent, font):

        # Create show camera switch
        show_camera_switch = ctk.CTkSwitch(
            master=parent,
            text="Camera Image",
            font=font,
            variable=self.app_state.show_camera,
        )

        # Create mirror effect switch
        mirror_effect_switch = ctk.CTkSwitch(
            master=parent,
            text="Mirror Effect",
            font=font,
            variable=self.app_state.mirror_effect,
        )

        theme_switch = ctk.CTkSwitch(
            master=parent,
            text="Light Theme",
            font=font,
            variable=self.app_state.light_theme,
            command=self._on_theme_toggle
        )

        # Grid controls in options_tab
        # parent.grid_rowconfigure(2, weight=1)  # Эта строка будет растягиваться

        show_camera_switch.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        mirror_effect_switch.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        theme_switch.grid(row=2, column=0, padx=5, pady=5, sticky="w")

    def _create_more_tab(self, parent, font, is_dark_mode):

        # Create controls container
        controls_frame = ctk.CTkFrame(parent)
        # controls_frame.grid_columnconfigure((0, 1), weight=1)
        # controls_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Create fullscreen alert frame
        fullscreen_alert_switch = ctk.CTkSwitch(
            master=controls_frame,
            text="Fullscreen Alert",
            font=font,
            variable=self.app_state.fullscreen_alert,
        )

        # Color controls
        overlay_color_label = ctk.CTkLabel(
            master=controls_frame,
            text="Color:",
            font=font,
        )

        overlay_color_entry = ctk.CTkEntry(
            master=controls_frame,
            width=60,
            height=26,
            border_width=0,
            fg_color=ctk.ThemeManager.theme["CTk"]["fg_color"][1 if is_dark_mode else 0],
            textvariable=self.app_state.overlay_color,
            font=font,
            justify=tk.CENTER
        )

        overlay_color_button = ctk.CTkButton(
            master=controls_frame,
            text="...",
            font=font,
            width=24,
            height=24,
            fg_color=self.app_state.overlay_color.get(),
            command=self._on_color_picker_click
        )

        # Opacity controls
        overlay_opacity_label = ctk.CTkLabel(
            master=controls_frame,
            text="Opacity:",
            font=font,
        )

        overlay_opacity_entry = ctk.CTkEntry(
            master=controls_frame,
            width=60,
            height=26,
            border_width=0,
            fg_color=ctk.ThemeManager.theme["CTk"]["fg_color"][1 if is_dark_mode else 0],
            textvariable=self.app_state.overlay_opacity,
            font=font,
            justify=tk.CENTER
        )

        overlay_opacity_slider = ctk.CTkSlider(
            master=controls_frame,
            from_=0,
            to=255,
            width=100,  # фиксированная ширина
            variable=self.app_state.overlay_opacity,
            command=self._on_opacity_change
        )

        color_settings_btn = ctk.CTkButton(
            parent,
            text="Color Settings",
            font=font,
            command=lambda: ColorSettingsWindow(self, self.model.image_processor).focus()
        )

        # Pack the container
        controls_frame.pack(fill="x", padx=0, pady=0)

        # Grid controls
        fullscreen_alert_switch.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        overlay_color_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        overlay_color_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        overlay_color_button.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        overlay_opacity_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        overlay_opacity_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        overlay_opacity_slider.grid(row=2, column=2, padx=5, pady=5, sticky="ew")

        # Bottom button
        color_settings_btn.pack(side="bottom", padx=5, pady=5)

    def update_video(self, results):
        """Update UI with processed results"""
        try:
            # Get required modules for display
            cv = self.modules['cv2']
            Image = self.modules['PIL']

            mesh_results = results['mesh_results']

            # Process results
            self.face_detected = bool(mesh_results.multi_face_landmarks)
            eye_distance_raw = results['normalized_eye_distance']
            self.app_state.eye_distance.set(self.format_eye_distance(eye_distance_raw))
            strabismus_detected = eye_distance_raw > results['threshold_value']

            # Show/hide overlay based on strabismus detection
            self.overlay.show(strabismus_detected and self.app_state.fullscreen_alert.get())

            # Calculate eye distance percentage
            eye_distance_percent = (
                (eye_distance_raw - STRABISMUS_RANGE_MIN) /
                (STRABISMUS_RANGE_MAX - STRABISMUS_RANGE_MIN)
            )

            # Create a line for the line chart
            self.chart_data.append(100 * eye_distance_percent)

            # Calculate and append threshold percentage
            threshold_percent = (
                (self.app_state.threshold_value.get() - STRABISMUS_RANGE_MIN) /
                (STRABISMUS_RANGE_MAX - STRABISMUS_RANGE_MIN)
            )
            self.chart_threshold_data.append(100 * threshold_percent)

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
            traceback.print_exc()

    def on_closing(self):
        """Clean up resources and handle window close"""

        # Hide main window first
        self.withdraw()

        # Stop processing thread
        if self.model:
            self.model.stop()

        # Close overlay window
        if self.overlay:
            self.overlay.close()

        # Release camera
        if self.cap:
            self.cap.release()

        # Destroy main window
        self.quit()

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
        Settings.set(APP_GEOMETRY_KEY, str(new_geometry))

    def _update_threshold_by_entry(self, *args):  # pylint: disable=unused-argument
        """Update threshold knob value from entry field.
        Args:
            *args: Variable arguments from StringVar trace callback (unused but required)
        """
        if self.threshold_knob:
            value = max(
                STRABISMUS_RANGE_MIN,
                min(
                    STRABISMUS_RANGE_MAX,
                    float(self.app_state.threshold_value.get())))
            self.threshold_knob.set(value)

    def _on_color_picker_click(self):
        """Handle color picker button click"""
        pick_color = AskColor(initial_color=self.overlay.get_color_hex())
        color = pick_color.get()
        if color:  # If color was selected (not cancelled)
            self.overlay.set_color_hex(color)
            # Update button color
            self.app_state.overlay_color.set(color)

    def _on_opacity_change(self, value):
        """Handle opacity slider change"""
        opacity = int(float(value))
        self.overlay.set_opacity(opacity)
        self.overlay.show()

    def _on_theme_toggle(self):
        """Handle theme change"""
        is_dark_mode = not self.app_state.light_theme.get()
        ctk.set_appearance_mode("Dark" if is_dark_mode else "Light")

        fg_color_ctk = ctk.ThemeManager.theme["CTk"]["fg_color"][1 if is_dark_mode else 0]
        fg_color_ctkframe = ctk.ThemeManager.theme["CTkFrame"]["fg_color"][1 if is_dark_mode else 0]

        self.threshold_inner_frame1.configure(fg_color=fg_color_ctkframe)
        self.eye_distance_entry.configure(fg_color=fg_color_ctk)
        self.chart.configure(
            axis_color=fg_color_ctk,
            bg_color=fg_color_ctk,
            fg_color=fg_color_ctk)
        self.threshold_inner_frame2.configure(fg_color=fg_color_ctkframe)
        self.threshold_entry.configure(fg_color=fg_color_ctk)

        self.threshold_knob.configure(
            scale_image="assets/knob4_scale.png" if is_dark_mode else "assets/knob4_scale_light.png",
            bg=fg_color_ctkframe)

    def check_results(self):
        """Check for processed results in main thread"""
        try:
            # Check for results and update UI
            results = self.model.get_next_result()
            if results is not None:
                self.update_video(results)

        except Exception as e:
            print(f"Error checking results: {e}")
            traceback.print_exc()

        finally:
            # Schedule next check
            self.after(REFRESH_DELAY_MS, self.check_results)

    @staticmethod
    def format_eye_distance(eye_distance):
        """Format eye distance for display"""
        if eye_distance is None:
            return "N/A"
        return f"{eye_distance:.3f}"

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
