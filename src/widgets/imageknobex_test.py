import tkinter as tk
import customtkinter as ctk
from .imageknobex import ImageKnobEx

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure main window
        self.title("Image Knob Test")
        self.geometry("800x600")

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Example of adding a widget
        self.label = ctk.CTkLabel(
            self.main_frame,
            text="Image Knob Test App",
            font=("Helvetica", 20)
        )
        self.label.pack(pady=20)

        self.threshold_knob = ImageKnobEx(
            self.main_frame,
            image="assets/knob4.png",
            scale_image="assets/knob4_scale.png",
            start=0.40,
            end=0.60,
            scroll_steps=0.005,
            scroll_steps_precise=0.001,
            start_angle=60, end_angle=-300,
            radius=160,
            text=None,
            command=self.update_threshold_by_knob
        )
        self.threshold_knob.pack(pady=(20, 0), anchor="center")

        self.threshold_mutex = False
        self.threshold_value = ctk.StringVar()
        self.threshold_value.trace_add("write", self.update_threshold_by_entry)

        self.threshold_entry = ctk.CTkEntry(
            self.main_frame,
            width=100,
            border_width=0,
            fg_color=ctk.ThemeManager.theme["CTk"]["fg_color"][1],
            textvariable=self.threshold_value,
            font=("Segoe UI", 16),
            justify=tk.CENTER,
        )
        self.threshold_entry.pack(pady=(0, 20), anchor="center")

        self.update_threshold_by_knob()

    def update_threshold_by_entry(self, *args): # pylint: disable=unused-argument
        try:
            self.threshold_mutex = True
            value = max(
                min(
                    float(self.threshold_value.get()),
                    self.threshold_knob.max),
                self.threshold_knob.start)
            self.threshold_knob.set(value)
        except ValueError:
            pass
        finally:
            self.threshold_mutex = False

    def update_threshold_by_knob(self):
        if not self.threshold_mutex:
            value =self.threshold_knob.get()
            self.threshold_value.set( f"{value:.3f}".lstrip('0'))

if __name__ == "__main__":
    app = App()
    app.mainloop()
